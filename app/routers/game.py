from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models import Game, Player, Question
from app.schemas import GameCreate, Game as GameSchema, PlayerCreate, Question as QuestionSchema
from typing import List

router = APIRouter(
    prefix="/game",
    tags=["game"]
)

@router.post("/create", response_model=GameSchema)
def create_game(game: GameCreate, db: Session = Depends(get_db)):
    db_game = Game(
        title=game.title,
        host_id=game.host_id,
        pin=Game.generate_pin()
    )
    db.add(db_game)
    db.commit()
    db.refresh(db_game)
    return db_game

@router.get("/{pin}", response_model=GameSchema)
def get_game(pin: str, db: Session = Depends(get_db)):
    game = db.query(Game).filter(Game.pin == pin).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game

@router.post("/{pin}/join", response_model=dict)
def join_game(pin: str, player: PlayerCreate, db: Session = Depends(get_db)):
    game = db.query(Game).filter(Game.pin == pin).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if game.started_at:
        raise HTTPException(status_code=400, detail="Game already started")
    
    db_player = Player(
        nickname=player.nickname,
        game_id=game.id,
        score=0,
        current_streak=0,
        is_ready=False
    )
    db.add(db_player)
    db.commit()
    db.refresh(db_player)
    
    return {
        "player_id": db_player.id,
        "game_pin": game.pin
    }

@router.get("/{pin}/questions", response_model=List[QuestionSchema])
def get_game_questions(pin: str, db: Session = Depends(get_db)):
    game = db.query(Game).filter(Game.pin == pin).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    questions = db.query(Question).filter(Question.game_id == game.id).all()
    return questions

@router.post("/{pin}/ready")
def mark_player_ready(pin: str, player_id: int, db: Session = Depends(get_db)):
    player = db.query(Player).filter(
        Player.id == player_id,
        Player.game_id == db.query(Game.id).filter(Game.pin == pin).scalar_subquery()
    ).first()
    
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    player.is_ready = True
    db.commit()
    
    return {"status": "success"}
