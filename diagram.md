# System Architecture and Flow Diagrams

## Game Flow

```mermaid
sequenceDiagram
    participant Host
    participant Server
    participant Player
    participant Database

    Host->>Server: Create Game
    Server->>Database: Store Game
    Server-->>Host: Game PIN

    Player->>Server: Join Game (PIN)
    Server->>Database: Verify Game
    Server->>Database: Store Player
    Server-->>Player: Join Confirmation
    Server-->>Host: Player Joined

    Host->>Server: Start Game
    Server->>Database: Update Game State
    Server-->>Player: Game Started
    Server-->>Host: Game Started

    loop Questions
        Host->>Server: Prepare Question
        Server->>Database: Get Question
        Server-->>Player: Question Preparing
        Server-->>Player: Question Started
        Player->>Server: Submit Answer
        Server->>Database: Store Answer
        Server-->>Player: Answer Result
        Server-->>Host: Answer Submitted
    end
```

## Test Flow

```mermaid
sequenceDiagram
    participant Test
    participant Server
    participant Database

    Note over Test: Setup Phase
    Test->>Database: Create Test User (Host)
    Test->>Database: Create Test Game
    Test->>Database: Add Test Questions

    Note over Test: Host Connection
    Test->>Server: Create Host Socket
    Test->>Server: Host Join Game
    Server-->>Test: Join Confirmation

    Note over Test: Player Setup
    Test->>Database: Create Test Player
    Test->>Server: Create Player Socket
    Test->>Server: Player Join Game
    Server-->>Test: Join Confirmation (Currently Failing)

    Note over Test: Game Flow
    Test->>Server: Start Game
    Server-->>Test: Game Started Event
    Test->>Server: Prepare Question
    Server-->>Test: Question Preparing Event
    Server-->>Test: Question Started Event

    Note over Test: Verification Points
    Test->>Test: Verify Join Events
    Test->>Test: Verify Game Start
    Test->>Test: Verify Question Flow
```

## Component Architecture

```mermaid
graph TD
    A[Flask App] --> B[Game Module]
    A --> C[Auth Module]
    A --> D[Main Module]
    A --> E[API Module]

    B --> F[Socket Events]
    B --> G[Game Routes]
    B --> H[Game Forms]

    F --> I[Event Handlers]
    I --> J[Database]
    I --> K[Room Management]
    I --> L[Session Management]

    subgraph Testing
        M[Test Cases]
        N[Test Database]
        O[Socket Client]
        P[Test Fixtures]
    end

    M --> O
    O --> F
    M --> N
```

## Current Testing Focus

```mermaid
graph TD
    A[test_game_questions.py] --> B[Socket Setup]
    B --> C[Host Connection]
    B --> D[Player Connection]
    
    C --> E[Host Join]
    D --> F[Player Join]
    F --> G{Join Event Issue}
    
    G --> H[Event Emission]
    G --> I[Room Management]
    G --> J[Session State]
    
    H --> K[Debugging]
    I --> K
    J --> K
```

## Event Flow (Current Issue)

```mermaid
sequenceDiagram
    participant Test
    participant Server
    participant Room
    participant Session

    Test->>Server: Player Join Request
    Server->>Session: Set Session Data
    Server->>Room: Join Room
    Server--xTest: Player Joined Event (Missing)
    Note over Server,Test: Event not reaching test client
