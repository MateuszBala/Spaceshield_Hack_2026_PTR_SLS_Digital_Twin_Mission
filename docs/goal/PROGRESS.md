# Rocket Digital Twin — Kompas projektu

JEDYNE źródło prawdy o tym, dokąd idziemy i gdzie jesteśmy. Zastępuje dawne
ROADMAP / CONCEPT / VERSION. Cztery sekcje: Wizja (statyczna), Cele (priorytety),
Stan bieżący (nadpisywany), Dziennik (narastający). Gdy się zgubisz — wracasz tu.

PISARZ KOMPASU: człowiek + doradca (jeden pisarz). Instancje NIE edytują tego
pliku — zgłaszają postęp w commitach i raportach, aktualizacja jest centralna.

Deadline: ~12 h od założenia tego pliku. Wszystko poniżej jest podporządkowane
temu ograniczeniu: najpierw rzeczy, bez których nie ma czego pokazać.

---

## 1. Wizja

Cyfrowy bliźniak rakiety wynoszącej mały satelita na niską orbitę (LEO).
Sednem jest PĘTLA Digital Twina: użytkownik zmienia parametr rakiety →
symulacja przelicza misję → widać wpływ na powodzenie (orbita osiągnięta lub
nie) i na trajektorię. To, co odróżnia projekt od zwykłego kalkulatora, to
możliwość eksperymentowania na żywo i natychmiastowego widzenia skutków.

Sukces za 12 h = działające demo tej pętli, które da się pokazać jurorom w 3
minuty: oto rakieta, zmieniam parametr, przeliczam, widzę inny wynik.

---

## 2. Cele (priorytety MUST / SHOULD / COULD)

Reguła czasu: NIE dotykamy SHOULD, póki wszystkie MUST nie działają end-to-end.
NIE dotykamy COULD, póki SHOULD nie są zrobione. To zabezpieczenie przed
„czterema niedokończonymi kawałkami o 4 nad ranem".

### MUST — bez tego nie ma projektu
- [ ] Silnik liczy poprawną trajektorię misji do LEO (model realistyczny;
      fallback uproszczony dopuszczalny — patrz Stan/decyzje).
      STAN: krok 1 (stub) gotowy; krok 2 (prawdziwa fizyka) W TOKU.
- [ ] Werdykt orbitalny z elementów keplerowskich (orbita: tak/nie + powód).
      STAN: część kroku 2 silnika, w toku.
- [x] API wystawia symulację: `SimRequest` → `SimResult` (HTTP/JSON).
      Endpoint `/simulate` odpowiada (na stubie silnika); spełnione strukturalnie,
      realna fizyka popłynie sama, gdy silnik krok 2 wyląduje.
- [ ] Frontend: PIONOWY PLASTER end-to-end — zmiana parametru → przelicz →
      nowa trajektoria 2D + werdykt. (To jest złoty scenariusz demo.)
      STAN: działa na danych SYNTETYCZNYCH (krok 1). Domknięcie na ŻYWYM API
      (werdykt z silnika, nie z JS) = część A briefu frontu krok 2.
      ZAKRES MUST: edycja WARTOŚCI parametrów istniejących stopni przy USTALONEJ
      liczbie stopni z presetu. Bez UI do dodawania/usuwania stopni.
- [x] Gotowy preset rakiety („złoty przykład”), który NA PEWNO osiąga orbitę.
      `GOLDEN_PRESET.md` + `golden_preset()` w silniku (trójstopniowy, Δv ideal
      ≈ 13 846 m/s, marża ~2,7 km/s nad LEO). Budżet zweryfikowany arytmetycznie;
      osiągnięcie orbity w pełnej fizyce potwierdza krok 2 silnika.
- [ ] Prezentacja (slajdy + scenariusz wideo) gotowa do nagrania.
      STAN: `PRESENTATION_OUTLINE.md` istnieje; do przeglądu pod realny stan demo.

### SHOULD — mocno wzmacnia, jeśli MUST gotowe
- [ ] Frontend: dodawanie/usuwanie stopni w UI (zmienna liczba stopni 1–4).
      Wzmacnia demo: „2 stopnie nie dolatują → dodaję 3. → orbita osiągnięta”.
      Kontrakt i silnik już to wspierają (stages: list 1–4); to praca tylko w UI.
- [ ] Dashboard telemetrii: prędkość / wysokość / masa w czasie (Recharts).
- [ ] Wizualizacja trajektorii dopracowana wizualnie (ładny wykres 2D).
- [ ] Wykresy walidacyjne backendu (skrypt PNG + JSON; patrz sekcja 2 dół).
- [ ] Widoczne zdarzenia misji na osi czasu (separacje, max-Q, wypalenia).
- [ ] Nagrane wideo demo (~3 min).

### COULD — tylko jeśli zostanie czas
- [ ] Pakiet AI: optymalizacja masy startowej przy warunku orbity.
- [ ] Wizualizacja 3D trajektorii (Three.js).
- [ ] Porównanie wielu scenariuszy obok siebie.

### Wykresy walidacyjne — co pokazują (decyzja: wszystkie trzy)
Jeden skrypt walidacyjny zrzuca PNG (dla człowieka / wideo) + JSON (dla analizy):
1. Zachowanie energii i pędu w czasie (czy solver nie dryfuje numerycznie).
2. Porównanie z równaniem Ciołkowskiego (czy budżet Δv się zgadza).
3. Trajektoria + profile prędkości/wysokości (czy lot jest fizyczny).

---

## 3. Stan bieżący (NADPISYWANY — zawsze aktualny obraz)

### Plaster: gdzie jest każdy kawałek
- **Silnik** — krok 1 DOMKNIĘTY i scalony do main (stub `simulate()` +
  `golden_preset()` + 13 testów). Krok 2 (prawdziwa fizyka: werdykt keplerowski →
  fazy → zdarzenia) W TOKU na `feat/engine`. To najwolniejsze ogniwo — słusznie
  ruszone najwcześniej. Reszta plastra czeka na jego realny `simulate()`.
- **API** — krok 1 DOMKNIĘTY (4 endpointy: /simulate, /capabilities, /health,
  /optimize; graceful AI = 503 nie 500; 10 testów; OpenAPI z kontraktu). Wykonuje
  poprawkę sygnatury (woła `simulate(request)` zamiast `request.rocket`). Potem
  CZEKA — endpoint nie wymaga zmian, gdy silnik dostarczy fizykę.
- **Frontend** — krok 1 DOMKNIĘTY (złoty scenariusz na danych SYNTETYCZNYCH:
  formularz, trajektoria 2D, werdykt, graceful AI). CZEKA na żywy silnik, by
  wykonać część A kroku 2 (podłączenie do API, werdykt z silnika, złoty preset).

### Styki uzgodnione w tej sesji (decyzje wykonawcze)
- **Sygnatura silnika: `simulate(request: SimRequest) -> SimResult`** (nie sam
  `RocketParams`). Powód: `include_telemetry` i `max_flight_time` żyją w
  `SimRequest`. Silnik i API dostosowują wywołanie. Kontrakt bez zmian.
- **Preset: jeden, złoty, trójstopniowy (decyzja A).** Frontend w kroku 1 użył
  własnej dwustopniowej rakiety (preset powstał po jego starcie) — w kroku 2
  front wyrównuje `src/data/preset.ts` do `GOLDEN_PRESET.md`. Silnik i front
  widzą TĘ SAMĄ rakietę (kotwica demo i testów).
- **Kompas ma jednego pisarza** (człowiek + doradca). Instancje nie edytują
  PROGRESS.md; zgłaszają postęp w commitach/raportach.
- **„Suwak demo"** — silnik w kroku 2 wyznacza empirycznie parametr+próg, przy
  którym werdykt spada (Akt 2 demo). Liczba czeka na zgłoszenie z silnika.

### Decyzje wykonawcze (wcześniejsze, nadal w mocy)
- Frontend: React + Vite + Recharts. Trajektoria 2D (MUST), 3D (COULD).
- Kolejność: PIONOWY PLASTER, potem pogrubianie. Merge: silnik → API → front.
- AI czeka (COULD). contracts read-only. Współdzielony uv.lock / root
  pyproject.toml — zmiany za zgodą człowieka.
- Fizyka: realistyczna jako cel, JAWNY fallback Δv (Ciołkowski − straty) jako
  świadoma gałąź, nie improwizacja.
- Graceful AI: API zwraca „niedostępne”, front chowa optymalizację (ADR).

### Następny krok
- Silnik kończy krok 2 (preset osiąga orbitę na prawdziwej fizyce + rekomendacja
  „suwaka demo"). Po scaleniu do main → API i front domykają MUST na żywym
  plastrze. To zamyka kolumnę MUST end-to-end.

### Zasoby wiedzy dla silnika
- `docs/architecture/PHYSICS_THEORY_BASE.md` — zweryfikowana baza teorii: wzory
  orbitalne ze slajdów astrodynamiki (wektor mimośrodu w 2D, energia, vis-viva,
  perygeum, Kepler), tabela liczb kontrolnych (v_circ, okres, ε dla orbit LEO —
  policzone numerycznie z μ/R), model oporu/gęstości, lista 7 „herezji" do
  uniknięcia. Silnik liczy ze źródła, nie z pamięci.
- `docs/tasks/GOLDEN_PRESET.md` — preset „złotej rakiety" (3 stopnie, Δv ideal
  ≈ 13 846 m/s, marża ~2,7 km/s nad LEO).

### Briefy gotowe (oczekują na moment wdrożenia)
- `BRIEF-engine-02-thickening.md` — silnik realizuje TERAZ.
- `BRIEF-frontend-02.md` — czeka na żywy silnik (część A = domknięcie MUST).

---

## 4. Dziennik (NARASTAJĄCY — kamienie milowe, nie usuwać)

Wpis = osiągnięty cel funkcjonalny (lub przygotowawczy na tym etapie).
Format: `RRRR-MM-DD [Mn] — nazwa`. Jedna–dwie linie opisu.

- 2026-05-23 [M1] — Fundament architektoniczny i kontrakt danych.
  Zatwierdzona architektura (monorepo/uv), gotowy kontrakt dt_contracts
  (schematy + stałe SMAD + testy logiki), komplet instrukcji dla instancji
  (CLAUDE.md, copilot, commity). Wejście do pracy równoległej zabezpieczone.
- 2026-05-24 [M2] — Pionowy plaster: silnik (krok 1) gotowy.
  `dt_physics.simulate(...) -> SimResult` wywoływalne, zwraca poprawny
  kontrakt (stub). `golden_preset()` zaimplementowany i zwalidowany (13 testów).
  API może importować i wołać silnik — pionowy plaster odblokowany.
- 2026-05-24 [M3] — Boczne kawałki plastra (krok 1) gotowe + styki uzgodnione.
  API krok 1 (4 endpointy, graceful AI, OpenAPI z kontraktu, 10 testów) i
  frontend krok 1 (złoty scenariusz na syntetyku, graceful AI) DOMKNIĘTE.
  Rozstrzygnięto trzy styki: sygnatura `simulate(SimRequest)`, jeden złoty preset
  (decyzja A), jeden pisarz kompasu. Briefy kroku 2 (silnik, front) gotowe.
  Plaster żyje strukturalnie end-to-end (stub/syntetyk); pozostaje pogrubienie do
  prawdziwej fizyki (silnik krok 2 w toku).
