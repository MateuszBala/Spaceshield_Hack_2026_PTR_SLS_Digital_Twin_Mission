# Brief: frontend — krok 2 (domknięcie MUST na żywym API, potem SHOULD)

Typ: zadaniowy (jednorazowy). Adresat: instancja w worktree `frontend`.
Poprzednik: `BRIEF-frontend-01-vertical-slice.md` (krok 1 — DOMKNIĘTY: szkielet,
formularz, trajektoria 2D, werdykt, graceful AI — wszystko na danych SYNTETYCZNYCH).
Powiązane: CLAUDE.md (root + frontend), kompas `docs/goal/PROGRESS.md`,
preset `docs/tasks/GOLDEN_PRESET.md`, ADR graceful AI, `docs/PRESENTATION_OUTLINE.md`.

Ten brief nie powtarza reguł z CLAUDE.md — odsyła do nich. Mówi: co zbudować
teraz, w jakiej kolejności, kiedy uznać za zrobione.

---

## Kontekst: MUST jeszcze NIE działa end-to-end

Krok 1 zbudował złoty scenariusz na danych SYNTETYCZNYCH (`syntheticResult.ts`
liczy werdykt z Ciołkowskiego po stronie JS). To było słuszne — API nie liczyło.
Ale MUST z PROGRESS.md brzmi „zmiana parametru → przelicz → nowa trajektoria +
werdykt", a werdykt ma pochodzić z SILNIKA, nie z JS. Dopóki front liczy własny
werdykt, pętla Digital Twina jest pozorna — to kalkulator JS, nie cyfrowy bliźniak.

Dlatego krok 2 zaczyna się od DOMKNIĘCIA MUST na żywym API, a SHOULD przychodzi
dopiero potem (reguła czasu z PROGRESS.md: nie dotykamy SHOULD, póki MUST nie
działa end-to-end).

---

## Kolejność pracy

### CZĘŚĆ A — domknięcie MUST na żywym API (priorytet, to jest reszta MUST)

1. **Podłączenie do żywego API.** API odpowiada na `http://localhost:8000`
   (proxy `/api/*` masz już z kroku 1). Przełącz `client.ts` tak, by `POST
   /api/simulate` faktycznie trafiał do API, a werdykt i trajektoria pochodziły
   z `SimResult` zwróconego przez SILNIK. Syntetyk (`syntheticResult.ts`) SCHODZI
   do roli czystego fallbacku „tryb demo offline" — gdy API nieosiągalne. NIE
   może być równoległym źródłem prawdy: gdy API żyje, werdykt idzie z API.

2. **Wyrównanie presetu do złotego (decyzja: front przyjmuje złoty preset).**
   Krok 1 użył własnej DWUSTOPNIOWEJ rakiety — bo `GOLDEN_PRESET.md` powstał po
   Twoim starcie. Teraz front i silnik MUSZĄ widzieć JEDNĄ rakietę (preset to
   wspólna kotwica demo i testów). Podmień `src/data/preset.ts` na złoty preset
   TRÓJSTOPNIOWY — wartości niżej (sekcja „Wartości złotego presetu"). Twój
   `StageCard` już edytuje właściwe pola (thrust/isp/burn_time/dry_mass) i liczy
   computed — to praca mechaniczna (podmiana wartości + trzeci stopień), nie
   przeprojektowanie.

3. **Typy TS z OpenAPI.** API wystawia pełny schemat OpenAPI z `dt_contracts`
   (`http://localhost:8000/openapi.json`). Wygeneruj z niego typy TS i podmień
   ręcznie odwzorowane `src/types/contracts.ts`. To eliminuje ryzyko rozjazdu
   typów front↔kontrakt. (Jeśli generator robi kłopot pod presją czasu —
   dopuszczalne zostać przy ręcznych typach, byle zgodnych z kontraktem; ale
   OpenAPI to docelowo właściwa droga.)

PO CZĘŚCI A: złoty scenariusz działa na PRAWDZIWEJ fizyce. Użytkownik zmienia
parametr złotego presetu → API woła silnik → werdykt z Keplera wraca do UI.
To domyka MUST frontu end-to-end. Zgłoś to — MUST plastra jest kompletny.

### CZĘŚĆ B — SHOULD (dopiero gdy CZĘŚĆ A działa)

Kolejność wg wartości dla demo:
4. **Dodawanie/usuwanie stopni (poziom 2).** Lista 1–4 stopni edytowalna w UI
   (kontrakt i silnik już wspierają `stages: list 1-4`). Mocno wzmacnia demo:
   „2 stopnie nie dolatują → dodaję 3. → orbita". To jest najsilniejszy pojedynczy
   SHOULD dla narracji wideo.
5. **Dashboard telemetrii.** Prędkość / wysokość / masa w czasie (Recharts,
   osobne wykresy lub panele). Dane z `TelemetryFrame[]` w `SimResult`.
6. **Zdarzenia na osi czasu.** Separacje, max-Q, wypalenia jako znaczniki na
   wykresach (masz już pionowe znaczniki w `TrajectoryChart` z kroku 1 — podłącz
   pod `MissionEvent[]` z realnego silnika).
7. **Dopracowanie wizualizacji trajektorii.** Lepsza paleta, etykiety, czytelność.

---

## Wartości złotego presetu (do `src/data/preset.ts`)

Trójstopniowa, payload 150 kg, start pionowy (`launch_angle_deg=90`). PODAJESZ
pola WEJŚCIOWE; computed (paliwo, frakcja, strumień) liczysz w UI jak dotąd.
Źródło: `docs/tasks/GOLDEN_PRESET.md` (zweryfikowane: Δv ideal ≈ 13 846 m/s,
masa startowa ≈ 39 304 kg, wszystkie frakcje w zakresie SMAD).

| stopień | name | dry_mass [kg] | thrust [N] | isp [s] | burn_time [s] | Cd | ref_area [m²] |
|---------|------|---------------|------------|---------|---------------|-----|---------------|
| S1 | `S1-core`  | 3000 | 780000 | 282 | 105 | 0.30 | 3.0 |
| S2 | `S2`       | 700  | 145000 | 345 | 120 | 0.25 | 1.2 |
| S3 | `S3-upper` | 120  | 22000  | 448 | 115 | 0.22 | 0.8 |

Payload: `mass=150`, `name="sat-150"`. `launch_angle_deg=90`.

Sanity (do podglądu Δv w UI): te wartości dają marżę ~2,7 km/s nad budżetem LEO
po stratach — preset osiąga orbitę. Jeśli Twój podgląd Δv_eff pokaże co innego,
to znak, że formuła podglądu różni się od silnika — to OK (podgląd to estymata),
ale prawdziwy werdykt ZAWSZE z API, nie z podglądu.

---

## „Suwak demo" (czeka na liczbę od silnika)

Silnik w kroku 2 wyznacza empirycznie, który parametr i o ile zmniejszony wywraca
werdykt na „BRAK ORBITY" (Akt 2 demo). Gdy silnik tę liczbę zarekomenduje (przez
PROGRESS.md / raport), warto, by UI miało ten parametr jako wyróżniony/wygodny do
zmiany (np. ten konkretny suwak na widoku). Do tego czasu: każdy parametr jest
edytowalny, więc demo i tak zadziała — to dopracowanie, nie blokada.

---

## Kryteria akceptacji

- Gdy API żyje: zmiana parametru złotego presetu → „Przelicz" → werdykt i
  trajektoria pochodzą z `SimResult` API (z SILNIKA), nie z `syntheticResult.ts`.
- Gdy API offline: UI nadal działa na syntetyku z czytelnym badge „tryb demo".
- Front i silnik liczą TĘ SAMĄ rakietę (złoty preset trójstopniowy).
- Zmiana parametru na gorszy → realny `reached_orbit=false` z silnika (nie z JS).
- (SHOULD, jeśli zrobione) dodawanie stopnia działa: 2 stopnie → brak orbity,
  dodaj 3. → orbita (lub odwrotnie, zależnie od wartości).
- Brak logiki domenowej/fizyki jako ŹRÓDŁA PRAWDY we froncie — syntetyk tylko fallback.

---

## Granice i zasady (przypomnienie z CLAUDE.md)

- Piszesz WYŁĄCZNIE w `frontend/`. Pakiet POZA uv workspace — npm/node, NIE uv.
- Z backendem rozmawiasz WYŁĄCZNIE po HTTP. Typy z OpenAPI.
- Logika domenowa/fizyka NIE należy do frontu — front wyświetla, co dostanie z API.
  Syntetyk to dozwolony FALLBACK offline, nie drugie źródło werdyktu.
- **NIE edytuj `docs/goal/PROGRESS.md`** — kompas ma jednego pisarza (człowiek).
  Postęp zgłaszasz w raporcie końcowym i w treści commita.
- Commity wg konwencji, np. `<feat>(frontend): podlaczenie zywego API + zloty preset`.

## Po ukończeniu
- Zgłoś (w raporcie, NIE w PROGRESS.md): MUST działa na żywym API end-to-end;
  które SHOULD domknięte.
