# PR Review Assistant

Review a GitHub pull request with the active runtime's native reviewer:

- Claude Code → `code-review-claude`
- Codex → `code-review-codex`

## Requirements

- [GitHub CLI](https://cli.github.com/) installed and authenticated
- A repository where the requested PR is accessible

## Usage

In Claude Code or Codex, ask for a PR review:

```text
Review PR #123
Help me review https://github.com/org/repo/pull/456
```

The skill fetches metadata and the diff with `gh`, then applies the active
runtime's native review workflow. It remains read-only until the user explicitly
asks to post a comment or review.

## Posting a Review

After reviewing the findings, use GitHub CLI only with explicit approval:

```bash
gh pr comment 123 --body-file /tmp/pr_review_result.txt
gh pr review 123 --request-changes --body-file /tmp/pr_review_result.txt
gh pr review 123 --approve --body-file /tmp/pr_review_result.txt
```

## Gemini Retirement

Gemini PR review is retired. `scripts/review_pr.sh` exits without reading or
sending a PR diff. Future external reviewers need an explicit model choice and
approval of the exact diff or data scope.
