// Servicio de pagos Open Payments con Express
import { createAuthenticatedClient, isFinalizedGrant } from "@interledger/open-payments";
import express from 'express';
import cors from 'cors';
import fs from "fs";

const app = express();
const PORT = 3001;

// Middleware
app.use(cors({
  origin: 'http://127.0.0.1:5000',
  credentials: true
}));
app.use(express.json());

// Almacenamiento temporal de información de pagos
const paymentCache = new Map();

// Configuración del cliente
const privateKey = fs.readFileSync('/home/alephantom/Hackaton/Dreamhack/static/admin/private.key', 'utf-8');
const CLIENT_WALLET = 'https://ilp.interledger-test.dev/aledev';
const KEY_ID = '30c571c4-3941-4221-8206-92eb2bedd81b';

let client = null;

// Inicializar cliente
async function initializeClient() {
  try {
    client = await createAuthenticatedClient({
      walletAddressUrl: CLIENT_WALLET,
      privateKey: privateKey,
      keyId: KEY_ID
    });
    console.log('✓ Cliente Open Payments inicializado correctamente');
    console.log('✓ Wallet configurada:', CLIENT_WALLET);
    return true;
  } catch (error) {
    console.error('✗ Error inicializando cliente:', error.message);
    return false;
  }
}

// Health check
app.get('/health', (req, res) => {
  res.json({ 
    status: 'ok', 
    service: 'open-payments-service',
    client_ready: !!client,
    wallet: CLIENT_WALLET
  });
});

// Iniciar pago
app.post('/initiate-payment', async (req, res) => {
  try {
    const { receiverWallet, amount, transactionId } = req.body;
    
    console.log('\n--- Iniciando nuevo pago ---');
    console.log('Transaction ID:', transactionId);
    console.log('Monto:', amount);
    console.log('Wallet receptor:', receiverWallet);

    if (!client) {
      throw new Error('Cliente Open Payments no está inicializado');
    }

    // Convertir Payment Pointer a URL
    const senderUrl = CLIENT_WALLET;
    const receiverUrl = receiverWallet.startsWith('$') 
      ? receiverWallet.replace('$', 'https://')
      : receiverWallet;

    console.log('Sender URL:', senderUrl);
    console.log('Receiver URL:', receiverUrl);

    // Obtener direcciones de billeteras
    console.log('Obteniendo wallet addresses...');
    const sendingWalletAddress = await client.walletAddress.get({ url: senderUrl });
    const receivingWalletAddress = await client.walletAddress.get({ url: receiverUrl });

    console.log('Sender wallet:', {
      id: sendingWalletAddress.id,
      assetCode: sendingWalletAddress.assetCode,
      assetScale: sendingWalletAddress.assetScale
    });
    console.log('Receiver wallet:', {
      id: receivingWalletAddress.id,
      assetCode: receivingWalletAddress.assetCode,
      assetScale: receivingWalletAddress.assetScale
    });

    // Crear pago entrante
    console.log('Solicitando grant para incoming payment...');
    const incomingPaymentGrant = await client.grant.request(
      { url: receivingWalletAddress.authServer },
      {
        access_token: {
          access: [{
            type: "incoming-payment",
            actions: ["read", "complete", "create"],
          }],
        },
      }
    );

    if (!isFinalizedGrant(incomingPaymentGrant)) {
      throw new Error("No se pudo finalizar la concesión del pago entrante");
    }

    console.log('✓ Grant para incoming payment obtenido');

    // Calcular monto en la escala correcta
    const incomingAmount = {
      assetCode: receivingWalletAddress.assetCode,
      assetScale: receivingWalletAddress.assetScale,
      value: String(Math.floor(amount * Math.pow(10, receivingWalletAddress.assetScale))),
    };

    console.log('Creando incoming payment con monto:', incomingAmount);

    const incomingPayment = await client.incomingPayment.create(
      {
        url: receivingWalletAddress.resourceServer,
        accessToken: incomingPaymentGrant.access_token.value,
      },
      {
        walletAddress: receivingWalletAddress.id,
        incomingAmount: incomingAmount,
      }
    );

    console.log('✓ Incoming payment creado:', incomingPayment.id);

    // Crear cotización
    console.log('Solicitando grant para quote...');
    const quoteGrant = await client.grant.request(
      { url: sendingWalletAddress.authServer },
      {
        access_token: {
          access: [{
            type: "quote",
            actions: ["create", "read"],
          }],
        },
      }
    );

    if (!isFinalizedGrant(quoteGrant)) {
      throw new Error("No se pudo finalizar la concesión de cotización");
    }

    console.log('✓ Grant para quote obtenido');
    console.log('Creando quote...');

    const quote = await client.quote.create(
      {
        url: sendingWalletAddress.resourceServer,
        accessToken: quoteGrant.access_token.value,
      },
      {
        walletAddress: sendingWalletAddress.id,
        receiver: incomingPayment.id,
        method: "ilp",
      }
    );

    console.log('✓ Quote creado:', {
      debitAmount: quote.debitAmount,
      receiveAmount: quote.receiveAmount
    });

    // Solicitar concesión para pago saliente (requiere interacción del usuario)
    console.log('Solicitando grant para outgoing payment con interacción...');
    const outgoingPaymentGrant = await client.grant.request(
      { url: sendingWalletAddress.authServer },
      {
        access_token: {
          access: [{
            type: "outgoing-payment",
            actions: ["read", "create"],
            limits: {
              debitAmount: quote.debitAmount,
            },
            identifier: sendingWalletAddress.id,
          }],
        },
        interact: {
          start: ["redirect"],
          finish: {
            method: "redirect",
            uri: `http://127.0.0.1:5000/payment-callback/${transactionId}`,
            nonce: transactionId,
          },
        },
      }
    );

    console.log('✓ Grant para outgoing payment obtenido');

    if (!outgoingPaymentGrant.interact || !outgoingPaymentGrant.interact.redirect) {
      throw new Error("No se obtuvo URL de interacción para autorización");
    }

    console.log('✓ URL de interacción:', outgoingPaymentGrant.interact.redirect);
    console.log('--- Pago iniciado exitosamente ---\n');

    // Guardar información para completar el pago después
    paymentCache.set(transactionId, {
      sendingWalletAddress,
      receivingWalletAddress,
      incomingPayment,
      quote,
      outgoingPaymentGrant,
      timestamp: Date.now()
    });

    res.json({
      success: true,
      transactionId,
      interactionUrl: outgoingPaymentGrant.interact.redirect,
      continueUri: outgoingPaymentGrant.continue.uri,
      continueToken: outgoingPaymentGrant.continue.access_token.value,
      quote: {
        debitAmount: quote.debitAmount,
        receiveAmount: quote.receiveAmount
      }
    });

  } catch (error) {
    console.error('✗ Error iniciando pago:', error.message);
    console.error('Stack:', error.stack);
    res.status(500).json({ 
      success: false, 
      error: error.message,
      stack: process.env.NODE_ENV === 'development' ? error.stack : undefined
    });
  }
});

// Completar pago después de la autorización del usuario
app.post('/complete-payment/:transactionId', async (req, res) => {
  try {
    const { transactionId } = req.params;
    const { interact_ref, continueUri, continueToken } = req.body;

    console.log('\n--- Completando pago ---');
    console.log('Transaction ID:', transactionId);
    console.log('Interact ref:', interact_ref);

    if (!client) {
      throw new Error('Cliente Open Payments no está inicializado');
    }

    // Continuar con el grant
    console.log('Continuando grant...');
    const grant = await client.grant.continue(
      {
        url: continueUri,
        accessToken: continueToken,
      },
      {
        interact_ref,
      }
    );

    if (!isFinalizedGrant(grant)) {
      throw new Error("No se pudo finalizar el grant después de la interacción");
    }

    console.log('✓ Grant finalizado después de autorización');

    // Recuperar información del pago del cache
    const paymentInfo = paymentCache.get(transactionId);
    
    if (!paymentInfo) {
      throw new Error('No se encontró información del pago. Puede haber expirado.');
    }

    const { sendingWalletAddress, quote } = paymentInfo;

    // Crear el outgoing payment para ejecutar la transacción
    console.log('Creando outgoing payment...');
    
    const outgoingPayment = await client.outgoingPayment.create(
      {
        url: sendingWalletAddress.resourceServer,
        accessToken: grant.access_token.value,
      },
      {
        walletAddress: sendingWalletAddress.id,
        quoteId: quote.id,
      }
    );

    console.log('✓ Outgoing payment creado:', outgoingPayment.id);
    console.log('Estado del pago:', outgoingPayment.receiveAmount);
    
    // Limpiar del cache
    paymentCache.delete(transactionId);
    
    console.log('✓ Pago ejecutado exitosamente');
    console.log('--- Pago completado ---\n');

    res.json({
      success: true,
      transactionId,
      status: 'completed',
      paymentId: outgoingPayment.id,
      receiveAmount: outgoingPayment.receiveAmount,
      debitAmount: outgoingPayment.debitAmount,
      grant: {
        access_token: grant.access_token.value
      }
    });

  } catch (error) {
    console.error('✗ Error completando pago:', error.message);
    console.error('Stack:', error.stack);
    res.status(500).json({ 
      success: false, 
      error: error.message 
    });
  }
});

// Manejo de errores
app.use((err, req, res, next) => {
  console.error('Error en servidor:', err);
  res.status(500).json({ 
    success: false, 
    error: err.message 
  });
});

// Inicializar y arrancar servidor
async function startServer() {
  console.log('Iniciando servicio de pagos Open Payments...');
  
  const initialized = await initializeClient();
  
  if (!initialized) {
    console.error('No se pudo inicializar el cliente. Saliendo...');
    process.exit(1);
  }
  
  app.listen(PORT, () => {
    console.log(`\n🚀 Servicio de pagos ejecutándose en http://localhost:${PORT}`);
    console.log(`📍 Health check: http://localhost:${PORT}/health\n`);
  });
}

startServer().catch(error => {
  console.error('Error fatal al iniciar servidor:', error);
  process.exit(1);
});