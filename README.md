# Shifting — P2P Payment Platform with Open Payments

**Shifting** is a P2P marketplace web application that facilitates secure transactions between buyers and sellers using **Open Payments** and **Interledger Protocol (ILP)** technology.

The system allows users to create "rooms" for products/services, where buyers can make secure payments using their Interledger wallets, eliminating intermediaries and excessive fees.

## Main Features

- Secure P2P payments with Open Payments SDK
- Fixed prices non-manipulable by users
- Strict validation of amounts and Payment Pointers
- Transaction tracking in database
- Room system to organize products/services
- User authentication with secure sessions

## Project Structure

```
Dreamhack/
├── app.py                      # Main Flask application
├── models.py                   # Database models (Users, Room, Transaction)
├── db.py                       # SQLAlchemy configuration
├── forms.py                    # Flask-WTF forms
├── init_db.sql                 # Database initialization script
├── start-services.sh           # Script to start everything
├── stop-services.sh            # Script to stop services
├── templates/                  # HTML templates
│   ├── index.html
│   ├── login.html
│   ├── signup.html
│   ├── principal.html
│   ├── crear-chat.html
│   └── ver-sala.html
├── static/
│   ├── css/                    # Styles separated by view
│   └── admin/
│       ├── payment-service-v2.js  # Node.js payment service
│       ├── private.key            # Private key for Open Payments
│       └── package.json
└── venv/                       # Python virtual environment
```

## Technologies

### Backend
- **Python 3.13** with Flask 3.1.2
- **PostgreSQL** with SQLAlchemy ORM
- **Flask-Migrate** for migrations
- **Flask-WTF** for forms

### Payment Service
- **Node.js 22.0.0**
- **@interledger/open-payments** v7.1.3
- **Express.js** for REST API

### Frontend
- HTML5, CSS3, vanilla JavaScript
- Professional responsive design

## Installation and Configuration

### Prerequisites

```bash
# Check versions
python3 --version  # 3.13+
node --version     # 22.0+
psql --version     # PostgreSQL installed
```

### 1. Clone and configure Python environment

```bash
cd /home/alephantom/Hackaton/Dreamhack

# Activate virtual environment (if it exists)
source venv/bin/activate

# Or create a new one
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requeriments.txt
```

### 2. Configure PostgreSQL

```bash
# Create database
sudo -u postgres psql
CREATE DATABASE dreamhack_db;
CREATE USER dreamhack_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE dreamhack_db TO dreamhack_user;
\q

# Execute initialization script
psql -U dreamhack_user -d dreamhack_db -f init_db.sql
```

### 3. Configure Payment Service (Node.js)

```bash
cd static/admin
npm install
```

### 4. Configure Open Payments credentials

Make sure you have a `static/admin/private.key` file with your Interledger private key.

To obtain test credentials:
- Visit: https://interledger-test.dev
- Create test wallets (aledev, aliciadev, bobdev, etc.)
- Download the private keys

## Start the Application

### Option 1: Automatic script (Recommended)

```bash
./start-services.sh
```

This script:
1. Stops previous services
2. Starts Payment Service (Node.js) on port 3001
3. Starts Flask Backend on port 5000
4. Verifies both respond correctly
5. Shows URLs and PIDs of the processes

### Option 2: Manual

```bash
# Terminal 1 - Payment Service
cd static/admin
node payment-service-v2.js

# Terminal 2 - Flask Backend
python app.py
```

### Verify everything works

```bash
# Payment Service
curl http://localhost:3001/health

# Flask Backend
curl http://127.0.0.1:5000
```

## Stop Services

```bash
./stop-services.sh
```

Or manually:
```bash
pkill -f "node.*payment-service"
pkill -f "python.*app.py"
```

## Using the Application

### 1. Registration and Login
- Go to http://127.0.0.1:5000
- Create an account or log in
- Configure your Payment Pointer ($domain/user)

### 2. Create a Room (Seller)
- Click on "Create Room"
- Enter: name, description, price
- Add your Payment Pointer to receive payments
- Share the room code

### 3. Join and Pay (Buyer)
- Enter the room code
- Review product details
- Select your payment wallet
- Click on "Pay with Open Payments"
- Authorize on the Interledger page
- The system automatically completes the transaction

## API Endpoints

### Flask Backend (Port 5000)

| Method | Route | Description |
|--------|------|-------------|
| GET | `/` | Home page |
| GET/POST | `/login` | Login |
| GET/POST | `/signup` | User registration |
| GET | `/principal` | User dashboard |
| POST | `/crear-sala` | Create new room |
| GET | `/ver-sala/<codigo>` | View room details |
| POST | `/initiate-payment` | Initiate Open Payments payment |
| GET | `/payment-callback/<id>` | Callback after authorization |

### Payment Service (Port 3001)

| Method | Route | Description |
|--------|------|-------------|
| GET | `/health` | Service status |
| POST | `/initiate-payment` | Create grant and payment quote |
| POST | `/complete-payment/:id` | Complete authorized payment |

## Database

### Main Tables

**usuarios**
- `id`, `username`, `email`, `password`, `wallet_link`

**sala**
- `id`, `codigo`, `nombre`, `descripcion`, `precio`, `creador_id`, `activa`

**transaccion**
- `id`, `transaction_id`, `sala_id`, `sender_id`, `receiver_wallet`, `amount`, `currency`, `status`

## Security

- Passwords hashed with bcrypt
- Secure Flask sessions
- Backend amount validation
- Validated Payment Pointer ($domain/user)
- CORS properly configured
- WARNING: DO NOT use in production without configuring environment variables

## Troubleshooting

## Troubleshooting

### Payment Service won't start
```bash
cd static/admin
npm install
node payment-service-v2.js
```

### Flask won't connect to PostgreSQL
- Verify credentials in `app.py`
- Make sure PostgreSQL is running: `sudo systemctl status postgresql`

### Python import errors
```bash
source venv/bin/activate
pip install -r requeriments.txt
```

## Logs


## Logs

- **Payment Service**: `static/admin/payment-service.log`
- **Flask Backend**: `flask.log`

## Testing

```bash
## Testing

```bash
# Test a sample payment
curl -X POST http://localhost:3001/initiate-payment \
  -H "Content-Type: application/json" \
  -d '{
    "receiverWallet": "$ilp.interledger-test.dev/aliciadev",
    "amount": 1000,
    "transactionId": "test-001"
  }'
```

## Roadmap

- [ ] Implement complete outgoing payment
- [ ] Add verification of completed payments
- [ ] Rating system
- [ ] Real-time chat between buyer/seller
- [ ] Administration panel
- [ ] Automated tests

## Contributions

---

For more complete technical documentation, check the `docs/` folder.
```

## Roadmap

- [ ] Implementar outgoing payment completo
- [ ] Agregar verificación de pagos completados
- [ ] Sistema de calificaciones
- [ ] Chat en tiempo real entre comprador/vendedor
- [ ] Panel de administración
- [ ] Tests automatizados

## Contribuciones

---

