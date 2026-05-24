# Rocket Digital Twin — Kompas projektu

JEDYNE źródło prawdy o tym, dokąd idziemy i gdzie jesteśmy. Zastępuje dawne
ROADMAP / CONCEPT / VERSION. Cztery sekcje: Wizja (statyczna), Cele (priorytety),
Stan bieżący (nadpisywany), Dziennik (narastający). Gdy się zgubisz — wracasz tu.

PISARZ KOMPASU: człowiek + doradca (jeden pisarz). Instancje NIE edytują tego
pliku — zgłaszają postęp w commitach i raportach, aktualizacja jest centralna.

Deadline: hackaton. Wszystko poniżej podporządkowane temu ograniczeniu: najpierw
rzeczy, bez których nie ma czego pokazać.

---

## 1. Wizja

Cyfrowy bliźniak rakiety wynoszącej mały satelita na niską orbitę (LEO).
Sednem jest PĘTLA Digital Twina: użytkownik zmienia parametr rakiety →
symulacja przelicza misję → widać wpływ na powodzenie (orbita osiągnięta lub
nie) i na trajektorię. To, co odróżnia projekt od zwykłego kalkulatora, to
możliwość eksperymentowania na żywo i natychmiastowego widzenia skutków.

Sukces = działające demo tej pętli, które da się pokazać jurorom w 3 minuty:
oto rakieta, zmieniam parametr, przeliczam, widzę inny wynik. **OSIĄGNIĘTE.**

---

## 2. Cele (priorytety MUST / SHOULD / COULD)

Reguła czasu: NIE dotykamy SHOULD, póki wszystkie MUST nie działają end-to-end.
NIE dotykamy COULD, póki SHOULD nie są zrobione.

### MUST — bez tego nie ma projektu
- [x] Silnik liczy poprawną trajektorię misji do LEO.
      Pełna fizyka: 3 fazy (wznoszenie z oporem ρ(h) → wstawienie → orbita),
      gravity turn, manewr Hohmanna (coast do apogeum + circularyzacja na S3),
      zdarzenia (max-Q, wypalenia, separacje). Fallback Δv jako jawna gałąź
      bezpieczeństwa. 19 testów zielonych.
- [x] Werdykt orbitalny z elementów keplerowskich (orbita: tak/nie + powód).
      ε, e, perygeum z wektora stanu (wektor Laplace'a). Werdykt z powodem i
      liczbami. Zweryfikowany: orbita kołowa → e≈0, v_circ@400km ≈ 7,67 km/s.
- [x] API wystawia symulację: SimRequest → SimResult (HTTP/JSON).
      4 endpointy, graceful AI, OpenAPI z kontraktu. Woła prawdziwy silnik
      (simulate(SimRequest)). Zweryfikowane przez /simulate na złotym presecie.
- [x] Frontend: PIONOWY PLASTER end-to-end — zmiana parametru → przelicz →
      nowa trajektoria 2D + werdykt. ZŁOTY SCENARIUSZ DZIAŁA NA ŻYWYM API.
      Badge "API LIVE · SILNIK ✓"; werdykt i trajektoria z silnika, nie z JS.
      Syntetyk zszedł do roli fallbacku offline.
- [x] Gotowy preset rakiety („złoty przykład"), który NA PEWNO osiąga orbitę.
      golden_preset() (3 stopnie). Osiąga orbitę na PRAWDZIWEJ fizyce:
      perygeum ~1244 km, apogeum ~1302 km, e=0,0038 (niemal kołowa).
- [ ] Prezentacja (slajdy + scenariusz wideo) gotowa do nagrania.
      STAN: NIETKNIĘTA poza zarysem. PRESENTATION_OUTLINE.md sprzed implementacji
      — wymaga aktualizacji pod realny stan demo. JEDYNY niedomknięty MUST.

**MUST techniczny (silnik + API + front + preset) DOMKNIĘTY END-TO-END NA
PRAWDZIWEJ FIZYCE.** Pozostaje prezentacja — jedyny MUST zależny wyłącznie od
człowieka, nie od instancji.

### SHOULD — mocno wzmacnia, jeśli MUST gotowe
- [x] Dashboard telemetrii: prędkość / wysokość / g-force / Q w czasie (Recharts).
      HUD transmisja-style ze scrubberem + wykresy g-force i ciśnienia dynamicznego.
- [x] Wizualizacja trajektorii (wykres 2D wysokość/prędkość z markerami zdarzeń).
- [x] Widoczne zdarzenia misji na osi czasu (sekwencja SpaceX-style):
      LIFTOFF → MAX-Q → MECO → SEP → SECO → APOGEE → TECO → ORBITAL INSERTION.
      Piki g-force zgrane ze separacjami (dowód spójności telemetrii).
- [ ] Frontend: dodawanie/usuwanie stopni w UI (zmienna liczba stopni 1–4).
      Wzmacnia demo: „2 stopnie nie dolatują → dodaję 3. → orbita". Kontrakt i
      silnik już wspierają. Najsilniejszy niezrobiony SHOULD. = część B frontu.
- [ ] Wykresy walidacyjne backendu (skrypt PNG + JSON).
- [ ] Nagrane wideo demo (~3 min).

### COULD — tylko jeśli zostanie czas
- [ ] Pakiet AI: optymalizacja masy startowej przy warunku orbity.
      Warstwa graceful w API i froncie GOTOWA (włączy się sama, gdy dt_ai powstanie).
- [ ] Wizualizacja 3D trajektorii (Three.js).
- [ ] Porównanie wielu scenariuszy obok siebie.

### Wykresy walidacyjne — co pokazują (decyzja: wszystkie trzy)
Jeden skrypt walidacyjny zrzuca PNG + JSON: (1) zachowanie energii/pędu,
(2) porównanie z Ciołkowskim, (3) trajektoria + profile. SHOULD, niezrobione.

---

## 3. Stan bieżący (NADPISYWANY — zawsze aktualny obraz)

### Plaster: DZIAŁA END-TO-END NA PRAWDZIWEJ FIZYCE
- **Silnik** — pełna fizyka scalona do main. Gravity turn + Hohmann + zdarzenia
  + werdykt keplerowski + acceleration w telemetrii. 19 testów. Złoty preset
  → orbita 1244 km, e=0,0038. Fallback Δv jako bezpiecznik.
- **API** — woła prawdziwy silnik (simulate(SimRequest)). Zweryfikowane:
  /simulate zwraca realny SimResult. Graceful AI gotowe (503 bez dt_ai).
- **Frontend** — podłączony do żywego API (część A domknięta). Złoty preset
  trójstopniowy, werdykt z silnika, sekwencja misji SpaceX, HUD telemetrii,
  g-force, trajektoria 2D. Badge sygnalizuje źródło danych (silnik/stub/offline).

### Zweryfikowane liczby (złoty preset, prawdziwa fizyka)
- Orbita: perygeum 1244 km, apogeum 1302 km, e=0,0038, okres 111 min.
- Max-Q 60 kPa, czas lotu ~1452 s (w tym coast do apogeum).
- Profil g-force: S1 ~1,3→7,8g, S2 →9g, coast ~0, S3 circularyzacja ~3g.

### Decyzje wykonawcze (w mocy)
- Sygnatura simulate(SimRequest). Jeden złoty preset (decyzja A). Jeden pisarz
  kompasu. Fizyka realistyczna z jawnym fallbackiem Δv. Graceful AI (ADR).
- Orbita ~1244 km (górny LEO) ZAAKCEPTOWANA — werdykt prawdziwy, niemal kołowa.
  Strojenie do niższego LEO = opcja, nie konieczność (do demo bez znaczenia,
  można pokazać inną orbitę zmieniając parametry na żywo).
- Merge zawsze przez main; współdzielony uv.lock / root pyproject — za zgodą człowieka.

### Następny krok
- **PREZENTACJA** — jedyny niedomknięty MUST. Aktualizacja PRESENTATION_OUTLINE.md
  pod realny stan + scenariusz 3-min demo (Akt 1: orbita osiągnięta → Akt 2:
  pogorszenie parametru → brak orbity) + narracja. To finisz MUST.
- Opcjonalnie potem (SHOULD): dodawanie stopni w UI (część B frontu); nagranie wideo.

### Dokumentacja dla jury (gotowa)
- docs/PHYSICS_MODEL.md — podstawy fizyczne (źródła MIT 16.346, SMAD).
- docs/SYSTEM_OVERVIEW.md — opis działania systemu (architektura, pętla, demo).
- docs/DESIGN_DECISIONS.md — uzasadnienia wyborów (OpenRocket, monorepo, fazy).
- docs/architecture/PHYSICS_THEORY_BASE.md — baza teorii dla silnika (wewn.).
- docs/tasks/GOLDEN_PRESET.md — wartości presetu.

---

## 4. Dziennik (NARASTAJĄCY — kamienie milowe, nie usuwać)

- 2026-05-23 [M1] — Fundament architektoniczny i kontrakt danych.
  Zatwierdzona architektura (monorepo/uv), gotowy kontrakt dt_contracts
  (schematy + stałe SMAD + testy logiki), komplet instrukcji dla instancji.
- 2026-05-24 [M2] — Pionowy plaster: silnik (krok 1) gotowy.
  simulate(...) -> SimResult (stub) + golden_preset() + 13 testów.
- 2026-05-24 [M3] — Boczne kawałki plastra (krok 1) + styki uzgodnione.
  API krok 1 (4 endpointy, graceful AI) i frontend krok 1 (na syntetyku) gotowe.
  Sygnatura simulate(SimRequest), jeden preset, jeden pisarz kompasu.
- 2026-05-24 [M4] — Prawdziwa fizyka: orbita z całkowania.
  Silnik krok 2/3: 3 fazy, werdykt keplerowski, gravity turn + manewr Hohmanna
  (coast do apogeum + circularyzacja). Złoty preset osiąga orbitę z PRAWDZIWEJ
  trajektorii (1244 km, e=0,0038), nie z fallbacku. Baza teorii fizycznej
  (źródła MIT/SMAD) jako referencja. 19 testów.
- 2026-05-24 [M5] — MUST DOMKNIĘTY END-TO-END NA ŻYWYM API.
  Front podłączony do żywego API (część A): werdykt i trajektoria z silnika,
  złoty preset trójstopniowy, badge źródła danych. Złoty scenariusz działa na
  prawdziwej fizyce: zmiana parametru → przelicz → realny werdykt z silnika.
  Pętla Digital Twina kompletna: UI → API → fizyka → werdykt → UI.
- 2026-05-24 [M6] — Wzbogacenie wizualne demo (SHOULD).
  Sekwencja misji SpaceX-style, HUD telemetrii transmisja-style ze scrubberem,
  wykresy g-force i ciśnienia dynamicznego. acceleration w telemetrii silnika
  (piki g-force zgrane ze separacjami). Dokumentacja techniczna dla jury (fizyka,
  system, decyzje). Pozostaje: prezentacja (MUST) + ew. dodawanie stopni (SHOULD).