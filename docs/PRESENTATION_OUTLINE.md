# Zarys prezentacji i wideo (zaktualizowany pod realny stan demo)

Cel: pokazać jurorom WARTOŚĆ w ~3 minuty. Cały czas idzie na ZŁOTY SCENARIUSZ
DEMO (pętla Digital Twina). Jurorzy oceniają obraz, nie kod.

Format: slajdy + osobne wideo. Język: polski. Czas: ~3 min (twardy limit).

## Stan systemu (do czego się odnosimy)
Demo DZIAŁA end-to-end na prawdziwej fizyce: UI → API → silnik → werdykt → UI.
Złoty preset (3 stopnie) osiąga orbitę: perygeum ~1244 km, apogeum ~1302 km,
e=0,0038 (niemal kołowa). Widoczne: werdykt, sekwencja misji SpaceX-style,
HUD telemetrii, g-force, trajektoria 2D, (jeśli gotowy) wykres orbity x–y.

## Zasada nadrzędna
Jeśli coś jest na slajdzie/w demo — MUSI działać. Nagrywamy DOPIERO gdy
przeklikanie jest sprawdzone na konkretnych wartościach.

---

## Część A — Slajdy (minimalne, ~5 slajdów, tło dla wideo)

Mało tekstu, duże hasła, jeden obraz na slajd. Slajdy są TŁEM, nie wykładem.

1. **Tytuł + jedno zdanie** — „Rocket Digital Twin: cyfrowy bliźniak rakiety
   wynoszącej satelitę na LEO. Zmień parametr, przelicz, zobacz wpływ na misję."
   W tle zrzut interfejsu z werdyktem „ORBITA OSIĄGNIĘTA".

2. **Problem / po co** — projektowanie rakiety to gra kompromisów (masa vs orbita).
   Hasło: „Co się stanie, jeśli zmienię ten stopień?" — odpowiadamy natychmiast,
   pełną symulacją misji, nie zgadywaniem.

3. **Złoty scenariusz (zapowiedź demo)** — grafika pętli:
   parametry → symulacja → werdykt + trajektoria. „Zaraz pokażemy na żywo."

4. **Co pod spodem (lekko, ale konkretnie)** — to nie zabawka:
   - pełna fizyka 3 faz lotu (wznoszenie z oporem → wstawienie → orbita),
   - werdykt z elementów keplerowskich (energia, mimośród, perygeum), NIE z wysokości,
   - gravity turn + manewr Hohmanna (coast do apogeum + circularyzacja),
   - oparte na realnych źródłach: MIT 16.346 Astrodynamics, SMAD.
   Jedno zdanie o architekturze: silnik / API / interfejs rozdzielone, budowane
   równolegle. Bez detali — tylko sygnał „solidne inżyniersko".

5. **Zamknięcie** — co osiągnęliśmy (działający cyfrowy bliźniak na prawdziwej
   fizyce) + co dalej (3D, optymalizacja AI, więcej scenariuszy). Podziękowanie.

---

## Część B — Scenariusz wideo (~3 min, to jest SEDNO)

Wideo to głównie samo demo z narracją. KAŻDY krok sprawdzony na konkretnych
wartościach PRZED nagraniem.

### Akt 1 — Punkt wyjścia (~40 s)
- Interfejs z załadowanym złotym presetem (3 stopnie: S1-core, S2, S3-upper).
  Badge „API LIVE · SILNIK ✓" — pokazuje, że to prawdziwa fizyka, nie atrapa.
- Kliknij „Przelicz". Pokaż werdykt „ORBITA OSIĄGNIĘTA" + elementy:
  perygeum ~1244 km, mimośród 0,0038, okres ~111 min.
- Pokaż sekwencję misji (LIFTOFF → MAX-Q → MECO → SEP → SECO → APOGEE →
  ORBITAL INSERTION) i trajektorię.
- Narracja: „Rakieta trójstopniowa. Symulujemy całą misję — od startu, przez
  separacje stopni, manewr na orbitę. Satelita osiąga stabilną orbitę."

### Akt 2 — Pętla Digital Twina (~90 s, NAJWAŻNIEJSZE)
- Zmień JEDEN parametr na gorszy — wartość USTALONA EMPIRYCZNIE przed nagraniem
  (patrz „Do sprawdzenia przed nagraniem" niżej). Kandydat: skrócenie czasu
  pracy lub ciągu górnego stopnia / S1.
- Przelicz. Pokaż werdykt „BRAK ORBITY" + powód (np. perygeum poniżej progu /
  orbita niezwiązana). Trajektoria pokazuje, że misja się nie domyka.
- Narracja: „Zmieniam jeden parametr — i misja się nie udaje. To jest sedno
  cyfrowego bliźniaka: natychmiast widzę skutek decyzji projektowej, zanim
  zbuduję cokolwiek z metalu."
- Pokaż dashboard telemetrii (prędkość/wysokość/g-force) jako dowód głębi symulacji.

### Akt 3 — Rozwiązanie (~40 s)
- AI jest COULD i niezrobione → idziemy WARIANTEM B (ręczna korekta):
  przywróć parametr / pokaż, że poprawna konfiguracja znów osiąga orbitę.
- Narracja: „Wracam do konfiguracji, która działa — albo szukam lepszej.
  Tyle eksperymentów, ile chcemy, bez budowania prawdziwej rakiety."
- (Jeśli zostanie czas i wykres orbity gotowy) pokaż tor x–y wokół Ziemi jako
  efektowne domknięcie — „tak wygląda osiągnięta orbita".

### Akt 4 — Domknięcie (~10 s)
- Hasło końcowe + ekran tytułowy.

---

## DO SPRAWDZENIA PRZED NAGRANIEM (krytyczne — nie zgadywać na żywo)

1. **Parametr psujący misję (Akt 2).** Stary „suwak demo" z fallbacku Δv jest
   NIEAKTUALNY (gravity turn zmienił fizykę). Przed nagraniem: w UI zmień
   kandydujący parametr (czas pracy/ciąg S3 lub S1), kliknij Przelicz, i ZNAJDŹ
   wartość, która NIEZAWODNIE daje „BRAK ORBITY". Zapisz tę wartość — to jest
   scenariusz Aktu 2. Sprawdź też, że powrót do oryginału znów daje orbitę (Akt 3).
2. **Czas obliczenia.** Lot ma ~22 min coastu (symulowane). Sprawdź, ile trwa
   realnie kliknięcie „Przelicz" — jeśli jest zauważalna pauza, w narracji ją
   „zagadaj" (mów w trakcie liczenia) albo przytnij w montażu.
3. **Stabilność.** Przeklikaj cały scenariusz 2-3 razy przed nagraniem — Akt 1
   (orbita) → Akt 2 (brak orbity) → Akt 3 (znów orbita). Ma działać za każdym razem.

---

## Zabezpieczenia (przy 3 min nie ma drugiego podejścia)
- Nagrywaj DOPIERO gdy demo działa stabilnie — nie improwizuj na żywo.
- Miej sprawdzony preset (Akt 1) i sprawdzoną wartość psującą (Akt 2).
- AI niegotowe → Akt 3 wariant B (ręczna korekta). Wideo nie zależy od COULD.
- Backup: nagraj kluczowe ujęcia osobno, gdyby demo na żywo padło — można zmontować.
- Uruchomienie przed nagraniem: API (`uvicorn dt_api.app:app --port 8000`) +
  front (`npm run dev`). Sprawdź badge „API LIVE · SILNIK ✓" przed startem.

## Co świadomie POMIJAMY w 3 minutach
- Architektura pakietów, kontrakt, uv workspace, worktree — szum dla jurorów.
  Jedno zdanie na slajdzie 4, nie więcej.
- Szczegóły numeryczne (solwery, fazy, zdarzenia) — tylko jeśli juror dopyta.
- Fakt, że orbita jest na 1244 km (górny LEO) — nie akcentować; „stabilna orbita
  okołoziemska" wystarcza. Jeśli juror techniczny dopyta: „to konkretny preset,
  system liczy dowolną orbitę — mogę pokazać niższą zmieniając parametry".