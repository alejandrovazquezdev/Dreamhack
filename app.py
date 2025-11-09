from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from flask_migrate import Migrate
from db import db
from models import Usuarios, Sala, MiembroSala, Transaccion
from forms import UserFrom, UserSignupForm, UserLoginForm
from functools import wraps
import requests
import uuid
import json
from datetime import datetime

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
        url_crear_sala=url_for('crear_sala'),
        url_compartir_sala=url_for('compartir_sala'),
        url_mis_salas=url_for('mis_salas'),
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
            'href="crear-sala.html"': f'href="{url_for("crear_sala")}"',
            "href='crear-sala.html'": f"href='{url_for('crear_sala')}'",
            'href="compartir-sala.html"': f'href="{url_for("compartir_sala")}"',
            "href='compartir-sala.html'": f"href='{url_for('compartir_sala')}'",
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


@app.route('/crear-sala', methods=['GET', 'POST'])
@login_required
def crear_sala():
    """Formulario para crear una nueva sala de negociación"""
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
        return redirect(url_for('compartir_sala'))
    
    return render_template('crear-sala.html')


@app.route('/compartir-sala')
@login_required
def compartir_sala():
    """Página para compartir link/código de la sala creada"""
    # Obtener la última sala creada
    sala_id = session.get('ultima_sala_id')
    
    print(f"DEBUG: sala_id en sesión: {sala_id}")  # Debug
    
    if not sala_id:
        flash('No hay ninguna sala creada. Crea una primero.', 'warning')
        return redirect(url_for('crear_sala'))
    
    sala = Sala.query.get(sala_id)
    
    print(f"DEBUG: sala encontrada: {sala}")  # Debug
    if sala:
        print(f"DEBUG: código: {sala.codigo}, link: {sala.get_link()}")  # Debug
    
    if not sala:
        flash('Sala no encontrada.', 'error')
        return redirect(url_for('crear_sala'))
    
    return render_template('compartir-sala.html', sala=sala)


@app.route('/sala/<codigo>')
@login_required
def ver_sala(codigo):
    """Ver detalles de una sala específica por código"""
    sala = Sala.query.filter_by(codigo=codigo).first()
    
    if not sala:
        flash('Sala no encontrada.', 'error')
        return redirect(url_for('dashboard'))
    
    # Obtener información del creador
    creador = Usuarios.query.get(sala.creador_id)
    
    # Verificar si el usuario actual es el creador
    user_id = session.get('user_id')
    es_creador = (user_id == sala.creador_id)
    
    # Verificar si el usuario ya está en la sala
    ya_unido = MiembroSala.query.filter_by(sala_id=sala.id, usuario_id=user_id).first() is not None
    
    # Obtener todos los miembros de la sala
    miembros = db.session.query(MiembroSala, Usuarios).join(
        Usuarios, MiembroSala.usuario_id == Usuarios.id
    ).filter(MiembroSala.sala_id == sala.id).all()
    
    return render_template('ver-sala.html', 
                         sala=sala, 
                         creador=creador, 
                         es_creador=es_creador,
                         ya_unido=ya_unido,
                         miembros=miembros)


@app.route('/sala/<codigo>/unirse', methods=['POST'])
@login_required
def unirse_sala(codigo):
    """Unirse a una sala como comprador"""
    sala = Sala.query.filter_by(codigo=codigo).first()
    
    if not sala:
        flash('Sala no encontrada.', 'error')
        return redirect(url_for('dashboard'))
    
    user_id = session.get('user_id')
    
    # Verificar que no sea el creador
    if user_id == sala.creador_id:
        flash('No puedes unirte a tu propia sala.', 'warning')
        return redirect(url_for('ver_sala', codigo=codigo))
    
    # Verificar si ya está unido
    miembro_existente = MiembroSala.query.filter_by(sala_id=sala.id, usuario_id=user_id).first()
    if miembro_existente:
        flash('Ya estás unido a esta sala.', 'info')
        return redirect(url_for('ver_sala', codigo=codigo))
    
    # Crear nueva membresía
    nuevo_miembro = MiembroSala()
    nuevo_miembro.sala_id = sala.id
    nuevo_miembro.usuario_id = user_id
    nuevo_miembro.rol = 'comprador'
    
    db.session.add(nuevo_miembro)
    db.session.commit()
    
    flash(f'¡Te has unido exitosamente a la sala "{sala.nombre_producto}"!', 'success')
    return redirect(url_for('ver_sala', codigo=codigo))


@app.route('/sala/<codigo>/salir', methods=['POST'])
@login_required
def salir_sala(codigo):
    """Salir de una sala"""
    sala = Sala.query.filter_by(codigo=codigo).first()
    
    if not sala:
        flash('Sala no encontrada.', 'error')
        return redirect(url_for('dashboard'))
    
    user_id = session.get('user_id')
    
    # Buscar membresía
    miembro = MiembroSala.query.filter_by(sala_id=sala.id, usuario_id=user_id).first()
    
    if not miembro:
        flash('No estás unido a esta sala.', 'warning')
        return redirect(url_for('ver_sala', codigo=codigo))
    
    db.session.delete(miembro)
    db.session.commit()
    
    flash('Has salido de la sala.', 'info')
    return redirect(url_for('mis_salas'))


@app.route('/unirse-por-codigo', methods=['POST'])
@login_required
def unirse_por_codigo():
    """Unirse a una sala ingresando el código"""
    codigo = request.form.get('codigo', '').strip()
    
    if not codigo:
        flash('Debes ingresar un código de sala.', 'error')
        return redirect(url_for('dashboard'))
    
    # Verificar que el código tenga 8 dígitos
    if len(codigo) != 8 or not codigo.isdigit():
        flash('El código debe tener exactamente 8 dígitos.', 'error')
        return redirect(url_for('dashboard'))
    
    # Buscar la sala
    sala = Sala.query.filter_by(codigo=codigo).first()
    
    if not sala:
        flash(f'No existe ninguna sala con el código {codigo}.', 'error')
        return redirect(url_for('dashboard'))
    
    if not sala.activa:
        flash('Esta sala ya no está activa.', 'warning')
        return redirect(url_for('dashboard'))
    
    # Redirigir a la página de la sala para que se una
    return redirect(url_for('ver_sala', codigo=codigo))


@app.route('/mis-salas')
@login_required
def mis_salas():
    """Listar todas las salas creadas por el usuario actual"""
    user_id = session.get('user_id')
    salas = Sala.query.filter_by(creador_id=user_id, activa=True).order_by(Sala.fecha_creacion.desc()).all()
    
    return render_template('mis-salas.html', salas=salas)
    
    return render_template('invitar-chat.html', sala=sala)


# ========== RUTAS DE PAGOS OPEN PAYMENTS ==========

PAYMENTS_SERVICE_URL = 'http://localhost:3001'

@app.route('/initiate-payment', methods=['POST'])
@login_required
def initiate_payment():
    """Iniciar un pago usando Open Payments"""
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        required_fields = ['receiverWallet', 'amount', 'salaId']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Campo requerido: {field}'}), 400
        
        # Obtener información del usuario actual
        user_id = session.get('user_id')
        usuario = Usuarios.query.get(user_id)
        
        if not usuario:
            return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404
        
        # Verificar que la sala exista y esté activa
        sala = Sala.query.get(data['salaId'])
        if not sala:
            return jsonify({'success': False, 'error': 'Sala no encontrada'}), 404
        
        if not sala.activa:
            return jsonify({'success': False, 'error': 'Esta sala ya no está disponible'}), 403
        
        # Verificar que el usuario no sea el creador de la sala
        if sala.creador_id == user_id:
            return jsonify({'success': False, 'error': 'No puedes pagar tu propio producto'}), 403
        
        # VALIDACIÓN CRÍTICA: El monto debe ser exactamente el precio de la sala
        amount_received = float(data['amount'])
        if abs(amount_received - sala.precio) > 0.01:  # Tolerancia de 1 centavo por redondeo
            return jsonify({
                'success': False, 
                'error': f'Monto inválido. El precio exacto es ${sala.precio:.2f} USD'
            }), 400
        
        # Validar formato del Payment Pointer
        receiver_wallet = data['receiverWallet'].strip()
        if not receiver_wallet.startswith('$'):
            return jsonify({
                'success': False, 
                'error': 'La billetera debe usar formato Payment Pointer ($domain/user)'
            }), 400
        
        # Generar ID único para la transacción
        transaction_id = str(uuid.uuid4())
        
        # Crear registro de transacción en la base de datos ANTES del pago
        nueva_transaccion = Transaccion(
            transaction_id=transaction_id,
            sala_id=sala.id,
            sender_id=user_id,
            receiver_wallet=receiver_wallet,
            amount=sala.precio,  # Usar siempre el precio exacto de la sala
            currency='USD',
            status='initiated'
        )
        
        try:
            db.session.add(nueva_transaccion)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': 'Error creando transacción'}), 500
        
        # Preparar datos para el servicio de pagos
        payment_data = {
            'senderWallet': '$ilp.interledger-test.dev/aledev',  # Usar siempre aledev como sender (tenemos las keys)
            'receiverWallet': receiver_wallet,
            'amount': sala.precio,  # Usar siempre el precio exacto de la sala
            'currency': 'USD',
            'transactionId': transaction_id
        }
        
        # Llamar al servicio de pagos
        try:
            import requests
            response = requests.post(f'{PAYMENTS_SERVICE_URL}/initiate-payment', 
                                   json=payment_data, 
                                   timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    # Guardar información de la transacción en la sesión
                    session[f'transaction_{transaction_id}'] = {
                        'sala_id': sala.id,
                        'sender_id': user_id,
                        'amount': payment_data['amount'],
                        'receiver_wallet': payment_data['receiverWallet'],
                        'continueUri': result.get('continueUri'),
                        'continueToken': result.get('continueToken'),
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    return jsonify({
                        'success': True,
                        'transactionId': transaction_id,
                        'interactionUrl': result['interactionUrl'],
                        'quote': result['quote']
                    })
                else:
                    return jsonify({'success': False, 'error': result.get('error', 'Error desconocido')}), 500
            else:
                return jsonify({'success': False, 'error': 'Error comunicándose con el servicio de pagos'}), 500
                
        except requests.RequestException as e:
            return jsonify({'success': False, 'error': f'Error de conexión: {str(e)}'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/payment-callback/<transaction_id>')
def payment_callback(transaction_id):
    """Callback después de la autorización del usuario en Open Payments"""
    try:
        # Obtener interact_ref de la URL
        interact_ref = request.args.get('interact_ref')
        
        if not interact_ref:
            flash('Error: No se recibió referencia de interacción', 'error')
            return redirect(url_for('dashboard'))
        
        # Verificar que la transacción exista en la sesión
        transaction_key = f'transaction_{transaction_id}'
        if transaction_key not in session:
            flash('Error: Transacción no encontrada', 'error')
            return redirect(url_for('dashboard'))
        
        transaction_info = session[transaction_key]
        
        # Completar el pago con los datos guardados
        try:
            import requests
            response = requests.post(f'{PAYMENTS_SERVICE_URL}/complete-payment/{transaction_id}',
                                   json={
                                       'interact_ref': interact_ref,
                                       'continueUri': transaction_info.get('continueUri'),
                                       'continueToken': transaction_info.get('continueToken')
                                   },
                                   timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    # Actualizar el estado de la transacción en la base de datos
                    transaccion = Transaccion.query.filter_by(transaction_id=transaction_id).first()
                    if transaccion:
                        transaccion.status = 'completed'
                        transaccion.payment_id = result.get('paymentId')
                        transaccion.fecha_completado = datetime.now()
                        try:
                            db.session.commit()
                        except Exception as e:
                            db.session.rollback()
                            print(f"Error actualizando transacción: {e}")
                    
                    # Limpiar la sesión
                    session.pop(transaction_key, None)
                    
                    flash(f'Pago completado exitosamente! ID: {result["paymentId"]}', 'success')
                    return redirect(url_for('ver_sala', codigo=Sala.query.get(transaction_info['sala_id']).codigo))
                else:
                    # Marcar transacción como fallida
                    transaccion = Transaccion.query.filter_by(transaction_id=transaction_id).first()
                    if transaccion:
                        transaccion.status = 'failed'
                        transaccion.error_message = result.get('error', 'Error desconocido')
                        try:
                            db.session.commit()
                        except:
                            db.session.rollback()
                    
                    flash(f'Error completando el pago: {result.get("error")}', 'error')
            else:
                flash('Error comunicándose con el servicio de pagos', 'error')
                
        except requests.RequestException as e:
            flash(f'Error de conexión: {str(e)}', 'error')
            
    except Exception as e:
        flash(f'Error procesando callback: {str(e)}', 'error')
    
    return redirect(url_for('dashboard'))


@app.route('/payment-status/<transaction_id>')
@login_required
def payment_status(transaction_id):
    """Obtener estado de una transacción"""
    try:
        import requests
        response = requests.get(f'{PAYMENTS_SERVICE_URL}/transaction-status/{transaction_id}',
                              timeout=10)
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'success': False, 'error': 'Transacción no encontrada'}), 404
            
    except requests.RequestException as e:
        return jsonify({'success': False, 'error': f'Error de conexión: {str(e)}'}), 500


# ========== RUTAS DE API Y ADMINISTRACIÓN ==========

@app.route('/static/admin/')
def api_status():
    """Endpoint de estado de la API"""
    data = {
        "status": "ok",
        "messange": "El servidor de la API está funcionando"
    }
    return jsonify(data)


@app.route('/payments-service/health')
def payments_health():
    """Verificar estado del servicio de pagos"""
    try:
        import requests
        response = requests.get(f'{PAYMENTS_SERVICE_URL}/health', timeout=5)
        return jsonify(response.json())
    except:
        return jsonify({'status': 'error', 'message': 'Servicio de pagos no disponible'}), 503


@app.route('/mis-transacciones')
@login_required
def mis_transacciones():
    """Ver historial de transacciones del usuario"""
    user_id = session.get('user_id')
    transacciones = Transaccion.query.filter_by(sender_id=user_id).order_by(Transaccion.fecha_creacion.desc()).all()
    
    return jsonify({
        'success': True,
        'transacciones': [t.to_dict() for t in transacciones]
    })


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


