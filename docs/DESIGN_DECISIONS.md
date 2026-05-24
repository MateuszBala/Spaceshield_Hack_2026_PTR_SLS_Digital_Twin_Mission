# Decyzje projektowe — uzasadnienia

Dokument dla oceniających. Pokazuje, dlaczego projekt zbudowano tak, a nie inaczej —
kluczowe wybory architektoniczne i inżynierskie wraz z uzasadnieniem. Uzupełnia
`SYSTEM_OVERVIEW.md` (co i jak) o warstwę „dlaczego".

---

## 1. Własny symulator zamiast OpenRocket

Zadanie dopuszczało integrację z OpenRocket. Świadomie z niej zrezygnowaliśmy.

OpenRocket to symulator rakiet modelarskich/amatorskich — jego model fizyczny
dotyczy lotu atmosferycznego i nie zna pojęcia orbity ani wstawienia na LEO.
Tymczasem **sednem zadania jest właśnie faza orbitalna**: werdykt, czy satelita
osiągnął stabilną orbitę. Tego OpenRocket nie obsługuje. Dodatkowo lot naddźwiękowy
jest jego słabą stroną.

Budowa własnego silnika dała pełną kontrolę nad tym, co najważniejsze — mechaniką
orbitalną i werdyktem z elementów keplerowskich — kosztem, który i tak trzeba było
ponieść, bo żadne gotowe narzędzie modelarskie nie liczy orbity.

## 2. Python jako ekosystem

Rozważaliśmy Scilab (w pełni wystarczyłby do numeryki), ale nie wnosi nic ponad
Pythona, a utrudnia warstwy punktowane w zadaniu (interaktywny interfejs,
dashboard, potencjalne AI/ML). Python pokrywa numerykę (NumPy/SciPy) i jednocześnie
otwiera cały ekosystem do interfejsu i rozszerzeń. MATLAB/Simulink i Unity
odrzucono jako nadmiarowe wobec uproszczonego prototypu.

## 3. Trzy fazy lotu jako trzy reżimy numeryczne

Misję dzielimy na wznoszenie, wstawienie i orbitę — nie arbitralnie, lecz dlatego,
że **każda faza ma inną dominującą fizykę**, a więc i inne wymagania numeryczne:

- wznoszenie: ciąg + grawitacja + opór atmosfery (sztywny, wymaga ciasnych tolerancji),
- wstawienie: opór znikomy, liczy się precyzja wektora prędkości,
- orbita: czysty problem dwóch ciał (gdzie liczy się długoterminowa stabilność energii).

Przejścia między fazami to wykrywane zdarzenia (max-Q, wypalenia, separacje), a nie
sztywne progi czasu — dzięki czemu ich położenie nie zależy od gęstości kroku
całkowania. To podejście „maszyny stanów faz" jest czystsze niż jeden uniwersalny
model na cały lot i bliższe temu, jak faktycznie analizuje się misje nośne.

## 4. Werdykt z elementów keplerowskich, nie z wysokości

Najważniejsza decyzja fizyczna. Naiwny symulator orzekłby „orbita osiągnięta", gdy
rakieta przekroczy zadaną wysokość — co jest błędem: można być na 400 km i spadać.
Liczymy werdykt z pełnych elementów orbity (energia, mimośród, perygeum), bo dopiero
one mówią, czy tor jest stabilną orbitą. To odróżnia projekt od kalkulatora wysokości
i jest opisane szczegółowo w `PHYSICS_MODEL.md`.

## 5. Monorepo z czterema pakietami i wspólnym kontraktem

Cały kod w jednym repozytorium, podzielony na rozłączne pakiety (silnik, API,
interfejs, opcjonalna optymalizacja) wokół wspólnej warstwy — kontraktu danych.

Dlaczego razem, a nie cztery osobne repozytoria: **atomowość zmian**. Zmiana
kontraktu dotykająca silnika i interfejsu to jeden spójny commit zamiast
rozjeżdżających się zmian w osobnych repo. Izolację między częściami daje podział
na katalogi i wspólny słownik typów, nie rozdzielenie repozytoriów.

Kontrakt danych jako pojedyncze źródło prawdy o kształcie danych był warunkiem
wejścia: zaprojektowany jako pierwszy, pozwolił budować wszystkie warstwy
równolegle wobec uzgodnionych typów (interfejs na atrapie wyniku, API na atrapie
silnika), zamiast czekać aż jedna część skończy, by zacząć następną.

## 6. Silnik jako czysta biblioteka, interfejs przez HTTP

Silnik fizyczny nie wie o istnieniu API ani interfejsu — to czyste funkcje
`parametry → wynik`, bez sieci i wejścia/wyjścia. Interfejs rozmawia z backendem
wyłącznie przez HTTP i nie importuje kodu fizycznego.

Konsekwencja: silnik jest trywialny do testowania (podaj parametry, sprawdź wynik) i
do ponownego użycia — ta sama funkcja obsługuje pojedynczą symulację z interfejsu i
mogłaby obsłużyć tysiące przebiegów w pętli optymalizacji, bez narzutu sieci.
Granica HTTP istnieje tam, gdzie jest naturalna (przeglądarka ↔ serwer), a nie
wewnątrz backendu.

## 7. Funkcje opcjonalne nie blokują rdzenia (graceful degradation)

Moduł optymalizacji parametrów (AI/ML) zaplanowano jako rozszerzenie realizowane na
końcu. Aby jego ewentualny brak nie zepsuł działającego rdzenia, system traktuje go
jako **możliwość opcjonalną, nie założenie**: API zgłasza, które funkcje są
dostępne, a interfejs pokazuje opcję optymalizacji tylko wtedy, gdy moduł istnieje.

Dzięki temu pętla demonstracyjna (zmiana → symulacja → werdykt) działa niezależnie
od tego, czy rozszerzenia są gotowe. To dobra praktyka inżynierska — rdzeń odporny
na nieukończenie dodatków — i jednocześnie zabezpieczenie demo: funkcja o najniższym
priorytecie nie może zagrozić temu, co najważniejsze.

## 8. Priorytetyzacja pod ograniczony czas

Projekt prowadzono pod twardym ograniczeniem czasu, z jawną hierarchią celów:
najpierw rdzeń bez którego nie ma projektu (pętla Digital Twina end-to-end), potem
wzmocnienia (dashboard, sekwencja misji, zmienna liczba stopni), na końcu dodatki
(optymalizacja, 3D). Zasada: nie zaczynać wzmocnień, póki rdzeń nie działa —
zabezpieczenie przed kilkoma niedokończonymi fragmentami zamiast jednego działającego
systemu. Budowę prowadzono „pionowym plastrem" (cienka, działająca kolumna przez
wszystkie warstwy), pogrubianą warstwami — tak, by w każdym momencie istniał
działający system, a nie zbiór niepołączonych części.
