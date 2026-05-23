# physics-engine — pamięć pakietu (dt_physics)

Silnik symulacji lotu rakiety: czysta numeryka. Bierze `RocketParams`, zwraca
`SimResult`. Reguły wspólne dla repo są w głównym CLAUDE.md — tu specyfika.

## Czym ten pakiet JEST, a czym NIE jest
- JEST: biblioteką `params → wynik`. Model fizyczny, solwery, analiza orbity.
- NIE jest: serwerem, nie zna HTTP, nie wie o istnieniu api ani frontu, nie
  robi I/O sieci. Jest wołany importem in-process przez api oraz ai.
- Funkcje sił i RHS są CZYSTE (bez efektów ubocznych) — bo dzięki temu da się je
  testować analitycznie (zachowanie energii/pędu) i wektoryzować w Monte Carlo.

## Fundament fizyczny — IMPORTANT (nie odstępuj bez zgody)
- Jednostki: SI. Układ: inercjalny kartezjański wokół środka Ziemi.
- Kanoniczny wektor stanu CAŁEGO lotu: [x, y, vx, vy, m]. Jeden, niezmienny.
  Nie wprowadzaj wariantów (np. [wysokość, prędkość]) — przejścia między fazami
  mają być identycznością na stanie, bez konwersji, którą można pomylić.
- Stałe (μ, R, g0) i progi importuj z `dt_contracts.constants`. Nie wpisuj
  własnych — to jedno źródło prawdy.

## Maszyna stanów faz — rdzeń architektury silnika
Lot to trzy RÓŻNE reżimy numeryczne, nie jeden solver z jednym ustawieniem:
1. Wznoszenie atmosferyczne — ciąg + grawitacja + opór ρ(h). Krytyczne: max-Q.
2. Wstawienie na orbitę — opór znikomy, g(h) zależne od wysokości.
3. Orbita — problem dwóch ciał, bez ciągu.

Zasady wynikające z tego podziału:
- Każda faza ma WŁASNY RHS, własny solver i własne tolerancje.
- Przejścia między fazami to ZDARZENIA (terminal), które modyfikują stan.
  Separacja stopnia/ładunku = skokowa zmiana TYLKO składowej masy; pozycja i
  prędkość pozostają ciągłe.
- max-Q oraz próg wyłączenia oporu (D/mg < ε) wykrywaj jako ZDARZENIA (zera
  funkcji), nie przez skanowanie zapisanej telemetrii — bo wynik nie może
  zależeć od gęstości kroku całkowania.
- Próg końca oporu opieraj na SILE (D/mg < ε, ε≈1e-3…1e-4), nie na twardej
  wysokości — bo to reaguje na to, co fizycznie nieistotne, a nie na zgadniętą
  wartość. (Uwaga: 30 km to wciąż ~1,5% gęstości przygruntowej.)

## Werdykt o orbicie — IMPORTANT
- Liczony z ELEMENTÓW KEPLEROWSKICH (energia ε, mimośród e, perygeum), NIE z
  chwilowej wysokości. Powód: orbita to prędkość styczna, nie wysokość — można
  być na 400 km i spadać.
- Kryterium sukcesu: orbita związana (ε<0) ORAZ perygeum > próg
  (constants.MIN_PERIAPSIS_ALTITUDE) ORAZ e ≤ MAX_ECCENTRICITY_LEO.
- Etap 3 można orzec ANALITYCZNIE z elementów w momencie wstawienia; pełna
  propagacja numeryczna służy weryfikacji/wizualizacji, nie werdyktowi.
- Jeśli propagujesz orbitę długo, używaj integratora symplektycznego (leapfrog)
  — zwykły RK akumuluje błąd energii i orbita sztucznie dryfuje.

## Stos i kolejność pracy
- NumPy + SciPy (`solve_ivp` z mechanizmem `events`). pandas do telemetrii/CSV.
- KOLEJNOŚĆ: najpierw POPRAWNOŚĆ (solve_ivp per trajektoria, zdarzenia,
  walidacja względem znanych przypadków), DOPIERO POTEM wydajność. Nie
  optymalizuj przedwcześnie.
- Wydajność, gdy profiler wskaże: Numba na RHS → własny zwektoryzowany stepper
  dla Monte Carlo → C++/pybind11 tylko w ostateczności.

## Struktura wewnętrzna (proponowana)
core/ (stan, stałe z contracts, atmosfera ρ(h), g(h)); forces/ (ciąg,
grawitacja, opór — czyste funkcje); phases/ (ascent, insertion, orbit);
events/ (max-Q, wypalenie, próg oporu, separacje); orchestrator (pętla po
fazach, sklejanie segmentów); analysis/ (elementy Keplera, werdykt, eksport).

## Walidacja modelu
- Sprawdzaj względem znanych wartości: Δv z równania Ciołkowskiego, prędkość
  orbitalna ~7,67 km/s na 400 km, budżet do LEO ~9,4 km/s (z stratami
  grawitacyjno-aerodynamicznymi 1,5–2 km/s wg SMAD 7.3).
- Testy zachowań fizycznych (energia, pęd) cenniejsze niż testy wartości.

## Granice i zgoda człowieka
- Piszesz wyłącznie w `packages/physics-engine/`. `dt_contracts` jest read-only.
- Zmiana fundamentu fizycznego (układ, kanoniczny stan, kryterium orbity)
  wymaga zgody — to są decyzje architektoniczne, nie implementacyjne.

## Głębszy kontekst
- Koncepcja faz i numeryki: `docs/architecture/` + ADR fizyczne w `docs/decisions/`.
- Wartości i progi ze SMAD: komentarze w `dt_contracts/constants.py`.
