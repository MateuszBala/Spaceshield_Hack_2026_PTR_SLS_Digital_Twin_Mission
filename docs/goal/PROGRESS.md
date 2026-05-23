# Stan projektu — podsumowanie (compact)

Skondensowany zapis decyzji i postępu. Służy jako punkt odniesienia niezależny
od długości rozmowy. Pełne uzasadnienia: `docs/architecture/`.

## Cel
Cyfrowy bliźniak (Digital Twin) rakiety wynoszącej małego satelitę na LEO.
Symulacja misji, zmiana parametrów, ponowne przebiegi, analiza wpływu — z
naciskiem na optymalizację masy przy osiągnięciu orbity. Zespół: 1 osoba
(fizyk, Python/C++/bash, Linux, MC), praca przez kilka instancji w git worktree.

## Decyzje narzędziowe
- OpenRocket — NIE (symulator modelarski, nie zna orbity).
- Scilab / MATLAB / Unity — NIE.
- Cały projekt w open-source Pythonie. Frontend w React/TS.

## Architektura (zatwierdzona)
Monorepo + uv workspace. Pięć elementów:
- `packages/contracts/`      (dt_contracts) — schematy Pydantic, ŹRÓDŁO PRAWDY, read-only
- `packages/physics-engine/` (dt_physics)   — czysta numeryka, biblioteka, bez HTTP
- `packages/api/`            (dt_api)        — FastAPI, skorupa HTTP
- `packages/ai/`            (dt_ai)         — Monte Carlo / optymalizacja
- `frontend/`                — React/TS, POZA uv workspace

Zależności: contracts ← physics-engine ← {api, ai}. Frontend ↔ api po HTTP/JSON
(OpenAPI). api→engine i ai→engine przez import in-process (hybryda). engine nie
zna api ani frontu.

## Fizyka / numeryka (zatwierdzone)
- SI, układ inercjalny kartezjański wokół środka Ziemi.
- Kanoniczny stan: [x, y, vx, vy, m] — jeden dla całego lotu.
- Trzy etapy = trzy reżimy: (1) wznoszenie atmosferyczne z oporem ρ(h) + max-Q;
  (2) wstawienie na orbitę, opór znikomy, g(h); (3) orbita — dwa ciała.
- Maszyna stanów faz: każda faza ma własny RHS/solver/tolerancje; przejścia to
  zdarzenia (terminal=True) modyfikujące stan (separacje = skok masy).
- max-Q i próg wyłączenia oporu (D/mg<ε) jako ZDARZENIA, nie próbki siatki.
- Werdykt o orbicie z elementów keplerowskich (ε, e, perygeum), nie z wysokości.
- Etap 3 możliwy analitycznie z Keplera; propagacja symplektyczna (leapfrog) gdy potrzebna.

## Stos numeryczny silnika
NumPy + SciPy (solve_ivp z events + optimize) → pandas (telemetria/CSV).
Rezerwa wydajności: Numba na RHS → własny zwektoryzowany stepper na MC → C++/pybind11
tylko jeśli profiler wskaże. Kolejność: poprawność najpierw, optymalizacja potem.

## Liczba stopni
PARAMETRYCZNA (list[Stage], 1–4). Liczba stopni to silny parametr Δv → musi być
zmienną, nie stałą.

## Stan prac (artefakty gotowe, czekają na wdrożenie/akceptację)
- [x] docs/architecture/ARCHITECTURE_DECISIONS.md
- [x] docs/architecture/COMMUNICATION.md (3 diagramy Mermaid)
- [x] Skrypt migracji src/ → packages/ (wykonany; struktura packages/ istnieje)
- [x] Poprawione manifesty uv (root + 4 człony) — ZWERYFIKOWANE na żywym uv
      (uv lock → Resolved 4 packages; zależności zgodne z architekturą).
      STATUS: do wdrożenia w repo (obecny root pyproject.toml ma tylko
      [tool.uv.workspace], brak [tool.uv.sources] i zależności).
- [x] Główny CLAUDE.md (58 linii) — do wdrożenia w root.
- [x] Szkielet kontraktu dt_contracts (5 plików, ~334 linie) — zweryfikowany
      składniowo i strukturalnie. Granice walidacji celowo jako TODO.

## Następne kroki
1. Wdrożyć poprawione manifesty + uv sync (wygeneruje uv.lock, do zacommitowania).
2. Wdrożyć główny CLAUDE.md i kontrakt dt_contracts.
3. DECYZJE FIZYCZNE do wypełnienia TODO w kontrakcie:
   - burn_time: liczony (propellant_mass/mass_flow) czy podawany jawnie?  ← OTWARTE
   - górna granica Isp, kryterium orbity (docelowa wysokość, min. perygeum, max. e),
     więzy optymalizacji, parametry gravity turn.
   - Źródło wartości: książki w docs/challenge/studentbooks/ (SMAD, Simulating
     Spacecraft Systems) — do przeczytania LUB wartości podane ręcznie.
4. Po zamrożeniu kontraktu: napisać packages/*/CLAUDE.md + frontend/CLAUDE.md
   (5 plików, ładowane leniwie per worktree).
5. git worktree add ×4 → praca równoległa.

## Otwarte pytania do rozstrzygnięcia
- burn_time: pochodna czy parametr? (wpływa na pole w Stage)
- Czy czytam książki ze studentbooks/, czy podajesz liczby sam?
- Drobne porządki: REPO_STRUCTURE.md vs .txt, rola .claude/CLAUDE.md i src/CLAUDE.md
  (ten ostatni traci sens po migracji — src/ znika).