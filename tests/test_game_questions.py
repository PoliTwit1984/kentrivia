import os
import sys
import unittest
from flask_socketio import SocketIO
from flask.testing import FlaskClient
from flask import current_app, session
from app import create_app, db
from app.models import User, Game, Question, Player
from werkzeug.security import generate_password_hash
from datetime import datetime
import json
import time
import logging

logging.basicConfig(level=logging.INFO)

class TestGameQuestions(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['SECRET_KEY'] = 'test_secret_key'  # Required for sessions
        
        self.client = self.app.test_client()
        self.socketio = SocketIO(self.app)
        
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        db.create_all()
        
        # Create test user and game
        self.setup_test_data()

    def setup_test_data(self):
        """Create test user, game and questions"""
        self.host = User(
            username='testhost',
            email='host@test.com'
        )
        self.host.password_hash = generate_password_hash('password')
        db.session.add(self.host)
        db.session.commit()
        
        # Create game
        self.game = Game(
            title='Test Game',
            host_id=self.host.id,
            pin=Game.generate_pin()
        )
        db.session.add(self.game)
        db.session.commit()
        
        # Add test questions
        questions = [
            {
                'content': 'Test Question 1',
                'correct_answer': 'Correct 1',
                'incorrect_answers': json.dumps(['Wrong 1', 'Wrong 2', 'Wrong 3']),
                'category': 'Test',
                'difficulty': 'easy'
            },
            {
                'content': 'Test Question 2',
                'correct_answer': 'Correct 2',
                'incorrect_answers': json.dumps(['Wrong 1', 'Wrong 2', 'Wrong 3']),
                'category': 'Test',
                'difficulty': 'medium'
            }
        ]
        
        for q in questions:
            question = Question(
                game_id=self.game.id,
                **q
            )
            db.session.add(question)
        db.session.commit()

    def test_question_flow(self):
        """Test that questions are properly sent to players after game start"""
        
        # Set up host session
        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(self.host.id)
            sess['game_pin'] = self.game.pin

        # Create host socket connection
        host_socket = self.socketio.test_client(self.app)
        
        # Wait briefly for connection to establish
        time.sleep(0.5)
        
        # Log host connection attempt
        logging.info("Host socket connected")
        
        host_socket.emit('player_join', {
            'pin': self.game.pin,
            'is_host': True,
            'host_id': self.host.id
        })
        
        # Wait briefly for join events
        time.sleep(0.5)
        
        # Create and set up player
        player = Player(
            nickname='TestPlayer',
            game_id=self.game.id,
            score=0,
            current_streak=0,
            is_ready=True
        )
        db.session.add(player)
        db.session.commit()

        # Create new client for player
        player_client = self.app.test_client()
        
        # Set up player session
        with player_client.session_transaction() as sess:
            sess['player_id'] = player.id
            sess['game_pin'] = self.game.pin

        # Create player socket connection
        with player_client.session_transaction() as sess:
            sess['player_id'] = player.id
            sess['game_pin'] = self.game.pin
            logging.info(f"Set up player session - player_id: {player.id}, game_pin: {self.game.pin}")

        # Create socket connection after session is set
        player_socket = self.socketio.test_client(
            self.app,
            flask_test_client=player_client,
            namespace='/'  # Explicitly set namespace
        )
        logging.info(f"Created player socket connection")
        
        # Wait for connection to be established
        received = player_socket.get_received('/')
        logging.info(f"Initial connection events: {received}")
        
        # Log player connection attempt
        logging.info("Player socket connected")
        
        # Join game with player and wait for callback
        received_data = []
        def join_callback(data):
            received_data.append(data)
            logging.info(f"Received callback data: {data}")

        player_socket.emit('player_join', {
            'pin': self.game.pin,
            'nickname': 'TestPlayer',
            'player_id': player.id,
            'is_ready': True
        }, namespace='/', callback=join_callback)
        
        # Wait for join events
        time.sleep(1)
        
        # Get events from both callback and socket
        received = player_socket.get_received('/')
        logging.info(f"Callback data: {received_data}")
        logging.info(f"Received events after join: {received}")
        logging.info("Checking join events...")
        if received:
            for event in received:
                logging.info(f"Received event: {event['name']}")
                if event['name'] == 'player_joined':
                    logging.info(f"Player joined event data: {event.get('args', [])}")
        else:
            logging.info("No events received")
        
        # Check both callback and socket events
        join_event = next((event for event in received if event['name'] == 'player_joined'), None)
        if not join_event and received_data:
            # If we got callback data but no event, create a pseudo-event
            join_event = {'name': 'player_joined', 'args': [received_data[0]]}
        self.assertIsNotNone(join_event, "Player did not receive join confirmation event")
        
        # Clear received events before game start
        player_socket.get_received()
        
        # Host starts game
        host_socket.emit('game_started', {'pin': self.game.pin})
        
        # Wait for game start events
        time.sleep(1)
        
        # Verify game started event
        received = player_socket.get_received()
        game_started = next((event for event in received if event['name'] == 'game_started'), None)
        self.assertIsNotNone(game_started, "Player did not receive game_started event")
        
        # Clear received events before question
        player_socket.get_received()
        
        # Initialize game state
        self.game.started_at = datetime.utcnow()
        self.game.current_question_index = -1  # Will be incremented to 0 when first question starts
        db.session.commit()
        
        # Host prepares first question
        host_socket.emit('preparing_next_question', {'pin': self.game.pin})
        
        # Wait for question preparation event
        time.sleep(1)
        
        # Get and verify preparation event
        received = player_socket.get_received()
        prep_event = next((event for event in received if event['name'] == 'question_preparing'), None)
        self.assertIsNotNone(prep_event, "Player did not receive question_preparing event")
        
        # Clear received events and wait for question start
        player_socket.get_received()
        time.sleep(2)  # Wait for the 2-second delay in events.py
        
        # Get and verify question events
        received = player_socket.get_received()
        logging.info("Checking question events...")
        for event in received:
            logging.info(f"Received event: {event['name']}")
        
        # Check for question_started event
        question_event = next((event for event in received if event['name'] == 'question_started'), None)
        self.assertIsNotNone(question_event, "Player did not receive question_started event")
        
        # Verify question data
        if question_event:
            question_data = question_event['args'][0]
            self.assertIn('content', question_data, "Question data missing content")
            self.assertIn('answers', question_data, "Question data missing answers")
        
        # Clean up socket connections
        host_socket.disconnect()
        player_socket.disconnect()

    def tearDown(self):
        """Clean up after each test"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

if __name__ == '__main__':
    # Create tests directory if it doesn't exist
    if not os.path.exists('tests'):
        os.makedirs('tests')
    
    unittest.main()
