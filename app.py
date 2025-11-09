from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from flask_migrate import Migrate
from db import db
from models import Usuarios, Sala
from forms import UserFrom, UserSignupForm, UserLoginForm
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
    form = UserSignupForm()
    
    if request.method == 'POST':
        if form.validate_on_submit():
            # Verificar si el email ya existe
            existing_user = Usuarios.query.filter_by(email=form.email.data).first()
            if existing_user:
                flash('El email ya está registrado. Por favor inicia sesión.', 'error')
                return redirect(url_for('login'))
            
            # Crear nuevo usuario
            usuario = Usuarios()
            usuario.name = form.name.data
            usuario.lastanme = form.lastanme.data
            usuario.lastname2 = form.lastname2.data
            usuario.email = form.email.data
            usuario.wallet_link = form.wallet_link.data
            usuario.set_password(form.password.data)  # Hashear contraseña
            
            db.session.add(usuario)
            db.session.commit()
            
            # Iniciar sesión automáticamente después del registro
            session['user_id'] = usuario.id
            session['user_name'] = usuario.name
            flash(f'¡Bienvenido {usuario.name}! Tu cuenta ha sido creada exitosamente.', 'success')
            return redirect(url_for('dashboard'))
    
    return render_template('signup.html', formulario=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Inicio de sesión - Solo email y contraseña"""
    form = UserLoginForm()
    
    if request.method == 'POST':
        if form.validate_on_submit():
            # Buscar usuario por email
            user = Usuarios.query.filter_by(email=form.email.data).first()
            
            if user and user.check_password(form.password.data):
                # Credenciales correctas - iniciar sesión
                session['user_id'] = user.id
                session['user_name'] = user.name
                flash(f'¡Bienvenido de nuevo, {user.name}!', 'success')
                return redirect(url_for('dashboard'))
            else:
                # Credenciales incorrectas
                flash('Email o contraseña incorrectos. Por favor intenta de nuevo.', 'error')
                return redirect(url_for('login'))
    
    return render_template('login.html', formulario=form)


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
        # Obtener datos del formulario
        nombre_producto = request.form.get('nombre-producto')
        precio = request.form.get('precio-producto')
        condicion = request.form.get('condicion-producto')
        descripcion = request.form.get('descripcion-producto')
        
        # Crear nueva sala
        nueva_sala = Sala()
        nueva_sala.codigo = Sala.generar_codigo()
        nueva_sala.nombre_producto = nombre_producto
        nueva_sala.precio = float(precio)
        nueva_sala.condicion = condicion
        nueva_sala.descripcion = descripcion
        nueva_sala.creador_id = session['user_id']
        
        db.session.add(nueva_sala)
        db.session.commit()
        
        # Guardar ID de la sala en sesión para mostrarla
        session['ultima_sala_id'] = nueva_sala.id
        
        flash(f'¡Sala creada exitosamente! Código: {nueva_sala.codigo}', 'success')
        return redirect(url_for('inviteChat'))
    
    return render_template('crear-chat.html')


@app.route('/invitar-chat')
@login_required
def inviteChat():
    """Página para compartir link/código del chat creado"""
    # Obtener la última sala creada
    sala_id = session.get('ultima_sala_id')
    
    if not sala_id:
        flash('No hay ninguna sala creada. Crea una primero.', 'warning')
        return redirect(url_for('crateChat'))
    
    sala = Sala.query.get(sala_id)
    
    if not sala:
        flash('Sala no encontrada.', 'error')
        return redirect(url_for('crateChat'))
    
    return render_template('invitar-chat.html', sala=sala)


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


