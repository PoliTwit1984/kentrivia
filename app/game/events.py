from flask import session, request, url_for, current_app
from flask_socketio import emit, join_room, leave_room, disconnect
from app import socketio, db
from app.models import Game, Player, Question, Answer, User
from datetime import datetime
import json
from collections import defaultdict
from threading import Lock
import time as time_module

# Track active connections and rooms
active_connections = {}  # sid -> {user_info}
room_participants = defaultdict(set)  # game_pin -> set of sids
connection_times = {}  # sid -> last_activity_timestamp
room_lock = Lock()

def update_connection_activity(sid):
    """Update the last activity timestamp for a connection"""
    connection_times[sid] = time_module.time()

def cleanup_stale_connections():
    """Remove stale connections and update room participants"""
    current_time = time_module.time()
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

@socketio.on('connect', namespace='/')
def handle_connect(auth=None):
    """Handle new socket connections"""
    sid = request.sid
    game_pin = session.get('game_pin')
    
    with room_lock:
        active_connections[sid] = {'connected_at': time_module.time()}
        update_connection_activity(sid)
        
        if game_pin:
            join_room(game_pin)
            room_participants[game_pin].add(sid)
            active_connections[sid]['game_pin'] = game_pin
            current_app.logger.info(f"Client {sid} joined room: {game_pin}")
            current_app.logger.info(f"Active connections: {active_connections}")
            current_app.logger.info(f"Room participants: {room_participants}")
            current_app.logger.info(f"Socket transport: {request.environ.get('wsgi.url_scheme', 'unknown')}")
            
            # If this is a player reconnecting during a game, sync their state
            player_id = session.get('player_id')
            if player_id:
                player = Player.query.get(player_id)
                if player and player.game.started_at:
                    game = player.game
                    current_app.logger.info(f"Found game state - Game ID: {game.id}, Started: {game.started_at}, Current Question Index: {game.current_question_index}")
                    
                    # Get all questions for this game
                    questions = Question.query.filter_by(game_id=game.id).order_by(Question.id).all()
                    current_app.logger.info(f"Total questions for game: {len(questions)}")
                    
                    # Check if game is in progress
                    if game.current_question_index >= 0:
                        # Get current question
                        if game.current_question_index < len(questions):
                            question = questions[game.current_question_index]
                            current_app.logger.info(f"Found current question - ID: {question.id}, Content: {question.content}, Game ID: {question.game_id}")
                            
                            # Check if player has already answered this question
                            existing_answer = Answer.query.filter_by(
                                player_id=player.id,
                                question_id=question.id
                            ).first()
                            
                            if not existing_answer:
                                try:
                                    incorrect_answers = json.loads(question.incorrect_answers)
                                    question_data = {
                                        'id': question.id,
                                        'content': question.content,
                                        'answers': [question.correct_answer] + incorrect_answers,
                                        'time_limit': question.time_limit or 20,
                                        'points': question.points or 1000
                                    }
                                    
                                    # Calculate remaining time for the question
                                    elapsed_time = (datetime.utcnow() - game.started_at).total_seconds()
                                    remaining_time = question.time_limit - elapsed_time if question.time_limit else 20
                                    
                                    if remaining_time > 0:
                                        # Send game state sync with current question
                                        emit('game_state_sync', {
                                            'currentQuestion': question_data,
                                            'questionStartedAt': game.started_at.isoformat(),
                                            'currentQuestionIndex': game.current_question_index,
                                            'total_questions': len(questions),
                                            'remainingTime': remaining_time
                                        })
                                        current_app.logger.info(f"Sent game state sync - Player: {player_id}, Game: {game.id}, Question: {question.id}")
                                        current_app.logger.info(f"Question data: {json.dumps(question_data, indent=2)}")
                                    else:
                                        current_app.logger.info(f"Question {question.id} time expired, waiting for next question")
                                except Exception as e:
                                    current_app.logger.error(f"Error syncing question state: {str(e)}")
                            else:
                                current_app.logger.info(f"Player {player_id} already answered question {question.id}")
                        else:
                            current_app.logger.error(f"Question index {game.current_question_index} out of range for game {game.id}")

@socketio.on('disconnect', namespace='/')
def handle_disconnect(auth=None):
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
                current_app.logger.info(f"Client {sid} left room: {game_pin}")
                current_app.logger.info(f"Updated room participants: {room_participants}")
            del active_connections[sid]
            current_app.logger.info(f"Updated active connections: {active_connections}")
        if sid in connection_times:
            del connection_times[sid]

@socketio.on('ping', namespace='/')
def handle_ping(auth=None):
    """Handle heartbeat pings from clients"""
    update_connection_activity(request.sid)
    emit('pong')

@socketio.on('player_join', namespace='/')
def handle_player_join(data, auth=None):
    sid = request.sid
    current_app.logger.info(f"handle_player_join called - SID: {sid}, Data: {data}")
    
    game = Game.query.filter_by(pin=data['pin']).first()
    if not game:
        current_app.logger.error(f"Game not found for PIN: {data['pin']}")
        emit('join_error', {'message': 'Game not found'})
        current_app.logger.info(f"handle_player_join: Game not found, returning")
        return

    # Handle host connection
    if data.get('is_host'):
        current_app.logger.info(f"handle_player_join: Host joining game {game.pin}")
        host_id = data.get('host_id')
        current_app.logger.info(f"handle_player_join: host_id from data: {host_id}, game.host_id: {game.host_id}")
        
        if not host_id or game.host_id != int(host_id):
            current_app.logger.error(f"handle_player_join: Invalid host_id {host_id} for game {game.pin}")
            emit('join_error', {'message': 'Unauthorized host'})
            current_app.logger.info(f"handle_player_join: Invalid host_id, returning")
            return
        
        host_id = int(host_id)
            
        with room_lock:
            join_room(game.pin)
            session['game_pin'] = game.pin
            session['_user_id'] = str(host_id)  # Set for auth_required decorator
            room_participants[game.pin].add(sid)
            active_connections[sid].update({
                'game_pin': game.pin,
                'is_host': True,
                'host_id': host_id
            })
            update_connection_activity(sid)
            current_app.logger.info(f"Host successfully joined game {game.pin}")
        current_app.logger.info(f"handle_player_join: Host connection handled, returning")
        return

    # Get player from data
    player_id = data.get('player_id')
    current_app.logger.info(f"Checking player data - SID: {sid}, Player ID: {player_id}, Game PIN: {game.pin}")
    
    player = Player.query.get(player_id)
    if not player:
        current_app.logger.error(f"Player not found. Player ID: {player_id}")
        emit('join_error', {'message': 'Player not found'})
        return
        
    current_app.logger.info(f"Found player - ID: {player.id}, Nickname: {player.nickname}, Game ID: {player.game_id}, Score: {player.score}")
    
    # Check if player belongs to this game
    if player.game_id != game.id:
        current_app.logger.error(f"Player game mismatch. Player ID: {player_id}, Expected Game: {game.id}, Actual Game: {player.game_id}")
        
        # Handle rejoin attempt
        if data.get('rejoin'):
            current_app.logger.info(f"Attempting rejoin - Player: {player.nickname}, From Game: {player.game_id}, To Game: {game.id}")
            try:
                player.game_id = game.id
                db.session.commit()
                current_app.logger.info(f"Successfully updated player {player_id} game ID")
            except Exception as e:
                current_app.logger.error(f"Failed to update player game ID: {str(e)}")
                emit('join_error', {'message': 'Failed to update player game'})
                return
        else:
            # Not a rejoin attempt, deny access
            emit('join_error', {'message': 'Player does not belong to this game'})
            return
    
    # Join the game room
    with room_lock:
        join_room(game.pin)
        session['game_pin'] = game.pin
        session['player_id'] = player.id  # Set player_id in session
        room_participants[game.pin].add(sid)
        
        # Update connection tracking
        active_connections[sid].update({
            'game_pin': game.pin,
            'player_info': {
                'id': player.id,
                'nickname': player.nickname,
                'score': player.score,
                'is_ready': data.get('is_ready', False)
            }
        })
        update_connection_activity(sid)
        
        current_app.logger.info(f"Player {player.nickname} joined game {game.pin}")
        
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
        
        current_app.logger.info(f"handle_player_join: Emitting room_participants_changed event - Player: {player.nickname}, Game: {game.pin}, Room Participants: {room_participants.get(game.pin, set())}")
        # Notify all clients about room participants
        emit('room_participants_changed', {
            'connected_players': current_participants
        }, room=game.pin, broadcast=True, include_self=True)
        
        current_app.logger.info(f"handle_player_join: Emitting player_joined event - Player: {player.nickname}, Game: {game.pin}, Room Participants: {room_participants.get(game.pin, set())}")

        # Check if the player is in the room participants
        current_app.logger.info(f"Room participants before emitting: {room_participants.get(game.pin, set())}")

        # Log session and room state
        current_app.logger.info(f"Session state before emit - game_pin: {session.get('game_pin')}, player_id: {session.get('player_id')}")
        current_app.logger.info(f"Room state before emit - participants: {room_participants.get(game.pin, set())}")
        current_app.logger.info(f"Socket ID: {request.sid}")
        
        # Prepare event data
        event_data = {
            'player_id': player.id,
            'nickname': player.nickname,
            'score': player.score,
            'is_ready': player.is_ready,
            'is_rejoin': is_rejoin
        }

        def ack():
            current_app.logger.info(f"Player joined event acknowledged for player {player.nickname}")
            return event_data

        # Emit join event with callback that returns data
        current_app.logger.info(f"Emitting player_joined event for player {player.nickname} (ID: {player.id})")
        emit('player_joined', event_data, callback=ack)
        current_app.logger.info("Emit completed")
        current_app.logger.info(f"handle_player_join: Emitted player_joined event - Player: {player.nickname}, Game: {game.pin}, Room Participants: {room_participants.get(game.pin, set())}")
        
        if player.is_ready:
            emit('player_ready', {
                'player_id': player.id,
                'nickname': player.nickname
            }, room=game.pin, broadcast=True, include_self=True)
        
        # Check if all players are ready
        all_players = Player.query.filter_by(game_id=game.id).all()
        ready_players = [p for p in all_players if p.is_ready]
        if len(ready_players) == len(all_players):
            current_app.logger.info(f"All players ready in game {game.pin}")
            emit('all_players_ready', room=game.pin, broadcast=True, include_self=True)
        
        # Start periodic cleanup of stale connections
        cleanup_stale_connections()

@socketio.on('preparing_next_question', namespace='/')
def handle_preparing_next_question(data, auth=None):
    game_pin = data.get('pin')
    if not game_pin:
        current_app.logger.error("No game pin provided for preparing_next_question")
        return
        
    # Verify user is host
    host_id = session.get('_user_id')  # Set by auth_required decorator
    if not host_id:
        current_app.logger.error("No user_id in session")
        emit('error', {'message': 'Authentication required'})
        return
        
    game = Game.query.filter_by(pin=game_pin).first()
    if not game:
        current_app.logger.error(f"Game not found for PIN: {game_pin}")
        emit('error', {'message': 'Game not found'})
        return
        
    if game.host_id != int(host_id):
        current_app.logger.error(f"User {host_id} is not host of game {game.pin}")
        emit('error', {'message': 'Unauthorized'})
        return
    
    # Get questions for this game
    questions = Question.query.filter_by(game_id=game.id).order_by(Question.id).all()
    if not questions:
        current_app.logger.error(f"No questions found for game {game.id}")
        emit('error', {'message': 'No questions available'})
        return
        
    # Increment question index
    game.current_question_index += 1
    if game.current_question_index >= len(questions):
        current_app.logger.error(f"Question index {game.current_question_index} out of range for game {game.id}")
        emit('error', {'message': 'No more questions available'})
        return
        
    try:
        db.session.commit()
        current_app.logger.info(f"Updated game state - Game: {game.id}, Question Index: {game.current_question_index}")
    except Exception as e:
        current_app.logger.error(f"Failed to update game state: {str(e)}")
        db.session.rollback()
        emit('error', {'message': 'Failed to prepare next question'})
        return
    
    # Get next question
    question = questions[game.current_question_index]
    current_app.logger.info(f"Preparing question {question.id} for game {game.pin}")
    
    try:
        incorrect_answers = json.loads(question.incorrect_answers)
        question_data = {
            'id': question.id,
            'content': question.content,
            'answers': [question.correct_answer] + incorrect_answers,
            'time_limit': question.time_limit or 20,
            'points': question.points or 1000
        }
        
        # Update game's question start time
        game.current_question_started_at = datetime.utcnow()
        db.session.commit()
        
        # Notify players to prepare for next question
        emit('question_preparing', {
            'question': question_data,
            'total_questions': len(questions),
            'current_index': game.current_question_index,
            'started_at': game.current_question_started_at.isoformat()
        }, room=game_pin)
        
        current_app.logger.info(f"Sent question_preparing event to room {game.pin}")
        current_app.logger.info(f"Question data: {json.dumps(question_data, indent=2)}")
        current_app.logger.info(f"Room participants: {room_participants.get(game.pin, set())}")
        
        # Short delay before sending question_started event
        import time
        time.sleep(2)  # Give clients time to prepare
        
        # Send the actual question
        emit('question_started', question_data, room=game_pin)
        current_app.logger.info(f"Sent question_started event to room {game.pin}")
        
    except Exception as e:
        current_app.logger.error(f"Error preparing question data: {str(e)}")
        emit('error', {'message': 'Failed to prepare question data'})

@socketio.on('game_started', namespace='/')
def handle_game_started(data=None, auth=None):
    game_pin = session.get('game_pin')
    if not game_pin:
        current_app.logger.error("No game_pin in session for game_started event")
        emit('error', {'message': 'Game session not found'})
        return
    
    # Verify user is host
    host_id = session.get('_user_id')  # Set by auth_required decorator
    if not host_id:
        current_app.logger.error("No user_id in session")
        emit('error', {'message': 'Authentication required'})
        return
        
    game = Game.query.filter_by(pin=game_pin).first()
    if not game:
        current_app.logger.error(f"Game not found for PIN: {game_pin}")
        emit('error', {'message': 'Game not found'})
        return
        
    if game.host_id != int(host_id):
        current_app.logger.error(f"User {host_id} is not host of game {game.pin}")
        emit('error', {'message': 'Unauthorized'})
        return

    # Initialize game state
    if not game.started_at:
        game.started_at = datetime.utcnow()
        game.current_question_index = -1  # Will be incremented to 0 when first question starts
        try:
            db.session.commit()
            current_app.logger.info(f"Initialized game state - Game: {game.id}, Started At: {game.started_at}")
        except Exception as e:
            current_app.logger.error(f"Failed to initialize game state: {str(e)}")
            db.session.rollback()
            emit('error', {'message': 'Failed to start game'})
            return
    
    current_app.logger.info(f"Broadcasting game_started to room: {game_pin}")
    current_app.logger.info(f"Current room participants: {room_participants.get(game_pin, set())}")
    
    # Get total questions for this game
    questions = Question.query.filter_by(game_id=game.id).order_by(Question.id).all()
    current_app.logger.info(f"Total questions for game {game.id}: {len(questions)}")
    
    # Emit to specific game room with start data
    emit('game_started', {
        'started_at': game.started_at.isoformat(),
        'total_questions': len(questions),
        'current_question_index': game.current_question_index,
        'redirect': {
            'host': url_for('game.host', pin=game_pin),
            'player': url_for('game.play', pin=game_pin)
        }
    }, room=game_pin, include_self=True)

@socketio.on('submit_answer', namespace='/')
def handle_submit_answer(data, auth=None):
    try:
        player_id = session.get('player_id')
        if not player_id:
            current_app.logger.error("No player_id in session")
            emit('answer_error', {'message': 'Player session not found'})
            return
            
        player = Player.query.get(player_id)
        if not player:
            current_app.logger.error(f"Player not found for ID: {player_id}")
            emit('answer_error', {'message': 'Player not found'})
            return
        
        if 'question_id' not in data:
            current_app.logger.error("No question_id provided in answer submission")
            emit('answer_error', {'message': 'Invalid answer data'})
            return
            
        question = Question.query.get(data['question_id'])
        if not question:
            current_app.logger.error(f"Question not found. Question ID: {data.get('question_id')}")
            emit('answer_error', {'message': 'Question not found'})
            return
            
        if question.game_id != player.game_id:
            current_app.logger.error(f"Question does not match player's game. Question Game: {question.game_id}, Player Game: {player.game_id}")
            emit('answer_error', {'message': 'Invalid question for this game'})
            return
        
        # Check if answer already submitted
        existing_answer = Answer.query.filter_by(
            player_id=player.id,
            question_id=question.id
        ).first()
        
        if existing_answer:
            current_app.logger.warning(f"Answer already submitted by player {player.id} for question {question.id}")
            emit('answer_error', {'message': 'Answer already submitted'})
            return
            
        if 'answer' not in data or 'response_time' not in data:
            current_app.logger.error("Missing answer or response_time in submission")
            emit('answer_error', {'message': 'Invalid answer data'})
            return
        
        # Calculate points based on response time
        response_time = data['response_time']
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
        current_app.logger.info(f"Answer processed - Player: {player.nickname}, Correct: {is_correct}, Points: {points_earned}")
        
        # Notify all clients about the answer
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
        current_app.logger.error(f"Error processing answer: {str(e)}")
        db.session.rollback()

@socketio.on('end_question', namespace='/')
def handle_end_question(data, auth=None):
    game = Game.query.filter_by(pin=data['pin']).first()
    if not game:
        current_app.logger.error(f"Game not found for PIN: {data['pin']}")
        emit('error', {'message': 'Game not found'})
        return
        
    # Verify user is host
    host_id = session.get('_user_id')  # Set by auth_required decorator
    if not host_id:
        current_app.logger.error("No user_id in session")
        emit('error', {'message': 'Authentication required'})
        return
        
    if game.host_id != int(host_id):
        current_app.logger.error(f"User {host_id} is not host of game {game.pin}")
        emit('error', {'message': 'Unauthorized'})
        return
    
    if 'question_id' not in data:
        current_app.logger.error("No question_id provided in end question request")
        emit('error', {'message': 'Invalid question data'})
        return
        
    question = Question.query.get(data['question_id'])
    if not question:
        current_app.logger.error(f"Question not found. Question ID: {data.get('question_id')}")
        emit('error', {'message': 'Question not found'})
        return
        
    if question.game_id != game.id:
        current_app.logger.error(f"Question does not match game. Question Game: {question.game_id}, Game: {game.id}")
        emit('error', {'message': 'Invalid question for this game'})
        return
    
    current_app.logger.info(f"Ending question {question.id} for game {game.pin}")
    
    # Get all answers for this question
    answers = Answer.query.filter_by(question_id=question.id).all()
    answer_data = [{
        'player_id': answer.player_id,
        'nickname': answer.player.nickname,
        'is_correct': answer.is_correct,
        'points_awarded': answer.points_awarded,
        'response_time': answer.response_time
    } for answer in answers]
    
    current_app.logger.info(f"Question {question.id} results - Total answers: {len(answers)}")
    
    # Send results to all players
    emit('question_ended', {
        'question_id': question.id,
        'correct_answer': question.correct_answer,
        'answers': answer_data
    }, room=game.pin)

@socketio.on('request_leaderboard', namespace='/')
def handle_leaderboard_request(data, auth=None):
    game = Game.query.filter_by(pin=data['pin']).first()
    if not game:
        current_app.logger.error(f"Game not found for PIN: {data['pin']}")
        emit('error', {'message': 'Game not found'})
        return
        
    # Verify user is host
    host_id = session.get('_user_id')  # Set by auth_required decorator
    if not host_id:
        current_app.logger.error("No user_id in session")
        emit('error', {'message': 'Authentication required'})
        return
        
    if game.host_id != int(host_id):
        current_app.logger.error(f"User {host_id} is not host of game {game.pin}")
        emit('error', {'message': 'Unauthorized'})
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
    
    current_app.logger.info(f"Sending leaderboard update for game {game.pin}")
    
    # Send leaderboard to the game room
    emit('leaderboard_update', {
        'leaderboard': leaderboard_data
    }, room=game.pin)
