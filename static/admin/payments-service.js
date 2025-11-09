// Servicio de pagos Open Payments integrado con Flask
// Corre como microservicio en puerto 3001

import { createAuthenticatedClient, isFinalizedGrant, OpenPaymentsClientError } from "@interledger/open-payments";
import Koa from 'koa';
import { koaBody } from 'koa-body';
import cors from '@koa/cors';
import fs from "fs";

const app = new Koa();
const PORT = 3001;

// Configuración CORS para comunicarse con Flask
app.use(cors({
  origin: 'http://127.0.0.1:5000', // Flask app
  credentials: true
}));

app.use(koaBody());

// Configuración del cliente Open Payments
const privateKey = fs.readFileSync('./private.key', 'utf-8');
const CLIENT_WALLET = 'https://ilp.interledger-test.dev/aledev';
const KEY_ID = '30c571c4-3941-4221-8206-92eb2bedd81b';

// Billeteras de prueba disponibles
const AVAILABLE_WALLETS = {
  aledev: 'https://ilp.interledger-test.dev/aledev',
  aliciadev: 'https://ilp.interledger-test.dev/aliciadev', 
  bobdev: 'https://ilp.interledger-test.dev/bobdev'
};

let client = null;

// Inicializar cliente Open Payments
async function initializeClient() {
  try {
    client = await createAuthenticatedClient({
      walletAddressUrl: CLIENT_WALLET,
      privateKey: privateKey,
      keyId: KEY_ID
    });
    console.log('Cliente Open Payments inicializado correctamente');
    console.log('Usando wallet cliente:', CLIENT_WALLET);
    console.log('Key ID:', KEY_ID);
  } catch (error) {
    console.error('Error inicializando cliente Open Payments:', error);
  }
}

// Store temporal para transacciones en progreso
const pendingTransactions = new Map();

// RUTA: Health check
app.use(async (ctx, next) => {
  if (ctx.path === '/health' && ctx.method === 'GET') {
    ctx.body = { 
      status: 'ok', 
      service: 'open-payments-service',
      client_ready: !!client 
    };
    return;
  }
  await next();
});

// RUTA: Iniciar pago
app.use(async (ctx, next) => {
  if (ctx.path === '/initiate-payment' && ctx.method === 'POST') {
    try {
      const { 
        senderWallet, 
        receiverWallet, 
        amount, 
        currency = 'USD',
        transactionId 
      } = ctx.request.body;

      console.log('Iniciando pago:', { senderWallet, receiverWallet, amount, currency, transactionId });

      // 1. Convertir Payment Pointers a URLs y obtener direcciones de billeteras
      
      // Función para convertir Payment Pointer ($domain/user) a URL HTTPS
      const convertPaymentPointer = (wallet) => {
        if (wallet.startsWith('$')) {
          // Convertir $ilp.interledger-test.dev/user -> https://ilp.interledger-test.dev/user
          return wallet.replace('$', 'https://');
        } else if (wallet.startsWith('https://')) {
          return wallet;
        } else {
          // Asumir que es solo el dominio/usuario sin protocolo
          return `https://${wallet}`;
        }
      };

      const sendingWalletUrl = convertPaymentPointer(senderWallet);
      const receivingWalletUrl = convertPaymentPointer(receiverWallet);

      console.log('URLs convertidas:', { sendingWalletUrl, receivingWalletUrl });

      const sendingWalletAddress = await client.walletAddress.get({
        url: sendingWalletUrl,
      });
      
      const receivingWalletAddress = await client.walletAddress.get({
        url: receivingWalletUrl,
      });

      // 2. Crear pago entrante
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

      // Verificar que ambas billeteras soporten USD
      console.log('Wallet info:', {
        sender: { code: sendingWalletAddress.assetCode, scale: sendingWalletAddress.assetScale },
        receiver: { code: receivingWalletAddress.assetCode, scale: receivingWalletAddress.assetScale }
      });

      const incomingPayment = await client.incomingPayment.create(
        {
          url: receivingWalletAddress.resourceServer,
          accessToken: incomingPaymentGrant.access_token.value,
        },
        {
          walletAddress: receivingWalletAddress.id,
          incomingAmount: {
            assetCode: 'USD', // Forzar USD
            assetScale: 2,    // 2 decimales para USD
            value: String(Math.round(amount * 100)), // Convertir a centavos
          },
        }
      );

      // 3. Crear cotización
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

      // 4. Solicitar concesión para pago saliente (requiere interacción del usuario)
      const outgoingPaymentGrant = await client.grant.request(
        { url: sendingWalletAddress.authServer },
        {
          access_token: {
            access: [{
              type: "outgoing-payment",
              actions: ["read", "create"],
              limits: {
                debitAmount: {
                  assetCode: quote.debitAmount.assetCode,
                  assetScale: quote.debitAmount.assetScale,
                  value: quote.debitAmount.value,
                },
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

      // Guardar información de la transacción
      pendingTransactions.set(transactionId, {
        quote,
        incomingPayment,
        outgoingPaymentGrant,
        sendingWalletAddress,
        amount,
        currency,
        timestamp: new Date().toISOString()
      });

      ctx.body = {
        success: true,
        transactionId,
        interactionUrl: outgoingPaymentGrant.interact?.redirect,
        quote: {
          debitAmount: quote.debitAmount,
          receiveAmount: quote.receiveAmount,
          exchangeRate: quote.exchangeRate
        }
      };

    } catch (error) {
      console.error('Error iniciando pago:', error);
      ctx.status = 500;
      ctx.body = {
        success: false,
        error: error.message
      };
    }
    return;
  }
  await next();
});

// RUTA: Completar pago
app.use(async (ctx, next) => {
  if (ctx.path.startsWith('/complete-payment/') && ctx.method === 'POST') {
    try {
      const transactionId = ctx.path.split('/')[2];
      const { interact_ref } = ctx.request.body;

      console.log('Completando pago:', { transactionId, interact_ref });

      const transaction = pendingTransactions.get(transactionId);
      if (!transaction) {
        ctx.status = 404;
        ctx.body = { success: false, error: 'Transacción no encontrada' };
        return;
      }

      // Continuar con la concesión usando interact_ref
      const finalizedOutgoingPaymentGrant = await client.grant.continue({
        url: transaction.outgoingPaymentGrant.continue.uri,
        accessToken: transaction.outgoingPaymentGrant.continue.access_token.value,
        interactRef: interact_ref
      });

      if (!isFinalizedGrant(finalizedOutgoingPaymentGrant)) {
        throw new Error("No se pudo finalizar la concesión del pago saliente");
      }

      // Crear el pago saliente
      const outgoingPayment = await client.outgoingPayment.create(
        {
          url: transaction.sendingWalletAddress.resourceServer,
          accessToken: finalizedOutgoingPaymentGrant.access_token.value,
        },
        {
          walletAddress: transaction.sendingWalletAddress.id,
          quoteId: transaction.quote.id,
        }
      );

      // Limpiar transacción pendiente
      pendingTransactions.delete(transactionId);

      console.log('Pago completado exitosamente:', outgoingPayment.id);

      ctx.body = {
        success: true,
        paymentId: outgoingPayment.id,
        status: outgoingPayment.status,
        sentAmount: outgoingPayment.sentAmount,
        receivedAmount: outgoingPayment.receivedAmount
      };

    } catch (error) {
      console.error('Error completando pago:', error);
      ctx.status = 500;
      ctx.body = {
        success: false,
        error: error.message
      };
    }
    return;
  }
  await next();
});

// RUTA: Obtener estado de transacción
app.use(async (ctx, next) => {
  if (ctx.path.startsWith('/transaction-status/') && ctx.method === 'GET') {
    const transactionId = ctx.path.split('/')[2];
    const transaction = pendingTransactions.get(transactionId);
    
    if (!transaction) {
      ctx.status = 404;
      ctx.body = { success: false, error: 'Transacción no encontrada' };
      return;
    }

    ctx.body = {
      success: true,
      transactionId,
      status: 'pending',
      amount: transaction.amount,
      currency: transaction.currency,
      timestamp: transaction.timestamp
    };
    return;
  }
  await next();
});

// Middleware de manejo de errores
app.on('error', (err, ctx) => {
  console.error('Error en servidor de pagos:', err);
});

// Inicializar servidor
async function startServer() {
  await initializeClient();
  
  app.listen(PORT, () => {
    console.log(`Servicio de pagos Open Payments ejecutándose en http://localhost:${PORT}`);
    console.log(`Integrado con Flask en http://127.0.0.1:5000`);
  });
}

startServer().catch(console.error);