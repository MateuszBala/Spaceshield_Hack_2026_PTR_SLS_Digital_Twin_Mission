# Zarys prezentacji i wideo

Cel: pokazać jurorom WARTOŚĆ w ~3 minuty. Przy tak krótkim czasie nie ma miejsca
na architekturę ani szczegóły techniczne — cały czas idzie na ZŁOTY SCENARIUSZ
DEMO (pętla Digital Twina). Jurorzy oceniają obraz, nie kod.

Format: slajdy + osobne wideo. Język: polski. Czas: ~3 min (twardy limit).

## Zasada nadrzędna
Prezentacja jest też SPECYFIKACJĄ celu MUST: jeśli coś jest na slajdzie/w demo,
to MUSI działać. Jeśli czegoś nie ma w tych 3 minutach — to nie jest MUST.

---

## Część A — Slajdy (minimalne, ~5 slajdów, tło dla wideo)

Slajdy mają być TŁEM, nie wykładem. Mało tekstu, duże hasła, jeden obraz na slajd.

1. **Tytuł + jedno zdanie** — „Cyfrowy bliźniak rakiety wynoszącej satelitę na
   LEO. Zmień parametr, przelicz, zobacz wpływ na misję.” Logo/wizualizacja w tle.

2. **Problem / po co** — projektowanie rakiety to gra kompromisów (masa vs orbita).
   Hasło: „Co się stanie, jeśli zmienię ten stopień?” — i że na to odpowiadamy
   natychmiast, symulacją.

3. **Złoty scenariusz (zapowiedź demo)** — jedna grafika pętli:
   parametry → symulacja → werdykt + trajektoria. „Zaraz pokażemy to na żywo.”

4. **Co pod spodem (1 slajd, lekko)** — fizyka oparta na realnych danych (SMAD),
   silnik liczący pełną misję, optymalizacja masy. Bez detali — tylko że to
   solidne, nie zabawka. (Jeśli AI gotowe: wspomnieć optymalizację.)

5. **Zamknięcie** — co osiągnęliśmy + co dalej (gdyby był czas: 3D, więcej
   scenariuszy). Podziękowanie.

---

## Część B — Scenariusz wideo (~3 min, to jest SEDNO)

Wideo to głównie samo demo z narracją. Kolejność przeklikania, pod którą budujemy
frontend. KAŻDY krok musi działać na presecie „złotego przykładu”.

### Akt 1 — Punkt wyjścia (~40 s)
- Pokaż interfejs z załadowanym PRESETEM rakiety, który osiąga orbitę.
- Uruchom symulację. Pokaż trajektorię 2D wznoszącą się na orbitę + werdykt
  „ORBITA OSIĄGNIĘTA” (z elementami: perygeum, mimośród).
- Narracja: „Oto rakieta trójstopniowa. Symulujemy jej misję — osiąga LEO.”

### Akt 2 — Pętla Digital Twina (~90 s, NAJWAŻNIEJSZE)
- Zmień JEDEN parametr na gorszy — np. zmniejsz masę paliwa stopnia 1 albo ciąg.
- Przelicz. Pokaż, że teraz trajektoria opada / orbita NIE osiągnięta
  („PERYGEUM PONIŻEJ PROGU” albo „BRAK ORBITY”).
- Narracja: „Zmieniam jeden parametr — i misja się nie udaje. To jest cyfrowy
  bliźniak: natychmiast widzę skutek decyzji projektowej.”
- (Jeśli telemetria gotowa) pokaż dashboard: profil prędkości/wysokości/masy.

### Akt 3 — Rozwiązanie (~40 s)
- Wariant A (jeśli AI gotowe): kliknij „optymalizuj” — pokaż, że AI znajduje
  konfigurację osiągającą orbitę przy minimalnej masie startowej.
- Wariant B (jeśli AI niegotowe): ręcznie skoryguj parametr z powrotem / pokaż
  inny preset, który się udaje. Narracja: „Wracam do konfiguracji, która działa.”
- Pointa: „Tyle eksperymentów, ile chcemy — bez budowania prawdziwej rakiety.”

### Akt 4 — Domknięcie (~10 s)
- (Jeśli gotowe) mignięcie 3D albo wykresów walidacyjnych jako dowód solidności.
- Hasło końcowe + ekran tytułowy.

---

## Zabezpieczenia (przy 3 min nie ma drugiego podejścia)
- Nagrywaj DOPIERO gdy demo działa stabilnie na presecie — nie improwizuj na żywo.
- Miej preset, który NA PEWNO przechodzi (Akt 1) i parametr, który NA PEWNO psuje
  misję (Akt 2) — sprawdzone wcześniej, nie zgadywane przy nagraniu.
- Jeśli AI niegotowe — Akt 3 wariant B działa bez AI. Wideo nie zależy od COULD.
- Backup: gdyby demo na żywo padło, miej nagrane wcześniej ujęcia kluczowych kroków.

## Co świadomie POMIJAMY w 3 minutach
- Architekturę pakietów, kontrakt, uv workspace, podział na worktree — to dla
  jurorów szum. Wspomnieć jednym zdaniem na slajdzie 4, nie więcej.
- Szczegóły numeryczne (solwery, fazy) — chyba że juror dopyta po prezentacji.
