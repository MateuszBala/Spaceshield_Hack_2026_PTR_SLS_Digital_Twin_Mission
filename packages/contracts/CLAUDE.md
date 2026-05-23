# contracts — pamięć pakietu (dt_contracts)

Wspólne schematy danych całego systemu. To jest ŹRÓDŁO PRAWDY: definiuje
kształt każdej informacji płynącej między pakietami. Reguły wspólne dla repo
są w głównym CLAUDE.md — tu tylko specyfika tego pakietu.

## Czym ten pakiet JEST, a czym NIE jest
- JEST: definicje schematów (Pydantic v2), stałe fizyczne, progi walidacji.
- NIE jest: miejscem na logikę biznesową, obliczenia, I/O, wywołania sieci.
  Jeśli kusi Cię dopisanie tu funkcji, która coś *liczy* poza trywialnym
  `computed_field` wynikającym wprost z pól — to nie należy tutaj.

## Status: READ-ONLY dla większości instancji — IMPORTANT
Zmiana w tym pakiecie to zmiana styku WSZYSTKICH pozostałych (engine, api, ai,
frontend zależą od tych schematów). Dlatego:
- Nie zmieniaj kształtu istniejących schematów bez zgody człowieka.
- Propozycję zmiany kontraktu ZGŁASZASZ (opis + uzasadnienie), nie wprowadzasz
  samodzielnie. To chroni przed cichym rozjazdem między instancjami w worktree.
- Dodanie NOWEGO, opcjonalnego pola bywa bezpieczne; usunięcie lub zmiana typu
  istniejącego — nigdy bez zgody.

## Zasady projektowe (dlaczego tak)
- Każdy schemat dziedziczy z `DTModel` (extra="forbid") lub `FrozenModel`.
  `extra="forbid"` odrzuca nieznane pola — to twarda bariera: jeśli inna
  instancja dośle pole spoza kontraktu, walidacja je wychwyci, zamiast po cichu
  przepuścić niespójność.
- Wejście i wyniki (`RocketParams`, `SimResult`) są `frozen` — bo te same
  obiekty krążą po tysiącach przebiegów Monte Carlo i mutacja byłaby źródłem
  trudnych błędów.
- Wielkości pierwotne to PARAMETRY; wielkości z nich wynikające to
  `computed_field`. Przykład: w `Stage` parametrami są thrust/isp/burn_time, a
  mass_flow/propellant_mass są liczone. Dzięki temu NIE DA SIĘ podać niespójnej
  fizycznie trójki — niespójność jest niemożliwa z definicji, nie wyłapywana.
- Granice walidacji nie są arbitralne: pochodzą ze SMAD (rozdz. 17, App. B/F).
  Zob. `constants.py` — komentarze wskazują źródło każdej wartości.

## Konwencje
- Wszystko w SI, układ inercjalny kartezjański, kanoniczny stan [x,y,vx,vy,m].
- Nazwy importu z prefiksem dt_ (`import dt_contracts`).
- Stałe fizyczne i progi żyją w `constants.py` — silnik importuje je STĄD,
  nie wpisuje własnych. To utrzymuje jedno źródło prawdy dla μ, R, g0, progów.

## Wersjonowanie
- `__contract_version__` w `__init__.py` — bump przy KAŻDEJ zmianie kształtu
  schematów. Pozwala pozostałym pakietom wykryć niezgodność wersji kontraktu.

## Testy
- Testy w `tests/` weryfikują sedno: niemożliwość niespójnych danych, twarde
  granice (Isp ≤ 455 s, masy > 0, 1–4 stopni), poprawność pól pochodnych,
  niemutowalność. Każda zmiana schematu musi przejść te testy.

## Głębszy kontekst (po „dlaczego")
- Decyzje o modelu napędu i wartościach: `docs/decisions/` (ADR napęd/SMAD).
- Architektura i przepływ danych: `docs/architecture/`.
