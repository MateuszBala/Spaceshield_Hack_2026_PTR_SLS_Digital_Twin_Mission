# Podstawy fizyczne modelu symulacji

Dokument techniczny — Rocket Digital Twin. Wyjaśnia, na jakiej teorii opiera się
silnik symulacji misji wynoszenia satelity na LEO. Adresat: oceniający projekt.

Zadanie dopuszcza uproszczone modele („nie musi odwzorowywać pełnej fizyki
orbitalnej w sposób profesjonalny — liczy się koncepcja, działający prototyp").
Skorzystaliśmy z tego świadomie: każde uproszczenie jest decyzją inżynierską z
uzasadnieniem, nie luką. Poniżej pokazujemy, co modelujemy dokładnie, co upraszczamy
i dlaczego — wraz ze źródłami.

Źródła teorii: wykłady MIT 16.346 *Astrodynamics* (problem dwóch ciał, elementy
keplerowskie) oraz *Space Mission Analysis and Design* (SMAD, 3rd ed.) — stałe
fizyczne, progi orbitalne, zakresy parametrów napędu.

---

## 1. Sformułowanie: jeden układ, jeden wektor stanu

Cały lot — od startu z powierzchni po orbitę — liczymy w **jednym układzie
odniesienia**: inercjalnym, kartezjańskim, ze środkiem Ziemi w początku. Stan
rakiety to pięć liczb:

```
[x, y, vx, vy, m]   —   pozycja (2D), prędkość (2D), masa
```

Lot toczy się w płaszczyźnie orbity (2D), co dla modelu uproszczonego w zupełności
wystarcza — orbita jest płaska, a wszystkie istotne wielkości (wysokość, prędkość,
energia, mimośród) liczą się z tego stanu.

Zaleta tego wyboru: **przejścia między fazami lotu nie wymagają konwersji układów.**
Faza wznoszenia, wstawienia i orbity to ten sam stan w tym samym układzie — zmienia
się tylko dominująca fizyka (które siły działają). Separacja stopnia to nieciągłość
wyłącznie w masie `m`; pozycja i prędkość są ciągłe. Eliminuje to całą klasę błędów
typowych dla symulatorów wielofazowych.

---

## 2. Trzy fazy lotu = trzy reżimy numeryczne

Misja dzieli się na trzy etapy, różniące się dominującą fizyką — a więc i metodą
całkowania. Przejścia między nimi to wykrywane **zdarzenia** (nie sztywne progi czasu).

| Faza | Dominująca fizyka | Zdarzenie kończące |
|------|-------------------|--------------------|
| Wznoszenie | ciąg + grawitacja + opór atmosfery ρ(h) | max-Q, separacje stopni, próg oporu |
| Wstawienie | ciąg + grawitacja (opór znikomy) | wypalenie / osiągnięcie prędkości orbitalnej |
| Orbita | dwa ciała, bez ciągu | werdykt z elementów keplerowskich |

Siły w fazach wznoszenia/wstawienia (układ inercjalny):

- **Grawitacja** — zawsze ku środkowi Ziemi: `g = −μ/r³ · (x, y)`, gdzie
  μ = 3,986·10¹⁴ m³/s² (stała grawitacyjna Ziemi, SMAD).
- **Ciąg** — wzdłuż osi rakiety, sterowany profilem kąta lotu. Masa maleje:
  `dm/dt = −ciąg/(Isp·g₀)` (zużycie paliwa, SMAD Eq. 17-4).
- **Opór** — `D = ½·ρ(h)·v²·C_d·A`, przeciwnie do prędkości; gęstość atmosfery
  malejąca wykładniczo z wysokością: `ρ(h) = ρ₀·exp(−h/H)`.

Krytyczne zdarzenia (max-Q, próg wyłączenia oporu, wypalenia, separacje) wykrywamy
jako **zera funkcji zdarzeń** w solverze, a nie skanując zapisaną telemetrię.
Dzięki temu ich położenie nie zależy od gęstości kroku całkowania — np. max-Q
(punkt maksymalnego ciśnienia dynamicznego, krytyczny dla obciążeń konstrukcji)
wykrywamy jako moment zerowania pochodnej dQ/dt.

---

## 3. Werdykt o orbicie — z elementów keplerowskich, nie z wysokości

To jest sedno modelu i najczęstsze źródło błędu w naiwnych symulatorach.
**Osiągnięcie wysokości orbitalnej nie oznacza orbity** — można być na 400 km z
prędkością skierowaną w górę i spaść z powrotem. O orbicie decydują elementy
toru, liczone z wektora stanu w momencie wstawienia (MIT 16.346, Lecture 1-2):

**Energia właściwa** (całka energii):
```
ε = v²/2 − μ/r
```
ε < 0 → orbita związana (rakieta nie ucieka). ε ≥ 0 → ucieczka. To pierwszy warunek.

**Półoś wielka** z energii: `a = −μ/(2ε)`.

**Wektor mimośrodu** (wektor Laplace'a, MIT 16.346):
```
μ·e = v × h − μ·r/|r|
```
gdzie h = r × v to moment pędu. Mimośród `e = |e|` mówi, jak wydłużona jest orbita.

**Perygeum** (najniższy punkt orbity): `r_p = a·(1−e)`. To on decyduje, czy orbita
jest stabilna — perygeum poniżej atmosfery oznacza powrót na Ziemię.

**Kryterium sukcesu** (progi ze SMAD, rozdz. 7.3):
- ε < 0 (orbita związana),
- wysokość perygeum > 200 km (powyżej gęstej atmosfery — stabilna LEO),
- mimośród e < 0,25 (orbita zbliżona do kołowej, nie skrajnie eliptyczna).

Werdykt podaje nie tylko „tak/nie", ale i powód oraz liczby (perygeum, apogeum,
mimośród, okres) — co czyni go interpretowalnym, nie magicznym.

**Weryfikacja poprawności:** dla idealnej orbity kołowej wektor mimośrodu daje
e ≈ 0 (sprawdzone numerycznie: rząd 10⁻¹⁶, czyli zero maszynowe), a prędkość
kołowa na 400 km wychodzi 7,67 km/s — zgodnie z wartością wynikającą z μ i promienia
Ziemi. To są testy, które łapią błędy implementacji niezależnie od reszty kodu.

---

## 4. Liczby kontrolne (orbity kołowe LEO)

Wartości referencyjne, którymi weryfikujemy poprawność silnika — policzone ze
stałych SMAD:

| Wysokość | Prędkość kołowa | Okres |
|----------|-----------------|-------|
| 200 km | 7,78 km/s | 88,5 min |
| 400 km | 7,67 km/s | 92,6 min |
| 800 km | 7,45 km/s | 100,9 min |

Budżet prędkości (Δv) wymagany do LEO: ~9,4 km/s — czyli ~7,7 km/s prędkości
orbitalnej plus ~1,75 km/s typowych strat grawitacyjnych i aerodynamicznych (SMAD
rozdz. 7.3). To pozwala szybko ocenić, czy dana konfiguracja rakiety w ogóle ma
szansę osiągnąć orbitę — niezależnie od pełnej symulacji.

---

## 5. Napęd — model spójny z definicji

Parametry stopnia to ciąg, impuls właściwy (Isp) i czas pracy. Z nich **wynikają**
(nie są podawane niezależnie) zużycie paliwa, masa paliwa i impuls całkowity:
```
strumień masy   = ciąg / (Isp · g₀)        [SMAD Eq. 17-4]
masa paliwa     = strumień masy · czas pracy
```
Dzięki temu nie da się zadać fizycznie sprzecznej konfiguracji — np. ciągu
niezgodnego ze zużyciem paliwa. Impuls właściwy ograniczamy do ≤ 455 s (twardy
limit napędu chemicznego wynoszącego z powierzchni; najwyższe sprawdzone w locie
wartości to RL10/SSME, ~446-455 s, SMAD rozdz. 17). Frakcje masowe stopni
(paliwo/masa całkowita) trzymamy w zakresie 0,80-0,95, zgodnym z realnymi stopniami
(SMAD: rakiety na paliwo ciekłe 0,85-0,93).

Budżet Δv pojedynczej konfiguracji szacujemy równaniem Ciołkowskiego per stopień:
```
Δv = Isp · g₀ · ln(masa_początkowa / masa_końcowa)
```
co służy też jako jawny, uproszczony tryb werdyktu (porównanie sumy Δv z budżetem
LEO) — zdefiniowana ścieżka awaryjna, gdyby pełne całkowanie zawiodło.

---

## 6. Co modelujemy, a co upraszczamy (świadomie)

**Modelujemy:** ruch w polu grawitacyjnym Ziemi (dwa ciała), ciąg i zużycie paliwa
per stopień, opór atmosferyczny z wykładniczym modelem gęstości, separacje stopni i
ładunku, max-Q, werdykt z pełnych elementów keplerowskich, parametryczną liczbę
stopni (1-4).

**Upraszczamy świadomie:**
- **Lot 2D** zamiast 3D — orbita jest płaska; trzeci wymiar nie wnosi nic do werdyktu.
- **Profil kąta lotu** zamiast pełnej optymalizacji sterowania — wystarcza do
  pokazania pętli Digital Twina (gravity turn jako ulepszenie).
- **Model gęstości atmosfery** wykładniczy zamiast warstwowego standardu — wpływ na
  bilans Δv pomijalny, bo opór wyłączamy progowo (gdy staje się nieistotny).
- **Brak modelu rotacji Ziemi, J2, oporu zależnego od kształtu** — poza zakresem
  zadania (uproszczony prototyp), nie wpływa na sedno: pętlę zmiana→symulacja→werdykt.

Te uproszczenia nie psują tezy projektu. Sednem Digital Twina jest **pętla**:
zmiana parametru rakiety → ponowne przeliczenie misji → widoczny wpływ na werdykt i
trajektorię. Ta pętla działa na prawdziwej fizyce dwóch ciał z prawdziwym werdyktem
keplerowskim — uproszczenia dotyczą wierności modelu lotu, nie poprawności mechaniki
orbitalnej, na której opiera się ocena sukcesu misji.

---

## Źródła

- MIT OpenCourseWare 16.346 *Astrodynamics* — problem dwóch ciał, wektor Laplace'a/
  mimośrodu, całka energii, prawa Keplera, wpływ oporu atmosferycznego na orbity.
- *Space Mission Analysis and Design* (SMAD), 3rd ed. — stałe Ziemi (App. B),
  standardowe g₀ (App. F), zakresy Isp i frakcji masowych oraz progi orbitalne
  (rozdz. 7, 17).
