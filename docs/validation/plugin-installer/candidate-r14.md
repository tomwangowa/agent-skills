# Installer candidate R14: Superpowers selection label

R14 adds `(strongly recommended)` next to Superpowers in the installation
checkbox menu for Claude and Codex. It remains unchecked by default. The
separate removal menu is unchanged. Other installation and source rules are
carried forward from [R13](candidate-r13.md).

- R14 ZIP (local artifact; not included in the repository),
  SHA-256 (local artifact; not included in the repository):
  `ba682de256d176f4d7cf1de21d28488eac6292f6f4f336dcea57089f3c9d2963`.
- Keyboard and selection tests: 6 passed. Removal tests: 31 passed.
- The relocated bundle rendered the label and unchecked default for both
  Claude and Codex. Repeat build was byte-identical; all provenance hashes
  matched; extracted bundle Gitleaks scan had zero findings.
- No native host installation, model workflow, or Windows/Linux terminal was
  tested in this batch. The R13 archive-installation limits still apply.
