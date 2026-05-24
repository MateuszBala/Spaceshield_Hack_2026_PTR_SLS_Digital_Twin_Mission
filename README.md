# 🛰️ Rocket Digital Twin

> Cyfrowy bliźniak rakiety wynoszącej satelitę na niską orbitę okołoziemską (LEO).
> Zmień parametr → przelicz → zobacz wpływ na misję.

**Zespół SpatiumCavum** · Hackaton Space Shield 2026

---

## Motywacja

Projektowanie rakiety nośnej to gra kompromisów: masa stopni, ciąg silników, liczba
stopni — każda decyzja zmienia szansę powodzenia misji. Tradycyjnie odpowiedź na
pytanie *„co się stanie, jeśli zmienię ten stopień?"* wymaga budowy i testów.

Ten projekt odpowiada na to pytanie **cyfrowo, w czasie rzeczywistym**. Symuluje pełną
misję wynoszenia satelity na orbitę i pozwala bezpiecznie eksperymentować z dowolnym
parametrem rakiety — natychmiast pokazując, czy satelita osiągnie stabilną orbitę.

## Opis

Rocket Digital Twin realizuje **pętlę Digital Twina**:

```
zmiana parametru  →  symulacja misji  →  werdykt + trajektoria  →  (powtórz)
```

System składa się z silnika fizycznego (pełna mechanika orbitalna), API (HTTP) oraz
interfejsu przeglądarkowego (wizualizacja). Wynosi rakietę na orbitę realistycznym
manewrem (gravity turn + manewr Hohmanna), a o sukcesie orzeka na podstawie
**elementów keplerowskich** (energia, mimośród, perygeum) — nie chwilowej wysokości.

**Co system pokazuje:** werdykt o orbicie z liczbami (perygeum, apogeum, mimośród,
okres), sekwencję misji (start, separacje, wejście na orbitę), telemetrię w czasie
(prędkość, wysokość, przeciążenie, ciśnienie dynamiczne) oraz wizualizację toru lotu
i orbity wokół Ziemi.

## Szybki start

Wymagania: **Python 3.13** + [`uv`](https://github.com/astral-sh/uv), **Node.js 18+** + `npm`.

**1. Backend** (API + silnik fizyczny) — z katalogu głównego:

```bash
uv sync                                      # instalacja zależności (jednorazowo)
uv run uvicorn dt_api.app:app --port 8000    # start API na :8000
```

**2. Frontend** (interfejs) — w osobnym terminalu:

```bash
cd frontend
npm install        # instalacja zależności (jednorazowo)
npm run dev        # start na :5173
```

**3. Otwórz** [`http://localhost:5173`](http://localhost:5173). Wskaźnik
**API LIVE · SILNIK ✓** w prawym górnym rogu potwierdza, że cały łańcuch działa.
Kliknij **Przelicz**, by uruchomić symulację złotego presetu.

> Interaktywna dokumentacja API (Swagger): [`http://localhost:8000/docs`](http://localhost:8000/docs)

## Prezentacja i dokumentacja oddania

Katalog [`presentation/`](presentation/) zawiera materiały oddania:

| Plik | Opis |
|------|------|
| `Rocket_Digital_Twin__SpatiumCavum_team.pptx` | Prezentacja (slajdy, edytowalne) |
| `Rocket_Digital_Twin__SpatiumCavum_team.pdf` | Prezentacja (PDF) |
| `dokumentacja.pdf` | Pełna dokumentacja techniczna: uruchomienie, opis interfejsu, podstawy fizyczne (wzory), architektura |

## Mapa repozytorium

```
.
├── packages/              # backend (monorepo, workspace uv)
│   ├── contracts/         # dt_contracts — schematy danych (Pydantic), źródło prawdy
│   ├── physics-engine/    # dt_physics — silnik fizyczny (NumPy/SciPy)
│   ├── api/               # dt_api — API HTTP (FastAPI)
│   └── ai/                # dt_ai — optymalizacja (opcjonalna)
├── frontend/              # interfejs (React + Vite + TypeScript)
│   └── src/components/    # wizualizacje: trajektoria, orbita, telemetria, werdykt
├── docs/                  # dokumentacja (patrz niżej)
├── presentation/          # materiały oddania (slajdy, dokumentacja PDF)
└── golden_preset.json     # przykładowa rakieta osiągająca orbitę
```

## Przewodnik po dokumentacji (`docs/`)

| Dokument | Zawartość |
|----------|-----------|
| [`docs/SYSTEM_OVERVIEW.md`](docs/SYSTEM_OVERVIEW.md) | Opis działania systemu: czym jest, jak zbudowany, co pokazuje |
| [`docs/PHYSICS_MODEL.md`](docs/PHYSICS_MODEL.md) | Podstawy fizyczne: model, werdykt keplerowski, źródła (MIT, SMAD) |
| [`docs/DESIGN_DECISIONS.md`](docs/DESIGN_DECISIONS.md) | Uzasadnienia kluczowych wyborów projektowych |
| [`docs/PRESENTATION_OUTLINE.md`](docs/PRESENTATION_OUTLINE.md) | Zarys prezentacji i scenariusz demonstracji |
| [`docs/architecture/`](docs/architecture/) | Decyzje architektoniczne, baza teorii fizycznej, komunikacja |
| [`docs/goal/PROGRESS.md`](docs/goal/PROGRESS.md) | Kompas projektu: cele, stan, dziennik kamieni milowych |
| [`docs/decisions/`](docs/decisions/) | Rekordy decyzji architektonicznych (ADR) |

## Autor

**Mateusz Bała** — zespół **SpatiumCavum**.
Repozytorium: [github.com/MateuszBala/Spaceshield_Hack_2026_PTR_DLD_Digital_Twin_Mission](https://github.com/MateuszBala/Spaceshield_Hack_2026_PTR_DLD_Digital_Twin_Mission)

## Licencja

Projekt udostępniony na licencji **MIT** — swobodne użycie, modyfikacja i dystrybucja
z zachowaniem informacji o autorstwie. Pełna treść w pliku [`LICENSE`](LICENSE).
