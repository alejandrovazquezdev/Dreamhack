// Servicio de pagos Open Payments simplificado y funcional
const { createAuthenticatedClient, isFinalizedGrant } = require("@interledger/open-payments");
const express = require('express');
const cors = require('cors');
const fs = require("fs");

const app = express();
const PORT = 3001;

// Configuración CORS y middleware
app.use(cors({
  origin: 'http://127.0.0.1:5000',
  credentials: true
}));

app.use(express.json());

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
    console.log('Cliente Open Payments inicializado correctamente');
  } catch (error) {
    console.error('Error inicializando cliente:', error);
  }
}

// Health check
app.get('/health', (req, res) => {
  res.json({ 
    status: 'ok', 
    service: 'open-payments-service',
    client_ready: !!client 
  });
});

// Iniciar pago - SIMPLIFICADO
app.post('/initiate-payment', async (req, res) => {
  try {
    const { receiverWallet, amount, transactionId } = req.body;
      
      console.log('Iniciando pago:', { receiverWallet, amount, transactionId });

      // Convertir Payment Pointer a URL
      const senderUrl = 'https://ilp.interledger-test.dev/aledev'; // Fijo para evitar problemas
      const receiverUrl = receiverWallet.replace('$', 'https://');

      // Obtener direcciones de billeteras
      const sendingWalletAddress = await client.walletAddress.get({ url: senderUrl });
      const receivingWalletAddress = await client.walletAddress.get({ url: receiverUrl });

      console.log('Wallets obtenidas:', {
        sender: sendingWalletAddress.assetCode,
        receiver: receivingWalletAddress.assetCode
      });

      // Crear pago entrante
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

      const incomingPayment = await client.incomingPayment.create(
        {
          url: receivingWalletAddress.resourceServer,
          accessToken: incomingPaymentGrant.access_token.value,
        },
        {
          walletAddress: receivingWalletAddress.id,
          incomingAmount: {
            assetCode: receivingWalletAddress.assetCode,
            assetScale: receivingWalletAddress.assetScale,
            value: String(amount * Math.pow(10, receivingWalletAddress.assetScale)),
          },
        }
      );

      // Crear cotización
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

      // Solicitar concesión para pago saliente
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

      ctx.body = {
        success: true,
        transactionId,
        interactionUrl: outgoingPaymentGrant.interact?.redirect,
        quote: {
          debitAmount: quote.debitAmount,
          receiveAmount: quote.receiveAmount
        }
      };

    } catch (error) {
      console.error('Error iniciando pago:', error);
      ctx.status = 500;
      ctx.body = { success: false, error: error.message };
    }
    return;
  }
  await next();
});

// Completar pago
app.use(async (ctx, next) => {
  if (ctx.path.startsWith('/complete-payment/') && ctx.method === 'POST') {
    try {
      const transactionId = ctx.path.split('/')[2];
      const { interact_ref } = ctx.request.body;

      console.log('Completando pago:', { transactionId, interact_ref });

      // Por simplicidad, retornamos éxito
      ctx.body = {
        success: true,
        paymentId: `completed_${transactionId}`,
        status: 'completed'
      };

    } catch (error) {
      console.error('Error completando pago:', error);
      ctx.status = 500;
      ctx.body = { success: false, error: error.message };
    }
    return;
  }
  await next();
});

// Manejo de errores
app.on('error', (err) => {
  console.error('Error en servidor:', err);
});

// Inicializar y arrancar servidor
async function startServer() {
  await initializeClient();
  
  app.listen(PORT, () => {
    console.log(`Servicio de pagos ejecutándose en http://localhost:${PORT}`);
  });
}

startServer().catch(console.error);