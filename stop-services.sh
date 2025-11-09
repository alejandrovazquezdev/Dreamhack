#!/bin/bash

# Script para detener todos los servicios de Shifting

echo "🛑 Deteniendo servicios de Shifting..."
echo ""

# Detener Payment Service
echo "💰 Deteniendo Payment Service..."
pkill -f "node.*payment-service"
if [ $? -eq 0 ]; then
    echo "   ✓ Payment Service detenido"
else
    echo "   • Payment Service no estaba corriendo"
fi

# Detener Flask Backend
echo ""
echo "🌐 Deteniendo Flask Backend..."
pkill -f "python.*app.py"
if [ $? -eq 0 ]; then
    echo "   ✓ Flask Backend detenido"
else
    echo "   • Flask Backend no estaba corriendo"
fi

echo ""
echo "✅ Servicios detenidos"
echo ""
