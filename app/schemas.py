from pydantic import BaseModel, EmailStr, constr
from typing import List, Optional
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

# Game schemas
class GameBase(BaseModel):
    title: str

class GameCreate(GameBase):
    host_id: int

class Game(GameBase):
    id: int
    pin: str
    host_id: int
    started_at: Optional[datetime]
    current_question_index: Optional[int]
    current_question_started_at: Optional[datetime]

    class Config:
        from_attributes = True

# Player schemas
class PlayerBase(BaseModel):
    nickname: str
    game_id: int

class PlayerCreate(PlayerBase):
    pass

class Player(PlayerBase):
    id: int
    score: int = 0
    current_streak: int = 0
    is_ready: bool = False

    class Config:
        from_attributes = True

# Question schemas
class QuestionBase(BaseModel):
    content: str
    correct_answer: str
    incorrect_answers: str  # JSON string of incorrect answers
    category: str
    difficulty: str
    game_id: int

class QuestionCreate(QuestionBase):
    pass

class Question(QuestionBase):
    id: int
    time_limit: Optional[int] = 20
    points: Optional[int] = 1000

    class Config:
        from_attributes = True

# Answer schemas
class AnswerBase(BaseModel):
    player_id: int
    question_id: int
    answer_text: str
    response_time: float

class AnswerCreate(AnswerBase):
    pass

class Answer(AnswerBase):
    id: int
    is_correct: bool
    points_awarded: int

    class Config:
        from_attributes = True

# WebSocket event schemas
class WebSocketMessage(BaseModel):
    event: str
    data: dict

class PlayerJoinEvent(BaseModel):
    pin: str
    player_id: int
    nickname: str
    is_ready: bool = True
    is_host: bool = False
    host_id: Optional[int] = None

class GameStartEvent(BaseModel):
    pin: str

class QuestionEvent(BaseModel):
    pin: str
    question_id: Optional[int] = None

class AnswerSubmitEvent(BaseModel):
    player_id: int
    question_id: int
    answer: str
    response_time: float
