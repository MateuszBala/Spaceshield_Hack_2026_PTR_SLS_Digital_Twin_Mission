#!/usr/bin/env bash
set -euo pipefail

# dump_repo_structure.sh
# Generates a concise, architecture-oriented snapshot of repository structure
# into a single text file.
#
# Usage:
#   bash scripts/dev/dump_repo_structure.sh [output_path]
#
# Default output:
#   docs/architecture/REPO_STRUCTURE.txt
#
# Requirements:
#   - bash, find, sort, sed
#   - optional: git (for git-aware sections and .gitignore filtering)
#   - optional: tree (preferred for directory tree rendering)
#
# Notes:
#   - Can be run from any directory.
#   - Overwrites the output file.
#   - To force the find fallback even when tree is available, set:
#     DUMP_REPO_STRUCTURE_FORCE_FIND=1

usage() {
  cat <<'USAGE'
Usage:
  bash scripts/dev/dump_repo_structure.sh [output_path]

Examples:
  bash scripts/dev/dump_repo_structure.sh
  bash scripts/dev/dump_repo_structure.sh docs/architecture/REPO_STRUCTURE.txt
USAGE
}

log_info() {
  echo "[INFO] $*" >&2
}

log_warn() {
  echo "[WARN] $*" >&2
}

has_command() {
  command -v "$1" >/dev/null 2>&1
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -gt 1 ]]; then
  echo "[ERROR] Too many arguments." >&2
  usage
  exit 1
fi

is_git_repo=0
scan_root="$PWD"
git_branch="N/A"
git_head="N/A"

if has_command git; then
  if detected_root="$(git rev-parse --show-toplevel 2>/dev/null)"; then
    scan_root="$detected_root"
    is_git_repo=1

    git_branch="$(git -C "$scan_root" branch --show-current 2>/dev/null || true)"
    if [[ -z "$git_branch" ]]; then
      git_branch="DETACHED"
    fi

    git_head="$(git -C "$scan_root" rev-parse --short HEAD 2>/dev/null || true)"
    if [[ -z "$git_head" ]]; then
      git_head="N/A"
    fi
  else
    log_warn "Not inside a git repository. Git sections will be skipped."
  fi
else
  log_warn "git is not available. Git sections will be skipped."
fi

output_arg="${1:-docs/architecture/REPO_STRUCTURE.txt}"
if [[ "$output_arg" = /* ]]; then
  output_path="$output_arg"
else
  output_path="$scan_root/$output_arg"
fi

mkdir -p "$(dirname "$output_path")"

find_workspace_paths_raw() {
  find "$scan_root" \
    \( -name '.git' \
      -o -name 'node_modules' \
      -o -name '.venv' \
      -o -name 'venv' \
      -o -name '__pycache__' \
      -o -name '.mypy_cache' \
      -o -name '.pytest_cache' \
      -o -name '.ruff_cache' \
      -o -name 'dist' \
      -o -name 'build' \
      -o -name '*.egg-info' \
      -o -name '.next' \
      -o -name 'target' \
      -o -name 'coverage' \) -prune \
    -o -name '.DS_Store' -prune \
    -o -print
}

find_workspace_files_raw() {
  find "$scan_root" \
    \( -name '.git' \
      -o -name 'node_modules' \
      -o -name '.venv' \
      -o -name 'venv' \
      -o -name '__pycache__' \
      -o -name '.mypy_cache' \
      -o -name '.pytest_cache' \
      -o -name '.ruff_cache' \
      -o -name 'dist' \
      -o -name 'build' \
      -o -name '*.egg-info' \
      -o -name '.next' \
      -o -name 'target' \
      -o -name 'coverage' \) -prune \
    -o -name '.DS_Store' -prune \
    -o -type f -print
}

find_manifest_files_raw() {
  find "$scan_root" \
    \( -name '.git' \
      -o -name 'node_modules' \
      -o -name '.venv' \
      -o -name 'venv' \
      -o -name '__pycache__' \
      -o -name '.mypy_cache' \
      -o -name '.pytest_cache' \
      -o -name '.ruff_cache' \
      -o -name 'dist' \
      -o -name 'build' \
      -o -name '*.egg-info' \
      -o -name '.next' \
      -o -name 'target' \
      -o -name 'coverage' \) -prune \
    -o -name '.DS_Store' -prune \
    -o \( -name 'pyproject.toml' -o -name 'package.json' -o -name 'uv.lock' \) -print
}

absolute_to_relative_sorted() {
  while IFS= read -r absolute_path; do
    if [[ "$absolute_path" == "$scan_root" ]]; then
      printf '.\n'
    else
      printf '%s\n' "${absolute_path#"$scan_root"/}"
    fi
  done | sort
}

filter_gitignored_stream() {
  if [[ "$is_git_repo" -ne 1 ]]; then
    cat
    return
  fi

  while IFS= read -r relative_path; do
    if [[ -z "$relative_path" ]]; then
      continue
    fi

    if [[ "$relative_path" == "." ]]; then
      printf '.\n'
      continue
    fi

    if git -C "$scan_root" check-ignore -q -- "$relative_path"; then
      continue
    fi

    printf '%s\n' "$relative_path"
  done
}

render_tree_with_find() {
  printf '.\n'
  find_workspace_paths_raw \
    | absolute_to_relative_sorted \
    | filter_gitignored_stream \
    | while IFS= read -r relative_path; do
        if [[ "$relative_path" == "." ]]; then
          continue
        fi

        depth=0
        basename_part="$relative_path"
        while [[ "$basename_part" == */* ]]; do
          depth=$((depth + 1))
          basename_part="${basename_part#*/}"
        done

        indent="$(printf '%*s' $((depth * 2)) '')"
        suffix=""
        if [[ -d "$scan_root/$relative_path" ]]; then
          suffix="/"
        fi

        printf '%s%s%s\n' "$indent" "$basename_part" "$suffix"
      done
}

render_tree_with_tree() {
  ignore_pattern='.git|node_modules|.venv|venv|__pycache__|.mypy_cache|.pytest_cache|.ruff_cache|dist|build|*.egg-info|.next|target|coverage|.DS_Store'
  tree_args=(-a -n --noreport -I "$ignore_pattern")

  if tree --help 2>&1 | grep -q -- '--charset'; then
    tree_args+=(--charset=ascii)
  fi

  if [[ "$is_git_repo" -eq 1 ]]; then
    if tree --help 2>&1 | grep -q -- '--gitignore'; then
      tree_args+=(--gitignore)
    else
      log_warn "tree is installed, but --gitignore is unavailable. Using find fallback."
      return 1
    fi
  fi

  (
    cd "$scan_root"
    tree "${tree_args[@]}" .
  )
}

write_tree_section() {
  if [[ "${DUMP_REPO_STRUCTURE_FORCE_FIND:-0}" == "1" ]]; then
    log_info "Using find fallback for directory tree (forced by env var)."
    render_tree_with_find
    return
  fi

  if has_command tree; then
    if render_tree_with_tree; then
      log_info "Using tree for directory tree."
      return
    fi
  fi

  log_info "Using find fallback for directory tree."
  render_tree_with_find
}

find_manifest_files() {
  find_manifest_files_raw \
    | absolute_to_relative_sorted \
    | filter_gitignored_stream \
    | sort -u
}

write_git_tracked_files_section() {
  if [[ "$is_git_repo" -eq 1 ]]; then
    git -C "$scan_root" ls-files
  else
    echo "(skipped: not a git repository)"
  fi
}

write_untracked_files_section() {
  if [[ "$is_git_repo" -eq 1 ]]; then
    git -C "$scan_root" ls-files --others --exclude-standard
  else
    echo "(skipped: not a git repository)"
  fi
}

write_workspace_manifests_section() {
  manifest_paths="$(find_manifest_files || true)"

  if [[ -z "$manifest_paths" ]]; then
    echo "(none)"
    return
  fi

  echo "PATHS:"
  printf '%s\n' "$manifest_paths"
  echo

  while IFS= read -r relative_path; do
    if [[ -z "$relative_path" ]]; then
      continue
    fi

    case "$relative_path" in
      pyproject.toml|*/pyproject.toml|package.json|*/package.json)
        echo "--- BEGIN FILE: $relative_path ---"
        cat "$scan_root/$relative_path"
        echo "--- END FILE: $relative_path ---"
        echo
        ;;
      *)
        # uv.lock and others are listed by path only.
        ;;
    esac
  done <<< "$manifest_paths"
}

collect_stats_lines() {
  if [[ "$is_git_repo" -eq 1 ]]; then
    git -C "$scan_root" ls-files \
      | sed 's/.*\.//' \
      | sort \
      | uniq -c \
      | sort -rn \
      | sed -n '1,15p'
    return
  fi

  find_workspace_files_raw \
    | absolute_to_relative_sorted \
    | filter_gitignored_stream \
    | sed 's/.*\.//' \
    | sort \
    | uniq -c \
    | sort -rn \
    | sed -n '1,15p'
}

write_stats_section() {
  stats_lines="$(collect_stats_lines || true)"

  if [[ -n "$stats_lines" ]]; then
    printf '%s\n' "$stats_lines"
  else
    echo "(none)"
  fi
}

generated_utc="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

{
  echo "Generated (UTC): $generated_utc"
  echo "Git branch: $git_branch"
  echo "Git HEAD: $git_head"
  echo

  echo "=== DIRECTORY TREE ==="
  write_tree_section
  echo

  echo "=== GIT TRACKED FILES ==="
  write_git_tracked_files_section
  echo

  echo "=== UNTRACKED (not ignored) ==="
  write_untracked_files_section
  echo

  echo "=== WORKSPACE MANIFESTS ==="
  write_workspace_manifests_section
  echo

  echo "=== STATS ==="
  write_stats_section
} > "$output_path"

log_info "Repository structure dump written to: $output_path"