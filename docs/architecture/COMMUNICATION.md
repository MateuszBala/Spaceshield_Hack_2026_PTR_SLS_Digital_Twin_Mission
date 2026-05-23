# Komunikacja między pakietami

Dokument obrazuje, jak komunikują się ze sobą cztery pakiety projektu oraz warstwa
wspólna `contracts`. Rozróżniamy dwie warstwy:

- **Kanał `import` (in-process)** — wywołanie funkcji w tym samym procesie Pythona,
  bez serializacji i sieci. Używany tam, gdzie liczy się przepustowość (AI → silnik).
- **Kanał `HTTP`** — granica procesu/sieci między przeglądarką a backendem. Używany
  tylko między frontendem a API.

`contracts` jest zależnością wszystkich pakietów, ale w runtime jest "niewidzialny":
to definicja *kształtu* danych płynących po strzałkach, nie osobny serwis.

---

## 1. Zależności + kanały komunikacji

```mermaid
graph TD
    subgraph BROWSER["Przeglądarka"]
        FE["③ frontend (React/TS)<br/>parametry, sterowanie, wizualizacja 3D<br/><i>poza uv workspace</i>"]
    end

    subgraph SERVER["Backend (Python, uv workspace)"]
        API["② api (FastAPI)<br/>cienka skorupa HTTP"]
        AI["④ ai<br/>Monte Carlo / optymalizacja"]
        ENG["① physics-engine<br/>czysta numeryka, params → wynik"]
    end

    CONTRACTS["⭐ contracts (Pydantic)<br/>RocketParams · SimRequest/Result<br/>TelemetryFrame · OrbitalElements"]

    FE -->|"HTTP / JSON<br/>(schemat OpenAPI)"| API
    API -->|"import (in-process)"| ENG
    AI -->|"import (in-process)<br/>tysiące wywołań w pętli"| ENG

    ENG -.->|zależy od| CONTRACTS
    API -.->|zależy od| CONTRACTS
    AI -.->|zależy od| CONTRACTS
    FE -.->|"typy TS<br/>generowane z OpenAPI"| CONTRACTS

    classDef engine fill:#dce9f5,stroke:#2e6da4,color:#1a1a1a;
    classDef api fill:#e7f0d9,stroke:#5a8a2e,color:#1a1a1a;
    classDef ai fill:#f5e6d3,stroke:#b5742e,color:#1a1a1a;
    classDef fe fill:#ead9f0,stroke:#7a3e9a,color:#1a1a1a;
    classDef contracts fill:#f7f2cf,stroke:#9a8a2e,color:#1a1a1a;

    class ENG engine;
    class API api;
    class AI ai;
    class FE fe;
    class CONTRACTS contracts;
```

Legenda:
- linia ciągła `→` = kanał komunikacji w runtime (HTTP lub import),
- linia przerywana `-.->` = zależność od warstwy wspólnej `contracts`.

Kluczowe granice:
- **frontend nie importuje Pythona** — gada z API wyłącznie po HTTP; typy TypeScript
  generuje z OpenAPI (które FastAPI produkuje z modeli `contracts`).
- **physics-engine nie wie o istnieniu API ani frontu** — jest czystą biblioteką.
- **AI woła silnik importem**, nie przez HTTP — bo robi tysiące przebiegów w pętli i
  narzut sieciowy byłby nieakceptowalny.

---

## 2. Przepływ danych: pojedyncza symulacja z frontu

```mermaid
sequenceDiagram
    actor User as Użytkownik
    participant FE as ③ frontend
    participant API as ② api (FastAPI)
    participant ENG as ① physics-engine

    User->>FE: ustawia parametry rakiety
    FE->>API: POST /simulate (SimRequest)
    Note over FE,API: kanał HTTP / JSON
    API->>ENG: run(RocketParams)
    Note over API,ENG: import in-process
    ENG->>ENG: maszyna stanów faz<br/>(wznoszenie → wstawienie → orbita)
    ENG-->>API: SimResult<br/>(TelemetryFrame[] + OrbitalElements + werdykt)
    API-->>FE: 200 OK (SimResult JSON)
    FE->>User: wykresy, telemetria, wizualizacja 3D
```

---

## 3. Przepływ danych: optymalizacja / Monte Carlo (AI)

```mermaid
sequenceDiagram
    participant AI as ④ ai
    participant ENG as ① physics-engine

    Note over AI: cel: min. masa startowa<br/>przy warunku osiągnięcia orbity
    loop tysiące iteracji (in-process)
        AI->>ENG: run(RocketParams_i)
        Note over AI,ENG: import — bez HTTP, bez serializacji
        ENG-->>AI: SimResult_i (werdykt orbitalny + metryki)
    end
    AI->>AI: agregacja / optymalizacja / dyspersja
    Note over AI: wynik (np. optymalne RocketParams)<br/>wyrażony w schematach contracts
```

Wynik pracy AI (zoptymalizowane parametry, statystyki dyspersji) jest wyrażony w tych
samych schematach `contracts`, więc może zostać podany dalej do API/frontu bez
tłumaczenia formatów.

---

## 4. Mapowanie na worktree i granice zapisu

| Pakiet | Instancja / worktree | Pisze w | Komunikuje się przez |
|--------|----------------------|---------|----------------------|
| ① physics-engine | `feat/engine` | `packages/physics-engine/` | wywoływany importem przez ② i ④ |
| ② api | `feat/api` | `packages/api/` | HTTP ↔ ③ ; import → ① |
| ③ frontend | `feat/frontend` | `packages/frontend/` | HTTP → ② |
| ④ ai | `feat/ai` | `packages/ai/` | import → ① |
| ⭐ contracts | — (read-only) | nikt samodzielnie | zależność wszystkich |

`contracts` jest jedynym współdzielonym punktem — dlatego pozostaje read-only dla
instancji i musi być zaprojektowany jako pierwszy. Każda zmiana kontraktu to zmiana
styku wielu pakietów, więc zgłaszana, nie wprowadzana samodzielnie.
