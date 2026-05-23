# Strategia plików CLAUDE.md

Decyzja o tym, jak organizujemy pamięć projektu dla instancji Claude. Utrwala
zasady, według których powstał główny CLAUDE.md i pliki zagnieżdżone.

## Dwa poziomy instrukcji dla instancji

Rozróżniamy instrukcje TRWAŁE i ZADANIOWE:
- Trwałe (`CLAUDE.md`): kim jest pakiet, jego granice, zasady, konwencje.
  Ładowane automatycznie, obowiązują w każdej sesji. To jest „kim jesteś i jak
  pracujesz w tym pakiecie".
- Zadaniowe (briefy): konkretne zlecenie „zaimplementuj X według tej koncepcji".
  Jednorazowe, opisują pojedyncze zadanie. Powstają w `docs/` (np. tasks/).

Ten dokument dotyczy poziomu TRWAŁEGO.

## Mechanika ładowania (dlaczego struktura jest taka)

- Główny `CLAUDE.md` (root) ładuje się ZAWSZE, w każdej sesji, jako przodek.
  Przeżywa kompaktację (jest re-wczytywany z dysku). Stąd: rzeczy KRYTYCZNE i
  WSPÓLNE dla wszystkich instancji idą do głównego.
- Zagnieżdżone `packages/*/CLAUDE.md` ładują się LENIWIE — tylko gdy instancja
  pracuje w danym katalogu. Nie są re-wstrzykiwane po kompaktacji. Stąd: rzeczy
  SPECYFICZNE dla pakietu, mniej krytyczne dla bezpieczeństwa całości.

Konsekwencja: granice zapisu i reguła read-only dla contracts są w GŁÓWNYM
(muszą przeżyć kompaktację i widzieć je wszyscy), a np. dobór solverów silnika
jest w zagnieżdżonym (potrzebny tylko instancji silnika).

## Zasada niepowtarzania

Zagnieżdżony plik NIE powtarza głównego — dokłada to, co odróżnia ten pakiet od
pozostałych. Dzięki temu pliki są krótkie i nie ma ryzyka, że dwa pliki powiedzą
sprzecznie to samo. Jeśli reguła dotyczy wszystkich — jej miejsce jest w głównym.

## CLAUDE.md vs ADR — podział „co" od „dlaczego"

- `CLAUDE.md` mówi CO ROBIĆ (trwała instrukcja). Zwięźle, z mikro-uzasadnieniem
  tylko przy regułach, które bez „dlaczego" kuszą do złamania.
- ADR (`docs/decisions/`) mówi DLACZEGO TAK ZDECYDOWALIŚMY (wiedza). Pełna
  narracja rozważań, alternatyw, trade-offów.
- `CLAUDE.md` ODSYŁA do ADR po głęboki kontekst, zamiast go zawierać. To trzyma
  instrukcje krótkie, a wiedzę dostępną dla zainteresowanej instancji.

## Konwencja przyjęta dla tego projektu

- Język: polski (spójnie z dokumentacją projektu).
- Obszerność zagnieżdżonych: bogatsze (z kontekstem i „dlaczego"), TWARDY LIMIT
  180 linii na plik. Powód limitu: powyżej pewnego rozmiaru pliki zużywają
  więcej kontekstu i obniżają przestrzeganie reguł.
- Każdy zagnieżdżony plik ma sekcje: czym pakiet JEST/NIE jest; reguły IMPORTANT
  z granicami; zasady projektowe z „dlaczego"; konwencje; granice i zgoda
  człowieka; odnośniki do głębszego kontekstu.

## Mapa plików

```
CLAUDE.md                        # root — wspólne, krytyczne, przeżywa kompaktację
packages/contracts/CLAUDE.md     # read-only, źródło prawdy, schematy
packages/physics-engine/CLAUDE.md# najbogatszy — maszyna faz, numeryka, Kepler
packages/api/CLAUDE.md           # cienka skorupa HTTP, import silnika
packages/ai/CLAUDE.md            # MC/optymalizacja, import in-process
frontend/CLAUDE.md               # React/TS, poza uv, granica językowa
```

## Utrzymanie

- Plik aktualizujemy, gdy instancja regularnie myli się w danym obszarze — to
  sygnał, że reguły brakuje. Nie dokładamy reguł „na zapas".
- Zmiana reguły wspólnej → główny CLAUDE.md. Zmiana specyfiki pakietu →
  odpowiedni zagnieżdżony. Zmiana uzasadnienia decyzji → ADR.
