import os

from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()
client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))

call = client.calls.create(
    to=os.getenv("MY_MOBILE"),
    from_=os.getenv("TWILIO_FROM"),
    url=os.getenv("PUBLIC_URL") + "/voice",
)
print(call.sid)
