from flask import jsonify, request
from flask_login import login_required, current_user
from app import db
from app.api import bp
from app.models import Game, Question, Player, Answer
from datetime import datetime

@bp.route('/game/<pin>/next-question', methods=['POST'])
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
    
    return jsonify({
        'question': {
            'id': question.id,
            'content': question.content,
            'correct_answer': question.correct_answer,
            'incorrect_answers': question.incorrect_answers,
            'time_limit': question.time_limit,
            'points': question.points
        }
    })

@bp.route('/question/<int:question_id>', methods=['DELETE'])
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

@bp.route('/game/<pin>/stats', methods=['GET'])
@login_required
def game_stats(pin):
    game = Game.query.filter_by(pin=pin).first_or_404()
    
    if game.host_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get game statistics
    total_players = game.players.count()
    total_questions = game.questions.count()
    
    # Get player statistics
    players = []
    for player in game.players.all():
        correct_answers = Answer.query.join(Question)\
            .filter(Answer.player_id == player.id,
                   Question.game_id == game.id,
                   Answer.is_correct == True)\
            .count()
        
        players.append({
            'nickname': player.nickname,
            'score': player.score,
            'correct_answers': correct_answers,
            'accuracy': round(correct_answers / total_questions * 100 if total_questions > 0 else 0, 1)
        })
    
    # Get question statistics
    questions = []
    for question in game.questions.all():
        total_answers = question.answers.count()
        correct_answers = question.answers.filter_by(is_correct=True).count()
        
        questions.append({
            'content': question.content,
            'correct_answer': question.correct_answer,
            'total_answers': total_answers,
            'correct_answers': correct_answers,
            'accuracy': round(correct_answers / total_answers * 100 if total_answers > 0 else 0, 1)
        })
    
    return jsonify({
        'game': {
            'title': game.title,
            'started_at': game.started_at.isoformat() if game.started_at else None,
            'ended_at': game.ended_at.isoformat() if game.ended_at else None,
            'total_players': total_players,
            'total_questions': total_questions
        },
        'players': players,
        'questions': questions
    })

@bp.route('/game/<pin>/leaderboard', methods=['GET'])
def leaderboard(pin):
    game = Game.query.filter_by(pin=pin).first_or_404()
    
    players = game.players.order_by(Player.score.desc()).all()
    leaderboard_data = [{
        'player_id': player.id,
        'nickname': player.nickname,
        'score': player.score,
        'streak': player.current_streak
    } for player in players]
    
    return jsonify({'leaderboard': leaderboard_data})
