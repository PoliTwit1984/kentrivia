from flask import session
from flask_socketio import emit, join_room, leave_room
from app import socketio, db
from app.models import Game, Player, Question, Answer
from datetime import datetime
import json

@socketio.on('connect')
def handle_connect():
    game_pin = session.get('game_pin')
    if game_pin:
        join_room(game_pin)
        print(f"Client joined room: {game_pin}")

@socketio.on('disconnect')
def handle_disconnect():
    game_pin = session.get('game_pin')
    if game_pin:
        leave_room(game_pin)
        print(f"Client left room: {game_pin}")

@socketio.on('player_join')
def handle_player_join(data):
    game = Game.query.filter_by(pin=data['pin']).first()
    if not game:
        return
    
    # Join the game room
    join_room(game.pin)
    session['game_pin'] = game.pin
    print(f"Player joined game room: {game.pin}")
    
    # Get player from session
    player_id = session.get('player_id')
    if not player_id:
        print("No player_id in session")
        return
        
    player = Player.query.get(player_id)
    if not player or player.game_id != game.id:
        print("Player not found or doesn't match game")
        return
    
    print(f"Player {player.nickname} joined game {game.pin}")
    
    # Mark player as ready
    player.is_ready = True
    db.session.commit()
    
    # Notify all clients in the game room about the new player
    emit('player_joined', {
        'player_id': player.id,
        'nickname': player.nickname,
        'score': player.score,
        'is_ready': True
    }, room=game.pin)
    
    # Also emit player_ready event
    emit('player_ready', {
        'player_id': player.id,
        'nickname': player.nickname
    }, room=game.pin)
    
    # Check if all players are ready
    all_players = Player.query.filter_by(game_id=game.id).all()
    ready_players = [p for p in all_players if p.is_ready]
    if len(ready_players) == len(all_players):
        print(f"All players ready in game {game.pin}")
        emit('all_players_ready', room=game.pin)

@socketio.on('game_started')
def handle_game_started(data=None):
    game_pin = session.get('game_pin')
    if not game_pin:
        return
    
    print(f"Broadcasting game_started to room: {game_pin}")
    # Emit to specific game room without broadcast
    emit('game_started', room=game_pin)

@socketio.on('submit_answer')
def handle_submit_answer(data):
    try:
        player = Player.query.get(session.get('player_id'))
        if not player:
            print("Player not found")
            return
        
        question = Question.query.get(data['question_id'])
        if not question or question.game_id != player.game_id:
            print("Question not found or doesn't match game")
            return
        
        # Check if answer already submitted
        existing_answer = Answer.query.filter_by(
            player_id=player.id,
            question_id=question.id
        ).first()
        
        if existing_answer:
            print("Answer already submitted")
            return
        
        # Calculate points based on response time
        response_time = data['response_time']  # Time taken to answer in seconds
        max_time = question.time_limit or 20
        time_factor = max(0, (max_time - response_time) / max_time)
        points_earned = int(question.points * time_factor)
        
        # Create answer record
        is_correct = data['answer'] == question.correct_answer
        answer = Answer(
            player_id=player.id,
            question_id=question.id,
            answer_text=data['answer'],
            is_correct=is_correct,
            response_time=response_time,
            points_awarded=points_earned if is_correct else 0
        )
        db.session.add(answer)
        
        # Update player score and streak
        if is_correct:
            player.current_streak += 1
            player.score += points_earned
        else:
            player.current_streak = 0
        
        db.session.commit()
        print(f"Answer processed - Correct: {is_correct}, Points: {points_earned}")
        
        # Notify all clients about the answer in the specific game room
        emit('answer_submitted', {
            'player_id': player.id,
            'nickname': player.nickname,
            'is_correct': is_correct,
            'points_awarded': points_earned if is_correct else 0,
            'new_score': player.score,
            'new_streak': player.current_streak
        }, room=player.game.pin)
        
        # Send individual result to the player
        emit('answer_result', {
            'is_correct': is_correct,
            'correct_answer': question.correct_answer,
            'points_awarded': points_earned if is_correct else 0,
            'new_score': player.score,
            'new_streak': player.current_streak
        })
        
    except Exception as e:
        print(f"Error processing answer: {str(e)}")
        db.session.rollback()

@socketio.on('end_question')
def handle_end_question(data):
    game = Game.query.filter_by(pin=data['pin']).first()
    if not game:
        return
    
    question = Question.query.get(data['question_id'])
    if not question or question.game_id != game.id:
        return
    
    # Get all answers for this question
    answers = Answer.query.filter_by(question_id=question.id).all()
    answer_data = [{
        'player_id': answer.player_id,
        'nickname': answer.player.nickname,
        'is_correct': answer.is_correct,
        'points_awarded': answer.points_awarded,
        'response_time': answer.response_time
    } for answer in answers]
    
    # Send results to all players in the specific game room
    emit('question_ended', {
        'question_id': question.id,
        'correct_answer': question.correct_answer,
        'answers': answer_data
    }, room=game.pin)

@socketio.on('request_leaderboard')
def handle_leaderboard_request(data):
    game = Game.query.filter_by(pin=data['pin']).first()
    if not game:
        return
    
    # Get all players sorted by score
    players = Player.query.filter_by(game_id=game.id)\
        .order_by(Player.score.desc())\
        .all()
    
    leaderboard_data = [{
        'player_id': player.id,
        'nickname': player.nickname,
        'score': player.score,
        'streak': player.current_streak
    } for player in players]
    
    # Send leaderboard to the specific game room
    emit('leaderboard_update', {
        'leaderboard': leaderboard_data
    }, room=game.pin)
