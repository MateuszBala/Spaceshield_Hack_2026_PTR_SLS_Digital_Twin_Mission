# frontend — pamięć pakietu (React/TS)

Aplikacja webowa: sterowanie parametrami, wizualizacja, dashboard telemetryczny.
Reguły wspólne dla repo są w głównym CLAUDE.md — tu specyfika. UWAGA: to JEDYNY
pakiet poza ekosystemem Pythona.

## Czym ten pakiet JEST, a czym NIE jest
- JEST: warstwą prezentacji w React/TypeScript. Zbiera parametry od użytkownika,
  wysyła do api, rysuje wyniki (wykresy trajektorii/telemetrii, wizualizacja 3D).
- NIE jest: miejscem na logikę domenową ani fizykę. Front nie liczy orbit — od
  tego jest silnik za api. Front wyświetla to, co dostanie.

## Granica językowa — IMPORTANT
- To NIE jest pakiet Pythona i jest POZA uv workspace. Ma własny `package.json`
  i `node_modules`.
- NIE używasz uv ani pytest. Komendy to npm/node: `npm install`, `npm run dev`,
  `npm run build`. Lint/format i testy w narzędziach JS (eslint/prettier, vitest
  /playwright), nie w narzędziach Pythona.
- NIE importujesz kodu Pythona. Jedyny kanał do backendu to HTTP.

## Jak front rozmawia z resztą — IMPORTANT
- Wyłącznie HTTP/JSON do api. Żadnych bezpośrednich wywołań silnika ani innych
  pakietów.
- Typy danych GENERUJ z OpenAPI (które api wystawia z `dt_contracts`). NIE pisz
  typów API ręcznie — bo ręczne typy rozjadą się z kontraktem przy pierwszej
  jego zmianie. To frontowy odpowiednik zasady „contracts to źródło prawdy".
- Nie odwołuj się do pól, których nie ma w wygenerowanym schemacie.

## Zasady projektowe
- Stan parametrów rakiety w stanie React; wysyłka jako SimRequest (kształt z
  OpenAPI). Odpowiedź SimResult → wykresy i wizualizacja.
- Wizualizacja 3D: biblioteka z ekosystemu React (np. react-three-fiber). To
  element punktowany w zadaniu — warto, ale nie kosztem poprawności danych.
- Telemetria bywa długa: gdy nie potrzebujesz pełnej, możesz prosić api o tryb
  bez telemetrii (kontrakt to przewiduje przez include_telemetry).

## Granice i zgoda człowieka
- Piszesz wyłącznie w `frontend/`. Nie dotykasz pakietów Pythona.
- Potrzeba nowego pola w danych = potrzeba zmiany kontraktu po stronie Pythona →
  ZGŁOŚ to. Front nie obchodzi braku pola lokalnym wymyślaniem danych.

## Głębszy kontekst
- Przepływ żądań front↔api: `docs/architecture/COMMUNICATION.md`.
- Dlaczego React, nie Streamlit (granica worktree, 3D): `docs/decisions/`.
