# Architecture Decisions — Satellite Launch System: Digital Twin

Dokument zamraża decyzje podjęte na wejściu projektu. Stanowi wspólne źródło prawdy
dla wszystkich równoległych instancji pracujących w osobnych git worktree.
Sekcje oznaczone ⭐ są krytyczne dla bezkonfliktowej pracy równoległej.

---

## 1. Kontekst i cel

Cel: cyfrowy bliźniak (Digital Twin) rakietowego systemu wynoszenia małego satelity
na niską orbitę okołoziemską (LEO). System symuluje misję, pozwala zmieniać parametry
rakiety, ponownie uruchamiać symulację i analizować wpływ zmian — z naciskiem na
optymalizację masy przy jednoczesnym osiągnięciu orbity.

Profil zespołu: jedna osoba (fizyk teoretyk, programista Python / C++ / bash, Linux,
doświadczenie w obliczeniach numerycznych i Monte Carlo). Praca realizowana przez
kilka równoległych instancji Claude, każda w osobnym git worktree.

---

## 2. Decyzje o narzędziach z dokumentu zadania

### OpenRocket — NIE używamy
Symulator rakiet modelarskich / amatorskich. Model fizyczny dotyczy lotu
atmosferycznego, nie zna pojęcia orbity ani wstawienia na LEO; symulacje
naddźwiękowe są jego słabym punktem (pozycja "planned features"). Sednem zadania
jest właśnie faza orbitalna, której OpenRocket nie obsługuje. Decyzja: własny
symulator od zera.

### Scilab — NIE używamy
W pełni wystarczyłby do samej numeryki (solwery ODE, optymalizacja, grafika), ale
nie wnosi nic ponad Pythona, a jednocześnie utrudnia warstwy punktowane w zadaniu
(dashboard, interaktywny UI, AI/ML). Python pokrywa numerykę i otwiera ekosystem
dodatków.

### MATLAB/Simulink, Unity — poza zakresem
Wykluczone decyzją zespołu.

### Wniosek
Cały projekt w ekosystemie open-source Python.

---

## 3. Podział misji na etapy numeryczne ⭐

Trzy etapy to trzy różne reżimy numeryczne — różna dominująca fizyka, sztywność,
kryterium poprawności. Każdy etap = osobny RHS + osobny solver + osobne tolerancje.
Przejścia między etapami to wykrywane zdarzenia (terminal=True), które modyfikują
wektor stanu.

| Etap | Dominująca fizyka | Solver | Zdarzenie kończące |
|------|-------------------|--------|--------------------|
| 1. Wznoszenie atmosferyczne | ciąg + grawitacja + opór ρ(h) | RK45 / DOP853, ciasne tolerancje | max-Q (krytyczny), separacje stopni, próg oporu D/mg<ε |
| 2. Wstawienie na orbitę | ciąg + grawitacja g(h), opór znikomy | DOP853, luźniejsze tolerancje | wypalenie ostatniego stopnia / separacja ładunku |
| 3. Utrzymanie na orbicie | dwa ciała, bez ciągu | symplektyczny (leapfrog) LUB analitycznie z elementów Keplera | werdykt z r_p, ε, e |

Ustalenia szczegółowe:
- **max-Q** wykrywany jako zdarzenie zerujące dQ/dt (direction=-1), nie skanowaniem
  zapisanej telemetrii — niezależność od gęstości kroku.
- **Wyłączenie oporu** sterowane progiem na sile (D/mg < ε, ε ≈ 1e-3…1e-4), nie
  twardym progiem wysokości. Realizowane jako zdarzenie kończące fazę z oporem.
  (Uwaga: 30 km daje jeszcze ~1,5% gęstości przygruntowej — dla obciążeń pomijalne,
  dla bilansu Δv niekoniecznie; stąd próg na sile, nie na wysokości.)
- **Werdykt o orbicie** liczony z elementów keplerowskich (energia ε=v²/2−μ/r,
  mimośród e, perygeum r_p = a(1−e)), nie z chwilowej wysokości. Sukces:
  r_p > R_Ziemi + ~150 km. Etap 3 można orzec analitycznie z momentu wstawienia;
  propagacja numeryczna tylko do weryfikacji/wizualizacji.
- Przy długiej propagacji orbity zwykły RK akumuluje błąd energii → integrator
  **symplektyczny** (leapfrog/Verlet) dla niedryfującej elipsy.

### Kanoniczny stan i układ odniesienia ⭐
Cały lot liczony w **SI, w inercjalnym układzie kartezjańskim wokół środka Ziemi**.
Wektor stanu: `y = [x, y, vx, vy, m]` (2D w płaszczyźnie orbity wystarczy dla modelu
uproszczonego). Konsekwencje:
- Przejścia między fazami to **identyczność na stanie** — brak konwersji do pomylenia.
- Nieciągłości (separacja stopnia/ładunku) dotyczą **tylko składowej m**; pozycja i
  prędkość ciągłe.
- "Etapowość" siedzi w wyborze RHS/solvera, nie w reprezentacji stanu.

---

## 4. Architektura repozytorium ⭐

Monorepo (jedno .git), cztery rozłączne pakiety + cienka, stabilna warstwa wspólna
(`contracts`). Narzędzie: **uv workspace** (jeden lockfile, jedno środowisko,
edytowalne importy między pakietami). Frontend React stoi poza uv workspace
(własny package.json / node_modules).

```
rocket-digital-twin/                 # monorepo, jedno .git, uv workspace
├── packages/
│   ├── contracts/        # ⭐ schematy danych (Pydantic): TelemetryFrame,
│   │                     #   OrbitalElements, RocketParams, SimRequest/Result
│   │                     #   zależność wszystkich, edytowany najrzadziej
│   ├── physics-engine/   # ① silnik (NumPy/SciPy, fazy, solvery) — czysta numeryka
│   ├── api/              # ② backend HTTP serwujący dane do frontu (FastAPI)
│   ├── ai/              # ④ backend AI (optymalizacja / Monte Carlo)
│   └── frontend/         # ③ aplikacja webowa React (poza uv workspace)
├── docs/                # ADR-y, kontrakt, opis faz
└── (worktrees poza drzewem repo)
```

### Kierunek zależności (nigdy w poprzek między elementami)
```
contracts  ←  physics-engine
contracts  ←  ai            →  woła physics-engine jako bibliotekę (in-process)
contracts  ←  api           →  woła physics-engine jako bibliotekę
contracts  ←  frontend      →  gada z api wyłącznie po HTTP, nie importuje Pythona
```

### Decyzje integracyjne
- **AI → silnik: import (in-process).** AI robi Monte Carlo i optymalizację (tysiące
  wywołań w pętli); HTTP byłby absurdalnym narzutem. Wołanie w procesie, najlepiej z
  wektoryzacją ensembli.
- **Frontend → silnik: przez API (HTTP).** Pojedyncze żądania z przeglądarki; narzut
  HTTP nieistotny, a granica procesu/sieci naturalna.
- **Silnik fizyczny jest czystą biblioteką** — nie wie o istnieniu API ani frontu
  (params → wynik, bez serwera, bez HTTP).
- **Stack frontu: FastAPI (API) + React/TS (frontend).** Twarda granica języka i
  katalogu między instancjami; wsparcie dla wizualizacji 3D (Three.js /
  react-three-fiber). Streamlit/Dash odrzucone — łamią granicę worktree (mieszają
  logikę i prezentację w jednym pakiecie Python) i słabo nadają się do 3D.

### Dlaczego monorepo, nie cztery repo
Atomowość zmian: zmiana kontraktu dotykająca silnika i frontu to jeden spójny
snapshot zamiast rozjeżdżających się commitów w osobnych repo. Izolację katalogów
daje worktree wewnątrz jednego repo.

---

## 5. Model pracy równoległej (git worktree) ⭐

Każdy pakiet = jedna instancja = jedna gałąź = jeden worktree:

```bash
git worktree add ../rdt-engine    feat/engine
git worktree add ../rdt-api       feat/api
git worktree add ../rdt-frontend  feat/frontend
git worktree add ../rdt-ai        feat/ai
```

Reguły operacyjne:
- Każda instancja **pisze wyłącznie w swoim `packages/<x>/`**.
- `contracts/` jest **read-only** dla instancji — propozycję zmiany kontraktu się
  zgłasza, nie wprowadza samodzielnie.
- `contracts` musi być **zaprojektowany pierwszy**, zanim odpalimy cztery instancje
  — to warunek wejścia do pracy równoległej (pozwala rozwijać pakiety wobec atrap
  sąsiadów: mock API, syntetyczna telemetria).

Ważne ograniczenie narzędzia: uv workspace **nie wymusza** izolacji importów
(Python nie ma izolacji zależności w runtime). Granica worktree pozostaje regułą
procesu i przeglądu, nie twardą gwarancją narzędzia.

---

## 6. Stos numeryczny silnika fizycznego

Faza "czysta numeryka" (bez grafiki):
- **NumPy** — wektor stanu, geometria; wektoryzacja ensembli (N,5) do Monte Carlo.
- **SciPy** — `solve_ivp` jako główny solver: mechanizm `events` (max-Q, wypalenie,
  próg oporu, separacje z terminal=True), dobór metody pod sztywność
  (RK45/DOP853 ↔ Radau/BDF). `scipy.optimize` do optymalizacji masy
  (SLSQP/trust-constr, ew. differential_evolution/dual_annealing).
- **pandas** — telemetria jako DataFrame, eksport CSV/Parquet (pomost do dashboardu).
- **Numba** (rezerwa) — kompilacja RHS, gdy profiler wskaże wąskie gardło w ciele
  funkcji przyspieszeń.
- **Własny zwektoryzowany stepper** (RK4/Dormand-Prince po ensemblu) — do masowych
  przebiegów Monte Carlo, gdy `solve_ivp` per-trajektoria nie wystarcza. Kompromis:
  tracimy `events`, zyskujemy throughput.
- **pybind11 / C++** — opcja ostateczna, tylko jeśli profiler wyraźnie wskaże.
- Dyscyplina jednostek: SI rygorystycznie; ew. `pint` poza hot-path.

Kolejność wdrażania: solve_ivp (poprawność + zdarzenia + walidacja) → profilowanie →
Numba na RHS → własny stepper na MC → C++ tylko w ostateczności.

### Struktura wewnętrzna pakietu physics-engine
```
physics_engine/
  core/        # stan, stałe (μ, R, g0), transformacje, atmosfera ρ(h), g(h)
  forces/      # ciąg, grawitacja, opór — czyste funkcje (t, y, params) → wektor
  phases/      # ascent.py, insertion.py, orbit.py — składają siły + definiują events
  events/      # max-Q, wypalenie, próg oporu D/mg<ε, separacje
  orchestrator # pętla po fazach, sklejanie segmentów w jedną trajektorię
  analysis/    # elementy keplerowskie, werdykt o orbicie, eksport telemetrii
```
Kontrakt fazy (interfejs wymienny): `rhs(t, y, params)`, `events(params)`,
`integrate(y0, t0, params) -> Segment`. Siły jako czyste funkcje — łatwe do
weryfikacji analitycznej i testów (zachowanie energii/pędu).

---

## 7. Status decyzji

| Obszar | Decyzja | Status |
|--------|---------|--------|
| OpenRocket | nie używamy | ✅ |
| Scilab / MATLAB / Unity | nie używamy | ✅ |
| Język/ekosystem | Python open-source | ✅ |
| Podział na 3 etapy numeryczne | tak, maszyna stanów faz | ✅ |
| Kanoniczny stan | SI, inercjalny kartezjański, [x,y,vx,vy,m] | ✅ |
| Repo | monorepo + uv workspace | ✅ |
| AI → silnik | import in-process | ✅ |
| Frontend → silnik | przez API (HTTP) | ✅ |
| Stack frontu | FastAPI + React/TS | ✅ |
| Praca równoległa | 4× git worktree, contracts read-only | ✅ |
| `contracts` (schematy) | do zaprojektowania PIERWSZY | ⏳ następny krok |
| RHS etapu 1 + model atmosfery | do rozpisania | ⏳ |
```
