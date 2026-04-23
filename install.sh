#!/bin/bash
# paper-wiki installer
# Copies skill files to the appropriate platform skill directory.
set -euo pipefail

SKILL_NAME="paper-wiki"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$SCRIPT_DIR/paper-wiki"
PLATFORM="auto"
DRY_RUN=0
TARGET_DIR=""

SKILL_PACKAGE_ITEMS=(
  "SKILL.md"
  "INSTALL.md"
  "examples"
  "references"
  "scripts"
  "templates"
  "schema"
)

info()  { printf '\033[36m[info]\033[0m %s\n' "$1"; }
ok()    { printf '\033[32m[done]\033[0m %s\n' "$1"; }
warn()  { printf '\033[33m[warn]\033[0m %s\n' "$1"; }
err()   { printf '\033[31m[error]\033[0m %s\n' "$1" >&2; }

usage() {
  cat <<'EOF'
Usage:
  bash install.sh --platform <claude|codex|gemini|auto> [--dry-run]
  bash install.sh --platform claude --target-dir <path>
  bash install.sh --init-vault <vault-path>

Options:
  --platform       Target platform (claude, codex, gemini, auto). Default: auto.
  --dry-run        Print install plan without writing files.
  --target-dir     Override the skill installation directory.
  --init-vault     Initialize a new paper vault at the given path.
  -h, --help       Show this help.

Examples:
  # Install skill for Claude Code
  bash install.sh --platform claude

  # Install skill for Gemini / Antigravity
  bash install.sh --platform gemini

  # Initialize a vault
  bash install.sh --init-vault ~/Documents/my-papers
EOF
}

resolve_skill_root() {
  local platform="$1"
  case "$platform" in
    claude)
      echo "$HOME/.claude/skills"
      ;;
    codex)
      if [ -d "$HOME/.codex/skills" ]; then
        echo "$HOME/.codex/skills"
      elif [ -d "$HOME/.Codex/skills" ]; then
        echo "$HOME/.Codex/skills"
      else
        echo "$HOME/.codex/skills"
      fi
      ;;
    gemini)
      echo "$HOME/.gemini/skills"
      ;;
    *)
      err "Unknown platform: $platform"
      exit 1
      ;;
  esac
}

detect_platform() {
  local found=()
  if [ -d "$HOME/.claude" ] || [ -d "$HOME/.claude/skills" ]; then
    found+=("claude")
  fi
  if [ -d "$HOME/.codex" ] || [ -d "$HOME/.codex/skills" ] || [ -d "$HOME/.Codex" ]; then
    found+=("codex")
  fi
  if [ -d "$HOME/.gemini" ] || [ -d "$HOME/.gemini/skills" ]; then
    found+=("gemini")
  fi

  if [ "${#found[@]}" -eq 1 ]; then
    echo "${found[0]}"
  elif [ "${#found[@]}" -eq 0 ]; then
    err "No supported platform detected. Use --platform claude, --platform codex, or --platform gemini."
    exit 1
  else
    err "Multiple platforms detected: ${found[*]}. Use --platform to specify."
    exit 1
  fi
}

run_cmd() {
  if [ "$DRY_RUN" -eq 1 ]; then
    printf '[dry-run] %s\n' "$*"
    return 0
  fi
  "$@"
}

copy_item() {
  local src="$1" dst="$2"
  if [ "$DRY_RUN" -eq 1 ]; then
    printf '[dry-run] copy %s -> %s\n' "$src" "$dst"
    return 0
  fi
  rm -rf "$dst"
  cp -R "$src" "$dst"
}

install_skill_package() {
  local target="$1"
  local platform="$2"
  local skill_dir="$SKILL_DIR"

  if [ ! -d "$skill_dir" ]; then
    err "Skill package not found at: $skill_dir"
    exit 1
  fi

  for item in "${SKILL_PACKAGE_ITEMS[@]}"; do
    local src="$skill_dir/$item"
    local dst="$target/$item"
    if [ ! -e "$src" ]; then
      warn "$item: source not found, skipping"
      continue
    fi
    copy_item "$src" "$dst"
  done

  # Platform-specific: only Codex gets agents/
  if [ "$platform" = "codex" ]; then
    if [ -d "$skill_dir/agents" ]; then
      copy_item "$skill_dir/agents" "$target/agents"
    fi
  fi
}

init_vault() {
  local vault_path="$1"

  info "Initializing paper vault at: $vault_path"

  run_cmd mkdir -p "$vault_path"
  run_cmd mkdir -p "$vault_path/paper"
  run_cmd mkdir -p "$vault_path/paper/web_search"
  run_cmd mkdir -p "$vault_path/library/papers"
  run_cmd mkdir -p "$vault_path/library/reports/journal"
  run_cmd mkdir -p "$vault_path/library/reports/direction"
  run_cmd mkdir -p "$vault_path/library/reports/idea"
  run_cmd mkdir -p "$vault_path/library/reports/paper"
  run_cmd mkdir -p "$vault_path/library/reports/submission"
  run_cmd mkdir -p "$vault_path/library/reports/web"
  run_cmd mkdir -p "$vault_path/library/indexes"
  run_cmd mkdir -p "$vault_path/workspace/cache"
  run_cmd mkdir -p "$vault_path/workspace/manifests"
  run_cmd mkdir -p "$vault_path/workspace/logs"
  run_cmd mkdir -p "$vault_path/workspace/web-inbox/imported"
  run_cmd mkdir -p "$vault_path/templates/generic"
  run_cmd mkdir -p "$vault_path/templates/domains"
  run_cmd mkdir -p "$vault_path/schema"

  # Copy example config
  if [ ! -f "$vault_path/config.json" ]; then
    if [ -f "$SKILL_DIR/examples/config.example.json" ]; then
      run_cmd cp "$SKILL_DIR/examples/config.example.json" "$vault_path/config.json"
    else
      warn "config.example.json not found, skipping config.json creation"
    fi
  fi

  # Copy schemas
  if [ ! -f "$vault_path/schema/tag_taxonomy.json" ]; then
    run_cmd cp "$SKILL_DIR/schema/tag_taxonomy.json" "$vault_path/schema/tag_taxonomy.json"
  fi
  if [ ! -f "$vault_path/schema/keyword_rules.json" ]; then
    run_cmd cp "$SKILL_DIR/schema/keyword_rules.json" "$vault_path/schema/keyword_rules.json"
  fi
  if [ ! -f "$vault_path/schema/journal_aliases.json" ]; then
    run_cmd cp "$SKILL_DIR/schema/journal_aliases.example.json" "$vault_path/schema/journal_aliases.json"
  fi
  if [ ! -f "$vault_path/schema/paper_frontmatter.schema.md" ]; then
    run_cmd cp "$SKILL_DIR/schema/paper_frontmatter.schema.md" "$vault_path/schema/paper_frontmatter.schema.md"
  fi

  # Copy generic templates
  for tmpl in "$SKILL_DIR"/templates/generic/*.md; do
    local basename="$(basename "$tmpl")"
    if [ ! -f "$vault_path/templates/generic/$basename" ]; then
      run_cmd cp "$tmpl" "$vault_path/templates/generic/$basename"
    fi
  done

  # Copy scripts
  run_cmd mkdir -p "$vault_path/scripts"
  for script in "$SKILL_DIR"/scripts/*.py; do
    run_cmd cp "$script" "$vault_path/scripts/$(basename "$script")"
  done

  # Create paper-library.md
  if [ ! -f "$vault_path/paper-library.md" ]; then
    if [ "$DRY_RUN" -eq 1 ]; then
      printf '[dry-run] create %s\n' "$vault_path/paper-library.md"
    else
      cat > "$vault_path/paper-library.md" <<'LIBRARY'
# Paper Library

## Source Roots

<!-- Add your research directions here, e.g.: -->
<!-- - Battery: `paper/Battery` -->
<!-- - TimeSeries: `paper/TimeSeries` -->

## Journal Organization

<!-- AUTO:journal-organization:start -->
- Last rebuild: never
- Unsorted root-level files: 0
- Unknown journal files: 0
<!-- AUTO:journal-organization:end -->

## Dashboard

<!-- AUTO:dashboard:start -->
- Total papers: 0
<!-- AUTO:dashboard:end -->

## User Notes

Write manual notes here. Scripts must preserve this section.
LIBRARY
    fi
  fi

  ok "Vault initialized at: $vault_path"
  echo ""
  echo "Next steps:"
  echo "  1. Add your research directions: mkdir -p $vault_path/paper/YourDirection"
  echo "  2. Place paper Markdown files in the direction folders"
  echo "  3. Tell your agent: \"scan papers\" or \"organize by journal\""
}

# Parse arguments
INIT_VAULT=""

while [ $# -gt 0 ]; do
  case "$1" in
    --platform)
      [ $# -ge 2 ] || { err "--platform requires a value"; usage; exit 1; }
      PLATFORM="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --target-dir)
      [ $# -ge 2 ] || { err "--target-dir requires a value"; usage; exit 1; }
      TARGET_DIR="$2"
      shift 2
      ;;
    --init-vault)
      [ $# -ge 2 ] || { err "--init-vault requires a path"; usage; exit 1; }
      INIT_VAULT="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      err "Unknown option: $1"
      usage
      exit 1
      ;;
  esac
done

# Handle vault initialization
if [ -n "$INIT_VAULT" ]; then
  init_vault "$INIT_VAULT"
  exit 0
fi

# Resolve platform
if [ "$PLATFORM" = "auto" ]; then
  PLATFORM="$(detect_platform)"
fi

SKILL_ROOT="$(resolve_skill_root "$PLATFORM")"

if [ -n "$TARGET_DIR" ]; then
  TARGET_SKILL_DIR="$TARGET_DIR"
else
  TARGET_SKILL_DIR="$SKILL_ROOT/$SKILL_NAME"
fi

echo ""
echo "================================"
echo "  paper-wiki install"
echo "================================"
echo ""
echo "Platform:    $PLATFORM"
echo "Skill root:  $SKILL_ROOT"
echo "Target:      $TARGET_SKILL_DIR"
echo ""

run_cmd mkdir -p "$SKILL_ROOT"
run_cmd mkdir -p "$TARGET_SKILL_DIR"

# Use unified skill package from paper-wiki/
install_skill_package "$TARGET_SKILL_DIR" "$PLATFORM"

echo ""
ok "paper-wiki installed to: $TARGET_SKILL_DIR"
echo ""
echo "Platform-specific files:"
if [ "$PLATFORM" = "codex" ]; then
  echo "  - agents/openai.yaml included (Codex/OpenAI agent config)"
else
  echo "  - agents/ excluded (not needed for $PLATFORM)"
fi
echo ""
echo "Next steps:"
echo "  1. Initialize a vault:  bash install.sh --init-vault ~/Documents/my-papers"
echo "  2. Or tell your agent:  \"Initialize a paper vault at ~/Documents/my-papers\""
