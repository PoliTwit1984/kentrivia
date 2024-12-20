import pytest
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
import json
from datetime import datetime

from main import app
from app.models_fastapi import Game, Player, Question, User, Answer
from app.database import SessionLocal, Base, engine
from sqlalchemy.orm import Session

@pytest.fixture(autouse=True)
def setup_db():
    # Drop all tables first to ensure clean state
    Base.metadata.drop_all(bind=engine)
    # Create all tables
    Base.metadata.create_all(bind=engine)
    yield
    # Drop all tables after tests
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def test_data(db: Session):
    # Create test user
    user = User(
        username="testhost",
        email="host@test.com",
        password_hash="hashed_password"
    )
    db.add(user)
    db.flush()

    # Create test game
    game = Game(
        title="Test Game",
        host_id=user.id,
        pin="123456"
    )
    db.add(game)
    db.flush()

    # Create test player
    player = Player(
        nickname="TestPlayer",
        game_id=game.id,
        score=0,
        current_streak=0,
        is_ready=True
    )
    db.add(player)
    db.flush()

    # Create test questions
    questions = [
        Question(
            game_id=game.id,
            content="Test Question 1",
            correct_answer="Correct 1",
            incorrect_answers=json.dumps(["Wrong 1", "Wrong 2", "Wrong 3"]),
            category="Test",
            difficulty="easy"
        ),
        Question(
            game_id=game.id,
            content="Test Question 2",
            correct_answer="Correct 2",
            incorrect_answers=json.dumps(["Wrong 1", "Wrong 2", "Wrong 3"]),
            category="Test",
            difficulty="medium"
        )
    ]
    for q in questions:
        db.add(q)
    
    db.commit()
    
    return {
        "user": user,
        "game": game,
        "player": player,
        "questions": questions
    }

@pytest.fixture
def client():
    return TestClient(app)

def test_websocket_game_flow(client: TestClient, test_data, db: Session):
    """Test the complete game flow through WebSocket"""
    # Create WebSocket connections for host and player
    with client.websocket_connect(
        f"/ws/game/{test_data['game'].pin}/host_{test_data['user'].id}"
    ) as host_ws:
        with client.websocket_connect(
            f"/ws/game/{test_data['game'].pin}/player_{test_data['player'].id}"
        ) as player_ws:
            # Test player join
            player_ws.send_json({
                "event": "player_join",
                "data": {
                    "pin": test_data['game'].pin,
                    "player_id": test_data['player'].id,
                    "nickname": "TestPlayer",
                    "is_ready": True
                }
            })

            # Verify player_joined event
            response = player_ws.receive_json()
            assert response["event"] == "player_joined"
            assert response["data"]["player_id"] == test_data['player'].id
            assert response["data"]["nickname"] == "TestPlayer"

            # Test game start
            host_ws.send_json({
                "event": "game_started",
                "data": {
                    "pin": test_data['game'].pin
                }
            })

            # Verify game_started event
            response = player_ws.receive_json()
            assert response["event"] == "game_started"
            assert "started_at" in response["data"]
            assert response["data"]["current_question_index"] == -1

            # Test question preparation
            host_ws.send_json({
                "event": "preparing_next_question",
                "data": {
                    "pin": test_data['game'].pin
                }
            })

            # Verify question_preparing event
            response = player_ws.receive_json()
            assert response["event"] == "question_preparing"
            assert "question" in response["data"]
            assert "total_questions" in response["data"]
            assert "current_index" in response["data"]

            # Wait for question_started event
            response = player_ws.receive_json()
            assert response["event"] == "question_started"
            assert "id" in response["data"]
            assert "content" in response["data"]
            assert "answers" in response["data"]

            # Test answer submission
            player_ws.send_json({
                "event": "submit_answer",
                "data": {
                    "player_id": test_data['player'].id,
                    "question_id": test_data['questions'][0].id,
                    "answer": "Correct 1",
                    "response_time": 5.0
                }
            })

            # Verify answer_result event
            response = player_ws.receive_json()
            assert response["event"] == "answer_result"
            assert response["data"]["is_correct"] is True
            assert "points_awarded" in response["data"]
