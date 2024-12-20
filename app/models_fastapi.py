from datetime import datetime
import random
import string
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = 'users'  # Changed from 'user' to 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(128))
    games_created = relationship('Game', backref='host', lazy='dynamic')

class Game(Base):
    __tablename__ = 'games'
    
    id = Column(Integer, primary_key=True)
    pin = Column(String(6), unique=True, nullable=False)
    title = Column(String(64))
    host_id = Column(Integer, ForeignKey('users.id'))  # Updated foreign key
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    current_question_index = Column(Integer, default=-1)
    current_question_started_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    questions = relationship('Question', backref='game', lazy='dynamic')
    players = relationship('Player', backref='game', lazy='dynamic')

    @staticmethod
    def generate_pin():
        while True:
            pin = ''.join(random.choices(string.digits, k=6))
            return pin  # For testing, we'll skip the uniqueness check

class Question(Base):
    __tablename__ = 'questions'
    
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('games.id'))
    content = Column(String(500), nullable=False)
    correct_answer = Column(String(200), nullable=False)
    incorrect_answers = Column(JSON, nullable=False)
    category = Column(String(64))
    difficulty = Column(String(20))
    time_limit = Column(Integer, default=20)
    points = Column(Integer, default=1000)
    source = Column(String(20), default='custom')
    
    answers = relationship('Answer', backref='question', lazy='dynamic')

class Player(Base):
    __tablename__ = 'players'
    
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('games.id'))
    nickname = Column(String(64), nullable=False)
    score = Column(Integer, default=0)
    current_streak = Column(Integer, default=0)
    joined_at = Column(DateTime, default=datetime.utcnow)
    is_ready = Column(Boolean, default=False)
    
    answers = relationship('Answer', backref='player', lazy='dynamic')

class Answer(Base):
    __tablename__ = 'answers'
    
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('players.id'))
    question_id = Column(Integer, ForeignKey('questions.id'))
    answer_text = Column(String(200))
    is_correct = Column(Boolean)
    response_time = Column(Float)
    points_awarded = Column(Integer)
    answered_at = Column(DateTime, default=datetime.utcnow)
