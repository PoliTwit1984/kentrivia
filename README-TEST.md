# Testing Documentation

## Current Test Status

We are transitioning from Flask-SocketIO to FastAPI WebSocket testing. The new test infrastructure uses pytest and FastAPI's test client for more reliable WebSocket testing.

### Test Description

The test `test_websocket_game_flow` in `tests/test_websocket.py` verifies:
1. Host can join a game
2. Player can join a game
3. Game can be started
4. Questions can be prepared and sent to players
5. Players can submit answers and receive results

### Current Issues

1. **WebSocket Connection Issues**
   - Tests occasionally hang during WebSocket connections
   - Connection errors in test environment
   - Need to improve connection handling and timeouts

2. **Event Handling**
   - Player join event not being properly handled
   - Event acknowledgments not implemented
   - Room broadcast behavior needs improvement

### Debugging Progress

1. **FastAPI Migration**
   - Implemented FastAPI WebSocket endpoints
   - Created new test client for WebSocket testing
   - Added async/await support for WebSocket operations

2. **Test Infrastructure**
   - Added pytest-asyncio support
   - Implemented WebSocket test client class
   - Added database fixtures for test data

3. **Event Handling**
   - Migrated event handlers to FastAPI
   - Added more detailed logging
   - Improved error handling

### Next Steps

1. **Test Stability**
   - Add timeouts to WebSocket operations
   - Improve error handling in tests
   - Add connection retry logic

2. **Event System**
   - Implement event acknowledgments
   - Add event validation
   - Improve room management

3. **Test Coverage**
   - Add more test cases
   - Implement integration tests
   - Add error scenario tests

### Running the Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run WebSocket tests
python -m pytest tests/test_websocket.py -v

# Run with detailed logging
python -m pytest tests/test_websocket.py -v --log-cli-level=DEBUG
```

### Test Dependencies

- pytest
- pytest-asyncio
- FastAPI
- SQLAlchemy
- httpx

### Notes for Next Developer

1. The main issue is WebSocket connection stability in tests
2. Event handling needs to be made more robust
3. Consider adding retry mechanisms for flaky connections
4. May need to review FastAPI WebSocket documentation for best practices
5. Consider implementing proper WebSocket connection pooling
