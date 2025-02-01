// Load Stripe public key from the backend
async function getStripePublicKey() {
    const response = await fetch("/get-stripe-public-key");
    const data = await response.json();
    return data.publicKey;
}

getStripePublicKey().then(publicKey => {
    if (!publicKey) {
        console.error("Failed to load Stripe public key");
        return;
    }

    const stripe = Stripe(publicKey);
    const elements = stripe.elements();
    const card = elements.create("card");
    card.mount("#card-element");

    // Handle form submission
    document.getElementById("payment-form").addEventListener("submit", async (event) => {
        event.preventDefault();

        // Disable button to prevent multiple clicks
        const submitButton = document.getElementById("submit-button");
        submitButton.disabled = true;

        // Request payment intent from backend
        const response = await fetch("/create-payment-intent", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ amount: 3900 }) // $39.00 in cents
        });

        const { clientSecret } = await response.json();

        // Confirm the payment with Stripe
        const { error, paymentIntent } = await stripe.confirmCardPayment(clientSecret, {
            payment_method: { card: card }
        });

        if (error) {
            console.error("Payment failed:", error);
            document.getElementById("payment-error").innerText = error.message;
            submitButton.disabled = false; // Re-enable button if error
        } else {
            console.log("Payment successful!", paymentIntent);
            window.location.href = "/success"; // Redirect on success
        }
    });
});
