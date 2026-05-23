# Konwencje commitów

Format commitów w tym repozytorium. Stosują się do nich wszyscy — człowiek
i instancje. Notacja jest zainspirowana Conventional Commits, ale świadomie się
od nich różni: dopuszcza WIELE tagów w jednym commicie i traktuje nawias jako
POZIOM repozytorium, nie dowolny opis.

## Format

```
<tag1,tag2,...>(zakres): treść commita
```

- `<...>` — jeden lub więcej TAGÓW oddzielonych przecinkiem (czego rodzaju jest
  zmiana). Nawiasy ostrokątne obowiązkowe.
- `(zakres)` — POZIOM repozytorium, którego dotyczy zmiana (gdzie w repo).
- `treść` — zwięzły opis w trybie rozkazującym lub opisowym, małą literą.

Przykład: `<feat,test>(physics-engine): dodaj fazę wznoszenia z modelem oporu`

## Tagi (rodzaj zmiany)

| Tag        | Kiedy używać |
|------------|--------------|
| `feat`     | nowa funkcjonalność / kod realizujący nową możliwość |
| `fix`      | naprawa błędu w istniejącym kodzie |
| `test`     | dodanie lub zmiana testów |
| `refactor` | zmiana kodu BEZ zmiany zachowania (czyszczenie, reorganizacja) |
| `perf`     | optymalizacja wydajności (zachowanie bez zmian, szybciej/lżej) |
| `docs`     | dokumentacja (markdown, docstringi, komentarze, README) |
| `script`   | skrypty pomocnicze (bash, narzędzia dev/ops) |
| `struct`   | zmiana struktury folderów (przenoszenie, tworzenie, usuwanie katalogów) |
| `config`   | pliki konfiguracyjne: json, yaml, toml, Makefile, pyproject.toml, .gitignore |
| `chore`    | drobne porządki niewchodzące w powyższe (bump zależności, sprzątanie) |

Uwaga: `style` (samo formatowanie) zwykle NIE jest osobnym commitem — formatowanie
robi ruff/prettier przy okazji `feat`/`fix`/`refactor`. Używaj tylko, gdy commit
naprawdę dotyczy wyłącznie formatu.

## Zakres (poziom repo, którego dotyczy)

Dopełnienie w nawiasie wskazuje, GDZIE w repo jest zmiana:

| Zakres            | Dotyczy |
|-------------------|---------|
| `contracts`       | pakiet wspólnych schematów (dt_contracts) |
| `physics-engine`  | silnik fizyczny (dt_physics) |
| `api`             | backend HTTP (dt_api) |
| `ai`              | backend optymalizacji (dt_ai) |
| `frontend`        | aplikacja React/TS |
| `docs/decisions`  | decyzje architektoniczne (ADR) |
| `docs/architecture` | dokumentacja architektury |
| `docs`            | pozostała dokumentacja (gdy nie wskazujemy podkatalogu) |
| `scripts`         | skrypty repo |
| `root`            | poziom korzenia (root pyproject.toml, .gitignore, CLAUDE.md, itp.) |
| `tests`           | testy cross-package w root (integration/soak) |

Zakres może być podkatalogiem, gdy precyzja pomaga (np. `docs/decisions` zamiast
`docs`). Wybieraj najbardziej konkretny sensowny poziom.

## Wiele tagów — zasada

Commit często dotyczy kilku wymiarów naraz (np. nowy kod + jego testy). Wtedy
podajemy WIELE tagów, zamiast sztucznie rozbijać commit:

- Tagi w kolejności WAŻNOŚCI — pierwszy oddaje dominujący charakter zmiany.
  `<feat,test>` znaczy „głównie funkcja, przy okazji testy".
- MIĘKKI SUFIT: jeśli potrzebujesz więcej niż 3 tagów, to sygnał, że commit
  robi za dużo — rozważ podział na atomowe commity. Nie jest to twardy zakaz,
  lecz wskaźnik diagnostyczny.
- Dawaj tyle tagów, ile PRAWDZIWYCH wymiarów ma zmiana — nie dokładaj „na zapas".

## Przykłady (z tego projektu)

```
<feat,test>(contracts): dodaj schematy RocketParams i SimResult z testami
<struct,config>(root): wydziel packages/ i przestaw root na uv workspace
<config>(root): dopisz tool.uv.sources z powiązaniami między członami
<docs>(docs/decisions): ADR wyboru modelu napędu (ciąg+Isp+czas)
<feat>(physics-engine): zaimplementuj fazę wstawienia na orbitę
<fix,test>(physics-engine): popraw wykrywanie max-Q jako zdarzenia
<perf>(ai): zwektoryzuj ensemble Monte Carlo do tablicy (N,5)
<refactor>(api): wydziel walidację żądania do osobnej zależności
<docs>(physics-engine): uzupełnij CLAUDE.md o regułę werdyktu keplerowskiego
<script>(scripts): dodaj dump_repo_structure.sh
<chore>(root): podbij wersje numpy i scipy w lockfile
```

## Zasady ogólne

- Treść w jednej linii nagłówka zwięźle; szczegóły w ciele commita (po pustej linii).
- Jeden commit = jedna spójna zmiana. Wiele tagów opisuje jej wymiary, nie
  usprawiedliwia mieszania niezwiązanych rzeczy.
- Tryb rozkazujący („dodaj", „popraw") lub opisowy — konsekwentnie w repo.
- Zmiany w `contracts` i root `pyproject.toml` wymagają zgody człowieka
  (patrz CLAUDE.md) — commit nie obchodzi tej zasady.