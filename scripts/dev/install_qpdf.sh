#!/usr/bin/env bash
set -euo pipefail

# install_qpdf.sh
# Prints installation instructions for qpdf and can optionally install it.
#
# Usage:
#   bash scripts/dev/install_qpdf.sh
#   bash scripts/dev/install_qpdf.sh --auto
#
# Requirements:
#   - bash
#   - optional: sudo (for --auto on Linux when not root)

usage() {
  cat <<'USAGE'
Usage:
  bash scripts/dev/install_qpdf.sh [--auto]

Options:
  --auto     Try to install qpdf using detected package manager.
  -h, --help Show this help.
USAGE
}

log_info() {
  echo "[INFO] $*" >&2
}

log_warn() {
  echo "[WARN] $*" >&2
}

log_error() {
  echo "[ERROR] $*" >&2
}

has_command() {
  command -v "$1" >/dev/null 2>&1
}

run_as_root() {
  if [[ "$(id -u)" -eq 0 ]]; then
    "$@"
    return
  fi

  if has_command sudo; then
    sudo "$@"
    return
  fi

  log_error "This action requires root privileges. Run as root or install sudo."
  exit 1
}

detect_package_manager() {
  if has_command apt-get; then
    echo "apt"
    return
  fi

  if has_command dnf; then
    echo "dnf"
    return
  fi

  if has_command yum; then
    echo "yum"
    return
  fi

  if has_command pacman; then
    echo "pacman"
    return
  fi

  if has_command apk; then
    echo "apk"
    return
  fi

  if has_command zypper; then
    echo "zypper"
    return
  fi

  if has_command brew; then
    echo "brew"
    return
  fi

  echo "unknown"
}

print_instructions() {
  cat <<'EOF'
Install qpdf with one of the commands below:

Debian/Ubuntu:
  sudo apt-get update && sudo apt-get install -y qpdf

Fedora:
  sudo dnf install -y qpdf

RHEL/CentOS (with yum):
  sudo yum install -y qpdf

Arch Linux:
  sudo pacman -Sy --noconfirm qpdf

Alpine:
  sudo apk add --no-cache qpdf

openSUSE:
  sudo zypper --non-interactive install qpdf

macOS (Homebrew):
  brew install qpdf
EOF
}

auto_install() {
  local pm="$1"

  case "$pm" in
    apt)
      run_as_root apt-get update
      run_as_root apt-get install -y qpdf
      ;;
    dnf)
      run_as_root dnf install -y qpdf
      ;;
    yum)
      run_as_root yum install -y qpdf
      ;;
    pacman)
      run_as_root pacman -Sy --noconfirm qpdf
      ;;
    apk)
      run_as_root apk add --no-cache qpdf
      ;;
    zypper)
      run_as_root zypper --non-interactive install qpdf
      ;;
    brew)
      brew install qpdf
      ;;
    *)
      log_error "Could not detect a supported package manager for auto-install."
      print_instructions
      exit 1
      ;;
  esac
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -gt 1 ]]; then
  log_error "Too many arguments."
  usage
  exit 1
fi

if has_command qpdf; then
  qpdf_version="$(qpdf --version 2>/dev/null | head -n 1 || true)"
  if [[ -n "$qpdf_version" ]]; then
    log_info "qpdf is already installed: $qpdf_version"
  else
    log_info "qpdf is already installed."
  fi
  exit 0
fi

package_manager="$(detect_package_manager)"

if [[ "${1:-}" == "--auto" ]]; then
  log_info "Auto-install requested. Detected package manager: $package_manager"
  auto_install "$package_manager"

  if has_command qpdf; then
    log_info "qpdf installation finished successfully."
    exit 0
  fi

  log_error "Installation command finished, but qpdf is still not available in PATH."
  exit 1
fi

print_instructions

if [[ "$package_manager" != "unknown" ]]; then
  log_info "Detected package manager: $package_manager"
  log_info "Run this script with --auto to install qpdf automatically."
else
  log_warn "No supported package manager detected automatically."
fi