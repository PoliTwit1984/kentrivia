# System Architecture and Flow Diagrams

## Game Flow

```mermaid
sequenceDiagram
    participant Host
    participant Server
    participant Socket.IO
    participant Database
    participant Player

    Host->>Server: Create Game
    Server->>Database: Store Game (Sequelize)
    Server-->>Host: Game PIN

    Player->>Server: Join Game (PIN)
    Server->>Database: Verify Game
    Server->>Database: Store Player
    Server-->>Player: Join Confirmation
    Server-->>Host: Player Joined

    Player->>Socket.IO: Connect WebSocket
    Socket.IO->>Server: Authenticate Session
    Server-->>Socket.IO: Session Valid
    Socket.IO-->>Player: Connected

    Host->>Socket.IO: Start Game
    Socket.IO->>Server: Validate Host
    Server->>Database: Update Game State
    Socket.IO-->>Player: Game Started
    Socket.IO-->>Host: Game Started

    loop Questions
        Host->>Socket.IO: Next Question
        Server->>Database: Get Question
        Socket.IO-->>Player: Question Preparing
        Socket.IO-->>Player: Question Started
        Player->>Socket.IO: Submit Answer
        Server->>Database: Store Answer
        Socket.IO-->>Player: Answer Result
        Socket.IO-->>Host: Answer Submitted
        Socket.IO-->>All: Update Leaderboard
    end
```

## Component Architecture

```mermaid
graph TD
    A[Express App] --> B[Game Routes]
    A --> C[Auth Routes]
    A --> D[Main Routes]
    A --> E[Socket.IO Server]

    B --> F[Socket Events]
    B --> G[Game Controllers]
    B --> H[View Templates]

    E --> I[Event Handlers]
    I --> J[Sequelize Models]
    I --> K[Room Management]
    I --> L[Session Store]

    subgraph Frontend
        M[EJS Templates]
        N[Socket.IO Client]
        O[Bootstrap UI]
        P[Client JS]
        Q[Connection Status]
    end

    subgraph Database
        R[PostgreSQL]
        S[Sessions Table]
        T[Game Tables]
        U[User Tables]
    end

    J --> R
    L --> S
    G --> T
    C --> U
```

## Authentication Flow

```mermaid
sequenceDiagram
    participant Client
    participant Server
    participant Passport
    participant Database
    participant Socket.IO

    Client->>Server: Login Request
    Server->>Passport: Authenticate
    Passport->>Database: Verify Credentials
    Database-->>Passport: User Data
    Passport-->>Server: Authentication Result
    Server-->>Client: Session Cookie

    Client->>Socket.IO: Connect WebSocket
    Socket.IO->>Server: Validate Session
    Server->>Database: Verify Session
    Database-->>Server: Session Valid
    Server-->>Socket.IO: Session Authenticated
    Socket.IO-->>Client: Connection Established
```

## Socket.IO Event Flow

```mermaid
graph TD
    A[Socket Connection] --> B{Event Type}
    
    B -->|player_join| C[Join Room]
    B -->|game_started| D[Start Game]
    B -->|preparing_next_question| E[Prepare Question]
    B -->|submit_answer| F[Process Answer]
    
    C --> G[Room Management]
    D --> H[Game State]
    E --> I[Question Flow]
    F --> J[Score Calculation]
    
    G --> K[Broadcast Updates]
    H --> K
    I --> K
    J --> K
    
    K --> L[Connected Clients]

    subgraph Session Handling
        M[Session Validation]
        N[Session Store]
        O[Session Recovery]
    end

    A --> M
    M --> N
    O --> N
```

## Data Models

```mermaid
erDiagram
    User ||--o{ Game : hosts
    Game ||--o{ Question : contains
    Game ||--o{ Player : has
    Player ||--o{ Answer : submits
    Question ||--o{ Answer : receives
    Session ||--o{ User : authenticates

    User {
        int id PK
        string username
        string email
        string password
        datetime created_at
        datetime updated_at
    }

    Game {
        int id PK
        string pin
        int host_id FK
        bool is_active
        datetime started_at
        datetime ended_at
        int current_question_index
        datetime current_question_started_at
        datetime created_at
        datetime updated_at
    }

    Question {
        int id PK
        int game_id FK
        text content
        string correct_answer
        json incorrect_answers
        int time_limit
        int points
        datetime created_at
        datetime updated_at
    }

    Player {
        int id PK
        int game_id FK
        string nickname
        int score
        int current_streak
        bool is_ready
        datetime created_at
        datetime updated_at
    }

    Answer {
        int id PK
        int player_id FK
        int question_id FK
        string answer_text
        bool is_correct
        float response_time
        int points_awarded
        datetime created_at
        datetime updated_at
    }

    Session {
        string id PK
        json data
        datetime expires
        datetime created_at
        datetime updated_at
    }
