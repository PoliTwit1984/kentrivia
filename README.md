# KenTrivia

A real-time multiplayer trivia game built with Flask and Socket.IO.

## Current Status

The project is transitioning from Flask-SocketIO to FastAPI with WebSocket support for improved performance and better async handling. We have implemented new test infrastructure using pytest and FastAPI's test client.

## Project Structure

```
kentrivia/
├── app/
│   ├── api/        # API endpoints
│   ├── auth/       # Authentication
│   ├── game/       # Game logic and events
│   ├── main/       # Main routes
│   ├── routers/    # FastAPI routers
│   ├── static/     # Static files
│   └── templates/  # HTML templates
├── tests/          # Test suite
└── docs/          # Documentation
```

## Setup

1. Clone the repository
```bash
git clone https://github.com/yourusername/kentrivia.git
cd kentrivia
```

2. Create and activate virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up environment variables
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize database
```bash
flask db upgrade
```

6. Run development server
```bash
python run.py
```

## Testing

### Running Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_websocket.py -v
```

### Current Test Status
- Implemented WebSocket testing with pytest and FastAPI test client
- Added game flow testing with WebSocket connections
- See README-TEST.md for detailed testing documentation
- Check tasks.md for current development tasks

## Features

### Implemented
- User authentication
- Game creation
- Player joining
- Basic question flow
- WebSocket event handling
- Real-time game state updates

### In Progress
- WebSocket test infrastructure
- Event handling improvements
- Session management refinement

### Planned
- Score calculation
- Leaderboard
- Tournament mode

## Documentation

- README-TEST.md: Testing documentation and current issues
- diagram.md: System architecture and flow diagrams
- tasks.md: Development tasks and progress
- TEST_GUIDE.md: Testing guide and procedures

## Contributing

1. Check tasks.md for current priorities
2. Review README-TEST.md for known issues
3. Follow test-driven development practices
4. Submit pull requests with tests

## Development Guidelines

1. Run tests before making changes
2. Add tests for new features
3. Update documentation
4. Follow FastAPI and Flask best practices

## Known Issues

See README-TEST.md for current issues and debugging progress.

## License

MIT License - see LICENSE file for details.
