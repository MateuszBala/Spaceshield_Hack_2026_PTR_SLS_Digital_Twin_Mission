# ADR: Graceful degradation przy braku pakietu AI

Status: zaakceptowana
Data: 2026-05-23
Kontekst czasowy: deadline ~12 h; pakiet AI ma priorytet COULD (realizowany na
końcu, jeśli starczy czasu).

## Kontekst

Pakiet `ai` (optymalizacja masy startowej) jest celowo odłożony na koniec jako
najmniej raniąca strata przy ograniczonym czasie. Powstaje ryzyko: jeśli API i
frontend założą, że AI ZAWSZE istnieje, to brak gotowego pakietu AI wywali
ścieżki, które się do niego odwołują — w najgorszym razie psując demo rdzenia
(MUST), które od AI w ogóle nie zależy.

Decyzja musi zapaść TERAZ, nie przy integracji, bo wpływa na kształt API i
frontendu od pierwszej linii.

## Decyzja

System traktuje AI jako MOŻLIWOŚĆ OPCJONALNĄ, nie założenie. Konkretnie:

1. **API**: endpoint optymalizacji istnieje zawsze, ale gdy pakiet `dt_ai` jest
   niedostępny (nie zaimportowany / nie zainstalowany), zwraca czytelną
   odpowiedź o niedostępności (status sygnalizujący „funkcja wyłączona”,
   nie błąd 500). API wykrywa dostępność AI przy starcie i wystawia to jako
   informację o możliwościach (np. pole w odpowiedzi „health”/„capabilities”).

2. **Frontend**: pyta API o dostępne możliwości i — gdy AI niedostępne —
   CHOWA lub wyszarza przycisk „optymalizuj”. UI nigdy nie wywołuje funkcji,
   o której wie, że jej nie ma. Brak AI = brak elementu UI, nie zepsuty ekran.

3. **Rdzeń (MUST) nie zależy od AI**: pętla zmiana→przeliczenie→werdykt działa
   wyłącznie na silniku + API + froncie. AI jest naddatkiem.

## Konsekwencje

- Rdzeń demo jest odporny na nieukończenie AI — Akt 1 i 2 scenariusza wideo
  nie wymagają AI; Akt 3 ma wariant bez AI (ręczna korekta parametru).
- API i frontend mają jawny mechanizm wykrywania możliwości — to dobre nie tylko
  dla AI, ale jako wzorzec dla każdej opcjonalnej funkcji w przyszłości.
- Koszt: kilkanaście minut na zaprojektowanie „capabilities” w API i prostą
  logikę chowania UI. Zwrot: zero ryzyka, że COULD zabije MUST.

## Implikacje dla briefów instancji

- Brief API: zaprojektuj wykrywanie dostępności AI i odpowiedź „niedostępne”
  ZANIM powstanie sam pakiet AI. Endpoint optymalizacji ma działać (zwracając
  niedostępność) nawet bez `dt_ai`.
- Brief frontend: steruj widocznością UI optymalizacji flagą z API
  („capabilities”), nie zakładaj obecności AI na sztywno.
- Brief AI (gdy ruszy): wystarczy zaimplementować funkcję; warstwa
  niedostępności już istnieje i sama się „włączy”, gdy pakiet się pojawi.
