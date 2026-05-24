# Brief: physics-engine — krok 2 (pogrubianie: pełna fizyka)

Typ: zadaniowy (jednorazowy). Adresat: instancja w worktree `physics-engine`.
Poprzednik: `BRIEF-engine-01-vertical-slice.md` (krok 1 — DOMKNIĘTY, ale TYLKO
jako stub: `simulate()` zwraca `reached_orbit=False` i pustą telemetrię,
`golden_preset()` zaimplementowany, 13 testów struktury). PRAWDZIWEJ FIZYKI NIE
MA — budujesz ją w tym kroku od zera.
Powiązane: ADR architektury (`docs/architecture/ARCHITECTURE_DECISIONS.md` — sekcje
3, 6), kontrakt `dt_contracts`, kompas `docs/goal/PROGRESS.md`, preset
`docs/tasks/GOLDEN_PRESET.md`.

Ten brief NIE powtarza fizyki z ADR ani reguł z CLAUDE.md — odsyła do nich. Mówi
WYŁĄCZNIE: co pogrubić teraz, w jakiej kolejności, kiedy uznać za zrobione.

---

## Cel (definicja ukończenia kroku 2)

Zamienić stub w prawdziwy silnik: `simulate(SimRequest(rocket=golden_preset()))`
ma zwrócić `SimResult` z `reached_orbit=True`, prawdziwą telemetrią lotu i
werdyktem policzonym z elementów keplerowskich. Po kroku 2 złoty scenariusz demo
działa na PRAWDZIWEJ fizyce: lepszy preset → orbita, gorszy parametr → brak
orbity, z policzonych liczb, nie z zaślepki.

Krok 2 jest zrobiony, gdy:
- preset osiąga orbitę (werdykt `reached_orbit=True` z prawdziwych ε, e, r_p),
- gorszy parametr daje `reached_orbit=False` (test negatywny z prawdziwej fizyki),
- telemetria pokazuje fizyczny profil lotu (wysokość rośnie, masa maleje skokami
  przy separacjach, prędkość narasta).

---

## Sygnatura: `simulate(request: SimRequest) -> SimResult` (DECYZJA STYKU)

ROZSTRZYGNIĘTE z człowiekiem. Silnik bierze pełny `SimRequest`, NIE sam
`RocketParams`. Parametry rakiety czytasz jako `request.rocket`. Powód: dwa pola
sterujące żyją w `SimRequest`, nie w `RocketParams`, i masz je uszanować:

- **`request.include_telemetry: bool`** — gdy `False`, zwróć `SimResult` z
  werdyktem i elementami, ale BEZ pełnej tablicy `TelemetryFrame[]` (pusta/
  minimalna). Gdy `True`, pełna telemetria. Oszczędza transfer, gdy front chce
  tylko werdykt (pętla „przelicz" bez rysowania pełnego toru).
- **`request.max_flight_time: float`** — twardy limit czasu całkowania [s].
  Przekaż jako górną granicę `t_span` w `solve_ivp`. Chroni przed nieskończoną
  propagacją, gdy rakieta nie osiąga orbity i „leci w nieskończoność".

Oba pola SĄ JUŻ w kontrakcie — nie zmieniasz kontraktu, tylko zaczynasz je czytać.
API woła `simulate(request)` (poinformowane). `golden_preset()` zwraca
`RocketParams`, więc w testach/wywołaniach opakuj: `SimRequest(rocket=golden_preset())`
(ew. dodaj pomocniczy `golden_request()`). Kontraktu NIE zmieniaj.

---

## Decyzja zakresu: faza 3 = werdykt analityczny (MUST), propagacja numeryczna (OPCJA)

POTWIERDZONA decyzja (rozstrzygnięta z człowiekiem):
- **Werdykt orbitalny liczymy ANALITYCZNIE z wektora stanu w momencie wstawienia**
  — ε = v²/2 − μ/r, e z wektora mimośrodu, r_p = a(1−e). To jest MUST i to
  wystarcza do werdyktu „orbita: tak/nie + perygeum + mimośród". NIE wymaga
  całkowania ani jednego kroku po orbicie.
- **Numeryczna propagacja orbity (leapfrog/Verlet) jest OPCJĄ** — tylko jeśli
  chcesz narysować pełną elipsę na wykresie i zostaje czas. Tor orbity da się też
  sparametryzować analitycznie z elementów Keplera bez integratora. NIE blokuj
  się na tym; werdykt nie zależy od propagacji.

Konsekwencja: faza 3 w kroku 2 to przede wszystkim ANALIZA stanu wstawienia, nie
kolejny reżim całkowania. Integrator symplektyczny schodzi do roli wizualnej opcji.

---

## Kolejność pracy (pogrubianie warstwami — preset ma osiągnąć orbitę JAK NAJWCZEŚNIEJ)

Kolejność jest tak dobrana, by `reached_orbit=True` na presecie pojawiło się
możliwie szybko, a realizm dokładał się warstwami. Po punkcie 3 demo działa na
prawdziwej fizyce.

1. **Werdykt keplerowski na prawdziwych wektorach (najpierw, bo to sedno).**
   Z dowolnego stanu [x, y, vx, vy] policz ε, e, r_p (wzory wyżej; progi z
   `dt_contracts.constants`: `MIN_PERIAPSIS_ALTITUDE`, `MAX_ECCENTRICITY_LEO`,
   `R_EARTH`, `MU_EARTH`). Wypełnij `OrbitVerdict` (reached_orbit + powód +
   elementy). Na tym etapie stan wstawienia może pochodzić jeszcze z uproszczenia
   — chodzi o to, by werdykt był PRAWDZIWY zanim fizyka lotu jest pełna.

2. **Faza 1 (wznoszenie) — budujesz od zera (krok 1 był tylko stubem).**
   Całkowanie: ciąg + grawitacja g(h) + opór ρ(h), zadany profil kąta (start
   pionowy → pochylanie wg `request.rocket.launch_angle_deg`; NIE gravity turn).
   `solve_ivp`. Telemetria z prawdziwych próbek.

3. **Faza 2 (wstawienie) + sklejenie segmentów.** Opór znikomy (próg D/mg<ε jako
   zdarzenie kończące fazę 1), ciąg + g(h). Orchestrator skleja segmenty faz w
   jedną trajektorię. Stan na końcu fazy 2 = stan wstawienia → karmi werdykt z
   punktu 1. PO TYM PUNKCIE: preset ma dać `reached_orbit=True`.

4. **Zdarzenia (terminal=True).** max-Q (zerowanie dQ/dt, direction=-1),
   wypalenie stopnia (mass_flow·burn_time), separacje (skok TYLKO masy m),
   próg wyłączenia oporu (D/mg<ε). Każde jako event w `solve_ivp`. Separacja =
   nieciągłość wyłącznie w składowej m; pozycja/prędkość ciągłe (patrz ADR 3).
   Wypełnij `MissionEvent[]` w telemetrii.

5. **(OPCJA) Propagacja orbity symplektyczna.** Tylko dla pełnej elipsy na
   wykresie. Leapfrog/Verlet. Sanity: energia nie dryfuje. Pomiń, jeśli brak czasu.

---

## Fallback uproszczony — wciąż JAWNY (i bardziej aktualny niż zwykle)

Decyzja niezmienna: jeśli pełne całkowanie z events/ρ(h)/g(h) grozi utratą czasu,
jest ZDEFINIOWANA prosta droga (budżet Δv z Ciołkowskiego per stopień − straty
`TYPICAL_LAUNCH_LOSSES_DV`, porównanie z budżetem LEO ~9,4 km/s; werdykt z
bilansu Δv; trajektoria parametryczna). Ma być WIDOCZNĄ gałęzią w kodzie
(flaga/funkcja), nie ukrytym skrótem. Lepszy działający uproszczony model niż
niedziałający realistyczny o 4 nad ranem.

UWAGA: jeśli po ~20–30 min realnej pracy pełne całkowanie nie daje
`reached_orbit=True` na presecie (zacina się, dryfuje, profil kąta nie wychodzi)
— NIE walcz dalej z solverem. Przełącz się na fallback Δv jako ścieżkę główną,
realistyczne fazy zostaw jako ulepszenie „jeśli starczy czasu". Werdykt z bilansu
Δv w zupełności wystarcza do złotego scenariusza demo.

---

## Kryteria akceptacji

- `simulate(SimRequest(rocket=golden_preset()))` → `reached_orbit=True`, z
  prawdziwych ε, e, r_p (nie z zaślepki). Perygeum > R_EARTH +
  MIN_PERIAPSIS_ALTITUDE, e < MAX_ECCENTRICITY_LEO.
- Test negatywny z PRAWDZIWEJ fizyki: gorszy parametr (np. skrócony burn_time S1
  lub osłabiony S3 — patrz GOLDEN_PRESET.md sekcja 4) → `reached_orbit=False`.
  Empirycznie wyznacz, ile trzeba uciąć, i ZAREKOMENDUJ tę wartość jako „suwak
  demo" (zgłoś w RAPORCIE, nie w PROGRESS.md — frontend użyje w Akcie 2 demo).
- Telemetria fizyczna: wysokość monotonicznie rośnie w fazie 1–2, masa maleje
  skokami przy separacjach, prędkość narasta do ~orbitalnej.
- Testy zachowania (cenniejsze niż testy wartości): v_circ@400km ≈ 7,67 km/s
  (z μ, R); budżet Δv presetu ~rzędu wymaganego; jeśli całkujesz orbitę —
  energia/pęd nie dryfują w fazie bez ciągu.
- Werdykt podaje POWÓD (czemu tak/nie) + kluczowe liczby (perygeum, mimośród).
- `include_telemetry=False` faktycznie pomija telemetrię; `max_flight_time`
  ogranicza całkowanie.

---

## Jeśli preset nie dolatuje (warunek konieczny ≠ gwarancja)

Budżet Δv presetu ma zapas ~2,7 km/s ponad LEO po stratach ryczałtowych. Ale
realne straty z całkowania (kąt, profil) mogą wyjść wyższe niż ryczałt 1750 m/s.
Jeśli `reached_orbit=False` na presecie mimo poprawnej fizyki — NIE strój po omacku:
1. Sprawdź, czy straty nie są patologiczne (zły profil kąta → rakieta leci w bok
   albo za stromo). Profil kąta to najczęstsza przyczyna.
2. Dopiero potem, jeśli to realne straty: wydłuż `burn_time` S2 lub S3 o ~10–15 %
   (więcej paliwa = większe Δv) i ZGŁOŚ zmianę presetu w raporcie do człowieka
   — preset to wspólna kotwica, jego zmianę się sygnalizuje (NIE edytuj
   GOLDEN_PRESET.md ani PROGRESS.md sam — zgłoś, człowiek zaktualizuje).

---

## Granice i zasady (z CLAUDE.md — przypomnienie, nie powtórka)

- Piszesz WYŁĄCZNIE w `packages/physics-engine/`. `dt_contracts` read-only.
- Stałe (μ, R, g0, progi) z `dt_contracts.constants`, NIE własne.
- SI, kanoniczny stan [x,y,vx,vy,m], układ inercjalny. Werdykt z Keplera.
- Czyste funkcje `params → wynik`: bez HTTP, bez I/O sieci, bez wiedzy o API/froncie.
- Jeśli uznasz, że kontraktowi czegoś brakuje (np. pole w telemetrii) — ZGŁOŚ,
  nie dodawaj sam. Nowa zależność / zmiana `pyproject.toml` — zgoda człowieka.
- **NIE edytuj `docs/goal/PROGRESS.md`** — kompas ma jednego pisarza (człowiek +
  doradca). Postęp ZGŁASZASZ w raporcie końcowym i w treści commita; aktualizacja
  kompasu dzieje się centralnie. To unika konfliktów merge w pliku wspólnym.
- Commity wg `docs/rules/COMMIT_CONVENTIONS.md`, np.
  `<feat,test>(physics-engine): werdykt keplerowski + 3 fazy`.

## Po ukończeniu kroku 2
- Zgłoś (w raporcie końcowym, NIE w PROGRESS.md): preset osiąga orbitę na
  prawdziwej fizyce + zarekomendowana wartość „suwaka demo" (parametr i próg,
  przy którym werdykt spada).
