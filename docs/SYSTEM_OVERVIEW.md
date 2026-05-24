# Rocket Digital Twin — opis działania systemu

Dokument dla oceniających. Wyjaśnia, czym jest projekt, jak zbudowany i co
pokazuje. Wysokopoziomowy — podstawy fizyczne opisuje osobny dokument
(`PHYSICS_MODEL.md`).

---

## 1. Czym to jest

Cyfrowy bliźniak (Digital Twin) rakietowego systemu wynoszenia małego satelity na
niską orbitę okołoziemską (LEO). System pozwala zaprojektować rakietę, przeliczyć
misję i zobaczyć, czy satelita osiąga orbitę — a potem **zmienić dowolny parametr i
natychmiast zobaczyć, jak zmienia się wynik**.

To właśnie odróżnia projekt od zwykłego kalkulatora: nie liczy jednej liczby, lecz
domyka **pętlę eksperymentu** — zmiana → symulacja → widoczny skutek na powodzeniu
misji i na trajektorii. Użytkownik bada „co się stanie, jeśli…" na żywo.

---

## 2. Pętla Digital Twina — sedno systemu

```
   ┌─────────────────────────────────────────────────────┐
   │                                                     │
   ▼                                                     │
[ zmiana parametru ] → [ symulacja misji ] → [ werdykt + trajektoria ]
  masa, ciąg, Isp,       fizyka lotu:          orbita TAK/NIE + powód,
  liczba stopni…         3 fazy, separacje     tor lotu, telemetria
   │                                                     ▲
   └─────────────────────── eksperyment ────────────────┘
```

Użytkownik zmienia parametr rakiety (np. masę paliwa stopnia), klika „Przelicz",
a system w ułamku sekundy przelicza całą misję i pokazuje nowy werdykt oraz nową
trajektorię. Można to powtarzać dowolnie — to jest cyfrowy bliźniak w działaniu:
bezpieczne eksperymentowanie na modelu przed rzeczywistym lotem.

---

## 3. Architektura — cztery warstwy, jedna granica prawdy

System składa się z czterech rozdzielnych części, komunikujących się przez wspólny,
ściśle zdefiniowany kontrakt danych:

```
   PRZEGLĄDARKA                      BACKEND (Python)
   ┌──────────────┐   HTTP/JSON   ┌──────────────┐   wywołanie    ┌──────────────┐
   │  frontend    │ ────────────▶ │     API      │ ────────────▶  │   silnik     │
   │  React/TS    │ ◀──────────── │  (FastAPI)   │ ◀────────────  │  fizyczny    │
   │  wizualizacja│   SimResult   │ cienka skorupa│   SimResult    │  numeryka    │
   └──────────────┘               └──────────────┘                └──────────────┘
          ▲                              ▲                                ▲
          └──────────────────────────────┼────────────────────────────────┘
                                          │
                              ┌───────────────────────┐
                              │  kontrakt danych      │
                              │  (schematy Pydantic)  │
                              │  RocketParams,        │
                              │  SimResult, …         │
                              └───────────────────────┘
```

- **Silnik fizyczny** — czysta numeryka (NumPy/SciPy). Bierze parametry rakiety,
  zwraca wynik misji. Nie wie o istnieniu sieci ani interfejsu — to biblioteka
  funkcji `parametry → wynik`, łatwa do testowania i ponownego użycia.
- **API** (FastAPI) — cienka warstwa HTTP. Przyjmuje żądanie symulacji z
  przeglądarki, woła silnik, zwraca wynik. Bez logiki fizycznej — całe „myślenie"
  jest w silniku.
- **Frontend** (React/TypeScript) — interfejs: edycja parametrów, wizualizacja
  trajektorii, telemetria, sekwencja misji, werdykt. Komunikuje się z backendem
  wyłącznie przez HTTP.
- **Kontrakt danych** — wspólny słownik kształtu danych (parametry rakiety, wynik
  symulacji, telemetria, elementy orbity). Wszystkie warstwy mówią tym samym
  językiem; typy interfejsu generują się automatycznie z definicji backendu, co
  eliminuje rozjazd między frontem a serwerem.

Dlaczego taki podział: każda warstwa ma jedną odpowiedzialność i wyraźną granicę.
Silnik można rozwijać i testować w izolacji (czysta fizyka), interfejs niezależnie
(czysta prezentacja), a kontrakt gwarantuje, że się dogadają. Pozwoliło to budować
wszystkie warstwy **równolegle** od pierwszego dnia.

---

## 4. Jak przebiega pojedyncza symulacja

1. Użytkownik ustawia parametry rakiety w interfejsie (stopnie: ciąg, impuls
   właściwy, czas pracy, masa; ładunek; kąt startu).
2. Frontend wysyła żądanie symulacji do API (HTTP/JSON).
3. API woła silnik fizyczny, przekazując parametry.
4. Silnik całkuje lot przez trzy fazy (wznoszenie → wstawienie → orbita),
   wykrywając zdarzenia misji (max-Q, wypalenia, separacje), i liczy werdykt o
   orbicie z elementów keplerowskich.
5. Wynik (werdykt + trajektoria + telemetria + sekwencja zdarzeń) wraca przez API
   do interfejsu.
6. Frontend rysuje trajektorię, pokazuje werdykt i odtwarza sekwencję misji.

Cała pętla trwa ułamek sekundy, co umożliwia interaktywne eksperymentowanie.

---

## 5. Co pokazuje interfejs

- **Werdykt misji** — duży, jednoznaczny: „ORBITA OSIĄGNIĘTA" / „BRAK ORBITY",
  z powodem i kluczowymi liczbami (perygeum, apogeum, mimośród, okres).
- **Trajektoria 2D** — tor lotu rakiety z zaznaczonymi zdarzeniami misji.
- **Sekwencja misji** — oś czasu kamieni milowych w stylu transmisji kosmicznych:
  start, max-Q, wypalenia i separacje stopni, separacja ładunku, wejście na orbitę.
- **Telemetria** — prędkość, wysokość, przeciążenie (g) w czasie; odczyt na żywo
  w stylu transmisji startu.
- **Edycja parametrów** — karty stopni z polami/suwakami; zmiana i ponowne
  przeliczenie to sedno demo.

---

## 6. Scenariusz demonstracyjny

Sednem pokazu jest pętla Digital Twina na konkretnym przykładzie:

1. **Rakieta startowa** — gotowy preset („złoty przykład"), który osiąga orbitę.
   Pokazujemy trajektorię i werdykt „ORBITA OSIĄGNIĘTA".
2. **Zmiana parametru** — pogarszamy jeden parametr (np. skracamy czas pracy
   silnika górnego stopnia). Przeliczamy.
3. **Inny wynik** — werdykt zmienia się na „BRAK ORBITY", trajektoria pokazuje, że
   rakieta nie domyka orbity. To jest dowód działania cyfrowego bliźniaka: zmiana
   wpływa na powodzenie misji, widoczna natychmiast.

Ten sam mechanizm pozwala badać dowolny scenariusz — więcej paliwa, inny rozkład
stopni, inny ładunek — i obserwować wpływ na misję.

---

## 7. Rozszerzalność

Architektura jest przygotowana na rozbudowę bez przebudowy rdzenia:
- **Optymalizacja parametrów** (minimalizacja masy startowej przy warunku orbity) —
  osobny moduł wołający silnik w pętli; interfejs wykrywa jego dostępność i
  pokazuje opcję optymalizacji tylko, gdy moduł jest obecny (rdzeń demo nie zależy
  od tej funkcji).
- **Zmienna liczba stopni** w interfejsie (1-4) — kontrakt i silnik już to wspierają.
- **Wizualizacja 3D**, dashboard, porównanie scenariuszy — warstwa prezentacji
  rozbudowywalna niezależnie od fizyki, bo czyta ten sam kontrakt.

System działa w trybie podstawowym (rdzeń pętli) niezależnie od tego, które
rozszerzenia są aktywne — funkcje opcjonalne nigdy nie blokują działania całości.
