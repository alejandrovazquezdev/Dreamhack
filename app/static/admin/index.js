// Tutorial del cliente de Open Payments
// Objetivo: Realizar un pago entre pares entre dos direcciones de billetera (usando cuentas en la cuenta de prueba)

// https://ilp.interledger-test.dev/aledev - cliente
// https://ilp.interledger-test.dev/aliciadev - remitente
// https://ilp.interledger-test.dev/bobdev - receptor

// Configuración inicial
import { createAuthenticatedClient, isFinalizedGrant, OpenPaymentsClientError } from "@interledger/open-payments";
import fs from "fs";
import readline from "readline/promises";

async function main() {
// a. Importar dependencias y configurar el cliente
const privateKey = fs.readFileSync('private.key', 'utf-8')

// Instanciar el cliente autenticado
const client = await createAuthenticatedClient({
  walletAddressUrl: 'https://ilp.interledger-test.dev/aledev',
  privateKey: privateKey,
  keyId: '30c571c4-3941-4221-8206-92eb2bedd81b'
});
// b. Crear una instancia del cliente Open Payments
// c. Cargar la clave privada del archivo
// d. Configurar las direcciones de las billeteras del remitente y el receptor
// Flujo de pago entre pares

// 1. Obtener una concesiÃ³n para un pago entrante)
  const sendingWalletAddress = await client.walletAddress.get({
    url: "https://ilp.interledger-test.dev/aliciadev", // Make sure the wallet address starts with https:// (not $)
  });
  const receivingWalletAddress = await client.walletAddress.get({
    url: "https://ilp.interledger-test.dev/bobdev", // Make sure the wallet address starts with https:// (not $)
  });

  console.log(sendingWalletAddress, receivingWalletAddress);

// 2. Obtener una concesion para un pago entrante
  const incomingPaymentGrant = await client.grant.request(
    {
      url: receivingWalletAddress.authServer,
    },
    {
      access_token: {
        access: [
          {
            type: "incoming-payment",
            actions: ["read", "complete", "create"],
          },
        ],
      },
    }
  );


    if (!isFinalizedGrant(incomingPaymentGrant)) {
        throw new Error("se espera que finalize la consesion");
  }

  console.log(incomingPaymentGrant);

// 3. Crear un pago entrante para el receptor
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
        value: "1000", //aqui son 10 dolares
      },
    }
  );

  console.log(incomingPayment);


// 4. Crear un concesión para una cotización

  const quoteGrant = await client.grant.request(
    {
      url: sendingWalletAddress.authServer,
    },
    {
      access_token: {
        access: [
          {
            type: "quote",
            actions: ["create", "read"],
          },
        ],
      },
    }
  );
  if(!isFinalizedGrant(quoteGrant)){
    throw new Error("Se espera finalice la concesion");
  }

    console.log(quoteGrant);
  


// 5. Obtener una cotización para el remitente

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

  console.log({quote});


// 6. Obtener una concesión para un pago saliente

const outgoingPaymentGrant = await client.grant.request(
    {
      url: sendingWalletAddress.authServer,
    },
    {
      access_token: {
        access: [
          {
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
          },
        ],
      },
      interact: {
        start: ["redirect"],
        // finish: {
        //   method: "redirect",
        //   // This is where you can (optionally) redirect a user to after going through interaction.
        //   // Keep in mind, you will need to parse the interact_ref in the resulting interaction URL,
        //   // and pass it into the grant continuation request.
        //   uri: "https://example.com",
        //   nonce: crypto.randomUUID(),
        // },
      },
    }
  );

  console.log({outgoingPaymentGrant});



// 7. Continuar con la concesión del pago saliente

  await readline
    .createInterface({ input: process.stdin, output: process.stdout })
    .question("Presiona Enter para continuar con el pago saliente...");

  let finalizedOutgoingPaymentGrant;




// 8. Finalizar la concesión del pago saliente

const grantContinuationErrorMessage = "\nThere was an error continuing the grant. You probably have not accepted the grant at the url (or it has already been used up, in which case, rerun the script).";

  try {
    finalizedOutgoingPaymentGrant = await client.grant.continue({
      url: outgoingPaymentGrant.continue.uri,
      accessToken: outgoingPaymentGrant.continue.access_token.value,
    });
  } catch (err) {
    if (err instanceof OpenPaymentsClientError) {
      console.log(grantContinuationErrorMessage);
      process.exit();
    }

    throw err;
  }

  if (!isFinalizedGrant(finalizedOutgoingPaymentGrant)) {
    console.log( "Se espera que finalize la concesion.");
    process.exit();
  }


// 9. Continuar con la cotización de pago saliente
const outgoingPayment = await client.outgoingPayment.create(
    {
      url: sendingWalletAddress.resourceServer,
      accessToken: finalizedOutgoingPaymentGrant.access_token.value,
    },
    {
      walletAddress: sendingWalletAddress.id,
      quoteId: quote.id,
    }
  );

  console.log(outgoingPayment);

  process.exit();
}

// Ejecutar la función principal
main().catch(console.error);


