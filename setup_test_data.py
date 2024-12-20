from app import create_app, db
from app.models import User, Game
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # Create test user
    user = User(
        username='testuser',
        email='test@example.com'
    )
    user.password_hash = generate_password_hash('password')
    db.session.add(user)
    db.session.commit()
    
    # Create test game
    game = Game(
        title='Test Game',
        host_id=user.id,
        pin=Game.generate_pin()
    )
    db.session.add(game)
    db.session.commit()
    
    print(f'Created test user (username: testuser, password: password)')
    print(f'Created test game (PIN: {game.pin})')
