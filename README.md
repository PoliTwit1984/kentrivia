# KenTrivia

A real-time multiplayer trivia game built with Node.js and Socket.IO.

## Features

- Real-time multiplayer gameplay with WebSocket communication
- Custom trivia game creation and hosting
- Live leaderboard and scoring system
- Time-based scoring with streak multipliers
- Player session management and reconnection
- QR code game joining
- Mobile-responsive design
- Visual connection status indicators

## Tech Stack

### Backend
- **Framework**: Express.js
- **Database**: PostgreSQL with Sequelize ORM
- **Real-time**: Socket.IO with session integration
- **Authentication**: Passport.js with local strategy
- **Session**: express-session with Sequelize store
- **Security**: CSRF protection, secure sessions

### Frontend
- **Templates**: EJS with layouts
- **UI Framework**: Bootstrap 5
- **WebSocket**: Socket.IO client with reconnection
- **JavaScript**: Vanilla JS with modular organization
- **CSS**: Custom responsive styles

### Development
- **Runtime**: Node.js (v14 or higher)
- **Package Manager**: npm
- **Development Server**: nodemon
- **Testing**: Jest
- **Version Control**: Git

## Prerequisites

- Node.js (v14 or higher)
- PostgreSQL (v13 or higher)
- npm (v6 or higher)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/kentrivia.git
   cd kentrivia
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Create a `.env` file in the root directory:
   ```env
   # Application
   NODE_ENV=development
   PORT=5001
   HOST=127.0.0.1
   SECRET_KEY=your-secret-key-here

   # Database
   DB_NAME=kentrivia
   DB_USER=postgres
   DB_PASS=your-password
   DB_HOST=localhost

   # Session
   SESSION_SECURE=false
   SESSION_HTTP_ONLY=true
   SESSION_MAX_AGE=86400000
   ```

4. Set up the database:
   ```bash
   # Create the database
   createdb kentrivia

   # Run migrations and seed data
   npm run setup-test-data
   ```

## Development

Start the development server:
```bash
npm run dev
```

The server will be running at `http://localhost:5001`

## Scripts

- `npm start`: Start the production server
- `npm run dev`: Start development server with hot reload
- `npm test`: Run test suite
- `npm run setup-test-data`: Initialize database with test data

## Project Structure

```
kentrivia/
├── src/                    # Source files
│   ├── config/            # Configuration files
│   ├── models/            # Sequelize models
│   ├── public/            # Static assets
│   │   ├── css/          # Stylesheets
│   │   ├── js/           # Client-side JavaScript
│   │   └── img/          # Images
│   ├── routes/           # Express routes
│   ├── views/            # EJS templates
│   │   ├── layouts/      # Layout templates
│   │   ├── auth/         # Authentication views
│   │   ├── game/         # Game views
│   │   └── main/         # Main views
│   └── server.js         # Application entry point
├── tests/                 # Test files
└── package.json          # Project metadata and dependencies
```

## Game Flow

1. **Host**:
   - Creates a game with questions
   - Gets a unique game PIN
   - Shares PIN with players
   - Controls game progression
   - Views real-time statistics

2. **Players**:
   - Join using game PIN
   - Enter lobby and wait
   - Answer questions in real-time
   - See immediate feedback
   - Track scores and rankings

## Scoring System

- Base points per question: 1,000
- Time bonus: Faster answers earn more points
- Streak multipliers:
  - 2 correct = 2x
  - 3 correct = 3x
  - 4+ correct = 4x

## WebSocket Events

### Client to Server
- `player_join`: Join a game room
- `game_started`: Start the game
- `submit_answer`: Submit an answer
- `request_leaderboard`: Request current standings

### Server to Client
- `room_participants_changed`: Player list update
- `game_started`: Game has begun
- `question_preparing`: Question is coming
- `question_started`: Question has started
- `answer_result`: Answer feedback
- `leaderboard_update`: New standings

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Testing

Run the test suite:
```bash
npm test
```

The tests cover:
- Model validations
- Route handlers
- WebSocket events
- Game logic
- Session management

## License

This project is licensed under the ISC License.

## Acknowledgments

- Bootstrap for the UI framework
- Socket.IO for real-time functionality
- All contributors and users of the application
