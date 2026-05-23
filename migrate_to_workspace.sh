#!/usr/bin/env bash
#
# migrate_to_workspace.sh
# -----------------------------------------------------------------------------
# Migruje repozytorium z układu pojedynczego pakietu (src/digital_twin/)
# do monorepo opartego na uv workspace z czterema członami Python:
#
#   packages/contracts/        (dt_contracts)  - schematy Pydantic [PIERWSZY]
#   packages/physics-engine/   (dt_physics)    - czysta numeryka
#   packages/api/              (dt_api)        - FastAPI, skorupa HTTP
#   packages/ai/              (dt_ai)         - Monte Carlo / optymalizacja
#
# oraz frontend/ (React/TS, POZA uv workspace).
#
# Root pyproject.toml staje się "virtual workspace" (bez [project], tylko
# [tool.uv.workspace]). Testy jednostkowe trafiają DO pakietów; integration/
# i soak/ zostają w root (cross-package).
#
# Zachowuje historię gita (git mv). Idempotentny. Domyślnie DRY-RUN.
#
# Uzycie:
#   ./migrate_to_workspace.sh            # dry-run: tylko pokazuje plan
#   ./migrate_to_workspace.sh --apply    # wykonuje migracje
#
# Wymaga: git, bash. Nie instaluje niczego, nie commituje, nie uruchamia uv.
# -----------------------------------------------------------------------------
set -euo pipefail

# ---- tryb ----
APPLY=0
if [[ "${1:-}" == "--apply" ]]; then APPLY=1; fi

# ---- kolory (tylko na stderr) ----
if [[ -t 2 ]]; then
  C_INFO=$'\033[36m'; C_OK=$'\033[32m'; C_WARN=$'\033[33m'; C_OFF=$'\033[0m'
else
  C_INFO=''; C_OK=''; C_WARN=''; C_OFF=''
fi
log()  { printf '%s%s%s\n' "$C_INFO" "$*" "$C_OFF" >&2; }
ok()   { printf '%s%s%s\n' "$C_OK"   "$*" "$C_OFF" >&2; }
warn() { printf '%s%s%s\n' "$C_WARN" "$*" "$C_OFF" >&2; }

# ---- ustal root repo ----
if ! command -v git >/dev/null 2>&1; then
  echo "BLAD: git nie jest zainstalowany." >&2; exit 1
fi
if ! ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"; then
  echo "BLAD: to nie jest repozytorium git." >&2; exit 1
fi
cd "$ROOT"

if [[ $APPLY -eq 0 ]]; then
  warn "=== TRYB DRY-RUN (nic nie zostanie zmienione). Uzyj --apply aby wykonac. ==="
else
  log "=== TRYB APPLY: wykonuje migracje w $ROOT ==="
fi

# ---- pomocnicze: wykonaj-lub-pokaz ----
run() {
  if [[ $APPLY -eq 1 ]]; then
    "$@"
  else
    printf '  + %s\n' "$*" >&2
  fi
}

# git mv jesli plik sledzony, zwykle mv jesli nie; pomija gdy cel istnieje
move() {
  local src="$1" dst="$2"
  if [[ ! -e "$src" ]]; then
    warn "  pomijam (brak zrodla): $src"
    return 0
  fi
  if [[ -e "$dst" ]]; then
    warn "  pomijam (cel istnieje): $dst"
    return 0
  fi
  run mkdir -p "$(dirname "$dst")"
  if git ls-files --error-unmatch "$src" >/dev/null 2>&1; then
    run git mv "$src" "$dst"
  else
    run mv "$src" "$dst"
  fi
}

# tworzy plik tylko jesli nie istnieje (idempotencja)
write_if_absent() {
  local path="$1"; shift
  if [[ -e "$path" ]]; then
    warn "  pomijam (istnieje): $path"
    return 0
  fi
  if [[ $APPLY -eq 1 ]]; then
    mkdir -p "$(dirname "$path")"
    cat > "$path"
  else
    printf '  + utworz plik: %s\n' "$path" >&2
    cat >/dev/null   # zjedz stdin w dry-run
  fi
}

# ---- definicje czlonow: katalog | nazwa-importu | opis ----
PKgs=(
  "contracts|dt_contracts|Wspoldzielone schematy danych (Pydantic)."
  "physics-engine|dt_physics|Silnik fizyczny - czysta numeryka (NumPy/SciPy)."
  "api|dt_api|Backend HTTP (FastAPI) serwujacy dane do frontendu."
  "ai|dt_ai|Backend AI - Monte Carlo i optymalizacja parametrow."
)

# =============================================================================
log ""
log "[1/5] Tworze szkielet packages/ dla czlonow uv workspace"
for entry in "${PKgs[@]}"; do
  IFS='|' read -r dir imp desc <<< "$entry"
  pkg="packages/$dir"
  run mkdir -p "$pkg/src/$imp"
  run mkdir -p "$pkg/tests"

  # __init__.py czlonu
  printf '"""%s"""\n' "$desc" | write_if_absent "$pkg/src/$imp/__init__.py"

  # pyproject.toml czlonu
  write_if_absent "$pkg/pyproject.toml" <<EOF
[project]
name = "$dir"
version = "0.1.0"
description = "$desc"
requires-python = ">=3.12"
dependencies = []

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/$imp"]
EOF

  # placeholder testu jednostkowego przy pakiecie
  printf '' | write_if_absent "$pkg/tests/__init__.py"
done

# =============================================================================
log ""
log "[2/5] Przenosze istniejacy src/digital_twin/ do packages/physics-engine/"
# Zakladamy, ze obecny pojedynczy pakiet to zalazek silnika fizycznego.
# Przenosimy ZAWARTOSC, nie sam katalog (nazwa importu sie zmienia na dt_physics).
if [[ -d src/digital_twin ]]; then
  shopt -s nullglob dotglob
  moved_any=0
  for item in src/digital_twin/*; do
    base="$(basename "$item")"
    # __init__.py celu juz utworzylismy - nie nadpisujemy
    if [[ "$base" == "__init__.py" ]]; then
      warn "  zostawiam stary src/digital_twin/__init__.py (cel ma juz wlasny)"
      continue
    fi
    move "$item" "packages/physics-engine/src/dt_physics/$base"
    moved_any=1
  done
  shopt -u nullglob dotglob
  [[ $moved_any -eq 0 ]] && warn "  src/digital_twin/ nie mial zawartosci poza __init__.py"
else
  warn "  brak src/digital_twin/ - pomijam (moze juz zmigrowane)"
fi

# =============================================================================
log ""
log "[3/5] Przenosze testy jednostkowe do pakietow, zostawiam integration/ i soak/ w root"
# Konwencja: testy jednostkowe silnika ida do packages/physics-engine/tests/.
# Jesli w tests/unit sa juz pliki testowe, przenosimy je tam; reszta zostaje.
if [[ -d tests/unit ]]; then
  shopt -s nullglob
  for t in tests/unit/test_*.py; do
    move "$t" "packages/physics-engine/tests/$(basename "$t")"
  done
  shopt -u nullglob
  warn "  (integration/ i soak/ celowo pozostaja w root jako cross-package)"
else
  warn "  brak tests/unit/ - pomijam"
fi

# =============================================================================
log ""
log "[4/5] Przeksztalcam root pyproject.toml w virtual workspace"
# Tworzymy kopie zapasowa i zapisujemy nowy root manifest (tylko jesli rozny).
if [[ -f pyproject.toml ]]; then
  NEW_ROOT_PYPROJECT="$(cat <<'EOF'
# Virtual workspace root - bez [project], tylko organizacja czlonow.
# Patrz: docs/architecture/ARCHITECTURE_DECISIONS.md
[tool.uv.workspace]
members = ["packages/*"]

[tool.uv.sources]
contracts      = { workspace = true }
physics-engine = { workspace = true }
api            = { workspace = true }
ai             = { workspace = true }

[tool.pytest.ini_options]
testpaths = ["packages", "tests"]

[tool.ruff]
line-length = 100
EOF
)"
  if [[ "$(cat pyproject.toml)" == "$NEW_ROOT_PYPROJECT" ]]; then
    warn "  root pyproject.toml juz w docelowej postaci - pomijam"
  else
    run cp pyproject.toml pyproject.toml.bak
    if [[ $APPLY -eq 1 ]]; then
      printf '%s\n' "$NEW_ROOT_PYPROJECT" > pyproject.toml
    else
      printf '  + nadpisz pyproject.toml (kopia: pyproject.toml.bak)\n' >&2
    fi
  fi
else
  warn "  brak root pyproject.toml - tworze nowy"
  printf '%s\n' "[tool.uv.workspace]
members = [\"packages/*\"]" | write_if_absent "pyproject.toml"
fi

# =============================================================================
log ""
log "[5/5] Tworze szkielet frontend/ (poza uv workspace)"
run mkdir -p frontend/src
write_if_absent "frontend/package.json" <<'EOF'
{
  "name": "rocket-digital-twin-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "description": "React/TS frontend - parametry, sterowanie, wizualizacja 3D",
  "scripts": {
    "dev": "vite",
    "build": "vite build"
  }
}
EOF
write_if_absent "frontend/.gitkeep" </dev/null

# sprzatanie pustego src/digital_twin (tylko jesli zostal pusty __init__)
if [[ -d src/digital_twin ]]; then
  remaining="$(find src/digital_twin -type f ! -name '__init__.py' | wc -l | tr -d ' ')"
  if [[ "$remaining" == "0" ]]; then
    warn "  src/digital_twin/ zawiera juz tylko __init__.py - mozesz usunac recznie po weryfikacji:"
    warn "      git rm -r src/digital_twin   (lub: rm -rf src/ jesli pusty)"
  fi
fi

log ""
ok "=== Plan migracji $([ $APPLY -eq 1 ] && echo 'WYKONANY' || echo 'wyswietlony (dry-run)') ==="
if [[ $APPLY -eq 0 ]]; then
  warn "Uruchom ponownie z --apply aby wykonac. Potem:"
  warn "  1) zweryfikuj: git status"
  warn "  2) usun pusty src/ jesli zostal"
  warn "  3) uv sync   (wygeneruje uv.lock)"
  warn "  4) zacommituj migracje"
fi
