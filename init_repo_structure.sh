#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  bash init_repo_structure.sh package-name

Example:
  bash init_repo_structure.sh mission_core
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -ne 1 ]]; then
  echo "[ERROR] Provide exactly one argument: package name." >&2
  usage
  exit 1
fi

raw_package_name="$1"

if [[ ! "$raw_package_name" =~ ^[A-Za-z_][A-Za-z0-9_-]*$ ]]; then
  echo "[ERROR] Invalid package name: '$raw_package_name'" >&2
  echo "Allowed: letters, digits, '_' and '-'; must start with a letter or '_'" >&2
  exit 1
fi

# Python package directory cannot contain '-', so normalize if needed.
package_name="${raw_package_name//-/_}"
if [[ "$package_name" != "$raw_package_name" ]]; then
  echo "[INFO] Normalized package dir for Python: '$raw_package_name' -> '$package_name'"
fi

created_count=0
skipped_count=0

create_dir() {
  local dir_path="$1"
  mkdir -p "$dir_path"
}

touch_file_if_missing() {
  local file_path="$1"

  if [[ -e "$file_path" ]]; then
    echo "[SKIP] Exists: $file_path (no overwrite)"
    skipped_count=$((skipped_count + 1))
    return
  fi

  mkdir -p "$(dirname "$file_path")"
  : > "$file_path"
  created_count=$((created_count + 1))
  echo "[OK] Created: $file_path"
}

create_text_file_if_missing() {
  local file_path="$1"

  if [[ -e "$file_path" ]]; then
    echo "[SKIP] Exists: $file_path (no overwrite)"
    skipped_count=$((skipped_count + 1))
    cat > /dev/null
    return
  fi

  mkdir -p "$(dirname "$file_path")"
  cat > "$file_path"
  created_count=$((created_count + 1))
  echo "[OK] Created: $file_path"
}

create_script_file_if_missing() {
  local file_path="$1"

  if [[ -e "$file_path" ]]; then
    echo "[SKIP] Exists: $file_path (no overwrite)"
    skipped_count=$((skipped_count + 1))
    cat > /dev/null
    return
  fi

  mkdir -p "$(dirname "$file_path")"
  cat > "$file_path"
  chmod +x "$file_path"
  created_count=$((created_count + 1))
  echo "[OK] Created +x: $file_path"
}

DIRS=(
  ".claude/agents"
  ".claude/commands"
  ".github"
  "configs"
  "docker"
  "docs/api"
  "docs/architecture"
  "docs/decisions"
  "docs/development"
  "docs/goal"
  "docs/rules"
  "docs/runbooks"
  "docs/version"
  "grafana"
  "migrations"
  "protos"
  "runtime-configs"
  "scripts/bootstrap"
  "scripts/dev"
  "scripts/ops"
  "scripts/proto"
  "scripts/systemd"
  "src"
  "src/$package_name"
  "tests"
  "tests/integration"
  "tests/soak"
  "tests/unit"
)

for dir_path in "${DIRS[@]}"; do
  create_dir "$dir_path"
done

EMPTY_FILES=(
  "configs/.gitkeep"
  "docker/.gitkeep"
  "docs/api/.gitkeep"
  "docs/architecture/.gitkeep"
  "docs/decisions/.gitkeep"
  "docs/development/.gitkeep"
  "docs/runbooks/.gitkeep"
  "grafana/.gitkeep"
  "migrations/.gitkeep"
  "protos/.gitkeep"
  "runtime-configs/.gitkeep"
  "scripts/dev/.gitkeep"
  "scripts/ops/.gitkeep"
  "scripts/proto/.gitkeep"
  "scripts/systemd/.gitkeep"
  "src/$package_name/__init__.py"
  "tests/.gitkeep"
  "tests/integration/__init__.py"
  "tests/soak/__init__.py"
  "tests/unit/__init__.py"
)

for file_path in "${EMPTY_FILES[@]}"; do
  touch_file_if_missing "$file_path"
done

create_text_file_if_missing ".claude/CLAUDE.md" <<'EOF'
# Claude Notes
EOF

create_text_file_if_missing ".claude/settings.json" <<'EOF'
{}
EOF

create_text_file_if_missing ".claude/settings.local.json" <<'EOF'
{}
EOF

create_text_file_if_missing ".gitignore" <<'EOF'
__pycache__/
*.py[cod]
*.egg-info/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.venv/
venv/
.env
EOF

create_text_file_if_missing ".github/copilot-instructions.md" <<'EOF'
# Copilot Instructions
EOF

create_script_file_if_missing ".github/get_review.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

echo "TODO: add repository review helper logic"
EOF

create_text_file_if_missing ".github/PULL_REQUEST_TEMPLATE.md" <<'EOF'
## Summary

## Changes

## Test Plan
EOF

create_text_file_if_missing "docs/goal/CONCEPT.md" <<'EOF'
# Concept
EOF

create_text_file_if_missing "docs/goal/ROADMAP.md" <<'EOF'
# Roadmap
EOF

create_text_file_if_missing "docs/goal/PROGRESS.md" <<'EOF'
# Progress
EOF

create_text_file_if_missing "docs/rules/COMMIT_CONVENTIONS.md" <<'EOF'
# Commit Conventions
EOF

create_text_file_if_missing "docs/version/VERSION.md" <<'EOF'
# Version
EOF

create_text_file_if_missing "docs/version/CHANGELOG.md" <<'EOF'
# Changelog
EOF

create_text_file_if_missing "scripts/bootstrap/ENVIRONMENT_SETUP.md" <<'EOF'
# Environment Setup
EOF

create_script_file_if_missing "scripts/bootstrap/init_environment.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

echo "TODO: add environment initialization steps"
EOF

create_text_file_if_missing "src/CLAUDE.md" <<'EOF'
# Source Notes
EOF

create_text_file_if_missing "CLAUDE.md" <<'EOF'
# Repository Notes
EOF

create_text_file_if_missing "README.md" <<'EOF'
# Project
EOF

create_text_file_if_missing "Makefile" <<'EOF'
.PHONY: test

test:
	@echo "TODO: add test command"
EOF

create_text_file_if_missing "pyproject.toml" <<'EOF'
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "replace-me"
version = "0.1.0"
description = ""
requires-python = ">=3.11"
EOF

echo
echo "Done."
echo "Created files: $created_count"
echo "Skipped existing files: $skipped_count"
