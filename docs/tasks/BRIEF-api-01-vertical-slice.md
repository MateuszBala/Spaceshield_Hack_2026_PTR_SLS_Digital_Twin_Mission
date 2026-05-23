# Brief: api — krok 1 (pionowy plaster)

Typ: zadaniowy (jednorazowy). Adresat: instancja w worktree `api`.
Powiązane: CLAUDE.md (root + api), kontrakt `dt_contracts`, ADR graceful AI
(`docs/decisions/ADR-graceful-ai-degradation.md`), kompas `docs/goal/PROGRESS.md`.

Ten brief nie powtarza reguł z CLAUDE.md — odsyła do nich. Mówi: co zbudować
teraz, w jakiej kolejności, kiedy uznać za zrobione.

---

## Cel (definicja ukończenia kroku 1)

Wystawić endpoint HTTP, który przyjmuje `SimRequest`, woła silnik importem
in-process i zwraca `SimResult` jako JSON. „Krok 1” jest zrobiony, gdy frontend
może wysłać żądanie symulacji i dostać poprawny `SimResult`. To domyka środek
pionowego plastra (silnik→API→front).

Drugi cel kroku 1: endpoint „capabilities” (lub „health”) sygnalizujący, które
funkcje są dostępne — w szczególności CZY pakiet AI jest obecny (patrz ADR).

---

## Praca równoległa — NIE czekaj na gotowy silnik

Silnik dostarcza `simulate(RocketParams) -> SimResult` (patrz brief silnika).
Na początku może to być zaślepka zwracająca `reached_orbit=False`. To WYSTARCZY,
byś budował API: importujesz `dt_physics.simulate`, wołasz, serializujesz wynik.
Gdy silnik pogrubieje, Twój endpoint nie wymaga zmian — kontrakt się nie zmienia.
Jeśli silnik jeszcze nie ma nawet zaślepki, wolno Ci tymczasowo zwrócić
syntetyczny `SimResult` zbudowany z kontraktu, oznaczony jako tymczasowy.

---

## Kolejność pracy

1. **Endpoint symulacji.** `POST` przyjmujący `SimRequest`, wołający
   `dt_physics.simulate(request.rocket)`, zwracający `SimResult`. Walidacja
   wejścia/wyjścia robi się sama z typów `dt_contracts` (Pydantic). Bez logiki
   domenowej pośrodku — API jest „głupie”.
2. **Capabilities/health.** Endpoint zwracający informację o dostępnych
   funkcjach. Wykryj obecność pakietu AI (próba importu `dt_ai` w try/except);
   wystaw flagę `ai_available: bool`. To czyta frontend, by chować UI optymalizacji.
3. **Endpoint optymalizacji (graceful).** Istnieje ZAWSZE, ale gdy `dt_ai`
   niedostępne — zwraca czytelną odpowiedź „funkcja niedostępna” (status
   sygnalizujący wyłączenie, NIE błąd 500). Gdy AI obecne — deleguje do niego.
   Patrz ADR graceful AI: warstwa niedostępności istnieje, zanim powstanie pakiet AI.
4. **OpenAPI.** Upewnij się, że schemat OpenAPI jest prawdziwym odbiciem
   `dt_contracts` — to z niego frontend generuje typy. Nie dodawaj pól spoza kontraktu.

Po punktach 1–2 plaster żyje i frontend ma czym sterować widocznością AI.

---

## Kryteria akceptacji

- `POST` na endpoint symulacji z presetem zwraca `SimResult` jako JSON (200).
- Niepoprawne wejście (np. >4 stopni) zwraca czytelny błąd walidacji (nie 500).
- Endpoint capabilities zwraca `ai_available` poprawnie w obu stanach
  (pakiet AI obecny / nieobecny) — testowalne przez podmianę importu.
- Endpoint optymalizacji przy braku `dt_ai` zwraca „niedostępne”, NIE wywala się.
- OpenAPI generuje się i zawiera schematy z `dt_contracts`.

---

## Granice i zasady (przypomnienie z CLAUDE.md)

- Piszesz WYŁĄCZNIE w `packages/api/`. `dt_contracts` read-only.
- Silnik wołasz IMPORTEM in-process (`import dt_physics`), NIE przez HTTP.
- Żadnej logiki domenowej/fizyki w API — to należy do silnika.
- Dane wch./wych. to instancje schematów `dt_contracts` — bez lokalnych modeli.
- Import jako `dt_api` (nazwa dystrybucji `api`).
- Commity wg konwencji, np. `<feat>(api): endpoint symulacji + capabilities`.

## Po ukończeniu kroku 1
- Zgłoś, że endpoint symulacji odpowiada — to odblokowuje integrację z frontem.
- Zaktualizuj „Stan bieżący” w `docs/goal/PROGRESS.md`.
