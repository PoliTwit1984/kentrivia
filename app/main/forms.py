from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError
from app.models import Game, Player

class JoinGameForm(FlaskForm):
    pin = StringField('Game PIN', validators=[
        DataRequired(),
        Length(min=6, max=6, message='Game PIN must be exactly 6 digits')
    ])
    nickname = StringField('Nickname', validators=[
        DataRequired(),
        Length(min=2, max=64, message='Nickname must be between 2 and 64 characters')
    ])
    submit = SubmitField('Join Game')

    def validate_pin(self, pin):
        game = Game.query.filter_by(pin=pin.data).first()
        if not game:
            raise ValidationError('Invalid game PIN.')
        if not game.is_active:
            raise ValidationError('This game has already ended.')
        if game.started_at:
            raise ValidationError('This game has already started.')

    def validate_nickname(self, nickname):
        # Check if nickname contains only allowed characters
        if not nickname.data.replace(' ', '').isalnum():
            raise ValidationError('Nickname can only contain letters, numbers, and spaces.')
        
        # If pin is valid, check if nickname is already taken in this game
        if self.pin.data and not self.pin.errors:
            game = Game.query.filter_by(pin=self.pin.data).first()
            if game:
                existing_player = Player.query.filter_by(
                    game_id=game.id,
                    nickname=nickname.data
                ).first()
                if existing_player:
                    raise ValidationError('This nickname is already taken in this game.')
