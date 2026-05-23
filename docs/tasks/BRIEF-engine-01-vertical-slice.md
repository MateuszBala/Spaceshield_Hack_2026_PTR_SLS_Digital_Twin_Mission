# Brief: physics-engine — krok 1 (pionowy plaster)

Typ: zadaniowy (jednorazowy). Adresat: instancja w worktree `physics-engine`.
Powiązane: CLAUDE.md (root + physics-engine), ADR architektury
(`docs/architecture/ARCHITECTURE_DECISIONS.md`), kontrakt `dt_contracts`,
kompas `docs/goal/PROGRESS.md`.

Ten brief NIE powtarza fizyki z ADR ani reguł z CLAUDE.md — odsyła do nich.
Mówi WYŁĄCZNIE: co zbudować teraz, w jakiej kolejności, kiedy uznać za zrobione.

---

## Cel (definicja ukończenia kroku 1)

Dostarczyć wywoływalną funkcję:

```
simulate(rocket: RocketParams) -> SimResult
```

która liczy trajektorię i zwraca POPRAWNY STRUKTURALNIE `SimResult` (zgodny z
kontraktem). „Krok 1” jest zrobiony, gdy API może zaimportować silnik, zawołać
`simulate(...)` na presecie i dostać `SimResult`, który da się odesłać do
frontu. To ożywia PIONOWY PLASTER (silnik→API→front) — priorytet nad pełną fizyką.

NIE celem kroku 1: idealne trzy fazy, gravity turn, mechanika Keplera w pełni.
Te przychodzą w kroku 2 (pogrubianie). Najpierw plaster ma ŻYĆ.

---

## Kolejność pracy (od najcieńszego działającego kawałka)

Rób w tej kolejności. Po każdym punkcie silnik jest „bardziej żywy”, ale już
punkt 1–2 wystarcza, by API miało co wołać.

1. **Szkielet + zaślepka.** `simulate()` zwraca poprawny `SimResult` z
   `verdict.reached_orbit=False`, pustą/krótką telemetrią, `final_phase=FAILED`.
   Cel: API i front dostają realny obiekt kontraktu. Plaster żyje.
2. **Faza 1 (wznoszenie) realna.** Całkowanie ruchu: ciąg + grawitacja g(h) +
   opór ρ(h), prosty zadany profil kąta (start pionowy → pochylanie do zadanego
   kąta; NIE gravity turn). Telemetria wypełnia się realnymi próbkami. Werdykt
   nadal zaślepka.
3. **Werdykt keplerowski.** Z wektorów stanu policz ε, e, perygeum (patrz ADR);
   `OrbitVerdict` na podstawie progów z `dt_contracts.constants`. Teraz „orbita:
   tak/nie” jest prawdziwe.
4. **Fazy 2 i 3 + zdarzenia.** Wstawienie (opór znikomy) i orbita/werdykt
   analityczny; separacje stopni i max-Q jako zdarzenia (terminal=True).

Po punkcie 3 złoty scenariusz demo już działa end-to-end. Punkt 4 to realizm.

---

## Fallback uproszczony — JAWNY, nie improwizowany (decyzja 3.3)

Cel: realistyczna fizyka. Ale jeśli pełen model (solve_ivp z events, ρ(h),
g(h)) sprawia kłopoty i grozi utratą czasu, jest ZDEFINIOWANA prostsza droga,
do której wolno się wycofać świadomie:

- Zamiast pełnego całkowania z oporem: budżet Δv z równania Ciołkowskiego per
  stopień, z odjęciem typowych strat startowych (constants.TYPICAL_LAUNCH_LOSSES_DV
  ~1750 m/s), i porównanie sumy Δv z wymaganym budżetem do LEO (~9,4 km/s).
- Werdykt orbity wtedy z bilansu Δv (osiągnięto wymaganą prędkość czy nie), a
  trajektoria do wizualizacji — uproszczona (parametryczna krzywa wznoszenia).
- Telemetria może być rzadsza, byle spójna z kontraktem.

Fallback ma być WIDOCZNY w kodzie jako świadoma gałąź (flaga/funkcja), nie ukryty
skrót. Lepszy działający uproszczony model niż niedziałający realistyczny o 4 nad ranem.

---

## Kryteria akceptacji (jak sprawdzić, że to działa)

- `simulate(preset)` zwraca `SimResult` zgodny z kontraktem (przechodzi walidację).
- Testy zachowania fizyki cenniejsze niż testy wartości:
  - prędkość orbitalna kołowa na 400 km wychodzi ~7,67 km/s (sanity z μ, R);
  - budżet Δv presetu osiągającego orbitę jest rzędu ~9,4 km/s (z stratami);
  - energia/pęd nie dryfują w fazie bez ciągu (jeśli całkujesz orbitę numerycznie).
- Preset „złoty przykład” (patrz niżej) NA PEWNO daje `reached_orbit=True`.
- Co najmniej jeden test, że gorszy parametr (mniej paliwa) daje `reached_orbit=False`
  — to fundament złotego scenariusza demo.

---

## Preset „złoty przykład” (uzgodnić wartości, ale dostarczyć)

Silnik musi udostępnić preset rakiety (np. funkcja `golden_preset() -> RocketParams`
albo plik danych), który NA PEWNO osiąga orbitę. To kotwica demo i testów.
Wartości dobierz tak, by budżet Δv z zapasem przekraczał ~9,4 km/s; trójstopniowy
preset jest naturalny. Jeśli nie masz pewności co do liczb — zaproponuj i oznacz
do weryfikacji, nie blokuj się.

---

## Granice i zasady (z CLAUDE.md — przypomnienie, nie powtórka)

- Piszesz WYŁĄCZNIE w `packages/physics-engine/`. `dt_contracts` jest read-only.
- Silnik to czyste funkcje `params → wynik`: bez HTTP, bez I/O sieci, bez wiedzy
  o API/froncie.
- Stałe (μ, R, g0, progi) z `dt_contracts.constants`, nie własne.
- SI, kanoniczny stan [x,y,vx,vy,m], układ inercjalny. Werdykt z Keplera.
- Import pakietu jako `dt_physics` (nazwa dystrybucji to `physics-engine`).
- Commity wg `docs/rules/COMMIT_CONVENTIONS.md`, np.
  `<feat,test>(physics-engine): faza wznoszenia + testy sanity`.

## Po ukończeniu kroku 1
- Zgłoś, że `simulate()` jest wywoływalne — to odblokowuje integrację z API.
- Zaktualizuj „Stan bieżący” w `docs/goal/PROGRESS.md` (jedna–dwie linie).
