# KenTrivia

A real-time multiplayer trivia game platform inspired by Kahoot!, built with Flask and WebSocket. Host engaging trivia games with custom questions or import from the Open Trivia Database.

## Features

- **User Authentication & Management**
  - Host account creation and login
  - Quick player join with game PIN
  - No account required for players

- **Game Session Management**
  - Create custom trivia games
  - Unique PIN generation for each game
  - Real-time player joining
  - Player ready status tracking
  - Flexible game start control
  - Late-join support for ongoing games
  - Reliable WebSocket connections with auto-reconnect
  - Connection status indicators

- **Question Management**
  - Create custom questions
  - Import questions from Open Trivia Database (OpenTDB)
  - Multiple choice format
  - Configurable time limits and points

- **Real-Time Gameplay**
  - Synchronized question display
  - Time-based scoring system
  - Answer streak bonuses
  - Live leaderboard updates
  - Reliable question delivery
  - Connection status monitoring
  - Automatic reconnection handling
  - Join ongoing games at any time

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/kentrivia.git
   cd kentrivia
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables in `.env`:
   ```
   SECRET_KEY=your-secret-key
   DATABASE_URL=sqlite:///kentrivia.db
   FLASK_APP=run.py
   FLASK_ENV=development
   ```

5. Initialize the database:
   ```bash
   flask db upgrade
   ```

6. Run the application:
   ```bash
   python run.py
   ```

The application will be available at `http://127.0.0.1:5001`.

## Usage

### For Hosts

1. Create an account and log in
2. Create a new game from your dashboard
3. Add questions manually or import from OpenTDB
4. Share the game PIN with players
5. Start the game when ready
6. Control the game flow and monitor progress
7. Monitor player connections and game status

### For Players

1. Go to the home page
2. Enter the game PIN and choose a nickname
3. Join the game at any time - before or during gameplay
4. Answer questions quickly for more points
5. Keep your streak going for bonus points
6. Check the leaderboard between questions
7. Monitor your connection status

## Project Structure

```
kentrivia/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── auth/
│   ├── game/
│   ├── main/
│   ├── static/
│   └── templates/
├── instance/
├── venv/
├── .env
├── config.py
├── requirements.txt
└── run.py
```

## Technology Stack

- **Backend**: Flask, Python
- **Database**: SQLAlchemy with SQLite
- **Real-time Communication**: Flask-SocketIO with reliable connection handling
- **Frontend**: Bootstrap 5, JavaScript
- **External APIs**: Open Trivia Database (OpenTDB)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

See [tasks.md](tasks.md) for a list of planned features and improvements.

## Troubleshooting

### Common Issues

1. **Questions not displaying**: If players don't see questions:
   - Ensure you have a stable internet connection
   - Check the connection status indicator
   - Try refreshing the page
   - You can rejoin at any time during the game

2. **Connection Issues**:
   - Check your internet connection
   - The system will attempt to reconnect automatically
   - Monitor the connection status indicator
   - Refresh the page if connection issues persist

3. **Game Start Issues**:
   - Host can start the game at any time
   - Players can join before or during gameplay
   - Check that host has proper permissions
   - Verify stable connection for all participants

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Inspired by Kahoot!
- Questions provided by Open Trivia Database
- Built with Flask and Flask extensions
