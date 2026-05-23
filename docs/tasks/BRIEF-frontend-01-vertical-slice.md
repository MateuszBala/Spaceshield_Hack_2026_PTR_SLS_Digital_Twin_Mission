# Brief: frontend — krok 1 (pionowy plaster)

Typ: zadaniowy (jednorazowy). Adresat: instancja w worktree `frontend`.
Powiązane: CLAUDE.md (root + frontend), kompas `docs/goal/PROGRESS.md`,
ADR graceful AI (`docs/decisions/ADR-graceful-ai-degradation.md`),
zarys demo (`docs/PRESENTATION_OUTLINE.md`).

Ten brief nie powtarza reguł z CLAUDE.md — odsyła do nich. Mówi: co zbudować
teraz, w jakiej kolejności, kiedy uznać za zrobione.

---

## Cel (definicja ukończenia kroku 1)

Działający ZŁOTY SCENARIUSZ demo end-to-end: użytkownik widzi rakietę z presetu,
zmienia WARTOŚĆ parametru (masa paliwa / ciąg / Isp / masa ładunku), klika
„przelicz”, dostaje z API nowy `SimResult` i widzi nową trajektorię 2D +
werdykt (orbita: tak/nie + powód). To jest sedno Digital Twina i sedno demo.

ZAKRES MUST (patrz PROGRESS): edycja wartości przy USTALONEJ liczbie stopni z
presetu. BEZ dodawania/usuwania stopni — to SHOULD (krok 2).

---

## Praca równoległa — NIE czekaj na gotowe API/silnik

Kontrakt `dt_contracts` definiuje kształt `SimRequest`/`SimResult`. Możesz:
- generować typy TS z OpenAPI, gdy API je wystawi; do tego czasu pracować na
  typach odwzorowanych z kontraktu;
- rozwijać UI na SYNTETYCZNYM `SimResult` (zaślepka odpowiedzi zgodna z
  kontraktem), zanim API liczy realnie. Gdy API ożyje, podmieniasz źródło danych,
  nie przepisujesz UI.

To pozwala Ci ruszyć równolegle z silnikiem i API.

---

## Kolejność pracy

1. **Szkielet React+Vite + klient HTTP.** Projekt startuje (`npm run dev`),
   prosty klient do API (fetch). Typy z OpenAPI lub odwzorowane z kontraktu.
2. **Formularz parametrów (poziom 1).** Karty stopni z presetu, pola/suwaki na
   wartości (masa paliwa, ciąg, Isp) + masa ładunku. Liczba stopni stała.
3. **Przycisk „przelicz” → API → render.** Wyślij `SimRequest`, odbierz
   `SimResult`, narysuj trajektorię 2D (wykres pozycji/wysokości) + pokaż
   werdykt (reached_orbit + reason). To domyka złoty scenariusz.
4. **Capabilities → UI AI.** Zapytaj endpoint capabilities; jeśli
   `ai_available=false`, SCHOWAJ/wyszarz przycisk „optymalizuj”. UI nigdy nie
   woła funkcji, o której wie, że jej nie ma (patrz ADR graceful AI).

Po punkcie 3 demo działa. Punkt 4 zabezpiecza brak AI.

---

## Wizualizacja (krok 1 = 2D)

- Trajektoria 2D: wykres toru lotu (x–y) lub wysokość w czasie. Recharts.
- Werdykt widoczny i czytelny: duży, jednoznaczny komunikat „ORBITA OSIĄGNIĘTA”
  / „BRAK ORBITY” + powód i kluczowe liczby (perygeum, mimośród) jeśli są.
- 3D (Three.js) to COULD — nie w kroku 1.
- Dashboard telemetrii (prędkość/wysokość/masa w czasie) to SHOULD — po MUST.

---

## Kryteria akceptacji

- `npm run dev` uruchamia aplikację bez błędów.
- Załadowany preset pokazuje rakietę i (po „przelicz”) trajektorię + werdykt
  „orbita osiągnięta”.
- Zmiana parametru na gorszy + „przelicz” pokazuje INNY wynik (np. brak orbity)
  — to dowód działania pętli Digital Twina (Akt 2 scenariusza wideo).
- Gdy API zgłasza `ai_available=false`, UI optymalizacji jest schowane/wyszarzone.
- Brak twardych odwołań do pól spoza wygenerowanego schematu.

---

## Granice i zasady (przypomnienie z CLAUDE.md)

- Piszesz WYŁĄCZNIE w `frontend/`. To pakiet POZA uv workspace — narzędzia
  npm/node, NIE uv/pytest. Nie importujesz Pythona.
- Z backendem rozmawiasz WYŁĄCZNIE po HTTP. Typy z OpenAPI, nie ręcznie.
- Logika domenowa/fizyka NIE należy do frontu — front wyświetla, co dostanie.
- Commity wg konwencji, np. `<feat>(frontend): formularz parametrów + render trajektorii`.

## Po ukończeniu kroku 1
- Zgłoś, że złoty scenariusz działa end-to-end (po podłączeniu realnego API).
- Zaktualizuj „Stan bieżący” w `docs/goal/PROGRESS.md`.
