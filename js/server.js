const express = require('express');
const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY); 
const app = express();

app.use(express.json()); 


app.post('/create-payment-intent', async (req, res) => {
  console.log('Received request at /create-payment-intent');
  const cors = require('cors');
  app.use(cors({
    origin: 'https://coastalrisk.org'
  }));

  const { amount } = req.body;
  console.log('Amount received from frontend:', amount);
  try {
    const paymentIntent = await stripe.paymentIntents.create({
      amount: 9900,      
      currency: 'usd',
      automatic_payment_methods: { enabled: true }, 
    });
    console.log('PaymentIntent created successfully');
    res.send({
      clientSecret: paymentIntent.client_secret,
    });
  } catch (error) {
    
    res.status(500).send({ error: error.message });
  }
});

app.listen(3000, () => console.log('Server running on http://localhost:3000'));
