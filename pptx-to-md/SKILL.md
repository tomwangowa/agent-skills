---
name: pptx-to-md
description: "Convert PPTX (PowerPoint) or other Office documents (DOCX, XLSX, PDF) to Markdown using the markitdown library. Use when the user wants to extract text content from a presentation or document into Markdown format, convert slides to readable notes, or batch-convert a folder of Office files. Triggers on requests like 'convert pptx to markdown', 'extract text from slides', 'turn this presentation into md', or any mention of markitdown."
compatibility: Requires Python with markitdown installed (uv or pip). Works on any OS.
allowed-tools: Bash Read Write Glob
---

# PPTX → Markdown Converter (markitdown)

Convert PowerPoint, Word, Excel, PDF, and other Office documents to Markdown using [Microsoft's markitdown](https://github.com/microsoft/markitdown).

## Supported Input Formats

| Format | Extensions |
|--------|-----------|
| PowerPoint | `.pptx` |
| Word | `.docx` |
| Excel | `.xlsx`, `.xls` |
| PDF | `.pdf` |
| HTML | `.html`, `.htm` |
| Images | `.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp` |

---

## Invocation

```
/pptx-to-md <file>             → convert single file, output alongside source
/pptx-to-md <file> -o <out>   → convert to specific output path
/pptx-to-md <dir>             → batch-convert all .pptx in directory
/pptx-to-md <file> --print    → print markdown to conversation (don't save)
```

---

## Step 1 — Resolve inputs

Parse the user's request to extract:
- **Source**: file path(s) or directory
- **Output**: explicit `-o` path, or derive from source (replace extension with `.md`)
- **Mode**: single file, batch directory, or print-only

If the user did not specify a file, ask:
> Which file or folder would you like to convert to Markdown?

---

## Step 2 — Check markitdown is available

Try ephemeral execution first — this requires no install:
```bash
uvx markitdown --version 2>/dev/null
```

If `uvx` succeeds, proceed to Step 3 using `uvx markitdown` for all conversions.

If `uvx` is unavailable, try system-installed versions:
```bash
python -m markitdown --version 2>/dev/null || markitdown --version 2>/dev/null
```

If none of the above work, **ask the user for permission before installing**:

> `markitdown` is not installed. Install it now?
> - `uv add 'markitdown[pptx,docx,xlsx,pdf]'` (adds to project dependencies)
> - `pip install 'markitdown[pptx,docx,xlsx,pdf]'` (user-level install)
>
> Which would you prefer, or skip?

Only run the install after the user confirms. Never auto-install without consent.

---

## Step 3 — Convert

### Single file

Derive the output path if not specified: replace the file extension with `.md`.

**Overwrite guard**: Before writing, check if the output file already exists. If it does, ask:
> Output file `<output_file.md>` already exists. Overwrite? (yes / no)

Only proceed if the user confirms, or if `-o` was explicitly provided with intent to overwrite.

```bash
uvx markitdown "<input_file>" -o "<output_file.md>"
```

**Examples:**
```bash
uvx markitdown "docs/slides/overview.pptx" -o "docs/slides/overview.md"
uvx markitdown "report.docx" -o "report.md"
```

### Batch directory

Find all `.pptx` files, using null-delimited output to handle filenames with spaces:

```bash
find "<dir>" -name "*.pptx" -print0 | while IFS= read -r -d '' f; do
  out="${f%.pptx}.md"
  if [ -f "$out" ]; then
    echo "Skipping (output exists): $f → $out"
    continue
  fi
  uvx markitdown "$f" -o "$out"
  echo "Converted: $f → $out"
done
```

Ask the user to confirm before batch-converting more than 5 files:

> Found **N** `.pptx` files in `<dir>`. Convert all of them?
> Output will be placed alongside each source file as `<name>.md`.
> Existing `.md` files with the same name will be skipped (use `--force` to overwrite).

### Print-only (no file saved)

```bash
uvx markitdown "<input_file>"
```

Print the Markdown output directly in the conversation. Truncate at 200 lines and note the total if longer.

---

## Step 4 — Verify output

After conversion, read the first 30 lines of the output file to confirm it looks reasonable:

```bash
head -30 "<output_file.md>"
```

Report to the user:
- Output file path
- Approximate line count (`wc -l <output_file.md>`)
- Any warnings printed by markitdown

---

## Step 5 — Report

Show the user a summary:

```
Converted: overview.pptx → docs/slides/overview.md
Lines: 142
```

For batch conversions, show a table:

| Source | Output | Lines |
|--------|--------|-------|
| slides/intro.pptx | slides/intro.md | 87 |
| slides/demo.pptx | slides/demo.md | 203 |

---

## Notes

- markitdown extracts **text content only** — images are noted as `[Image]` placeholders unless OCR is configured.
- Slide **speaker notes** are included in the output when present.
- For scanned PDFs or image-heavy PPTX, the output may be sparse (mostly `[Image]` placeholders). In that case, suggest the user explore markitdown's OCR options — check `uvx markitdown --help` or the [markitdown repo](https://github.com/microsoft/markitdown) for current plugin availability, as plugin names may change across versions.
- Output encoding is always UTF-8.
- Overwrite protection is enforced in Step 3 for both single-file and batch modes. The `--print` mode never writes files.
