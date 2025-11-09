from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Email, Length, EqualTo

# Formulario de Registro (Signup)
class UserSignupForm(FlaskForm):
    name = StringField('Nombre(s)', validators=[DataRequired()])
    lastanme = StringField('Apellido Paterno', validators=[DataRequired()])
    lastname2 = StringField('Apellido Materno', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[
        DataRequired(),
        Length(min=6, message='La contraseña debe tener al menos 6 caracteres')
    ])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[
        DataRequired(),
        EqualTo('password', message='Las contraseñas deben coincidir')
    ])
    wallet_link = StringField('Link de Wallet')
    enviar = SubmitField('Registrarse')

# Formulario de Login
class UserLoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    enviar = SubmitField('Iniciar Sesión')

# Formulario antiguo para compatibilidad (deprecado)
class UserFrom(FlaskForm):
    name = StringField('Nombre(s)', validators=[DataRequired()])
    lastanme = StringField('Apellido Paterno', validators=[DataRequired()])
    lastname2 = StringField('Apellido Materno', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    wallet_link = StringField('Link de Wallet', validators=[DataRequired()])
    enviar = SubmitField('Guardar')
