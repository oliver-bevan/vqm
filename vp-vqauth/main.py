import os
import random
import stripe
from google.cloud import secretmanager
from google.cloud import firestore

#Get necessary keys
def get_keys(key_names):
    project_id = os.environ["GCP_PROJECT"]
    client = secretmanager.SecretManagerServiceClient()

    keys = []

    for key_name in key_names:
        resource_name = f"projects/{project_id}/secrets/{key_name}/versions/latest"
        response = client.access_secret_version(resource_name)

        keys.append(response.payload.data.decode("UTF-8"))
        return keys

keys = get_keys([os.environ["WHSEC"], os.environ["PAYKEY"]])

stripe.api_key = keys[1]

def process_payment(request):
    #Verify payment:
    signing_header = request.headders("http-stripe-signature")
    request_data = request.get_json()

    try:
        event = stripe.Webhook.construct_event(request_data, signing_header, keys[1])
    except ValueError:
        return "Bad Request: Unexpected", 400
    except stripe.error.SignatureVerificationError:
        return "Unauthorized: Cannot verify signature", 401

    if event.type == "checkout.session.completed":
        checkout_session = event["data"]["object"]

        if checkout_session["display_items"]["sku"]["id"] == os.environ["PRODSKU"]:
            customer_id = stripe.Customer.retrieve(checkout_session["customer"])
            payment_id = checkout_session["payment_intent"]
            
            mint_key(payment_id, customer_id)

        else:
            return "SKU not valid for this service, however request was recieved.", 205
    else:
        return "Unexpected Even.t", 402

    return "Key Created.", 201

def mint_key(payment_id, customer_id):
    database = firestore.Client()
    keys_ref = database.collection("otkeys").document(os.environ["KEY_STORE_DOCUMENT"])
    
    keys_file = keys_ref.get()

    if not keys_file.exists:
        keys_ref.set({"creation": firestore.SERVER_TIMESTAMP, "valid": True})

    key_taken = True

    while key_taken:
        key = int(str(random.randrange(1, 10 ** int(os.environ["KEY_LENGTH"]))).zfill(int(os.environ["KEY_LENGTH"])))

        key_ref = keys_ref.collection("keys").document(key)
        key_file = key_ref.get()

        if not key_file.exists:
            key_taken = False
    
    customer = stripe.Customer.retrieve(customer_id)
    key_data = {
        "customer_id": customer["id"],
        "customer_email": customer["email"],
        "payment_id": payment_id,
        "valid": True
    }

    key_ref.set(key_data)