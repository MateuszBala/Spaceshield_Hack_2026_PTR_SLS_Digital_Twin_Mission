# ai — pamięć pakietu (dt_ai)

Backend optymalizacji i analizy: Monte Carlo, optymalizacja parametrów rakiety.
Reguły wspólne dla repo są w głównym CLAUDE.md — tu specyfika.

## Czym ten pakiet JEST, a czym NIE jest
- JEST: warstwą, która WIELOKROTNIE woła silnik, by szukać dobrych parametrów
  rakiety i analizować rozrzut wyników.
- NIE jest: miejscem na fizykę. Nie reimplementuj modelu lotu — silnik jest
  jedynym źródłem dynamiki. AI tylko zadaje parametry i czyta wyniki.

## Jak ai rozmawia z silnikiem — IMPORTANT
- Silnik wołasz IMPORTEM in-process (`import dt_physics`), NIE przez HTTP.
  Powód: optymalizacja i Monte Carlo to tysiące wywołań w pętli; narzut HTTP
  (serializacja, sieć) byłby tu nieakceptowalny. To świadoma decyzja
  architektoniczna, inna niż dla frontu.
- Parametry przekazujesz jako `RocketParams`, wyniki czytasz jako `SimResult` —
  zawsze schematy `dt_contracts`. Wynik (zoptymalizowane parametry, statystyki
  dyspersji) wyrażaj też w schematach contracts, by dało się podać dalej bez
  tłumaczenia formatów.

## Cel optymalizacji (sedno zadania)
- Minimalizuj `RocketParams.liftoff_mass` przy TWARDYM warunku osiągnięcia
  orbity (verdict.reached_orbit). To jest główny cel projektu.
- Liczba stopni jest parametrem — jednym z najsilniejszych dla budżetu Δv.
  Optymalizacja może nim kręcić w granicach kontraktu (1–4).
- Wiązania (zakresy Isp, frakcje masowe) egzekwuje sam kontrakt — nie musisz ich
  dublować, ale generuj kandydatów w granicach, które kontrakt przyjmie.

## Wydajność (dlaczego to ważne właśnie tu)
- Dla masowego Monte Carlo wektoryzuj ensemble: stan jako tablica (N, 5), jeden
  krok przesuwa wszystkie trajektorie naraz — to różnica rzędów wielkości wobec
  pętli po pojedynczych przebiegach.
- Tryb lekki: dla MC ustawiaj `SimRequest.include_telemetry=False`, by nie
  zbierać pełnej telemetrii, której nie analizujesz.
- Optymalizacja: `scipy.optimize` (SLSQP/trust-constr dla wypukłych, dual_
  annealing/differential_evolution dla niewypukłego krajobrazu wielostopniowego).

## Konwencje
- Python ≥ 3.12, NumPy/SciPy, nazwy importu z prefiksem dt_.
- SI, kanoniczny stan — spójnie z silnikiem (nie konwertuj jednostek na styku).

## Granice i zgoda człowieka
- Piszesz wyłącznie w `packages/ai/`. `dt_contracts` i `physics-engine` są dla
  Ciebie zależnościami, nie polem edycji.
- Jeśli optymalizacja wymaga nowego pola wejścia/wyniku — ZGŁOŚ zmianę
  kontraktu, nie obchodź go.

## Głębszy kontekst
- Decyzja „import in-process vs HTTP”: `docs/architecture/COMMUNICATION.md`.
- Model napędu i co jest „pokrętłem”: ADR napęd + `dt_contracts/rocket.py`.
