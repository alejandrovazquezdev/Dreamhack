from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Email

# Formulario de Usuario

class UserFrom(FlaskForm):
    name = StringField('Nombre(s)', validators=[DataRequired()])
    lastanme = StringField('Apellido Materno', validators=[DataRequired()])
    lastname2 = StringField('Apellido Paterno', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    enviar = SubmitField('Guardar')
