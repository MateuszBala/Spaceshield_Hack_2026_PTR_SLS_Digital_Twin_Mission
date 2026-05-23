# api — pamięć pakietu (dt_api)

Cienka skorupa HTTP (FastAPI) między frontendem a silnikiem. Reguły wspólne dla
repo są w głównym CLAUDE.md — tu specyfika.

## Czym ten pakiet JEST, a czym NIE jest
- JEST: warstwą HTTP. Przyjmuje żądania (SimRequest), woła silnik, zwraca wyniki
  (SimResult) jako JSON. Generuje schemat OpenAPI z modeli `dt_contracts`.
- NIE jest: miejscem na logikę domenową ani fizykę. Jeśli kusi Cię policzenie tu
  czegokolwiek z dziedziny rakiet — to należy do physics-engine. API ma być
  „głupie": walidacja wejścia, wywołanie, serializacja wyjścia.

## Jak api rozmawia z resztą — IMPORTANT
- Silnik wołasz IMPORTEM in-process (`import dt_physics`), NIE przez HTTP.
  Pojedyncze żądanie z frontu → jedno wywołanie funkcji silnika → odpowiedź.
- Z frontendem rozmawiasz po HTTP/JSON. Kontrakt tej rozmowy to OpenAPI
  generowane z `dt_contracts` — nie wymyślaj własnych kształtów odpowiedzi.
- Dane wchodzące i wychodzące MUSZĄ być instancjami schematów `dt_contracts`.
  Nie twórz lokalnych, równoległych modeli danych — to rozjechałoby kontrakt
  z frontem i silnikiem.

## Zasady projektowe (dlaczego)
- Endpointy cienkie: walidacja (Pydantic robi ją automatycznie z typów
  contracts) → wywołanie silnika → zwrot. Bez logiki pośrodku.
- Długie symulacje: respektuj `SimRequest.max_flight_time` i `include_telemetry`
  (False → lżejsza odpowiedź bez pełnej telemetrii). To kontrakt już przewiduje.
- Błędy walidacji zwracaj jako czytelne odpowiedzi HTTP — nie połykaj ich.

## Konwencje
- Python ≥ 3.12, nazwy importu z prefiksem dt_ (`import dt_api`, `import dt_physics`).
- FastAPI + uvicorn. OpenAPI ma być prawdziwym odbiciem `dt_contracts`.
- SI, kanoniczny stan — ale api ich nie interpretuje, tylko przekazuje.

## Granice i zgoda człowieka
- Piszesz wyłącznie w `packages/api/`. `dt_contracts` jest read-only.
- Potrzeba nowego pola w odpowiedzi = potrzeba zmiany kontraktu → ZGŁOŚ to,
  nie obchodź kontraktu lokalnym modelem.

## Głębszy kontekst
- Przepływ żądań i decyzja „import vs HTTP”: `docs/architecture/COMMUNICATION.md`.
- Schematy: `dt_contracts` (SimRequest, SimResult i pochodne).
