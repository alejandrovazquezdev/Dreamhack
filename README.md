# Shifting — Plataforma P2P de Pagos con Open Payments

**Shifting** es una aplicación web de marketplace P2P que facilita transacciones seguras entre compradores y vendedores usando la tecnología **Open Payments** e **Interledger Protocol (ILP)**. 

El sistema permite a los usuarios crear "salas" para productos/servicios, donde los compradores pueden realizar pagos seguros usando sus wallets de Interledger, eliminando intermediarios y comisiones excesivas.

## 🌟 Características Principales

- ✅ **Pagos P2P seguros** con Open Payments SDK
- ✅ **Interfaz profesional** sin emojis, diseño limpio
- ✅ **Precios fijos** no manipulables por usuarios
- ✅ **Validación estricta** de montos y Payment Pointers
- ✅ **Rastreo de transacciones** en base de datos
- ✅ **Sistema de salas** para organizar productos/servicios
- ✅ **Autenticación de usuarios** con sesiones seguras

## 📁 Estructura del Proyecto

```
Dreamhack/
├── app.py                      # Aplicación Flask principal
├── models.py                   # Modelos de base de datos (Usuarios, Sala, Transaccion)
├── db.py                       # Configuración SQLAlchemy
├── forms.py                    # Formularios Flask-WTF
├── init_db.sql                 # Script de inicialización de BD
├── start-services.sh           # 🚀 Script para iniciar todo
├── stop-services.sh            # 🛑 Script para detener servicios
├── templates/                  # Plantillas HTML
│   ├── index.html
│   ├── login.html
│   ├── signup.html
│   ├── principal.html
│   ├── crear-chat.html
│   └── ver-sala.html
├── static/
│   ├── css/                    # Estilos separados por vista
│   └── admin/
│       ├── payment-service-v2.js  # Servicio de pagos Node.js
│       ├── private.key            # Clave privada para Open Payments
│       └── package.json
└── venv/                       # Entorno virtual Python
```

## 🛠️ Tecnologías

### Backend
- **Python 3.13** con Flask 3.1.2
- **PostgreSQL** con SQLAlchemy ORM
- **Flask-Migrate** para migraciones
- **Flask-WTF** para formularios

### Payment Service
- **Node.js 22.0.0**
- **@interledger/open-payments** v7.1.3
- **Express.js** para API REST

### Frontend
- HTML5, CSS3, JavaScript vanilla
- Diseño responsive profesional

## ⚙️ Instalación y Configuración

### Prerrequisitos

```bash
# Verificar versiones
python3 --version  # 3.13+
node --version     # 22.0+
psql --version     # PostgreSQL instalado
```

### 1. Clonar y configurar entorno Python

```bash
cd /home/alephantom/Hackaton/Dreamhack

# Activar entorno virtual (si existe)
source venv/bin/activate

# O crear uno nuevo
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requeriments.txt
```

### 2. Configurar PostgreSQL

```bash
# Crear base de datos
sudo -u postgres psql
CREATE DATABASE dreamhack_db;
CREATE USER dreamhack_user WITH PASSWORD 'tu_password';
GRANT ALL PRIVILEGES ON DATABASE dreamhack_db TO dreamhack_user;
\q

# Ejecutar script de inicialización
psql -U dreamhack_user -d dreamhack_db -f init_db.sql
```

### 3. Configurar Payment Service (Node.js)

```bash
cd static/admin
npm install
```

### 4. Configurar credenciales de Open Payments

Asegúrate de tener un archivo `static/admin/private.key` con tu clave privada de Interledger.

Para obtener credenciales de prueba:
- Visita: https://interledger-test.dev
- Crea wallets de prueba (aledev, aliciadev, bobdev, etc.)
- Descarga las claves privadas

## 🚀 Iniciar la Aplicación

### Opción 1: Script automático (Recomendado)

```bash
./start-services.sh
```

Este script:
1. Detiene servicios anteriores
2. Inicia Payment Service (Node.js) en puerto 3001
3. Inicia Flask Backend en puerto 5000
4. Verifica que ambos respondan correctamente
5. Muestra URLs y PIDs de los procesos

### Opción 2: Manual

```bash
# Terminal 1 - Payment Service
cd static/admin
node payment-service-v2.js

# Terminal 2 - Flask Backend
python app.py
```

### Verificar que todo funcione

```bash
# Payment Service
curl http://localhost:3001/health

# Flask Backend
curl http://127.0.0.1:5000
```

## 🛑 Detener Servicios

```bash
./stop-services.sh
```

O manualmente:
```bash
pkill -f "node.*payment-service"
pkill -f "python.*app.py"
```

## 🎯 Uso de la Aplicación

### 1. Registro e Inicio de Sesión
- Ve a http://127.0.0.1:5000
- Crea una cuenta o inicia sesión
- Configura tu Payment Pointer ($domain/user)

### 2. Crear una Sala (Vendedor)
- Click en "Crear Sala"
- Ingresa: nombre, descripción, precio
- Añade tu Payment Pointer para recibir pagos
- Comparte el código de la sala

### 3. Unirse y Pagar (Comprador)
- Ingresa el código de sala
- Revisa detalles del producto
- Selecciona tu wallet de pago
- Click en "Pagar con Open Payments"
- Autoriza en la página de Interledger
- El sistema completa automáticamente la transacción

## 📊 Endpoints API

### Flask Backend (Puerto 5000)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/` | Página principal |
| GET/POST | `/login` | Inicio de sesión |
| GET/POST | `/signup` | Registro de usuarios |
| GET | `/principal` | Dashboard del usuario |
| POST | `/crear-sala` | Crear nueva sala |
| GET | `/ver-sala/<codigo>` | Ver detalles de sala |
| POST | `/initiate-payment` | Iniciar pago Open Payments |
| GET | `/payment-callback/<id>` | Callback después de autorización |

### Payment Service (Puerto 3001)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/health` | Estado del servicio |
| POST | `/initiate-payment` | Crear grant y quote de pago |
| POST | `/complete-payment/:id` | Completar pago autorizado |

## 🗃️ Base de Datos

### Tablas Principales

**usuarios**
- `id`, `username`, `email`, `password`, `wallet_link`

**sala**
- `id`, `codigo`, `nombre`, `descripcion`, `precio`, `creador_id`, `activa`

**transaccion**
- `id`, `transaction_id`, `sala_id`, `sender_id`, `receiver_wallet`, `amount`, `currency`, `status`

## 🔐 Seguridad

- ✅ Contraseñas hasheadas con bcrypt
- ✅ Sesiones Flask seguras
- ✅ Validación de montos en backend
- ✅ Payment Pointer validado ($domain/user)
- ✅ CORS configurado correctamente
- ⚠️ **NO usar en producción** sin configurar variables de entorno

## 🐛 Solución de Problemas

### Payment Service no inicia
```bash
cd static/admin
npm install
node payment-service-v2.js
```

### Flask no conecta a PostgreSQL
- Verifica credenciales en `app.py`
- Asegúrate de que PostgreSQL esté corriendo: `sudo systemctl status postgresql`

### Errores de importación Python
```bash
source venv/bin/activate
pip install -r requeriments.txt
```

## 📝 Logs

- **Payment Service**: `static/admin/payment-service.log`
- **Flask Backend**: `flask.log`

## 🧪 Testing

```bash
# Probar pago de prueba
curl -X POST http://localhost:3001/initiate-payment \
  -H "Content-Type: application/json" \
  -d '{
    "receiverWallet": "$ilp.interledger-test.dev/aliciadev",
    "amount": 1000,
    "transactionId": "test-001"
  }'
```

## 🚧 Roadmap

- [ ] Implementar outgoing payment completo
- [ ] Agregar verificación de pagos completados
- [ ] Sistema de calificaciones
- [ ] Chat en tiempo real entre comprador/vendedor
- [ ] Panel de administración
- [ ] Tests automatizados

## 👥 Contribuciones

---

Para documentación técnica más completa, revisar la carpeta `docs/`.