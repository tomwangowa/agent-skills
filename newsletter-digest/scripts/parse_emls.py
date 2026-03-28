#!/usr/bin/env python3
"""Parse .eml files from a folder and output structured JSON.

Usage:
    python parse_emls.py <folder_path> [--recursive] [--output <path>]

Output JSON schema:
    {
        "folder": "/path/to/emls",
        "parsed_at": "2026-03-26T12:00:00",
        "total": 26,
        "failed": [],
        "emails": [
            {
                "file": "filename.eml",
                "sender": "Name <email@example.com>",
                "subject": "Subject line",
                "date": "2026-03-20",
                "body": "Cleaned plain text body..."
            }
        ]
    }
"""

import argparse
import email
import email.policy
import json
import re
import sys
from datetime import datetime
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path


class HTMLTextExtractor(HTMLParser):
    """Strip HTML tags and extract readable text."""

    # Tags whose entire content should be discarded
    SKIP_TAGS = {"script", "style", "head", "meta", "link", "noscript"}
    # Block-level tags that should insert a newline
    BLOCK_TAGS = {
        "p", "div", "br", "h1", "h2", "h3", "h4", "h5", "h6",
        "li", "tr", "blockquote", "section", "article", "header", "footer",
        "table", "thead", "tbody", "hr",
    }

    def __init__(self):
        super().__init__()
        self._pieces: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in self.SKIP_TAGS:
            self._skip_depth += 1
        if tag.lower() in self.BLOCK_TAGS and not self._skip_depth:
            self._pieces.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self.SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
        if tag.lower() in self.BLOCK_TAGS and not self._skip_depth:
            self._pieces.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            self._pieces.append(data)

    def get_text(self) -> str:
        return "".join(self._pieces)


def html_to_text(html: str) -> str:
    """Convert HTML to plain text."""
    extractor = HTMLTextExtractor()
    try:
        extractor.feed(html)
    except (AssertionError, UnicodeDecodeError):
        # Fallback: brute-force strip tags on malformed HTML
        return re.sub(r"<[^>]+>", " ", html)
    return extractor.get_text()


# Patterns to match and remove single lines containing unsubscribe/footer text
_UNSUBSCRIBE_PATTERNS = [
    re.compile(
        r"^.*unsubscribe.*$", re.IGNORECASE | re.MULTILINE
    ),
    re.compile(
        r"^.*opt[ -]?out.*$", re.IGNORECASE | re.MULTILINE
    ),
    re.compile(
        r"^.*email preferences.*$", re.IGNORECASE | re.MULTILINE
    ),
    re.compile(
        r"^.*manage.*subscription.*$", re.IGNORECASE | re.MULTILINE
    ),
    re.compile(
        r"^.*you (are |were )?receiving this.*$", re.IGNORECASE | re.MULTILINE
    ),
    re.compile(
        r"^.*sent to .+@.+\..+$", re.IGNORECASE | re.MULTILINE
    ),
    re.compile(
        r"^.*view (this |it )?in (your )?browser.*$", re.IGNORECASE | re.MULTILINE
    ),
]

# Lines to strip that are not article content (gateway warnings, forwarding notices)
# Note: these regexes are single-line only. If a gateway warning is line-wrapped
# by the email client, only the first line will be removed.
_NOISE_LINE_PATTERNS = [
    re.compile(
        r"^This message was sent from outside of .+?\."
        r"( Please do not click links or open attachments unless .+?\.)?",
        re.IGNORECASE | re.MULTILINE,
    ),
    re.compile(
        r"^You don't often get email from .+?\. Learn why this is important.*$",
        re.IGNORECASE | re.MULTILINE,
    ),
    re.compile(
        r"^.*forwarded this email\?.*$", re.IGNORECASE | re.MULTILINE
    ),
]

# Footer separator patterns
_FOOTER_SEPARATORS = re.compile(
    r"^[-=_]{3,}\s*$", re.MULTILINE
)


def clean_body(text: str, max_chars: int = 3000) -> str:
    """Remove signatures, footers, unsubscribe notices, and truncate."""
    # Strip gateway warnings, forwarding notices, and other non-content lines
    for pattern in _NOISE_LINE_PATTERNS:
        text = pattern.sub("", text)

    # Truncate at first footer separator (e.g. "---", "===", "___")
    parts = _FOOTER_SEPARATORS.split(text, maxsplit=1)
    text = parts[0]

    # Remove single lines containing unsubscribe/footer keywords
    for pattern in _UNSUBSCRIBE_PATTERNS:
        text = pattern.sub("", text)

    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Strip leading/trailing whitespace
    text = text.strip()

    # Truncate to max_chars (find a clean break point)
    if len(text) > max_chars:
        cut = text[:max_chars].rfind("\n\n")
        if cut < max_chars * 0.5:
            cut = text[:max_chars].rfind("\n")
        if cut < max_chars * 0.3:
            cut = max_chars
        text = text[:cut].rstrip() + "\n\n[...truncated]"

    return text


def extract_body(msg: email.message.EmailMessage) -> str:
    """Extract the best plain-text body from a MIME message."""
    # Try plain text first
    plain = msg.get_body(preferencelist=("plain",))
    if plain:
        content = plain.get_content()
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")
        return content

    # Fall back to HTML
    html_part = msg.get_body(preferencelist=("html",))
    if html_part:
        content = html_part.get_content()
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")
        return html_to_text(content)

    # Last resort: walk all parts
    for part in msg.walk():
        ct = part.get_content_type()
        if ct == "text/plain":
            content = part.get_content()
            if isinstance(content, bytes):
                content = content.decode("utf-8", errors="replace")
            return content
        if ct == "text/html":
            content = part.get_content()
            if isinstance(content, bytes):
                content = content.decode("utf-8", errors="replace")
            return html_to_text(content)

    return ""


def parse_date(msg: email.message.EmailMessage) -> str:
    """Extract and normalize the date to YYYY-MM-DD."""
    date_str = msg.get("Date", "")
    if not date_str:
        return ""
    try:
        dt = parsedate_to_datetime(date_str)
        return dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError, IndexError):
        return date_str


def parse_sender(msg: email.message.EmailMessage) -> str:
    """Extract sender as 'Name <email>' or just email."""
    raw = msg.get("From", "")
    # The email policy should already decode RFC2047 for us
    return str(raw).strip()


def parse_eml(filepath: Path, max_chars: int = 3000) -> dict:
    """Parse a single .eml file and return structured data."""
    with open(filepath, "rb") as f:
        msg = email.message_from_binary_file(f, policy=email.policy.default)

    raw_body = extract_body(msg)
    cleaned = clean_body(raw_body, max_chars)

    return {
        "file": filepath.name,
        "sender": parse_sender(msg),
        "subject": str(msg.get("Subject", "")),
        "date": parse_date(msg),
        "body": cleaned,
    }


def find_eml_files(folder: Path, recursive: bool = False) -> list[Path]:
    """Find all .eml files in folder, optionally recursive."""
    if recursive:
        return sorted(folder.rglob("*.eml"))
    return sorted(folder.glob("*.eml"))


def main():
    parser = argparse.ArgumentParser(
        description="Parse .eml files into structured JSON"
    )
    parser.add_argument("folder", help="Path to folder containing .eml files")
    parser.add_argument(
        "--recursive", "-r", action="store_true",
        help="Include subfolders"
    )
    parser.add_argument(
        "--output", "-o", default=None,
        help="Output file path (default: stdout)"
    )
    parser.add_argument(
        "--max-chars", type=int, default=3000,
        help="Max characters per email body (default: 3000)"
    )
    args = parser.parse_args()

    folder = Path(args.folder).expanduser().resolve()
    if not folder.is_dir():
        print(f"Error: {folder} is not a directory", file=sys.stderr)
        sys.exit(1)

    eml_files = find_eml_files(folder, args.recursive)
    if not eml_files:
        print(f"No .eml files found in {folder}", file=sys.stderr)
        sys.exit(1)

    emails = []
    failed = []

    for filepath in eml_files:
        try:
            data = parse_eml(filepath, max_chars=args.max_chars)
            emails.append(data)
        except Exception as e:
            failed.append({"file": filepath.name, "error": str(e)})

    result = {
        "folder": str(folder),
        "parsed_at": datetime.now().isoformat(timespec="seconds"),
        "total": len(eml_files),
        "parsed": len(emails),
        "failed": failed,
        "emails": emails,
    }

    output = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        out_path = Path(args.output).expanduser().resolve()
        out_path.write_text(output, encoding="utf-8")
        print(f"Written to {out_path}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
