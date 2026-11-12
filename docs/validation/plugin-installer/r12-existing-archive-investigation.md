# Existing official archive investigation

Date: 2026-11-12. This is investigation evidence, not acceptance or a completed fix.

The observed local `.gcs-sha` value identifies commit
`dceb15d50832e6adf380bedc26dde03d251324b9`. The Superpowers entry in the
[public Anthropic catalog at that commit](https://raw.githubusercontent.com/anthropics/claude-plugins-official/dceb15d50832e6adf380bedc26dde03d251324b9/.claude-plugin/marketplace.json)
was copied as structured data and compared locally with the matching installed
catalog entry. The complete entries are equal, including the pinned upstream
repository and commit `bb92a77741419a4ab5f06e711a283343f1ada0c3`. This is an
independent comparison of that entry, not of the full catalog or archive.

The local marketplace JSON SHA-256 is
`5f9301da52e2475036a921c7199a764a72d0f3661c83c189fb317bec97044cf2`.
It is an observation, not an independently sourced trusted hash. A request to
the GitHub tree API through the web tool returned an internal error; no tree or
whole-file comparison resulted. No repeated GitHub API call was made.

A suitable cold-start policy must define how to authenticate the catalog bytes
independently, bind the observed catalog and pinned selected entry into the
approved plan, reject any changes before installation, and verify the native
result and complete payload afterwards. Existing acceptance covers a Git
catalog; it cannot be silently extended to archive form. In particular, the
marker is local mutable data, and matching it to a public commit does not
establish that other archive files or native processing are trustworthy.

No native install, account access, model request, personal setting write,
acceptance record or candidate package was created during this investigation.
The message-only change from the preceding turn remains in the worktree and
does not allow this archive through the installation gate.

## Follow-up public-source comparisons

The user approved a single retry of the GitHub tree API. It returned a complete
non-truncated tree: official marketplace JSON blob
`3482b58b0502334f140975834731b9b6984ee98b` matched the independently computed
Git blob hash of the local file. This verifies the entire marketplace JSON at
that fixed commit, not the native archive lifecycle.

One separate public GitHub fixed-commit tarball was downloaded for file-by-file
comparison in memory. It contained 642 files. The local archive had 627 files
(excluding its `.gcs-sha` marker): 627 matching, zero changed, zero extra and
15 upstream-only files. No local files were deleted or changed. The comparison
printed counts but did not save the 15 names. Therefore their relationship to
the selected plugin is unknown; this run cannot justify ignoring them or
assert that the complete archive matches. Repeating this external download
requires new user approval under the session instructions.
