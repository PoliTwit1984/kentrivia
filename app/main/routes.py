from flask import render_template, redirect, url_for, flash, session
from flask_login import current_user
from app import db
from app.main import bp
from app.main.forms import JoinGameForm
from app.models import Game, Player

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def index():
    # If user is logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('game.dashboard'))
    
    form = JoinGameForm()
    if form.validate_on_submit():
        game = Game.query.filter_by(pin=form.pin.data).first()
        
        if not game:
            flash('Invalid game PIN. Please try again.', 'danger')
            return redirect(url_for('main.index'))
        
        if not game.is_active:
            flash('This game has ended.', 'warning')
            return redirect(url_for('main.index'))
        
        # Create new player
        player = Player(
            game_id=game.id,
            nickname=form.nickname.data
        )
        db.session.add(player)
        db.session.commit()
        
        # Store player info in session
        session['player_id'] = player.id
        session['game_pin'] = game.pin
        
        flash('Successfully joined the game!', 'success')
        
        # Redirect to game lobby or play based on game state
        if game.started_at:
            return redirect(url_for('game.play', pin=game.pin))
        else:
            return redirect(url_for('game.lobby', pin=game.pin))
    
    # Get active games count and total players
    active_games = Game.query.filter_by(is_active=True).count()
    total_players = Player.query.join(Game).filter(Game.is_active == True).count()
    
    return render_template('main/index.html',
                         title='Welcome to KenTrivia',
                         form=form,
                         active_games=active_games,
                         total_players=total_players)

@bp.route('/how-to-play')
def how_to_play():
    return render_template('main/how_to_play.html', title='How to Play')
