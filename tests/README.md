# KenTrivia Tests

This directory contains automated tests for KenTrivia functionality.

## Running Tests

1. Make sure you have all dependencies installed:
   ```bash
   pip install -r requirements.txt
   ```

2. Run a specific test:
   ```bash
   python -m unittest tests/test_game_questions.py
   ```

3. Run all tests:
   ```bash
   python -m unittest discover tests
   ```

## Test Files

- `test_game_questions.py`: Tests the game question flow, verifying that:
  - Questions are properly sent to players after game start
  - Question preparation events are received
  - Question started events are received with correct data
  - WebSocket connections are properly managed

## Test Structure

Each test file follows this structure:
1. Setup test environment and data
2. Execute test scenarios
3. Verify expected outcomes
4. Clean up test environment

## Writing New Tests

When adding new tests:
1. Create a new test file in the tests directory
2. Inherit from `unittest.TestCase`
3. Use the provided setup and teardown patterns
4. Follow the existing naming conventions
5. Include clear docstrings and comments
6. Test both success and failure cases
7. Clean up all resources in tearDown

## Test Coverage

The current test suite covers:
- WebSocket connection management
- Game flow events
- Question delivery
- Player-host interaction

Future tests should cover:
- Answer submission
- Score calculation
- Leaderboard updates
- Connection reliability
- Error handling
