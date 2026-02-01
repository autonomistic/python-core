from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, IntegerField, SelectField
from wtforms.validators import DataRequired, Email, Length


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    invite_code = StringField("Invite Code", validators=[DataRequired()])


class ChapterForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=120)])
    position = IntegerField("Position", default=0)


class ProblemForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    difficulty = SelectField("Difficulty", choices=[("easy","Easy"),("medium","Medium"),("hard","Hard")])
    points = IntegerField("Points", default=10)
    tags = StringField("Tags (comma-separated)")
    prompt = TextAreaField("Prompt")
