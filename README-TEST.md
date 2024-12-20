# Testing Documentation

## Current Test Status

The test suite uses Jest and Supertest for API testing, along with Socket.IO client for WebSocket testing.

### Test Description

The test suite verifies:
1. Host can join a game
2. Player can join a game
3. Game can be started
4. Questions can be prepared and sent to players
5. Players can submit answers and receive results

### Current Setup

1. **WebSocket Testing**
   - Socket.IO client for WebSocket connections
   - Mock Socket.IO server for isolated testing
   - Event handling and room management tests

2. **API Testing**
   - Supertest for HTTP endpoint testing
   - Jest matchers for response validation
   - Database transaction rollback for test isolation

3. **Test Infrastructure**
   - Jest test runner
   - Test database setup and teardown
   - Automated fixture loading

### Running the Tests

```bash
# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch

# Run specific test file
npm test -- tests/websocket.test.js
```

### Test Dependencies

```json
{
  "devDependencies": {
    "jest": "^29.0.0",
    "supertest": "^6.0.0",
    "socket.io-client": "^4.0.0"
  }
}
```

### Test Structure

```
tests/
├── setup/              # Test setup and configuration
│   ├── jest.setup.js   # Jest configuration
│   └── db.setup.js     # Database setup
├── fixtures/           # Test data
│   └── games.json      # Sample game data
├── unit/               # Unit tests
│   ├── models/         # Model tests
│   └── utils/          # Utility function tests
└── integration/        # Integration tests
    ├── api/            # API endpoint tests
    └── websocket/      # WebSocket tests
```

### Writing Tests

Example test structure:

```javascript
describe('Game WebSocket', () => {
  let io;
  let clientSocket;
  
  beforeAll((done) => {
    // Setup Socket.IO server
    server.listen(0, () => {
      const port = server.address().port;
      clientSocket = io(`http://localhost:${port}`);
      clientSocket.on('connect', done);
    });
  });

  afterAll(() => {
    io.close();
    clientSocket.close();
  });

  test('should handle player join', (done) => {
    clientSocket.emit('player_join', { gameId: 'test', name: 'Player1' });
    clientSocket.on('player_joined', (data) => {
      expect(data.name).toBe('Player1');
      done();
    });
  });
});
```

### Best Practices

1. **Test Isolation**
   - Use beforeEach/afterEach for setup/cleanup
   - Reset database state between tests
   - Clean up WebSocket connections

2. **Async Testing**
   - Use async/await for cleaner test code
   - Handle promises properly
   - Set appropriate timeouts

3. **Mocking**
   - Mock external services
   - Use Jest mock functions
   - Stub database calls when needed

### Common Issues & Solutions

1. **WebSocket Connection Issues**
   - Ensure proper connection cleanup
   - Use appropriate timeouts
   - Handle disconnection events

2. **Database State**
   - Use transactions for isolation
   - Clear data between tests
   - Use separate test database

3. **Async Operations**
   - Wait for operations to complete
   - Handle promise rejections
   - Use Jest's done callback correctly

### Notes for Developers

1. Always run tests before pushing code
2. Maintain test database fixtures
3. Add tests for new features
4. Keep tests focused and isolated
5. Use meaningful test descriptions
