# Brief: physics-engine — krok 3 (gravity turn: prawdziwa orbita związana)

Typ: zadaniowy (jednorazowy). Adresat: instancja w worktree `physics-engine`.
Poprzednik: `BRIEF-engine-02-thickening.md` (krok 2 — fazy, werdykt keplerowski,
fallback Δv ZROBIONE; ale prawdziwa trajektoria NIE domyka orbity).
Powiązane: `PHYSICS_THEORY_BASE.md`, `GOLDEN_PRESET.md`, ADR architektury sekcja 3,
kompas `docs/goal/PROGRESS.md`.

Ten brief naprawia JEDEN problem fizyczny zdiagnozowany po kroku 2. Nie przepisuje
silnika — dokłada gravity turn i domknięcie orbity do istniejących faz.

---

## Problem do naprawienia (diagnoza — przeczytaj, bo zmienia Twoje założenie)

W kroku 2 pełne całkowanie na złotym presecie dawało orbitę HIPERBOLICZNĄ (ε>0,
ucieczka) lub skrajnie eliptyczną, więc werdykt `reached_orbit=True` pochodził z
fallbacku Δv, nie z trajektorii. Raport kroku 2 zdiagnozował przyczynę jako
„nadmiar Δv przy spalaniu poziomym". **TA DIAGNOZA JEST BŁĘDNA** — zweryfikowano
niezależnym całkowaniem:

- Przyczyną NIE jest nadmiar paliwa. Te same stopnie dają orbitę związaną LUB
  ucieczkę zależnie WYŁĄCZNIE od profilu kąta. Gdyby winne było paliwo, żaden
  profil nie dałby orbity związanej — a wolniejsze profile ją dają.
- Prawdziwa przyczyna: **prosty profil kąta (pochyl-i-trzymaj) zostawia orbitę
  OTWARTĄ.** Perygeum trafia blisko celu, ale apogeum ucieka w kosmos (e ≈ 0,6–0,9),
  bo nie ma sprzężenia kąta ciągu z wektorem prędkości. Prosty profil wpycha
  energię w prędkość, ale nie „domyka" elipsy do orbity o bezpiecznym perygeum.
- To jest dokładnie powód, dla którego prawdziwe rakiety używają GRAVITY TURN, a
  nie zadanego profilu czasowego.

Wniosek: fallback Δv ma zostać jako bezpiecznik, ale CEL kroku 3 to żeby
PRAWDZIWA trajektoria (gałąź keplerowska) dawała orbitę związaną — wtedy werdykt
i rysowana trajektoria są spójne, a demo pokazuje prawdziwy cyfrowy bliźniak.

---

## Cel (definicja ukończenia kroku 3)

`simulate(SimRequest(rocket=golden_preset()))` zwraca `reached_orbit=True` z
**gałęzi keplerowskiej** (prawdziwego całkowania, NIE fallbacku Δv), z orbitą:
- ε < 0 (związana),
- perygeum > R⊕ + MIN_PERIAPSIS_ALTITUDE (>200 km nad powierzchnią),
- e < MAX_ECCENTRICITY_LEO (< 0,25).

CEL werdyktu (POTWIERDZONY z człowiekiem): orbita ZWIĄZANA z bezpiecznym
perygeum, e < 0,25 — NIE idealnie kołowa. Trafienie e<0,05 jest niepotrzebnie
trudne; próg kontraktu (e<0,25) to realistyczny i wystarczający cel.

---

## Kierunek techniczny (zweryfikowany kierunkowo — Ty stroisz na żywym solverze)

Diagnoza wskazała dwie dźwignie. Prawdopodobnie potrzebujesz OBU:

1. **Gravity turn (kąt prograde).** Po krótkim locie pionowym (kick przy małej
   wysokości/prędkości — rzędu 1–2 km wysokości albo kilkanaście s), kierunek
   ciągu PODĄŻA ZA WEKTOREM PRĘDKOŚCI (prograde), zamiast być zadaną funkcją
   czasu. Kąt ciągu = kąt wektora prędkości względem lokalnej pionowej (promienia).
   To naturalnie kładzie rakietę i domyka tor — kąt sam dąży do poziomu, gdy
   rakieta nabiera prędkości orbitalnej. Mały początkowy „pitch kick" (kilka
   stopni od pionu tuż po starcie) inicjuje turn.

2. **Cutoff górnego stopnia na prędkości orbitalnej.** Górny stopień NIE musi
   wypalać całego paliwa. Odetnij ciąg (zdarzenie terminal=True), gdy prędkość
   osiągnie wartość kołową dla bieżącego promienia (`v ≈ sqrt(μ/r)`) NA DOCELOWEJ
   wysokości — nie tuż po starcie (uwaga: tuż po starcie v chwilowo przekracza
   lokalne v_circ przy małym r — to NIE jest moment cutoffu; warunek musi być
   bramkowany minimalną wysokością, np. h > 150 km). To zapobiega przepaleniu,
   które wypycha apogeum w kosmos. Nadmiarowe paliwo S3 zostaje niewykorzystane —
   to fizycznie poprawne (rezerwa).

UWAGA na pułapkę (sam w nią wpadłem podczas diagnozy): zdarzenie „v == v_circ"
bez bramki wysokościowej odpala natychmiast po starcie (bo przy r≈R⊕ prędkość
szybko przekracza lokalne v_circ), urywając stopień w złym momencie i dając
r_p=0. Bramkuj warunek minimalną wysokością LUB minimalnym czasem lotu.

Preset (`golden_preset()`) prawdopodobnie NIE wymaga zmiany wartości — problem był
w sterowaniu, nie w paliwie. Jeśli po wdrożeniu gravity turn + cutoff orbita
domyka się z zapasem, zostaw preset jak jest. Jeśli marża jest za duża/za mała,
możesz dostroić `burn_time` górnego stopnia — ale to wtórne wobec sterowania.

---

## Kolejność pracy

1. **Gravity turn w profilu kąta.** Zamień zadany profil czasowy na prograde:
   pionowo do kicku → mały pitch kick → kąt podąża za wektorem prędkości. Faza 1
   i 2 używają tego samego mechanizmu.
2. **Cutoff górnego stopnia.** Zdarzenie terminal=True na `v ≥ sqrt(μ/r)`
   bramkowane minimalną wysokością (h > ~150 km). Po cutoffie reszta paliwa S3
   niewykorzystana.
3. **Werdykt z prawdziwej trajektorii.** Po sklejeniu faz stan końcowy → elementy
   keplerowskie (jak w kroku 2) → werdykt. Teraz gałąź keplerowska MA dać
   reached_orbit=True, a fallback Δv przestaje być potrzebny dla presetu (zostaje
   jako bezpiecznik dla skrajnych wejść).
4. **Test: trajektoria spójna z werdyktem.** Telemetria pokazuje wznoszenie →
   wypłaszczenie → orbita związana (apogeum i perygeum skończone, w LEO). To jest
   to, co front narysuje — nie może być uciekającej hiperboli przy werdykcie
   „orbita osiągnięta".

---

## Bezpiecznik: jeśli gravity turn nie domyka w czasie

Masz ~godzinę. Jeśli po realnej pracy gravity turn wciąż nie daje orbity z e<0,25
(stroisz kick, bramkę cutoffu, a orbita zostaje zbyt eliptyczna):
1. NIE wracaj do prostego profilu — gorszy.
2. Zostaw fallback Δv jako gałąź werdyktu (działa, da reached_orbit=True), ALE
   zadbaj, by trajektoria RYSOWANA była spójna — przy aktywnym fallbacku zwróć
   telemetrię parametryczną (krzywa wznoszenia kończąca się na wysokości orbity),
   NIE uciekającą hiperbolę z całkowania. To zabezpiecza demo przed rozjazdem
   „werdykt mówi orbita, wykres pokazuje ucieczkę".
3. ZGŁOŚ stan w raporcie — człowiek zdecyduje, czy to wystarcza, czy stroimy dalej.

---

## Kryteria akceptacji

- `simulate(SimRequest(rocket=golden_preset()))` → `reached_orbit=True` z gałęzi
  KEPLEROWSKIEJ (sprawdź, że fallback NIE jest aktywny dla presetu).
- Orbita: ε<0, perygeum>200 km nad powierzchnią, e<0,25.
- Trajektoria spójna z werdyktem (apogeum/perygeum skończone, w LEO; brak hiperboli).
- Test negatywny: gorszy parametr → reached_orbit=False (zaktualizuj „suwak demo"
  jeśli gravity turn zmienił próg — zgłoś nową wartość w raporcie).
- Liczby kontrolne nadal trzymają (v_circ@400km≈7,67 km/s — PHYSICS_THEORY_BASE §2).
- Sanity z bazy teorii §5: werdykt z elementów nie z wysokości; ε<0 dla orbity.

---

## Granice i zasady (przypomnienie)

- Piszesz WYŁĄCZNIE w `packages/physics-engine/`. `dt_contracts` read-only —
  progi (MIN_PERIAPSIS, MAX_ECCENTRICITY) bierzesz z `constants`, NIE zmieniasz.
- Stałe z `dt_contracts.constants`. SI, kanoniczny stan, werdykt z Keplera.
- NIE edytuj `docs/goal/PROGRESS.md` — zgłaszasz w raporcie i commicie.
- Commit np. `<feat,fix>(physics-engine): gravity turn + cutoff orbity`.

## Po ukończeniu kroku 3
- Zgłoś (w raporcie): preset osiąga orbitę z PRAWDZIWEJ trajektorii (gałąź
  keplerowska, nie fallback) + wartości orbity (perygeum, apogeum, e) +
  zaktualizowany „suwak demo".
