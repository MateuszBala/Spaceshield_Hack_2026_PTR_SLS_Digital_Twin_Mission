# Preset „złota rakieta" — wartości referencyjne (krok 1)

Typ: dokument wiedzy (wartości + uzasadnienie). Adresat: instancja `physics-engine`
(materializuje preset), pomocniczo `api`/`frontend` (preset jako punkt startowy UI).
Powiązane: `BRIEF-engine-01-vertical-slice.md` (sekcja „Preset złoty przykład"),
kontrakt `dt_contracts/rocket.py`, stałe `dt_contracts/constants.py`, kompas
`docs/goal/PROGRESS.md`.

Ten dokument NIE jest kodem. Podaje liczby i pokazuje, że budżet Δv się domyka.
Materializacja (funkcja `golden_preset() -> RocketParams` lub plik danych) należy
do instancji silnika — to ona widzi kontrakt na żywo i mapuje wartości na pola.

---

## 0. Po co ten preset

To kotwica demo i testów: rakieta, która NA PEWNO osiąga orbitę, dobrana tak, by
budżet Δv przekraczał wymagany do LEO z **umiarkowanym** zapasem (~2,7 km/s po
stratach). Umiarkowanym celowo — gdyby zapas był ogromny (5+ km/s), odcięcie
paliwa w demo nie psułoby werdyktu i złoty scenariusz „zmieniam parametr → inny
wynik" przestałby działać wizualnie. Przy tym zapasie odcięcie ~20–25 % paliwa
dowolnego stopnia powinno już wywrócić werdykt na `reached_orbit=False`.

Konfiguracja: trójstopniowa, ładunek 150 kg (mały satelita), start pionowy.

---

## 1. Wartości WEJŚCIOWE (to się podaje do kontraktu)

Kontrakt `Stage` przyjmuje SZEŚĆ pól wejściowych: `name`, `dry_mass`, `thrust`,
`isp`, `burn_time`, `drag_coefficient`, `reference_area`. Reszta (`mass_flow`,
`propellant_mass`, `total_impulse`, `wet_mass`, `mass_fraction`) to `computed_field`
— **NIE podawać**, policzą się same.

### Stopień 1 (dolny — kerolox-podobny)
| pole | wartość | jednostka |
|------|---------|-----------|
| `name` | `"S1-core"` | — |
| `dry_mass` | `3000.0` | kg |
| `thrust` | `780000.0` | N |
| `isp` | `282.0` | s |
| `burn_time` | `105.0` | s |
| `drag_coefficient` | `0.30` | — |
| `reference_area` | `3.0` | m² |

### Stopień 2 (środkowy)
| pole | wartość | jednostka |
|------|---------|-----------|
| `name` | `"S2"` | — |
| `dry_mass` | `700.0` | kg |
| `thrust` | `145000.0` | N |
| `isp` | `345.0` | s |
| `burn_time` | `120.0` | s |
| `drag_coefficient` | `0.25` | — |
| `reference_area` | `1.2` | m² |

### Stopień 3 (górny — LO2/LH2-podobny, wysokie Isp)
| pole | wartość | jednostka |
|------|---------|-----------|
| `name` | `"S3-upper"` | — |
| `dry_mass` | `120.0` | kg |
| `thrust` | `22000.0` | N |
| `isp` | `448.0` | s |
| `burn_time` | `115.0` | s |
| `drag_coefficient` | `0.22` | — |
| `reference_area` | `0.8` | m² |

### Ładunek i parametry globalne
| pole | wartość | jednostka |
|------|---------|-----------|
| `payload.mass` | `150.0` | kg |
| `payload.name` | `"sat-150"` | — |
| `launch_angle_deg` | `90.0` | deg (start pionowy) |

Uwaga do `isp`: wszystkie wartości ≤ 455 s (limit `ISP_MAX_CHEMICAL`), więc
walidator `_check_isp_range` przepuści. S3 = 448 s siedzi tuż pod limitem —
realistyczne dla LO2/LH2 (RL10), zgodne z komentarzem w `constants.py`.

Uwaga do aerodynamiki: `drag_coefficient` i `reference_area` są zgadywane
rozsądnie (Cd ~0,2–0,3, malejący przekrój ku górze). NIE są krytyczne dla budżetu
Δv — wpływają tylko na straty aerodynamiczne w fazie 1, które i tak mieszczą się w
ryczałcie strat. Można je dostroić bez ruszania reszty.

---

## 2. Wartości POCHODNE (kontrakt policzy — tu dla weryfikacji)

Te liczby NIE są wejściem. Podaję je, żeby instancja mogła sprawdzić, że jej
`computed_field` dają to samo (sanity po materializacji). Wzory z `rocket.py`:
`mass_flow = thrust/(isp·g0)`, `propellant_mass = mass_flow·burn_time`,
`wet_mass = dry_mass + propellant_mass`, `mass_fraction = propellant_mass/wet_mass`.

| stopień | mass_flow [kg/s] | propellant_mass [kg] | wet_mass [kg] | mass_fraction |
|---------|------------------|----------------------|---------------|---------------|
| S1 | 282,05 | 29 615,2 | 32 615,2 | 0,908 |
| S2 | 42,86 | 5 142,9 | 5 842,9 | 0,880 |
| S3 | 5,01 | 575,9 | 695,9 | 0,828 |

**`liftoff_mass` = 39 303,9 kg** (suma wet_mass stopni + payload).

Wszystkie `mass_fraction` mieszczą się w `[STAGE_MASS_FRACTION_TYPICAL_MIN,
STAGE_MASS_FRACTION_TYPICAL_MAX]` = `[0,80, 0,95]` — żadnych ostrzeżeń o frakcji.

---

## 3. Budżet Δv — dlaczego osiąga orbitę

Δv liczone równaniem Ciołkowskiego per stopień: `Δv_i = isp_i · g0 · ln(m0_i/m1_i)`,
gdzie `m0_i` = masa na początku spalania stopnia i (payload + wszystkie wet_mass
od i w górę), `m1_i = m0_i − propellant_mass_i`.

| stopień | m0 [kg] | m1 [kg] | Isp [s] | Δv [m/s] |
|---------|---------|---------|---------|----------|
| S1 | 39 304 | 9 689 | 282 | 3 873 |
| S2 | 6 689 | 1 546 | 345 | 4 956 |
| S3 | 846 | 270 | 448 | 5 017 |

- **Δv idealne (suma)**: ≈ 13 846 m/s
- **Typowe straty startowe** (`TYPICAL_LAUNCH_LOSSES_DV`): −1 750 m/s
- **Δv efektywne**: ≈ 12 096 m/s
- **Wymagany budżet do LEO**: ~9 400 m/s
- **ZAPAS ponad budżet**: ≈ **+2 696 m/s** ✅

Sanity orbitalne (z μ, R_earth): prędkość kołowa @400 km = 7 669 m/s, @200 km =
7 784 m/s. Budżet efektywny z dużym marginesem pokrywa orbitę kołową LEO plus
straty — preset osiąga orbitę z zapasem.

TWR startowy (S1): `thrust / (liftoff_mass · g0)` = 780000 / (39304 · 9,80665) ≈
**2,02** — zdrowy (powyżej progu 1,2; rakieta rusza z ziemi bez problemu).

---

## 4. Test negatywny (dla złotego scenariusza demo)

Brief silnika wymaga testu, że gorszy parametr daje `reached_orbit=False`. Przy
zapasie 2 696 m/s wystarczy odebrać Δv większe niż to. Propozycja konkretnej
„gorszej" rakiety do testu i do Aktu 2 demo:

- **Wariant „za mało paliwa"**: skróć `burn_time` stopnia 1 ze 105 s do **70 s**
  (mniej spalonego paliwa → mniej Δv). To odbiera z S1 rzędu ~1,3–1,5 km/s Δv,
  ale uwaga: zmiana `burn_time` przy fallbacku Δv liczy się wprost, natomiast w
  pełnym całkowaniu trajektorii efekt jest mocniejszy (krótszy ciąg = niższy
  pułap i prędkość). Instancja silnika powinna **zweryfikować empirycznie**, ile
  trzeba uciąć, by werdykt spadł — i tę wartość użyć w teście negatywnym oraz
  zarekomendować froncie jako „suwak demo".
- Alternatywa czystsza do demo: obniż `thrust` S3 lub skróć jego `burn_time` —
  górny stopień jest najbliżej progu orbity, więc jego osłabienie najpewniej i
  najczytelniej wywróci werdykt.

To do empirycznego potwierdzenia przez silnik (zależy od tego, czy liczy pełną
trajektorię, czy fallback Δv). Wartość docelowa: jeden parametr, jeden suwak,
który w demo przełącza „ORBITA OSIĄGNIĘTA" ↔ „BRAK ORBITY".

---

## 5. Status i co zweryfikować

- Liczby sprawdzone arytmetycznie (Ciołkowski + frakcje + TWR) — budżet się domyka.
- **Do potwierdzenia przez silnik**: czy pełne całkowanie trajektorii (faza 1 z
  oporem + wstawienie) faktycznie daje `reached_orbit=True` na tym presecie. Budżet
  Δv to warunek konieczny, nie gwarancja — profil lotu (kąt, moment odpaleń) wpływa
  na straty. Jeśli realne straty wyjdą wyższe niż ryczałt 1 750 m/s, zapas 2 696
  m/s daje poduszkę, ale gdyby preset nie dolatywał — najprostsza korekta to
  wydłużyć `burn_time` S2 lub S3 o ~10–15 % (więcej paliwa, większe Δv).
- Aerodynamika (Cd, pole) — wartości orientacyjne, do dostrojenia bez wpływu na
  budżet.

Jeśli instancja silnika znajdzie, że preset wymaga korekty — zgłasza do PROGRESS.md
i do mnie, ustalamy nowe wartości. To jest punkt startowy z zapasem, nie dogmat.
