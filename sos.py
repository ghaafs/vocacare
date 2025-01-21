import os
from twilio.rest import Client

account_sid = os.getenv("account_sid")
auth_token = os.getenv("auth_token")
client = Client(account_sid, auth_token)

message = client.messages.create(
  from_='whatsapp:+14155238886',
  content_sid='HXcbb3da70a852d2593972b7b122bd1f46',
  content_variables='{"1":"12/1","2":"3pm"}',
  to='whatsapp:+6281513365871'
)

print(message.sid)
