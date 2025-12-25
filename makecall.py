import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

# Configuration
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')


account_sid = TWILIO_ACCOUNT_SID
auth_token = TWILIO_AUTH_TOKEN


client = Client(account_sid, auth_token)


call = client.calls.create(
    url='https://enormous-krill-one.ngrok-free.app/webhook/voice',  # Replace with your ngrok URL
    from_="+17625720754",
    to="+923198660652",
)


print(call.sid)