# Installer candidate R15: selected-package messages

R15 limits duplicate-scope notices to package names selected for the relevant
host. Unrelated installed plugins remain in native inventory and retain all
existing protections; they are not mentioned in the selection flow. Selected
packages with multiple copies still receive the preservation notice and are
not updated without an eligible plan.

Candidate ZIP (local artifact; not included in the repository),
SHA-256 (local artifact; not included in the repository):
`3ddcc4c7ddc3e9222bb6ac6cd4f966bc42e712f65b84c0941b0a4a397a01a8fe`.

Six scoped-inventory tests passed, including an unrelated `skill-creator`
retained silently and a selected duplicate that still displays its warning.
Six Superpowers planning tests passed. Repeat build and bundled provenance
matched; the exact extracted bundle scanned with Gitleaks had zero findings.
No native install, update or model interaction ran in this batch. R14's other
behavior and R13's archive-source acceptance limits remain applicable.
