# Copilot — instrukcje repozytorium

Cyfrowy bliźniak rakiety wynoszącej satelitę na LEO. Monorepo (uv workspace)
z czterema pakietami Python + frontendem React/TS. Pełna architektura, granice
pracy i zasady są w `CLAUDE.md` (root) oraz `packages/*/CLAUDE.md` — Copilot
powinien je respektować. Ten plik dodaje konwencje generowania KODU.

## Stos i wersje
- Python ≥ 3.12. Menedżer: uv (workspace). Nie używaj pip/poetry/conda w kodzie.
- Pydantic v2 dla modeli danych. NumPy/SciPy dla numeryki. FastAPI dla HTTP.
- Frontend: React + TypeScript, narzędzia npm/node (NIE uv) — osobny stos.

## Konwencje kodu Python
- Type hints OBOWIĄZKOWE dla parametrów i wartości zwracanych funkcji.
- Modele danych jako Pydantic v2: `Annotated[type, Field(...)]`, nie `x: t = Field(...)`.
- Docstringi zwięzłe; komentarze wyjaśniają „dlaczego", nie „co".
- Importy pakietów workspace z prefiksem `dt_` (np. `import dt_physics`).
- Stałe fizyczne bierz z `dt_contracts.constants` — nie wpisuj własnych μ, R, g0.
- Wszystkie wielkości w SI; układ inercjalny kartezjański; stan `[x, y, vx, vy, m]`.
- f-stringi do formatowania; `pathlib` zamiast `os.path`.

## Zasady architektoniczne, których kod musi przestrzegać
- Dane między pakietami to instancje schematów `dt_contracts` — nie twórz
  lokalnych, równoległych modeli danych.
- `physics-engine` to czyste funkcje `params → wynik`: bez I/O sieci, bez stanu
  globalnego, bez wiedzy o api/froncie.
- `api` woła silnik importem in-process; `ai` również. Tylko frontend↔api po HTTP.
- Werdykt o orbicie z elementów keplerowskich, nie z chwilowej wysokości.

## Jakość (by PR przeszedł CI)
- Każda nowa funkcjonalność ma testy w `packages/<pkg>/tests/` (pytest).
- Kod musi przechodzić `uv run ruff check .` (line-length 100).
- Testy uruchamiaj: `uv run pytest` (całość) lub `uv run --package <pkg> pytest`.
- Nie commituj kodu, który nie przechodzi lintu i testów lokalnie.

## Czego NIE robić
- Nie edytuj `packages/contracts/` ani root `pyproject.toml` bez wyraźnej zgody —
  to wspólny styk wszystkich pakietów (patrz CLAUDE.md, sekcja zgody człowieka).
- Nie mieszaj logiki domenowej do `api`/`frontend` — fizyka należy do silnika.
- Nie reimplementuj modelu lotu w `ai` — silnik jest jedynym źródłem dynamiki.
- Nie używaj jednostek innych niż SI ani wariantów wektora stanu.

## Konwencje pomocnicze
- Commity: `docs/rules/COMMIT_CONVENTIONS.md`.
- Decyzje architektoniczne: `docs/decisions/` (ADR). Nowa decyzja = nowy ADR.
- Reguły zależne od ścieżki można dodać jako `.github/instructions/*.instructions.md`
  z polem `applyTo` (np. osobne dla Pythona i dla frontendu), jeśli zajdzie potrzeba.