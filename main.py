from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Dict
import json
from datetime import datetime
import asyncio
from collections import defaultdict

from app.models_fastapi import Game, Player, Question, Answer, User
from app.database import SessionLocal, engine
from app.schemas import GameCreate, PlayerCreate, QuestionCreate
from app.dependencies import get_db

app = FastAPI(title="KenTrivia")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Dict[str, WebSocket]] = defaultdict(dict)
        self.game_pins: Dict[str, str] = {}  # socket_id -> game_pin

    async def connect(self, websocket: WebSocket, game_pin: str, client_id: str):
        await websocket.accept()
        self.active_connections[game_pin][client_id] = websocket
        self.game_pins[client_id] = game_pin

    def disconnect(self, client_id: str):
        if client_id in self.game_pins:
            game_pin = self.game_pins[client_id]
            if game_pin in self.active_connections:
                self.active_connections[game_pin].pop(client_id, None)
                if not self.active_connections[game_pin]:
                    self.active_connections.pop(game_pin)
            self.game_pins.pop(client_id)

    async def broadcast_to_game(self, game_pin: str, message: dict):
        if game_pin in self.active_connections:
            for connection in self.active_connections[game_pin].values():
                await connection.send_json(message)

    async def send_personal_message(self, client_id: str, message: dict):
        game_pin = self.game_pins.get(client_id)
        if game_pin:
            connection = self.active_connections[game_pin].get(client_id)
            if connection:
                await connection.send_json(message)

manager = ConnectionManager()

# WebSocket endpoint for game events
@app.websocket("/ws/game/{game_pin}/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    game_pin: str,
    client_id: str,
    db: Session = Depends(get_db)
):
    await manager.connect(websocket, game_pin, client_id)
    try:
        while True:
            data = await websocket.receive_json()
            event = data.get("event")
            
            if event == "player_join":
                # Handle player join
                player_id = data.get("player_id")
                player = db.query(Player).get(player_id)
                if player:
                    # Send join confirmation
                    await manager.send_personal_message(
                        client_id,
                        {
                            "event": "player_joined",
                            "data": {
                                "player_id": player.id,
                                "nickname": player.nickname,
                                "score": player.score,
                                "is_ready": player.is_ready
                            }
                        }
                    )
                    # Broadcast to other players
                    await manager.broadcast_to_game(
                        game_pin,
                        {
                            "event": "room_participants_changed",
                            "data": {
                                "player_id": player.id,
                                "nickname": player.nickname,
                                "score": player.score
                            }
                        }
                    )
            
            elif event == "game_started":
                game = db.query(Game).filter(Game.pin == game_pin).first()
                if game:
                    game.started_at = datetime.utcnow()
                    game.current_question_index = -1
                    db.commit()
                    
                    await manager.broadcast_to_game(
                        game_pin,
                        {
                            "event": "game_started",
                            "data": {
                                "started_at": game.started_at.isoformat(),
                                "total_questions": db.query(Question).filter(Question.game_id == game.id).count(),
                                "current_question_index": game.current_question_index
                            }
                        }
                    )
            
            elif event == "preparing_next_question":
                game = db.query(Game).filter(Game.pin == game_pin).first()
                if game:
                    questions = db.query(Question).filter(Question.game_id == game.id).all()
                    game.current_question_index += 1
                    
                    if game.current_question_index < len(questions):
                        question = questions[game.current_question_index]
                        incorrect_answers = json.loads(question.incorrect_answers)
                        
                        question_data = {
                            "id": question.id,
                            "content": question.content,
                            "answers": [question.correct_answer] + incorrect_answers,
                            "time_limit": question.time_limit or 20,
                            "points": question.points or 1000
                        }
                        
                        await manager.broadcast_to_game(
                            game_pin,
                            {
                                "event": "question_preparing",
                                "data": {
                                    "question": question_data,
                                    "total_questions": len(questions),
                                    "current_index": game.current_question_index
                                }
                            }
                        )
                        
                        # Wait before sending question_started
                        await asyncio.sleep(2)
                        
                        await manager.broadcast_to_game(
                            game_pin,
                            {
                                "event": "question_started",
                                "data": question_data
                            }
                        )
            
            elif event == "submit_answer":
                # Handle answer submission
                player_id = data.get("player_id")
                question_id = data.get("question_id")
                answer_text = data.get("answer")
                response_time = data.get("response_time")
                
                player = db.query(Player).get(player_id)
                question = db.query(Question).get(question_id)
                
                if player and question:
                    is_correct = answer_text == question.correct_answer
                    points_earned = int(question.points * ((question.time_limit - response_time) / question.time_limit)) if is_correct else 0
                    
                    answer = Answer(
                        player_id=player_id,
                        question_id=question_id,
                        answer_text=answer_text,
                        is_correct=is_correct,
                        response_time=response_time,
                        points_awarded=points_earned
                    )
                    db.add(answer)
                    
                    if is_correct:
                        player.score += points_earned
                        player.current_streak += 1
                    else:
                        player.current_streak = 0
                    
                    db.commit()
                    
                    # Send personal result
                    await manager.send_personal_message(
                        client_id,
                        {
                            "event": "answer_result",
                            "data": {
                                "is_correct": is_correct,
                                "points_awarded": points_earned,
                                "correct_answer": question.correct_answer
                            }
                        }
                    )
                    
                    # Broadcast answer submission
                    await manager.broadcast_to_game(
                        game_pin,
                        {
                            "event": "answer_submitted",
                            "data": {
                                "player_id": player.id,
                                "nickname": player.nickname,
                                "is_correct": is_correct,
                                "points_awarded": points_earned,
                                "new_score": player.score,
                                "new_streak": player.current_streak
                            }
                        }
                    )

    except WebSocketDisconnect:
        manager.disconnect(client_id)
        await manager.broadcast_to_game(
            game_pin,
            {
                "event": "client_disconnected",
                "client_id": client_id
            }
        )

# Include routers for REST endpoints
from app.routers import auth_router, game_router, main_router
app.include_router(auth_router)
app.include_router(game_router)
app.include_router(main_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
