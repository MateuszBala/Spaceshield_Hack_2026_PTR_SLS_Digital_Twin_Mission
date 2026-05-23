# Rocket Digital Twin — Project Memory (root)

Cyfrowy bliźniak rakietowego systemu wynoszenia małego satelity na LEO.
Symuluje misję, pozwala zmieniać parametry, ponownie liczyć i analizować wpływ
na powodzenie misji — z naciskiem na optymalizację masy przy osiągnięciu orbity.

Ten plik ładuje się w KAŻDEJ sesji (przodek). Zawiera tylko reguły wspólne dla
całego repo. Szczegóły pakietów są w `packages/*/CLAUDE.md` (ładowane leniwie).
Zasady organizacji pamięci: `docs/architecture/CLAUDE_MD_STRATEGY.md`.

## Model pracy
Decyzje architektoniczne, plany i dokumentacja powstają na poziomie projektu
(rozmowa z człowiekiem); IMPLEMENTACJA należy do instancji w worktree. Instancja
realizuje zadania zgodnie z dokumentacją w `docs/` i regułami w CLAUDE.md, a nie
wymyśla architektury od nowa.

## Architektura (stan bieżący)
Monorepo + uv workspace. Cztery pakiety Python + wspólne schematy + frontend JS:
- `packages/contracts/`      → `dt_contracts` — schematy Pydantic (źródło prawdy); GOTOWE
- `packages/physics-engine/` → `dt_physics`   — czysta numeryka (NumPy/SciPy), bez HTTP
- `packages/api/`            → `dt_api`        — FastAPI, cienka skorupa HTTP
- `packages/ai/`            → `dt_ai`         — Monte Carlo / optymalizacja
- `frontend/`                → React/TS — POZA uv workspace

Komunikacja: frontend ↔ api po HTTP/JSON (OpenAPI); api → engine i ai → engine
przez import in-process. engine NIE zna api ani frontu. Pełny opis:
`docs/architecture/ARCHITECTURE_DECISIONS.md` i `COMMUNICATION.md`.

## Granice pracy (worktree) — IMPORTANT
Każda instancja pracuje w osobnym worktree i pisze TYLKO w swoim pakiecie:
- engine → `packages/physics-engine/`   - api → `packages/api/`
- ai     → `packages/ai/`               - frontend → `frontend/`
- IMPORTANT: `packages/contracts/` jest READ-ONLY. Zmianę kontraktu się ZGŁASZA,
  nie wprowadza samodzielnie — to wspólny styk czterech pakietów.
- IMPORTANT: nie edytuj plików spoza swojej strefy zapisu, nawet jeśli kuszą.
- Wszystkie worktree dzielą jedną auto-pamięć repo — nie zakładaj prywatności notatek.

## Zasady techniczne (całe repo)
- Język: Python ≥ 3.12, jednostki w SI, układ inercjalny kartezjański.
- Kanoniczny wektor stanu lotu: `[x, y, vx, vy, m]`. Nie wprowadzaj wariantów.
- Dane przepływające między pakietami MUSZĄ być instancjami schematów `dt_contracts`.
- Stałe fizyczne i progi (μ, R, g0, granice) pochodzą z `dt_contracts.constants`
  — jedno źródło prawdy, nie wpisuj własnych.
- Silnik fizyczny to czyste funkcje `params → wynik` — bez efektów ubocznych, bez I/O sieci.
- Werdykt o orbicie liczony z elementów keplerowskich (ε, e, perygeum), nie z chwilowej wysokości.

## Komendy
- `uv sync`                      — instalacja środowiska (generuje uv.lock)
- `uv run pytest`                — wszystkie testy (testpaths: packages, tests)
- `uv run --package physics-engine pytest` — testy jednego członu workspace
- `uv run ruff check .`          — lint (line-length 100)
- frontend: `cd frontend && npm install && npm run dev`

## Testy
- Testy jednostkowe pakietu ŻYJĄ przy pakiecie: `packages/<pkg>/tests/`.
- `tests/integration/` i `tests/soak/` w root — tylko scenariusze cross-package.

## Wymaga zgody człowieka — IMPORTANT
- Zmiany w `packages/contracts/` (kontrakt danych).
- Zmiany w root `pyproject.toml` (członowie workspace, zależności współdzielone).
- Zmiana decyzji architektonicznej (wtedy: najpierw ADR w `docs/decisions/`).
- `git push`, operacje na historii, kasowanie śledzonych plików.

## Konwencje
- Commity: patrz `docs/rules/COMMIT_CONVENTIONS.md`.
- Nazwy importów pakietów zawsze z prefiksem `dt_` (np. `import dt_physics`).
- Nowa decyzja architektoniczna = nowy plik w `docs/decisions/` (ADR).
- CLAUDE.md mówi CO ROBIĆ; pełne uzasadnienia („dlaczego") żyją w ADR-ach.