from flask_wtf import FlaskForm
from wtforms import TextAreaField, validators, SubmitField
from wtforms.fields.datetime import DateField, TimeField
from wtforms.fields.simple import StringField
from wtforms.validators import DataRequired, Optional


class MakeNoteForm(FlaskForm):
    note_text = TextAreaField('Текст', validators=[DataRequired(), validators.Length(min=4, max=2048)])
    submit = SubmitField('Обдумать', name='obs_submit')

class NoteForm(FlaskForm):
    birds = StringField('Птица', validators=[DataRequired(), validators.Length(min=2, max=64)])
    date = DateField('Дата', validators=[Optional()])
    time = TimeField('Время', validators=[Optional()])
    geo = StringField('Геопозиция')
    submit = SubmitField('Записать', name='note_submit')
