# Rocket Digital Twin — Kompas projektu

JEDYNE źródło prawdy o tym, dokąd idziemy i gdzie jesteśmy. Zastępuje dawne
ROADMAP / CONCEPT / VERSION. Cztery sekcje: Wizja (statyczna), Cele (priorytety),
Stan bieżący (nadpisywany), Dziennik (narastający). Gdy się zgubisz — wracasz tu.

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
- [ ] Werdykt orbitalny z elementów keplerowskich (orbita: tak/nie + powód).
- [ ] API wystawia symulację: `SimRequest` → `SimResult` (HTTP/JSON).
- [ ] Frontend: PIONOWY PLASTER end-to-end — zmiana parametru → przelicz →
      nowa trajektoria 2D + werdykt. (To jest złoty scenariusz demo.)
      ZAKRES MUST: edycja WARTOŚCI parametrów istniejących stopni (masa paliwa,
      ciąg, Isp, masa ładunku) przy USTALONEJ liczbie stopni z presetu. Bez UI
      do dodawania/usuwania stopni — to wystarcza, by pokazać pętlę Digital Twina.
- [ ] Gotowy preset rakiety („złoty przykład”), który NA PEWNO osiąga orbitę.
- [ ] Prezentacja (slajdy + scenariusz wideo) gotowa do nagrania.

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

### Co gotowe
- Architektura: monorepo + uv workspace, 4 pakiety + frontend. Zatwierdzona.
- Kontrakt `dt_contracts`: schematy + stałe SMAD + testy (logika zweryfikowana;
  runtime Pydantica do potwierdzenia pierwszym `uv run pytest`).
- Komplet instrukcji: CLAUDE.md (root + 5 zagnieżdżonych), copilot-instructions,
  konwencje commitów, strategia CLAUDE.md.

### Decyzje wykonawcze (z tej sesji planistycznej)
- Frontend: React + Vite. Wykresy: Recharts. Trajektoria: 2D (MUST), 3D (COULD).
- Kolejność: PIONOWY PLASTER (cienka kolumna silnik→API→front), potem pogrubianie.
  NIE „skończ silnik, potem API, potem front”.
- Instancje: 2–3 równolegle. Pierwsza obsada pod plaster: silnik, API, frontend.
  AI czeka (COULD). contracts read-only — bez instancji.
- Fizyka: realistyczna jako cel, uproszczona jako JAWNY fallback (nie improwizacja).
- Brak AI obsłużony przez graceful degradation: API zwraca „niedostępne”, front
  chowa przycisk optymalizacji. Szczegóły: docs/decisions (ADR graceful AI).
- Preset rakiety: parametryczny, ale z gotowym presetem startowym osiągającym orbitę.

### Następny krok
- Spisać briefy zadaniowe dla instancji (silnik / API / frontend) pod pionowy
  plaster. To pierwszy realny task-level dokument.

---

## 4. Dziennik (NARASTAJĄCY — kamienie milowe, nie usuwać)

Wpis = osiągnięty cel funkcjonalny (lub przygotowawczy na tym etapie).
Format: `RRRR-MM-DD [Mn] — nazwa`. Jedna–dwie linie opisu.

- 2026-05-23 [M1] — Fundament architektoniczny i kontrakt danych.
  Zatwierdzona architektura (monorepo/uv), gotowy kontrakt dt_contracts
  (schematy + stałe SMAD + testy logiki), komplet instrukcji dla instancji
  (CLAUDE.md, copilot, commity). Wejście do pracy równoległej zabezpieczone.

  