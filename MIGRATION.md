# Skill Namespace Migration Plan

This document outlines the migration plan for renaming all skills to include the `tm-` namespace prefix.

## Table of Contents

- [Overview](#overview)
- [Migration Scope](#migration-scope)
- [Timeline](#timeline)
- [Pre-Migration Checklist](#pre-migration-checklist)
- [Migration Steps](#migration-steps)
- [Post-Migration Tasks](#post-migration-tasks)
- [Rollback Plan](#rollback-plan)
- [FAQ](#faq)

---

## Overview

### Purpose

Migrate all skills from legacy naming (e.g., `code-review-gemini`) to namespaced naming (e.g., `tm-code-review-gemini`) to:
- Prevent naming conflicts when sharing skills
- Establish clear ownership and organization
- Improve discoverability and maintainability
- Align with team-wide naming standards

### Namespace

**Selected namespace:** `tm-`
- Short and memorable
- Easy to type in CLI
- Represents the skill repository owner/team

### Migration Strategy

**Approach:** Rename with backward compatibility
- Rename all skill directories
- Update SKILL.md frontmatter
- Create symlinks for legacy names (temporary)
- Update all documentation
- 30-day grace period before removing symlinks

---

## Migration Scope

### Skills to Migrate

| # | Legacy Name | New Name | Status |
|---|-------------|----------|--------|
| 1 | `ui-design-analyzer` | `tm-ui-design-analyzer` | 🔄 Pending |
| 2 | `activity-logger` | `tm-activity-logger` | 🔄 Pending |
| 3 | `code-review-gemini` | `tm-code-review-gemini` | 🔄 Pending |
| 4 | `code-story-teller` | `tm-code-story-teller` | 🔄 Pending |
| 5 | `commit-msg-generator` | `tm-commit-msg-generator` | 🔄 Pending |
| 6 | `interactive-presentation-generator` | `tm-interactive-presentation-generator` | 🔄 Pending |
| 7 | `skill-auditor` | `tm-skill-auditor` | 🔄 Pending |
| 8 | `pr-review-assistant` | `tm-pr-review-assistant` | 🔄 Pending |
| 9 | `spec-generator` | `tm-spec-generator` | 🔄 Pending |
| 10 | `spec-review-assistant` | `tm-spec-review-assistant` | 🔄 Pending |
| 11 | `work-log-analyzer` | `tm-work-log-analyzer` | 🔄 Pending |

**Total:** 11 skills

### Files Affected

For each skill, the following files will be updated:

- **Skill directory**: Renamed with `tm-` prefix
- **SKILL.md**: Frontmatter updated with new metadata
- **Documentation**: All references updated
  - README.md
  - SKILLS_ROADMAP.md
  - Individual skill documentation
  - CLAUDE.md
- **Backward compatibility**: Symlinks created (temporary)

### External Dependencies

**None.** This is a local repository migration with no external dependencies.

---

## Timeline

### Phase 1: Preparation (Day 1)

- ✅ Create naming conventions document
- ✅ Create migration script
- ✅ Create migration plan document
- ⏳ Review and approve migration plan
- ⏳ Backup current state

### Phase 2: Migration Execution (Day 1-2)

- ⏳ Run migration script in dry-run mode
- ⏳ Review proposed changes
- ⏳ Execute migration script
- ⏳ Verify all skills migrated correctly
- ⏳ Test skill functionality

### Phase 3: Documentation Update (Day 2-3)

- ⏳ Update README.md
- ⏳ Update SKILLS_ROADMAP.md
- ⏳ Update CLAUDE.md
- ⏳ Update individual skill docs
- ⏳ Update examples and references

### Phase 4: Validation & Rollout (Day 3-4)

- ⏳ Run skill-auditor on all migrated skills
- ⏳ Test trigger phrases with Claude Code
- ⏳ Verify symlinks work correctly
- ⏳ Commit changes to repository
- ⏳ Update team documentation

### Phase 5: Grace Period (Day 5-34)

- ⏳ Monitor for issues
- ⏳ Gather feedback
- ⏳ Address any problems
- ⏳ Update documentation as needed

### Phase 6: Cleanup (Day 35+)

- ⏳ Remove legacy symlinks
- ⏳ Archive old documentation
- ⏳ Update MIGRATION.md with completion status
- ⏳ Celebrate! 🎉

---

## Pre-Migration Checklist

Before running the migration script, ensure:

- [ ] Reviewed and understood NAMING_CONVENTIONS.md
- [ ] Backed up the entire skills repository
  ```bash
  tar -czf skills_backup_$(date +%Y%m%d).tar.gz ~/.claude/skills/
  ```
- [ ] Committed all pending changes
  ```bash
  cd ~/.claude/skills
  git add .
  git commit -m "chore: pre-migration checkpoint"
  ```
- [ ] Closed all Claude Code sessions
- [ ] No skills are currently running
- [ ] Reviewed migration script: `scripts/migrate_skill_names.sh`
- [ ] Tested migration in dry-run mode
- [ ] Documented any custom configurations

---

## Migration Steps

### Step 1: Dry-Run Preview

**Preview changes without executing:**

```bash
cd ~/.claude/skills
./scripts/migrate_skill_names.sh --dry-run
```

**Review the output:**
- Check directory renames
- Verify frontmatter updates
- Confirm symlink creation
- Review migration log

### Step 2: Execute Migration

**Run the migration script:**

```bash
cd ~/.claude/skills
./scripts/migrate_skill_names.sh
```

**What happens:**
1. Backup created: `backup_YYYYMMDD_HHMMSS/`
2. Each skill directory renamed with `tm-` prefix
3. SKILL.md frontmatter updated with:
   - `id`: New skill name
   - `namespace`: `tm`
   - `domain`: Extracted from name
   - `action`: Extracted from name
   - `qualifier`: Extracted from name (if present)
   - `updated`: Current date
4. Symlinks created: `old-name -> tm-old-name`
5. Migration log generated: `migration_YYYYMMDD_HHMMSS.log`

### Step 3: Verify Migration

**Check that all skills migrated successfully:**

```bash
# List new skill directories
ls -la ~/.claude/skills/ | grep "^d" | grep "^tm-"

# Verify symlinks
ls -la ~/.claude/skills/ | grep "^l"

# Count migrated skills (should be 11)
ls -d ~/.claude/skills/tm-* | wc -l
```

**Test a skill:**

```bash
# Read a migrated SKILL.md
cat ~/.claude/skills/tm-code-review-gemini/SKILL.md

# Verify frontmatter includes new fields
grep -A5 "^---" ~/.claude/skills/tm-code-review-gemini/SKILL.md
```

### Step 4: Update Documentation

**Update all documentation references:**

See [Post-Migration Tasks](#post-migration-tasks) for detailed steps.

### Step 5: Test Functionality

**Test skills in Claude Code:**

1. Open Claude Code:
   ```bash
   claude
   ```

2. Test trigger phrases (should work with both old and new names):
   ```
   > review the staged files
   > use tm-code-review-gemini to analyze my code
   ```

3. Verify skill invocation:
   - Check that the skill executes correctly
   - Verify scripts run with correct paths
   - Confirm output is as expected

---

## Post-Migration Tasks

### Task 1: Update README.md

**Update skill listings with new names:**

```bash
# Before
| [code-review-gemini](./code-review-gemini/) | ... |

# After
| [tm-code-review-gemini](./tm-code-review-gemini/) | ... |
```

**Files to update:**
- Main skill tables
- Quick start examples
- Usage instructions
- Installation commands

### Task 2: Update SKILLS_ROADMAP.md

**Update all skill references:**

```bash
# Search for legacy names
grep -r "code-review-gemini" SKILLS_ROADMAP.md

# Replace with new names
# (Manual editing recommended)
```

### Task 3: Update CLAUDE.md

**Update repository instructions:**

```markdown
## Available Skills

### tm-code-review-gemini

Performs code review using the Gemini CLI.

**Trigger phrases:** ...
```

### Task 4: Update Individual Skill Documentation

**For each skill with additional documentation:**

```bash
# Example: Update README.md in skill directory
cd ~/.claude/skills/tm-code-review-gemini
vim README.md  # Update references to skill name
```

### Task 5: Update Examples and Tutorials

**Update any code examples:**

```bash
# Search for legacy references
grep -r "code-review-gemini" docs/

# Update examples in:
# - Tutorial documents
# - Example workflows
# - Screenshots/images (if any)
```

### Task 6: Run Quality Audits

**Audit migrated skills:**

```bash
# Use skill-auditor (if it's migrated to tm-skill-auditor)
# Or run manual checks

# Verify SKILL.md format
for skill in ~/.claude/skills/tm-*; do
    echo "Checking: $(basename $skill)"
    head -20 "$skill/SKILL.md"
    echo "---"
done
```

### Task 7: Commit Changes

**Create migration commit:**

```bash
cd ~/.claude/skills

git add .

git commit -m "$(cat <<'EOF'
feat: migrate skills to tm- namespace

Migrated all 11 skills to use the tm- namespace prefix for better
organization and team sharing.

Changes:
- Renamed all skill directories (e.g., code-review-gemini -> tm-code-review-gemini)
- Updated SKILL.md frontmatter with namespace metadata
- Created backward-compatible symlinks (30-day grace period)
- Updated all documentation and references
- Added NAMING_CONVENTIONS.md
- Added migration script and plan

Breaking changes:
- Skill directory names changed (symlinks provide backward compatibility)
- SKILL.md frontmatter structure updated

Migration log: migration_YYYYMMDD_HHMMSS.log
Backup: backup_YYYYMMDD_HHMMSS/

See NAMING_CONVENTIONS.md and MIGRATION.md for details.

Co-Authored-By: Claude Sonnet 4.5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Rollback Plan

### If Migration Fails

**Option 1: Restore from backup (safest)**

```bash
cd ~/.claude/skills

# Remove new directories
rm -rf tm-*

# Restore from backup
cp -r backup_YYYYMMDD_HHMMSS/* .

# Remove backup
rm -rf backup_YYYYMMDD_HHMMSS/
```

**Option 2: Revert individual skills**

```bash
# Remove new skill directory
rm -rf tm-skill-name

# The old directory is preserved via symlink
# Remove symlink if it was created
rm skill-name  # (if it's a symlink)

# Restore from backup
cp -r backup_YYYYMMDD_HHMMSS/skill-name .
```

**Option 3: Git revert**

```bash
cd ~/.claude/skills

# If changes were committed
git log --oneline -5
git revert <commit-hash>

# If changes were not committed
git restore .
git clean -fd
```

### Validation After Rollback

```bash
# Verify original structure
ls -la ~/.claude/skills/

# Test a skill
cat ~/.claude/skills/code-review-gemini/SKILL.md

# Confirm with Claude Code
claude
> review the staged files  # Should work
```

---

## FAQ

### Q1: Will my existing trigger phrases still work?

**Yes.** Symlinks provide backward compatibility. Both old and new names work:

```
> review the staged files                    ✅ Works
> use code-review-gemini                     ✅ Works (via symlink)
> use tm-code-review-gemini                  ✅ Works (new name)
```

### Q2: When will the symlinks be removed?

**After 30 days** (grace period). You'll be notified before removal.

To check symlinks:
```bash
ls -la ~/.claude/skills/ | grep "^l"
```

### Q3: What if I have custom skills not in the migration list?

**Manual migration required:**

1. Rename directory: `my-skill` → `tm-my-skill`
2. Update SKILL.md frontmatter (follow NAMING_CONVENTIONS.md)
3. Create symlink if needed: `ln -s tm-my-skill my-skill`

Or use the migration script with custom mapping:
```bash
# Edit scripts/migrate_skill_names.sh
# Add to SKILL_MAPPING array:
["my-skill"]="tm-my-skill"

# Run migration
./scripts/migrate_skill_names.sh
```

### Q4: Can I use a different namespace?

**Yes.** Use the `--namespace` option:

```bash
./scripts/migrate_skill_names.sh --namespace myteam
```

This will create skills like `myteam-code-review-gemini`.

### Q5: What if migration fails halfway?

**The script creates backups automatically.** Restore from backup:

```bash
# Check for backup
ls -d ~/.claude/skills/backup_*

# Restore
cd ~/.claude/skills
rm -rf tm-*
cp -r backup_YYYYMMDD_HHMMSS/* .
```

### Q6: Do I need to update my workflows?

**No immediate changes required** due to symlinks. However, **update references in documentation** to use new names:

```bash
# Old
> use code-review-gemini

# New (preferred)
> use tm-code-review-gemini
```

### Q7: How do I verify frontmatter was updated correctly?

**Check any SKILL.md file:**

```bash
head -20 ~/.claude/skills/tm-code-review-gemini/SKILL.md
```

**Should include:**
```yaml
---
name: "Code Review with Gemini"
id: tm-code-review-gemini
namespace: tm
domain: code
action: review
qualifier: gemini
version: "1.0.0"
updated: "2025-01-17"
---
```

### Q8: Can I run the migration multiple times?

**No.** After the first migration:
- Old directories are renamed
- Symlinks are created

Running again will fail because old directories no longer exist.

To re-migrate:
1. Restore from backup
2. Run migration script again

### Q9: What about skills in development?

**Commit or stash changes before migrating:**

```bash
cd ~/.claude/skills/my-wip-skill
git add .
git commit -m "wip: checkpoint before migration"

# Or stash
git stash
```

After migration, continue work in `tm-my-wip-skill/`.

### Q10: How do I create new skills after migration?

**Follow new naming conventions:**

```bash
# Create new skill directory
mkdir ~/.claude/skills/tm-my-new-skill

# Create SKILL.md with proper frontmatter
cat > ~/.claude/skills/tm-my-new-skill/SKILL.md << 'EOF'
---
name: "My New Skill"
id: tm-my-new-skill
description: "..."
version: "1.0.0"
namespace: tm
domain: <domain>
action: <action>
---

# My New Skill
...
EOF
```

See [NAMING_CONVENTIONS.md](./NAMING_CONVENTIONS.md) for full guidelines.

---

## Support and Questions

**Issues or questions?**

1. Check the [FAQ](#faq) above
2. Review [NAMING_CONVENTIONS.md](./NAMING_CONVENTIONS.md)
3. Check migration log: `migration_YYYYMMDD_HHMMSS.log`
4. Open an issue in the repository
5. Contact: Tom Wang

---

## Migration Status

**Current Status:** 🔄 **Planning**

**Last Updated:** 2025-01-17

**Completed Phases:**
- [x] Phase 1: Preparation
  - [x] Created NAMING_CONVENTIONS.md
  - [x] Created migration script
  - [x] Created MIGRATION.md
  - [ ] Migration plan approved
  - [ ] Backup created

**Pending Phases:**
- [ ] Phase 2: Migration Execution
- [ ] Phase 3: Documentation Update
- [ ] Phase 4: Validation & Rollout
- [ ] Phase 5: Grace Period (30 days)
- [ ] Phase 6: Cleanup

**Next Action:** Review and approve migration plan, then run dry-run migration.

---

## Changelog

| Date | Action | Notes |
|------|--------|-------|
| 2025-01-17 | Migration plan created | Initial version |
| | | |

---

**Maintainer:** Tom Wang
**Document Version:** 1.0.0
**Last Updated:** 2025-01-17
