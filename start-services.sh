#!/bin/bash

# Script para ejecutar Flask + Servicio de pagos Open Payments
# Ejecuta ambos servicios en paralelo

echo "🚀 Iniciando Shifting - Plataforma P2P con Open Payments"
echo "=================================================="

# Función para limpiar procesos al salir
cleanup() {
    echo -e "\n🛑 Deteniendo servicios..."
    kill $FLASK_PID $PAYMENTS_PID 2>/dev/null
    exit 0
}

# Configurar trap para limpiar al salir
trap cleanup SIGINT SIGTERM

# Verificar dependencias de Python
echo "📦 Verificando dependencias de Python..."
if ! pip show requests flask > /dev/null 2>&1; then
    echo "📦 Instalando dependencias de Python..."
    pip install -r requeriments.txt
fi

# Verificar dependencias de Node.js
echo "📦 Verificando dependencias de Node.js..."
cd static/admin
if [ ! -d "node_modules" ]; then
    echo "📦 Instalando dependencias de Node.js..."
    npm install
fi
cd ../..

echo ""
echo "🐍 Iniciando Flask (Puerto 5000)..."
python app.py &
FLASK_PID=$!

sleep 3

echo "💳 Iniciando Servicio de Pagos Open Payments (Puerto 3001)..."
cd static/admin
node payments-service.js &
PAYMENTS_PID=$!
cd ../..

sleep 2

echo ""
echo "✅ Servicios iniciados correctamente:"
echo "   🌐 Flask App:          http://127.0.0.1:5000"
echo "   💳 Payments Service:   http://localhost:3001"
echo ""
echo "💡 Funcionalidades disponibles:"
echo "   • Registro y autenticación de usuarios"
echo "   • Creación y gestión de salas P2P"
echo "   • Pagos seguros con Open Payments"
echo "   • Billeteras Interledger integradas"
echo ""
echo "🔗 Billeteras de prueba disponibles:"
echo "   • aledev:    https://ilp.interledger-test.dev/aledev"
echo "   • aliciadev: https://ilp.interledger-test.dev/aliciadev"
echo "   • bobdev:    https://ilp.interledger-test.dev/bobdev"
echo ""
echo "⚠️  Presiona Ctrl+C para detener ambos servicios"
echo ""

# Verificar que los servicios estén funcionando
sleep 3
echo "🔍 Verificando estado de servicios..."

# Verificar Flask
if curl -s http://127.0.0.1:5000 > /dev/null; then
    echo "✅ Flask: Funcionando correctamente"
else
    echo "❌ Flask: No responde"
fi

# Verificar Servicio de pagos
if curl -s http://localhost:3001/health > /dev/null; then
    echo "✅ Payments Service: Funcionando correctamente"
else
    echo "❌ Payments Service: No responde"
fi

echo ""
echo "🎯 Sistema listo para usar. Ve a http://127.0.0.1:5000"
echo ""

# Mantener el script corriendo hasta que se termine
wait