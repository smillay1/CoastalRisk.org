const stripe = require('pk_live_51QHBJ6HqTa92s2ZvyoFNByzoLlnAYIZEzKC6BIm8bucP9c1AkjrF1gA6TnNMEC5GEbFGMXXAgzbmy2OjeYfDwhbi00ruaHJMvi');
const cors = require('cors');
const app = express();

app.use(express.json());
app.use(cors({
    origin: 'https://coastalrisk.org' 
}));

app.post('/create-payment-intent', async (req, res) => {
    console.log('Received request at /create-payment-intent');
    
    const { amount } = req.body;  
    console.log('Amount received from frontend:', amount);

    try {
        const paymentIntent = await stripe.paymentIntents.create({
            amount: amount,  
            currency: 'usd',  
            automatic_payment_methods: { enabled: true }, 
        });
        console.log('PaymentIntent created successfully');
        
        res.send({
            clientSecret: paymentIntent.client_secret,
        });
    } catch (error) {
        console.error('Error creating payment intent:', error);
        res.status(500).send({ error: error.message });
    }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on http://localhost:${PORT}`));
