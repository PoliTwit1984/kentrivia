from flask import render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_required, current_user
from flask_socketio import emit
import requests
from app import db, socketio
from app.game import bp
from app.game.forms import CreateGameForm, CreateQuestionForm, ImportQuestionsForm
from app.models import Game, Question, Player, Answer
from datetime import datetime
import json

@bp.route('/dashboard')
@login_required
def dashboard():
    active_games = Game.query.filter_by(
        host_id=current_user.id,
        is_active=True
    ).order_by(Game.created_at.desc()).all()
    
    past_games = Game.query.filter_by(
        host_id=current_user.id,
        is_active=False
    ).order_by(Game.ended_at.desc()).all()
    
    return render_template('game/dashboard.html',
                         title='Dashboard',
                         active_games=active_games,
                         past_games=past_games)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = CreateGameForm()
    if form.validate_on_submit():
        game = Game(
            title=form.title.data,
            host_id=current_user.id,
            pin=Game.generate_pin()
        )
        db.session.add(game)
        db.session.commit()
        flash('Game created successfully!', 'success')
        return redirect(url_for('game.edit', game_id=game.id))
    return render_template('game/create.html', title='Create Game', form=form)

@bp.route('/edit/<int:game_id>', methods=['GET', 'POST'])
@login_required
def edit(game_id):
    game = Game.query.get_or_404(game_id)
    if game.host_id != current_user.id:
        flash('You can only edit your own games.', 'danger')
        return redirect(url_for('game.dashboard'))
    
    if game.started_at:
        flash('Cannot edit a game that has already started.', 'warning')
        return redirect(url_for('game.dashboard'))
    
    question_form = CreateQuestionForm()
    import_form = ImportQuestionsForm()
    
    # Get OpenTDB categories for import form
    try:
        categories_response = requests.get('https://opentdb.com/api_category.php')
        categories = categories_response.json().get('trivia_categories', [])
        import_form.set_categories(categories)
    except:
        flash('Failed to load trivia categories. Please try again later.', 'warning')
        categories = []
    
    if question_form.submit.data and question_form.validate():
        question = Question(
            game_id=game.id,
            content=question_form.content.data,
            correct_answer=question_form.correct_answer.data,
            incorrect_answers=json.dumps([
                question_form.incorrect_answer1.data,
                question_form.incorrect_answer2.data,
                question_form.incorrect_answer3.data
            ]),
            category=question_form.category.data,
            difficulty=question_form.difficulty.data,
            time_limit=question_form.time_limit.data or 20,
            points=question_form.points.data or 1000
        )
        db.session.add(question)
        db.session.commit()
        flash('Question added successfully!', 'success')
        return redirect(url_for('game.edit', game_id=game_id))
    
    if import_form.submit.data and import_form.validate():
        params = {
            'amount': import_form.amount.data,
            'type': 'multiple'
        }
        if import_form.category.data:
            params['category'] = import_form.category.data
        if import_form.difficulty.data:
            params['difficulty'] = import_form.difficulty.data
            
        try:
            response = requests.get('https://opentdb.com/api.php', params=params)
            data = response.json()
            
            if data['response_code'] == 0:
                for q in data['results']:
                    question = Question(
                        game_id=game.id,
                        content=q['question'],
                        correct_answer=q['correct_answer'],
                        incorrect_answers=json.dumps(q['incorrect_answers']),
                        category=q['category'],
                        difficulty=q['difficulty'],
                        source='opentdb'
                    )
                    db.session.add(question)
                
                db.session.commit()
                flash(f'Successfully imported {len(data["results"])} questions!', 'success')
            else:
                flash('Failed to import questions. Please try different parameters.', 'danger')
        except:
            flash('Failed to import questions. Please try again later.', 'danger')
        
        return redirect(url_for('game.edit', game_id=game_id))
    
    questions = Question.query.filter_by(game_id=game_id).order_by(Question.id).all()
    return render_template('game/edit.html',
                         title='Edit Game',
                         game=game,
                         questions=questions,
                         question_form=question_form,
                         import_form=import_form)

@bp.route('/lobby/<pin>')
def lobby(pin):
    game = Game.query.filter_by(pin=pin).first_or_404()
    
    # Store game PIN in session for WebSocket room
    session['game_pin'] = pin
    
    # Check if user is host
    is_host = current_user.is_authenticated and current_user.id == game.host_id
    
    # Check if user is player
    player_id = session.get('player_id')
    is_player = False
    if player_id:
        player = Player.query.get(player_id)
        is_player = player and player.game_id == game.id
    
    if not (is_host or is_player):
        flash('You must join the game first.', 'warning')
        return redirect(url_for('main.index'))
    
    # If game has started, redirect to play
    if game.started_at and is_player:
        return redirect(url_for('game.play', pin=pin))
    
    return render_template('game/lobby.html',
                         title='Game Lobby',
                         game=game,
                         is_host=is_host)

@bp.route('/play/<pin>')
def play(pin):
    game = Game.query.filter_by(pin=pin).first_or_404()
    
    # Store game PIN in session for WebSocket room
    session['game_pin'] = pin
    
    # Verify game is active
    if not game.is_active:
        flash('This game has ended.', 'warning')
        return redirect(url_for('main.index'))
    
    # Check if user is player
    player_id = session.get('player_id')
    if not player_id:
        flash('You must join the game first.', 'warning')
        return redirect(url_for('main.index'))
    
    player = Player.query.get(player_id)
    if not player or player.game_id != game.id:
        flash('You are not a player in this game.', 'warning')
        return redirect(url_for('main.index'))
    
    return render_template('game/play.html',
                         title='Play Game',
                         game=game,
                         player=player)

@bp.route('/host/<pin>')
@login_required
def host(pin):
    game = Game.query.filter_by(pin=pin).first_or_404()
    
    # Store game PIN in session for WebSocket room
    session['game_pin'] = pin
    
    if game.host_id != current_user.id:
        flash('You can only host your own games.', 'danger')
        return redirect(url_for('game.dashboard'))
    
    if not game.is_active:
        flash('This game has ended.', 'warning')
        return redirect(url_for('game.dashboard'))
    
    return render_template('game/host.html',
                         title='Host Game',
                         game=game)

@bp.route('/api/game/<pin>/next-question', methods=['POST'])
@login_required
def next_question(pin):
    game = Game.query.filter_by(pin=pin).first_or_404()
    
    if game.host_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get next question
    next_index = game.current_question_index + 1
    question = Question.query.filter_by(game_id=game.id)\
        .order_by(Question.id)\
        .offset(next_index)\
        .first()
    
    if not question:
        return jsonify({'message': 'No more questions'})
    
    game.current_question_index = next_index
    db.session.commit()
    
    # Emit question_started event directly with full question data
    socketio.emit('question_started', {
        'question_id': question.id,
        'content': question.content,
        'answers': [question.correct_answer] + json.loads(question.incorrect_answers),
        'time_limit': question.time_limit,
        'points': question.points
    }, room=game.pin)
    
    return jsonify({
        'question': {
            'id': question.id,
            'content': question.content,
            'correct_answer': question.correct_answer,
            'incorrect_answers': json.loads(question.incorrect_answers),
            'time_limit': question.time_limit,
            'points': question.points
        }
    })

@bp.route('/api/game/<pin>/start', methods=['POST'])
@login_required
def start_game(pin):
    game = Game.query.filter_by(pin=pin).first_or_404()
    
    if game.host_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if game.started_at:
        return jsonify({'error': 'Game already started'}), 400
    
    if not game.questions.count():
        return jsonify({'error': 'Cannot start game without questions'}), 400
    
    # Mark all players as ready
    for player in game.players.all():
        player.is_ready = True
    
    # Update game state
    game.started_at = datetime.utcnow()
    game.current_question_index = -1  # Will be incremented to 0 when first question starts
    db.session.commit()
    
    # Emit game_started event to the game room
    socketio.emit('game_started', {
        'started_at': game.started_at.isoformat(),
        'redirect': {
            'host': url_for('game.host', pin=game.pin),
            'player': url_for('game.play', pin=game.pin)
        }
    }, room=game.pin)
    
    return jsonify({'success': True})

@bp.route('/api/game/<pin>/end', methods=['POST'])
@login_required
def end_game(pin):
    game = Game.query.filter_by(pin=pin).first_or_404()
    
    if game.host_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    game.ended_at = datetime.utcnow()
    game.is_active = False
    db.session.commit()
    
    return jsonify({'success': True})

@bp.route('/api/question/<int:question_id>', methods=['DELETE'])
@login_required
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)
    game = Game.query.get(question.game_id)
    
    if game.host_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if game.started_at:
        return jsonify({'error': 'Cannot delete questions from an active game'}), 400
    
    db.session.delete(question)
    db.session.commit()
    
    return jsonify({'success': True})
