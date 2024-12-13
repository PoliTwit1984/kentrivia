from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

class CreateGameForm(FlaskForm):
    title = StringField('Game Title', validators=[
        DataRequired(),
        Length(min=3, max=64, message='Title must be between 3 and 64 characters')
    ])
    submit = SubmitField('Create Game')

class CreateQuestionForm(FlaskForm):
    content = TextAreaField('Question', validators=[
        DataRequired(),
        Length(min=5, max=500, message='Question must be between 5 and 500 characters')
    ])
    correct_answer = StringField('Correct Answer', validators=[
        DataRequired(),
        Length(min=1, max=200, message='Answer must be between 1 and 200 characters')
    ])
    incorrect_answer1 = StringField('Incorrect Answer 1', validators=[
        DataRequired(),
        Length(min=1, max=200, message='Answer must be between 1 and 200 characters')
    ])
    incorrect_answer2 = StringField('Incorrect Answer 2', validators=[
        DataRequired(),
        Length(min=1, max=200, message='Answer must be between 1 and 200 characters')
    ])
    incorrect_answer3 = StringField('Incorrect Answer 3', validators=[
        DataRequired(),
        Length(min=1, max=200, message='Answer must be between 1 and 200 characters')
    ])
    category = StringField('Category', validators=[
        Optional(),
        Length(max=64, message='Category must be less than 64 characters')
    ])
    difficulty = SelectField('Difficulty',
        choices=[
            ('easy', 'Easy'),
            ('medium', 'Medium'),
            ('hard', 'Hard')
        ],
        validators=[DataRequired()]
    )
    time_limit = IntegerField('Time Limit (seconds)', validators=[
        Optional(),
        NumberRange(min=5, max=60, message='Time limit must be between 5 and 60 seconds')
    ], default=20)
    points = IntegerField('Points', validators=[
        Optional(),
        NumberRange(min=100, max=2000, message='Points must be between 100 and 2000')
    ], default=1000)
    submit = SubmitField('Add Question')

class ImportQuestionsForm(FlaskForm):
    category = SelectField('Category', choices=[], validators=[DataRequired()])
    difficulty = SelectField('Difficulty',
        choices=[
            ('', 'Any Difficulty'),
            ('easy', 'Easy'),
            ('medium', 'Medium'),
            ('hard', 'Hard')
        ],
        validators=[Optional()]
    )
    amount = IntegerField('Number of Questions', validators=[
        DataRequired(),
        NumberRange(min=1, max=50, message='Can import between 1 and 50 questions at a time')
    ], default=10)
    submit = SubmitField('Import Questions')

    def set_categories(self, categories):
        self.category.choices = [('', 'Any Category')] + [
            (str(cat['id']), cat['name']) for cat in categories
        ]
