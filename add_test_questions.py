import requests
import json
from app import create_app, db
from app.models import Question, Game

def fetch_trivia_questions(amount=10):
    url = 'https://opentdb.com/api.php'
    params = {
        'amount': amount,
        'type': 'multiple'
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if data['response_code'] == 0:
        return data['results']
    return []

def add_questions_to_game(game_id):
    questions = fetch_trivia_questions()
    
    for q in questions:
        question = Question(
            game_id=game_id,
            content=q['question'],
            correct_answer=q['correct_answer'],
            incorrect_answers=json.dumps(q['incorrect_answers']),
            category=q['category'],
            difficulty=q['difficulty'],
            source='opentdb'
        )
        db.session.add(question)
    
    db.session.commit()
    print(f'Added {len(questions)} questions to game {game_id}')

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        # Get the first game or create one if none exists
        game = Game.query.first()
        if game:
            add_questions_to_game(game.id)
        else:
            print('No games found. Please create a game first.')
