from flask import Flask, request
import requests, os

app = Flask(__name__)

TOKEN = os.environ.get("ACCESS_TOKEN")
PHONE_ID = os.environ.get("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")

user_state = {}

@app.route("/")
def home():
    return "Pharmalabs Bot Live"

def send_message(to, text, buttons=None):
    url = f"https://graph.facebook.com/v20.0/{PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    if buttons:
        data = {"messaging_product":"whatsapp","to":to,"type":"interactive","interactive":{"type":"button","body":{"text":text},"action":{"buttons":buttons}}}
    else:
        data = {"messaging_product":"whatsapp","to":to,"type":"text","text":{"body":text}}
    resp = requests.post(url, headers=headers, json=data)
    print(f"SEND TO {to} STATUS {resp.status_code} RESPONSE {resp.text}")
    return resp

@app.route("/webhook", methods=["GET"])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Failed", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print(f"INCOMING: {data}")
    try:
        entry = data['entry'][0]['changes'][0]['value']
        if 'messages' in entry:
            msg = entry['messages'][0]
            from_number = msg['from']
            text = msg.get('text',{}).get('body','').lower()
            button = msg.get('interactive',{}).get('button_reply',{}).get('id','')
            print(f"FROM {from_number} TEXT {text} BUTTON {button}")
            state = user_state.get(from_number,"START")

            if state == "START":
                send_message(from_number,"Assalam-o-Alaikum! Pharmalabs here Rs.2199 Free Delivery COD\nKya chahiye?",[{"type":"reply","reply":{"id":"price","title":"Price?"}},{"type":"reply","reply":{"id":"order","title":"Order"}}])
                user_state[from_number]="ASK_INTENT"
            elif "price" in text or button=="price":
                send_message(from_number,"Price Rs.2199 Free Delivery - Order?",[{"type":"reply","reply":{"id":"order","title":"Yes Order"}}])
            elif "order" in text or button=="order" or state=="ASK_INTENT":
                send_message(from_number,"Naam bhej dein?")
                user_state[from_number]="ASK_NAME"
            elif state=="ASK_NAME":
                user_state[from_number+"_name"]=text
                send_message(from_number,f"Shukriya {text}! City?")
                user_state[from_number]="ASK_CITY"
            elif state=="ASK_CITY":
                user_state[from_number+"_city"]=text
                send_message(from_number,"Full Address?")
                user_state[from_number]="ASK_ADDRESS"
            elif state=="ASK_ADDRESS":
                name=user_state.get(from_number+"_name","")
                city=user_state.get(from_number+"_city","")
                print(f"NEW ORDER: {name} {from_number} {city} {text}")
                send_message(from_number,f"Done {name}! Order Confirmed {city} {text} Rs.2199 COD - 2 din me TCS")
                user_state[from_number]="DONE"
    except Exception as e:
        print(f"ERROR {e}")
    return "OK",200
