# Install paper-wiki Skill

## Overview

This skill supports multiple agent platforms. Platform-specific files are selected during installation.

## Target Paths

| Platform | Skill Directory |
|----------|-----------------|
| Claude Code | `$HOME/.claude/skills/paper-wiki` |
| Codex | `$HOME/.codex/skills/paper-wiki` |
| Gemini | `$HOME/.gemini/skills/paper-wiki` |

## Install Methods

### Option 1: Using install.sh

```bash
bash install.sh --platform claude
bash install.sh --platform codex
bash install.sh --platform gemini
```

### Option 2: Manual copy

```bash
# Claude Code
cp -R skills/paper-wiki ~/.claude/skills/paper-wiki

# Codex (includes agents/openai.yaml)
cp -R skills/paper-wiki ~/.codex/skills/paper-wiki

# Gemini
cp -R skills/paper-wiki ~/.gemini/skills/paper-wiki
```

## Platform-Specific Files

| File | Claude | Codex | Gemini |
|------|:------:|:-----:|:------:|
| SKILL.md | ✅ | ✅ | ✅ |
| references/ | ✅ | ✅ | ✅ |
| scripts/ | ✅ | ✅ | ✅ |
| templates/ | ✅ | ✅ | ✅ |
| schema/ | ✅ | ✅ | ✅ |
| agents/openai.yaml | ❌ | ✅ | ❌ |

## Verification

After installation, verify:

1. SKILL.md frontmatter contains only `name` and `description` (max 1024 chars)
2. Run from vault root; scripts read/write against current working directory

```bash
cd /path/to/your/vault
python -m py_compile ~/.claude/skills/paper-wiki/scripts/*.py
python ~/.claude/skills/paper-wiki/scripts/report_family.py --help
python ~/.claude/skills/paper-wiki/scripts/status_report.py --help
```

## Initialize a Vault

After installing the skill:

```bash
bash install.sh --init-vault ~/Documents/my-papers
```

Or tell your agent: "Initialize a paper vault at ~/Documents/my-papers"