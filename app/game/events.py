from flask import session, request
from flask_socketio import emit, join_room, leave_room, disconnect
from app import socketio, db
from app.models import Game, Player, Question, Answer
from datetime import datetime
import json
from collections import defaultdict
import time
from threading import Lock

# Track active connections and rooms
active_connections = {}  # sid -> {user_info}
room_participants = defaultdict(set)  # game_pin -> set of sids
connection_times = {}  # sid -> last_activity_timestamp
room_lock = Lock()

def update_connection_activity(sid):
    """Update the last activity timestamp for a connection"""
    connection_times[sid] = time.time()

def cleanup_stale_connections():
    """Remove stale connections and update room participants"""
    current_time = time.time()
    stale_threshold = 30  # seconds
    
    with room_lock:
        # Find stale connections
        stale_sids = [
            sid for sid, last_time in connection_times.items()
            if current_time - last_time > stale_threshold
        ]
        
        # Clean up stale connections
        for sid in stale_sids:
            if sid in active_connections:
                game_pin = active_connections[sid].get('game_pin')
                if game_pin and game_pin in room_participants:
                    room_participants[game_pin].discard(sid)
                    if not room_participants[game_pin]:
                        del room_participants[game_pin]
                del active_connections[sid]
            if sid in connection_times:
                del connection_times[sid]

def verify_room_presence():
    """Verify all room participants are still connected"""
    with room_lock:
        for game_pin, participants in room_participants.items():
            # Get currently connected participants
            connected_participants = {
                sid for sid in participants 
                if sid in active_connections
            }
            
            # Update room participants
            if connected_participants != participants:
                room_participants[game_pin] = connected_participants
                
                # Notify remaining participants about disconnected players
                if connected_participants:
                    connected_players = [
                        active_connections[sid].get('player_info')
                        for sid in connected_participants
                    ]
                    emit('room_participants_changed', {
                        'connected_players': connected_players
                    }, room=game_pin)

@socketio.on('connect')
def handle_connect():
    """Handle new socket connections"""
    sid = request.sid
    game_pin = session.get('game_pin')
    
    with room_lock:
        active_connections[sid] = {'connected_at': time.time()}
        update_connection_activity(sid)
        
        if game_pin:
            join_room(game_pin)
            room_participants[game_pin].add(sid)
            active_connections[sid]['game_pin'] = game_pin
            print(f"Client {sid} joined room: {game_pin}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle socket disconnections"""
    sid = request.sid
    
    with room_lock:
        if sid in active_connections:
            game_pin = active_connections[sid].get('game_pin')
            if game_pin:
                leave_room(game_pin)
                room_participants[game_pin].discard(sid)
                if not room_participants[game_pin]:
                    del room_participants[game_pin]
                print(f"Client {sid} left room: {game_pin}")
            del active_connections[sid]
        if sid in connection_times:
            del connection_times[sid]

@socketio.on('ping')
def handle_ping():
    """Handle heartbeat pings from clients"""
    update_connection_activity(request.sid)
    emit('pong')

@socketio.on('player_join')
def handle_player_join(data):
    sid = request.sid
    game = Game.query.filter_by(pin=data['pin']).first()
    if not game:
        return
    
    # Join the game room
    with room_lock:
        join_room(game.pin)
        session['game_pin'] = game.pin
        room_participants[game.pin].add(sid)
        
        # Get player from session
        player_id = session.get('player_id')
        if not player_id:
            print("No player_id in session")
            return
            
        player = Player.query.get(player_id)
        if not player or player.game_id != game.id:
            print("Player not found or doesn't match game")
            return
        
        # Update connection tracking
        active_connections[sid].update({
            'game_pin': game.pin,
            'player_info': {
                'id': player.id,
                'nickname': player.nickname,
                'score': player.score
            }
        })
        update_connection_activity(sid)
        
        print(f"Player {player.nickname} joined game {game.pin}")
        
        # Handle rejoin scenario
        is_rejoin = data.get('rejoin', False)
        if not is_rejoin:
            player.is_ready = True
            db.session.commit()
        
        # Get current room participants
        current_participants = [
            active_connections[p_sid].get('player_info')
            for p_sid in room_participants[game.pin]
            if p_sid in active_connections
        ]
        
        # Notify all clients about room participants
        emit('room_participants_changed', {
            'connected_players': current_participants
        }, room=game.pin)
        
        # Notify about the new/rejoined player
        emit('player_joined', {
            'player_id': player.id,
            'nickname': player.nickname,
            'score': player.score,
            'is_ready': player.is_ready,
            'is_rejoin': is_rejoin
        }, room=game.pin)
        
        if player.is_ready:
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
        
        # Start periodic cleanup of stale connections
        cleanup_stale_connections()

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
