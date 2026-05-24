# Brief: frontend — rozszerzenie wizualne (warstwa prezentacji, na syntetyku)

Typ: zadaniowy (jednorazowy). Adresat: instancja w worktree `frontend`.
Kontekst: krok 1 DOMKNIĘTY (złoty scenariusz na syntetyku). Część A kroku 2
(podłączenie żywego API) CZEKA na silnik — patrz niżej. Ten brief to praca
WIZUALNA niezależna od źródła danych, do zrobienia TERAZ na syntetycznym
`SimResult`, podczas gdy silnik kończy fizykę.
Powiązane: `BRIEF-frontend-02.md` (część A), kontrakt `dt_contracts/telemetry.py`,
`PRESENTATION_OUTLINE.md`, kompas `docs/goal/PROGRESS.md`.

---

## Zasada nadrzędna: pracujesz na SYNTETYKU, część A czeka

Werdykt z prawdziwej fizyki jeszcze nie istnieje (silnik kończy gravity turn).
NIE podłączaj się do żywego API w tym briefie — to część A kroku 2, czeka na
silnik. Pracujesz na syntetycznym `SimResult` zgodnym z kontraktem. Gdy silnik
ożyje, PODMIENISZ źródło danych (część A), a cała poniższa warstwa wizualna
zacznie pokazywać prawdziwe dane BEZ przepisywania. Dlatego buduj wszystko jako
prezentację `SimResult`, nie jako logikę specyficzną dla syntetyku.

To formalnie SHOULD (dopracowanie wizualne + zdarzenia misji). Robimy je teraz
ŚWIADOMIE, bo MUST frontu jest zablokowany cudzym ogniwem (silnik), a ta praca i
tak jest potrzebna do demo i nie zależy od fizyki. To wykorzystanie przymusowego
przestoju, nie łamanie reguły MUST→SHOULD.

---

## Co budujemy (wszystko czyta pola, które SĄ w kontrakcie — zweryfikowane)

### 1. Oś czasu misji — styl SpaceX (milestones)
Z `SimResult.events` (`list[MissionEvent]`). Każdy event ma `kind`, `t`,
`altitude`, `speed`, `note`. Wyrenderuj jako oś czasu / sekwencję kamieni
milowych, jak na transmisjach SpaceX.

Dostępne `EventKind` (z kontraktu — NIE wymyślaj nowych): `LIFTOFF`, `MAX_Q`,
`STAGE_BURNOUT`, `STAGE_SEPARATION`, `DRAG_NEGLIGIBLE`, `PAYLOAD_SEPARATION`,
`ORBIT_INSERTION`, `APOGEE`, `IMPACT`.

Mapowanie na ładne etykiety SpaceX (warstwa PREZENTACJI, nie zmiana kontraktu):
- `LIFTOFF` → „LIFTOFF"
- `MAX_Q` → „MAX-Q" (maksymalne ciśnienie dynamiczne)
- `STAGE_BURNOUT` → „MECO" dla 1. stopnia, „BECO"/„SECO" dla kolejnych
  (rozróżnij po kolejności zdarzenia lub po `active_stage` z najbliższej ramki
  telemetrii — to czysto etykieta, dane te same)
- `STAGE_SEPARATION` → „STAGE SEP"
- `PAYLOAD_SEPARATION` → „PAYLOAD DEPLOY"
- `ORBIT_INSERTION` → „ORBITAL INSERTION"
- `APOGEE` → „APOGEE", `IMPACT` → „IMPACT" (porażka)
- `DRAG_NEGLIGIBLE` → opcjonalnie ukryj lub „DRAG NEGLIGIBLE" (techniczne)

Każdy milestone pokazuje czas (T+ MM:SS), wysokość, prędkość — jak na transmisji.

### 2. Odczyt telemetrii — styl transmisji
Z `SimResult.telemetry` (`list[TelemetryFrame]`). Każda ramka ma `t`, `altitude`,
`speed`, `acceleration`, `mass`, `phase`, `active_stage`, `dynamic_pressure`.
Zrób charakterystyczny dla transmisji odczyt na żywo wzdłuż lotu:
- duże, czytelne „SPEED" (km/h lub m/s) i „ALTITUDE" (km),
- opcjonalnie aktualna faza (`phase`) i numer aktywnego stopnia (`active_stage`).
Jeśli animujesz przelot — odczyt aktualizuje się wzdłuż osi czasu trajektorii.

### 3. Wykres telemetrii w czasie — GENERYCZNY komponent
Zbuduj JEDEN generyczny komponent „wykres pola TelemetryFrame w czasie",
parametryzowany tym, KTÓRE pole rysować. Na teraz karm go polem `acceleration`
(g-force = acceleration / 9,80665) — daje charakterystyczny „zębaty" profil:
przyspieszenie rośnie w trakcie spalania stopnia (masa maleje, ciąg stały), spada
przy MECO, skacze przy zapłonie kolejnego stopnia. To wizualnie efektowne i
„kosmiczne" (widzowie znają g-force z transmisji).

WAŻNE — czemu generyczny: kontrakt NIE ma pola `thrust` (ciąg chwilowy). Decyzja:
rysujemy przyspieszenie (g-force), które jest za darmo i niesie tę samą dramaturgię.
Jeśli później (ulepszenie) dojdzie pole `thrust` do kontraktu, generyczny komponent
obsłuży je BEZ przepisywania — tylko podmienisz, które pole karmi wykres. Nie
buduj „wykresu przyspieszenia" na sztywno; buduj „wykres telemetrii(pole=...)".

Możesz pokazać kilka pól tym samym komponentem: g-force, prędkość, wysokość,
ciśnienie dynamiczne (Q — ładnie pokazuje max-Q jako szczyt).

### 4. VerdictCard z elementami orbity
Z `SimResult.verdict` (`reached_orbit`, `reason`, `elements`). `OrbitalElements`
ma komplet: `semi_major_axis`, `eccentricity`, `periapsis_altitude`,
`apoapsis_altitude`, `specific_energy`, `period` (None gdy niezwiązana). Duży,
jednoznaczny komunikat „ORBITA OSIĄGNIĘTA" / „BRAK ORBITY" + `reason` + kluczowe
liczby (perygeum, apogeum, mimośród, okres). To jury widzi najpierw.

### 5. Wykres trajektorii — dopracowanie
Tor lotu (x–y lub wysokość w czasie) z `telemetry`. Paleta, etykiety osi,
czytelność, skala. Zaznacz na nim milestones (znaczniki z osi czasu).

### 6. Layout / motyw / responsywność
Spójny motyw kosmiczny, czytelny układ pod demo (jeden ekran, 3 min dla jury).

---

## Granice i zasady

- Piszesz WYŁĄCZNIE w `frontend/`. Pakiet POZA uv workspace — npm/node.
- NIE podłączaj żywego API (to część A, czeka na silnik). Pracuj na syntetyku.
- NIE wymyślaj nowych typów zdarzeń ani pól — czytasz to, co jest w kontrakcie.
  Etykiety SpaceX to warstwa prezentacji (mapowanie), nie zmiana kontraktu.
- Logika domenowa/fizyka NIE należy do frontu — NIE licz ciągu/orbity sam.
  Rysujesz pola, które silnik wystawi; g-force = acceleration/9,80665 to jedyne
  dozwolone proste przeliczenie prezentacyjne.
- NIE edytuj `docs/goal/PROGRESS.md` — postęp w raporcie i commicie.
- Commit np. `<feat>(frontend): os czasu misji + telemetria transmisja-style`.

## Kryteria akceptacji
- Oś czasu pokazuje milestones z `events` z etykietami SpaceX i czasem/wys./prędk.
- Odczyt prędkość/wysokość w stylu transmisji działa na syntetyku.
- Generyczny wykres telemetrii rysuje g-force (i ew. inne pola) z „zębatym" profilem.
- VerdictCard pokazuje werdykt + komplet elementów orbity.
- Wszystko na syntetyku; podmiana na żywe API (część A) nie wymaga przepisania UI.

## Po ukończeniu
- Zgłoś (w raporcie): które elementy gotowe; potwierdź, że część A (żywe API)
  pozostaje nietknięta i gotowa do podłączenia, gdy silnik dostarczy fizykę.
