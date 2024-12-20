# KenTrivia Test Guide

This document provides step-by-step instructions for testing the functionality of KenTrivia. It covers setup, host features, player features, and various test scenarios.

## Prerequisites

1. Install the application following README.md instructions
2. Set up test data:
   ```bash
   npm run setup-test-data    # Creates test user and game with questions
   ```

## Test Environment Setup

1. Run the application:
   ```bash
   npm run dev
   ```
2. Open multiple browser windows/tabs for testing:
   - One for the host
   - 2-3 for players
   - Keep Developer Tools open (F12) to monitor WebSocket connections

## Test Scenarios

### 1. Authentication Testing

#### Host Account
1. Register new account:
   - Navigate to /auth/register
   - Test validation:
     - Try submitting empty form
     - Try password mismatch
     - Try existing username
   - Complete valid registration
2. Login testing:
   - Try invalid credentials
   - Login with test account:
     - Username: testuser
     - Password: password
   - Verify redirect to dashboard

#### Player Join
1. Test PIN entry:
   - Try invalid PIN
   - Try expired PIN
   - Enter valid PIN
2. Test nickname:
   - Try empty nickname
   - Try duplicate nickname
   - Enter valid nickname

### 2. Game Creation & Setup

1. Create new game:
   - Test form validation
   - Create game with manual questions
   - Create game with OpenTDB import
2. Edit existing game:
   - Modify title
   - Add/remove questions
   - Change question order
3. Test lobby management:
   - Verify PIN display
   - Monitor player join notifications
   - Check player ready status updates
   - Test start game button activation

### 3. Game Flow Testing

#### Host Perspective
1. Start game:
   - Verify all players receive start notification
   - Check question preparation screen
2. Question flow:
   - Verify synchronized question display
   - Monitor answer submissions
   - Check timer accuracy
   - View question results
3. Game progression:
   - Navigate through multiple questions
   - Check leaderboard updates
   - End game and view final results

#### Player Perspective
1. Join game:
   - Enter PIN and nickname
   - Wait in lobby
   - Mark as ready
2. Answer questions:
   - View preparation screen
   - See question display
   - Submit answers
   - View personal results
   - Check leaderboard position

### 4. Connection Reliability Testing

1. Test reconnection scenarios:
   - Temporarily disable network
   - Close and reopen browser tab
   - Switch between networks
2. Test late join:
   - Join ongoing game
   - Verify correct game state sync
   - Check score tracking
3. Monitor connection indicators:
   - Check status display
   - Verify heartbeat mechanism
   - Observe reconnection attempts

### 5. Edge Cases

1. Browser compatibility:
   - Test on Chrome, Firefox, Safari
   - Test on mobile devices
2. Network conditions:
   - Test with slow connection
   - Test with intermittent connection
   - Test with high latency
3. Concurrent users:
   - Test with 5+ simultaneous players
   - Monitor server performance
   - Check synchronization accuracy

### 6. Error Handling

1. Test invalid operations:
   - Submit answer after time expires
   - Submit multiple answers
   - Join non-existent game
2. Connection errors:
   - Force WebSocket disconnection
   - Test timeout handling
   - Verify error messages
3. State recovery:
   - Test browser refresh during game
   - Check game state persistence
   - Verify score preservation

## Test Checklist

### Host Features
- [ ] Account creation and login
- [ ] Game creation with manual questions
- [ ] Game creation with OpenTDB import
- [ ] Lobby management
- [ ] Player monitoring
- [ ] Question control
- [ ] Results viewing
- [ ] Game deletion

### Player Features
- [ ] PIN entry and nickname selection
- [ ] Lobby interaction
- [ ] Question answering
- [ ] Score tracking
- [ ] Leaderboard viewing
- [ ] Connection status monitoring
- [ ] Reconnection handling

### Technical Features
- [ ] WebSocket connection stability
- [ ] Question synchronization
- [ ] Timer accuracy
- [ ] State preservation
- [ ] Error handling
- [ ] Late join functionality
- [ ] Browser compatibility

## Reporting Issues

When reporting issues, include:
1. Test scenario being performed
2. Expected behavior
3. Actual behavior
4. Browser console logs
5. Network request logs
6. Steps to reproduce
7. Screenshots (if applicable)

## Success Criteria

A successful test should demonstrate:
1. Stable WebSocket connections
2. Accurate game state synchronization
3. Proper score calculation
4. Reliable player reconnection
5. Consistent question timing
6. Clear error messaging
7. Smooth game progression
