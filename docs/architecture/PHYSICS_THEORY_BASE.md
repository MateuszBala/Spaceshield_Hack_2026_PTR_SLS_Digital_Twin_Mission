# Baza teorii fizycznej — Rocket Digital Twin

Typ: dokument wiedzy (referencja). Adresat: instancja `physics-engine` (źródło
wzorów i liczb kontrolnych), pomocniczo człowiek (weryfikacja, czy wyniki silnika
są prawdziwe). Powiązane: `BRIEF-engine-02-thickening.md`, `GOLDEN_PRESET.md`,
`dt_contracts/constants.py`, ADR architektury sekcja 3.

Cel: zamrozić POPRAWNE sformułowania wzorów i PEWNE liczby kontrolne, żeby silnik
liczył fizykę ze źródła, a nie z pamięci modelu. Wszystkie wzory pochodzą ze
slajdów wykładów astrodynamiki (16.346, MIT — problem dwóch ciał, Lecture 1-2);
wszystkie liczby kontrolne zweryfikowane numerycznie ze stałymi z `constants.py`.

Konwencja: SI, inercjalny układ kartezjański wokół środka Ziemi, stan
[x, y, vx, vy, m] (2D). Stałe: μ = 3.986004418e14 m³/s², R⊕ = 6378136.49 m,
g0 = 9.80665 m/s².

---

## 1. Mechanika orbitalna — rdzeń werdyktu (Lecture 1-2)

To są wzory, na których stoi werdykt „orbita: tak/nie". Liczone z wektora stanu
w momencie wstawienia — NIE wymagają całkowania po orbicie.

### Moment pędu (Kepler II)
W 2D, ze stanu [x, y, vx, vy]: `h = r × v`, czyli składowa z:
```
h = x·vy − y·vx          [m²/s]   (skalar w 2D)
```
h jest stałą ruchu (kierunek i wartość). Ruch zachodzi w płaszczyźnie.

### Wektor mimośrodu (Laplace Vector) — KLUCZOWE, łatwe o błąd w 2D
Ze slajdów: `μ·e = v × h − μ·r/|r|`. W 2D, gdzie h = h·îz (wektor wzdłuż osi z),
iloczyn v × h rozpisuje się jako:
```
(v × h)_x =  vy · h
(v × h)_y = −vx · h
```
Stąd składowe wektora mimośrodu:
```
e_x = (vy·h)/μ − x/|r|
e_y = (−vx·h)/μ − y/|r|
e   = sqrt(e_x² + e_y²)        (mimośród, bezwymiarowy)
```
**Test poprawności (definitywny):** dla orbity kołowej e MUSI wyjść ≈ 0
(numerycznie < 1e-9). Jeśli nie wychodzi zero na ręcznie podanym stanie orbity
kołowej — wzór jest źle zredukowany do 2D. To jest pierwszy test do napisania.

### Energia właściwa i półoś wielka (Lecture 2)
Całka energii ze slajdów: `ε = v²/2 − μ/r = −μ/(2a)`. Stąd:
```
v² = vx² + vy²;   r = sqrt(x² + y²)
ε = v²/2 − μ/r                 [J/kg]   (energia właściwa)
a = −μ/(2ε)                    [m]      (półoś wielka; a>0 dla orbity związanej)
```
- **ε < 0** → orbita związana (elipsa/okrąg). **ε ≥ 0** → ucieczka (parabola/hiperbola).
- Werdykt orbitalny WYMAGA ε < 0 (rakieta nie ucieka).

### Vis-viva (do sanity prędkości)
```
v² = μ·(2/r − 1/a)
```
Dla orbity kołowej (a = r): `v_circ = sqrt(μ/r)`. Dla ucieczki: `v_esc = sqrt(2μ/r)`.

### Perygeum i apogeum (Lecture 1)
Parametr orbity `p = h²/μ`. Promienie skrajne:
```
r_p = p/(1+e) = a·(1−e)        (perygeum — najniższy punkt)
r_a = p/(1−e) = a·(1+e)        (apogeum)
```
**Werdykt sukcesu** (z `constants.py`): `r_p > R⊕ + MIN_PERIAPSIS_ALTITUDE`
(czyli r_p > 6578.1 km) ORAZ `e < MAX_ECCENTRICITY_LEO` (e < 0.25).
Wysokość perygeum: `h_p = r_p − R⊕`.

### Okres (Kepler III, do telemetrii/wizualizacji)
```
P = 2π · sqrt(a³/μ)            [s]   (tylko dla orbity związanej, a>0)
```

---

## 2. Liczby kontrolne — orbity kołowe LEO (ZWERYFIKOWANE)

Twarde wartości odniesienia. Silnik liczy → porównuje z tą tabelą. Rozjazd =
błąd w implementacji, nie w fizyce. (μ, R⊕ z `constants.py`.)

| h [km] | r [km] | v_circ [m/s] | okres [min] | ε [MJ/kg] |
|--------|--------|--------------|-------------|-----------|
| 200 | 6578.1 | 7784.26 | 88.49 | −30.297 |
| 300 | 6678.1 | 7725.76 | 90.52 | −29.844 |
| 400 | 6778.1 | 7668.56 | 92.56 | −29.403 |
| 500 | 6878.1 | 7612.61 | 94.62 | −28.976 |
| 800 | 7178.1 | 7451.83 | 100.87 | −27.765 |

Kanoniczne sanity (najczęściej cytowane): **prędkość kołowa na 400 km ≈ 7,67 km/s**,
okres ≈ 92,6 min. To jest test, który brief wymienia w kryteriach akceptacji.

Granica orbity związanej @400 km: v_circ = 7668,6 m/s, v_esc = 10845,0 m/s
(stosunek √2). Między nimi — orbita eliptyczna.

### Test mimośrodu (do napisania jako pierwszy)
- Orbita kołowa 400 km: stan [r, 0, 0, v_circ] → e ≈ 0 (zweryfikowano: 1.6e-16). ✓
- Elipsa r_p=300 km, r_a=800 km: e = 0.0361 (teoria = obliczone). ✓
  (a = 6928,1 km, v w perygeum = 7863,9 m/s.)

---

## 3. Siły w fazie wznoszenia/wstawienia (Lecture 10.6 + napęd SMAD)

Te równania budują prawą stronę (RHS) całkowania faz 1-2. Wszystkie w układzie
inercjalnym kartezjańskim — UWAGA NA KIERUNKI (najczęstsze źródło cichego błędu).

### Grawitacja — zawsze do środka Ziemi
```
g_vec = −μ/r³ · (x, y)        [m/s²]   (przyspieszenie, NIE siła)
|g| = μ/r²
```
„Pionowo w górę" w tym układzie = wzdłuż +r/|r| (od środka), NIE wzdłuż osi y.
To rozróżnienie jest krytyczne: start „pionowy" to start wzdłuż wektora promienia.

### Ciąg — wzdłuż osi rakiety (profil kąta)
Siła ciągu `F_thrust = thrust` (z `Stage`), kierunek wg profilu kąta.
Przyspieszenie = F_thrust/m (m = bieżąca masa, MALEJĄCA). Profil kąta dla kroku 2:
start pionowy (wzdłuż r) → stopniowe pochylanie wg `launch_angle_deg`. NIE gravity
turn (to ulepszenie). Strumień masy: `dm/dt = −thrust/(Isp·g0)` (ujemny, paliwo ubywa).

### Opór atmosferyczny (Lecture 10.6)
Ze slajdów — przyspieszenie zaburzające: `a_drag = −c·ρ·v²·î_t` (przeciwnie do
wektora prędkości). W formie inżynierskiej dla silnika:
```
D = 0.5 · ρ(h) · v² · Cd · A          [N]   (siła oporu)
a_drag = −(D/m) · v_vec/|v|           (przyspieszenie, przeciw prędkości)
```
gdzie Cd = `drag_coefficient`, A = `reference_area` (z `Stage`).

### Gęstość atmosfery — model eksponencjalny (Lecture 10.6)
Ze slajdów: `ρ(r) = ρ0·exp(−(r−q)/H)`, gdzie H = wysokość skali. W formie
wysokościowej dla silnika:
```
ρ(h) = ρ0 · exp(−h/H)         [kg/m³]
```
Wartości orientacyjne (do dostrojenia, NIE krytyczne — opór i tak w ryczałcie
strat): ρ0 ≈ 1,225 kg/m³ (poziom morza), H ≈ 7000-8500 m (wysokość skali troposfery).
UWAGA: to przybliżenie. Slajdy podają model, nie konkretne H dla Ziemi — wartość
dostrojeniowa. Dla bilansu Δv nieistotna (patrz próg wyłączenia oporu niżej).

### Próg wyłączenia oporu (decyzja z ADR sekcja 3)
Opór wyłączamy, gdy `D/(m·g) < ε` (ε ≈ 1e-3…1e-4) — jako ZDARZENIE kończące fazę
z oporem, NIE twardym progiem wysokości. Powód (z ADR): 30 km daje jeszcze ~1,5%
gęstości przygruntowej; próg na sile jest fizycznie czystszy niż na wysokości.

---

## 4. Budżet Δv — fallback i sanity (równanie Ciołkowskiego)

Dla fallbacku uproszczonego (brief sekcja „Fallback") oraz jako sanity budżetu.
Równanie Ciołkowskiego per stopień:
```
Δv_i = Isp_i · g0 · ln(m0_i / m1_i)
```
gdzie m0_i = masa na początku spalania stopnia i (payload + wszystkie wet_mass
od i w górę), m1_i = m0_i − propellant_mass_i.

Budżet do LEO (z `constants.py` + SMAD):
- Idealna prędkość orbitalna LEO: ~7,7 km/s (patrz tabela sekcja 2).
- Typowe straty (grawitacyjne + aero): `TYPICAL_LAUNCH_LOSSES_DV` = 1750 m/s.
- **Wymagany budżet Δv do LEO: ~9,4 km/s** (orbita + straty).
- Werdykt fallbacku: suma Δv stopni − straty ≥ ~9,4 km/s → orbita osiągnięta.

Złoty preset (`GOLDEN_PRESET.md`): Δv idealne ≈ 13 846 m/s, po stratach ≈ 12 096
m/s, zapas ≈ 2 696 m/s ponad budżet. To warunek KONIECZNY (paliwa wystarcza),
nie gwarancja — pełna fizyka z profilem kąta potwierdza osiągnięcie orbity.

---

## 5. Lista herezji, których NIE popełniać

Najczęstsze ciche błędy w tej klasie problemów — sprawdź, że żadnego nie ma:

1. **Werdykt z wysokości, nie z elementów.** „Rakieta osiągnęła 400 km → orbita"
   jest FAŁSZEM — można być na 400 km z prędkością pionową i spaść z powrotem.
   Werdykt liczymy z ε, e, r_p (sekcja 1), nie z chwilowej wysokości. (ADR sekcja 3.)
2. **Mylenie „pionowo" z osią y.** W układzie inercjalnym pionowo = wzdłuż promienia.
   Grawitacja zawsze do środka (−r/|r|), nie „w dół" po osi y. (sekcja 3.)
3. **Źle zredukowany wektor mimośrodu w 2D.** Test: orbita kołowa → e≈0. (sekcja 1.)
4. **Stała masa przy liczeniu ciągu.** Masa MALEJE (dm/dt = −thrust/(Isp·g0));
   przyspieszenie = thrust/m rośnie w trakcie spalania. (sekcja 3.)
5. **Zwykły RK na długiej propagacji orbity → dryf energii.** Jeśli całkujesz
   orbitę (OPCJA), użyj symplektycznego (leapfrog). Werdykt analityczny tego
   unika całkowicie. (ADR sekcja 3, brief.)
6. **Separacja stopnia zmieniająca pozycję/prędkość.** Separacja to skok TYLKO
   masy m; x, y, vx, vy ciągłe. (ADR sekcja 3.)
7. **ε ≥ 0 zinterpretowane jako orbita.** ε ≥ 0 to ucieczka, NIE orbita. Werdykt
   wymaga ε < 0 ORAZ r_p i e w progach. (sekcja 1.)

---

## Źródła
- Wzory orbitalne: slajdy wykładów astrodynamiki (16.346, problem dwóch ciał,
  Lecture 1-2; opór atmosferyczny Lecture 10.6).
- Stałe i progi: `dt_contracts/constants.py` (pochodzą ze SMAD 3rd ed.).
- Liczby kontrolne (sekcja 2): policzone i zweryfikowane numerycznie z μ, R⊕.
