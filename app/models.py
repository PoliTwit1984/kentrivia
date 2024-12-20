from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager
import random
import string

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    games_created = db.relationship('Game', backref='host', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pin = db.Column(db.String(6), unique=True, nullable=False)
    title = db.Column(db.String(64))
    host_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    ended_at = db.Column(db.DateTime)
    current_question_index = db.Column(db.Integer, default=-1)
    current_question_started_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    questions = db.relationship('Question', backref='game', lazy='dynamic')
    players = db.relationship('Player', backref='game', lazy='dynamic')

    @staticmethod
    def generate_pin():
        while True:
            pin = ''.join(random.choices(string.digits, k=6))
            if not Game.query.filter_by(pin=pin).first():
                return pin

    def start_game(self):
        self.started_at = datetime.utcnow()
        self.current_question_index = 0
        db.session.commit()

    def end_game(self):
        self.ended_at = datetime.utcnow()
        self.is_active = False
        db.session.commit()

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
    content = db.Column(db.String(500), nullable=False)
    correct_answer = db.Column(db.String(200), nullable=False)
    incorrect_answers = db.Column(db.JSON, nullable=False)  # List of wrong answers
    category = db.Column(db.String(64))
    difficulty = db.Column(db.String(20))
    time_limit = db.Column(db.Integer, default=20)
    points = db.Column(db.Integer, default=1000)
    source = db.Column(db.String(20), default='custom')  # 'custom' or 'opentdb'
    
    answers = db.relationship('Answer', backref='question', lazy='dynamic')

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
    nickname = db.Column(db.String(64), nullable=False)
    score = db.Column(db.Integer, default=0)
    current_streak = db.Column(db.Integer, default=0)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_ready = db.Column(db.Boolean, default=False)  # New field to track ready status
    
    answers = db.relationship('Answer', backref='player', lazy='dynamic')

    def add_points(self, points, correct=True):
        if correct:
            self.current_streak += 1
            streak_bonus = min(self.current_streak * 0.1, 0.5)  # Max 50% bonus
            self.score += int(points * (1 + streak_bonus))
        else:
            self.current_streak = 0
        db.session.commit()

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    answer_text = db.Column(db.String(200))
    is_correct = db.Column(db.Boolean)
    response_time = db.Column(db.Float)  # Time taken to answer in seconds
    points_awarded = db.Column(db.Integer)
    answered_at = db.Column(db.DateTime, default=datetime.utcnow)
