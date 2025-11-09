from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from flask_migrate import Migrate
from db import db
from models import Usuarios
from forms import UserFrom
from functools import wraps

# Crea la app
app = Flask(__name__)

USER_DB = 'postgres'
USER_PASS = '1234'
SERVER_DB = 'localhost'
NAME_DB = 'demo'

URL_DB = f'postgresql://{USER_DB}:{USER_PASS}@{SERVER_DB}/{NAME_DB}'

# Variable de configuracion que se integra a Flask 
app.config['SQLALCHEMY_DATABASE_URI'] = URL_DB
app.config['SECRET_KEY'] = 'YOLOLO'
db.init_app(app)  # inicializar la aplicacion

# Migrar el modelo
migrate = Migrate(app, db)

# Decorador para rutas que requieren autenticación
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor inicia sesión para continuar', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Context processor para inyectar URLs en todos los templates
@app.context_processor
def inject_urls():
    """Inyecta URLs de navegación para que los templates puedan usarlas"""
    return dict(
        # Usuario actual
        current_user=Usuarios.query.get(session.get('user_id')) if 'user_id' in session else None,
        is_authenticated='user_id' in session,
        # URLs principales
        url_inicio=url_for('inicio'),
        url_signup=url_for('login'),
        url_login=url_for('signup'),
        url_logout=url_for('logout'),
        url_dashboard=url_for('dashboard'),
        url_crear_chat=url_for('crateChat'),
        url_invitar_chat=url_for('inviteChat'),
    )

# Middleware para reemplazar automáticamente links hardcodeados en HTML
@app.after_request
def fix_html_links(response):
    """Reemplaza automáticamente los links .html por rutas Flask"""
    if response.content_type and 'text/html' in response.content_type:
        data = response.get_data(as_text=True)
        
        # Mapeo de archivos HTML a rutas
        replacements = {
            'href="index.html"': f'href="{url_for("dashboard")}"',
            "href='index.html'": f"href='{url_for('dashboard')}'",
            'href="crear-chat.html"': f'href="{url_for("crateChat")}"',
            "href='crear-chat.html'": f"href='{url_for('crateChat')}'",
            'href="invitar-chat.html"': f'href="{url_for("inviteChat")}"',
            "href='invitar-chat.html'": f"href='{url_for('inviteChat')}'",
            'href="signup.html"': f'href="{url_for("signup")}"',
            "href='signup.html'": f"href='{url_for('signup')}'",
            'href="login.html"': f'href="{url_for("login")}"',
            "href='login.html'": f"href='{url_for('login')}'",
            'href="principal.html"': f'href="{url_for("inicio")}"',
            "href='principal.html'": f"href='{url_for('inicio')}'",
        }
        
        # Reemplazar cada ocurrencia
        for old, new in replacements.items():
            data = data.replace(old, new)
        
        response.set_data(data)
    
    return response


# ========== RUTAS PÚBLICAS ==========

@app.route('/')
def inicio():
    """Landing page principal - Página pública de bienvenida"""
    return render_template('principal.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Registro de nuevos usuarios"""
    usuarios = Usuarios()
    userFrom = UserFrom(obj=usuarios)
    
    if request.method == 'POST':
        if userFrom.validate_on_submit():
            # Verificar si el email ya existe
            existing_user = Usuarios.query.filter_by(email=userFrom.email.data).first()
            if existing_user:
                flash('El email ya está registrado. Por favor inicia sesión.', 'error')
                return redirect(url_for('login'))
            
            # Crear nuevo usuario
            userFrom.populate_obj(usuarios)
            db.session.add(usuarios)
            db.session.commit()
            
            # Iniciar sesión automáticamente después del registro
            session['user_id'] = usuarios.id
            session['user_name'] = usuarios.name
            flash(f'¡Bienvenido {usuarios.name}! Tu cuenta ha sido creada exitosamente.', 'success')
            return redirect(url_for('dashboard'))
    
    return render_template('signup.html', formulario=userFrom)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Inicio de sesión de usuarios existentes"""
    usuarios = Usuarios()
    userFrom = UserFrom(obj=usuarios)
    
    if request.method == 'POST':
        if userFrom.validate_on_submit():
            # Buscar usuario por email
            user = Usuarios.query.filter_by(email=userFrom.email.data).first()
            
            if user:
                # Usuario encontrado - iniciar sesión
                session['user_id'] = user.id
                session['user_name'] = user.name
                flash(f'¡Bienvenido de nuevo, {user.name}!', 'success')
                return redirect(url_for('dashboard'))
            else:
                # Usuario no encontrado - registrarlo
                userFrom.populate_obj(usuarios)
                db.session.add(usuarios)
                db.session.commit()
                
                session['user_id'] = usuarios.id
                session['user_name'] = usuarios.name
                flash(f'¡Cuenta creada exitosamente! Bienvenido {usuarios.name}.', 'success')
                return redirect(url_for('dashboard'))
    
    return render_template('login.html', formulario=userFrom)


@app.route('/logout')
def logout():
    """Cerrar sesión del usuario"""
    user_name = session.get('user_name', 'Usuario')
    session.clear()
    flash(f'Hasta luego, {user_name}. Has cerrado sesión exitosamente.', 'info')
    return redirect(url_for('inicio'))


# ========== RUTAS PROTEGIDAS (REQUIEREN AUTENTICACIÓN) ==========

@app.route('/dashboard')
@login_required
def dashboard():
    """Panel principal del usuario autenticado"""
    user = Usuarios.query.get(session['user_id'])
    return render_template('user_view.html', user=user)


@app.route('/crear-chat', methods=['GET', 'POST'])
@login_required
def crateChat():
    """Formulario para crear un nuevo chat de negociación"""
    if request.method == 'POST':
        # Aquí iría la lógica para guardar el chat en la BD
        # Por ahora, solo redirigimos a invitar
        producto = request.form.get('nombre-producto')
        precio = request.form.get('precio-producto')
        
        # Guardar datos en la sesión temporalmente (idealmente en BD)
        session['temp_chat'] = {
            'producto': producto,
            'precio': precio,
            'condicion': request.form.get('condicion-producto'),
            'descripcion': request.form.get('descripcion-producto')
        }
        
        flash(f'Chat creado para: {producto}', 'success')
        return redirect(url_for('inviteChat'))
    
    return render_template('crear-chat.html')


@app.route('/invitar-chat')
@login_required
def inviteChat():
    """Página para compartir link/código del chat creado"""
    # Obtener datos temporales del chat (en producción vendría de BD)
    chat_data = session.get('temp_chat', {})
    return render_template('invitar-chat.html', chat=chat_data)


# ========== RUTAS DE API Y ADMINISTRACIÓN ==========

@app.route('/static/admin/')
def api_status():
    """Endpoint de estado de la API"""
    data = {
        "status": "ok",
        "messange": "El servidor de la API está funcionando"
    }
    return jsonify(data)


@app.route('/usuarios')
@login_required
def listar_usuarios():
    """Vista antigua de listado de usuarios (para debugging)"""
    usuarios = Usuarios.query.all()
    total_usuarios = Usuarios.query.count()
    return render_template('index.html', total=total_usuarios, datos=usuarios)


# ========== EJECUCIÓN DE LA APLICACIÓN ==========

if __name__ == '__main__':
    app.run(debug=True, port=5000)


