from flask import Flask, render_template,request,redirect,url_for
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column
from .db import db
from models import Usuarios
from forms import UserFrom
from flask import Flask, jsonify 

app = Flask(__name__)

USER_DB = 'postgres'
USER_PASS = '1234'
SERVER_DB = 'localhost'
NAME_DB = 'demo'

URL_DB = f'postgresql://{USER_DB}:{USER_PASS}@{SERVER_DB}/{NAME_DB}'

#Variable de configuracion que se integra a Flask 
app.config['SQLALCHEMY_DATABASE_URI'] = URL_DB
db.init_app(app) #inicializar la aplicacion


#Migrar el modelo
migrate = Migrate(app,db)

app.config['SECRET_KEY']='YOLOLO'
app = Flask(__name__)

@app.route('/')
def inicio():
    usuarios = Usuarios.query.all() #Consulta a toda la tabla de Usuarios
    total_usuarios = Usuarios.query.count() #count es una funcion para contar cuantos registros tengo en la tabla Usuarios
    return render_template('index.html', total = total_usuarios, datos = usuarios)


@app.route('/login', methods=['GET','POST'])
def login():
    usuarios = Usuarios()
    userFrom = UserFrom(obj=usuarios)
    
    if request.method == 'POST':
        if userFrom.validate_on_submit():
            userFrom.populate_obj(usuarios)
            db.session.add(usuarios)
            db.session.commit()
            return redirect(url_for('inicio'))
    return render_template('login.html', formulario = userFrom)



@app.route('/static/admin/')
def api_status():
    data = {
        "status": "ok",
        "messange": "El servidor de la API está funcionando"
    }
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, port=5000)

