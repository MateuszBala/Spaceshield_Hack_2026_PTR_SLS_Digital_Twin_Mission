# 🛰️ Rocket Digital Twin

[![Python](https://img.shields.io/badge/Python-3.13.x-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![pyenv](https://img.shields.io/badge/pyenv-required-4B8BBE?logo=python&logoColor=white)](https://github.com/pyenv/pyenv)
[![uv](https://img.shields.io/badge/uv-workspace-2E3440?logo=python&logoColor=white)](https://github.com/astral-sh/uv)
[![Node.js](https://img.shields.io/badge/Node.js-18+-339933?logo=node.js&logoColor=white)](https://nodejs.org/)
[![React](https://img.shields.io/badge/React-18.3.x-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.4+-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![NumPy](https://img.shields.io/badge/NumPy-2.x-013243?logo=numpy&logoColor=white)](https://numpy.org/)
[![SciPy](https://img.shields.io/badge/SciPy-1.13+-8CAAE6?logo=scipy&logoColor=white)](https://scipy.org/)
[![Pydantic](https://img.shields.io/badge/Pydantic-2.x-E92063?logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)

> Cyfrowy bliźniak rakiety wynoszącej satelitę na niską orbitę okołoziemską (LEO).
> Zmień parametr → przelicz → zobacz wpływ na misję.

**Zespół SpatiumCavum** · Hackaton Space Shield 2026

[ENGLISH README VERSION](README_ENG.md)

---

![Widok głównego okna aplikacji webowej](docs/imgs/RocketDigitaTwin_WebView.png)

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

## Wymagania systemowe (Debian)

Przed przejściem do sekcji **Szybki start** zainstaluj poniższe zależności systemowe.

**1. Narzędzia systemowe (APT):**

```bash
sudo apt update
sudo apt install -y curl ca-certificates git build-essential
```

**2. Python 3.13 przez `pyenv` (zalecane na Debianie):**

Zainstaluj zależności wymagane do budowania Pythona:

```bash
sudo apt install -y make libssl-dev zlib1g-dev libbz2-dev libreadline-dev \
	libsqlite3-dev libffi-dev liblzma-dev tk-dev xz-utils wget llvm
```

Zainstaluj `pyenv`:

```bash
curl https://pyenv.run | bash
```

Dodaj `pyenv` do konfiguracji shella (bash):

```bash
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init - bash)"' >> ~/.bashrc
exec "$SHELL"
```

Zainstaluj Python 3.13 i ustaw go lokalnie dla tego repozytorium:

```bash
pyenv install 3.13.7
pyenv local 3.13.7
python --version
```

Po `pyenv local` w katalogu repozytorium pojawi się plik `.python-version`, dzięki czemu
wszystkie komendy `uv` będą używać właściwej wersji Pythona lokalnie.

**3. Menedżer `uv` (backend):**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Po instalacji upewnij się, że `uv` jest w `PATH`:

```bash
uv --version
```

**4. Node.js 18+ oraz `npm` (frontend):**

```bash
sudo apt install -y nodejs npm
node --version
npm --version
```

> Dla Debiana stable pakiet `nodejs` bywa starszy niż 18. Jeśli tak, doinstaluj Node.js 18+
> z oficjalnego repozytorium NodeSource lub użyj menedżera `nvm`.

Po spełnieniu powyższych wymagań możesz przejść do sekcji **Szybki start**.

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
