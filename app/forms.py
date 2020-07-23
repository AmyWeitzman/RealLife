from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, ValidationError
from app.models import Player

class LoginForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    submit = SubmitField('Sign In')
