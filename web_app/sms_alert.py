import os
import requests

FREE_USER = os.environ.get("FREE_USER")
FREE_PASS = os.environ.get("FREE_PASS")

def send_sms(message):
    url = f"https://smsapi.free-mobile.fr/sendmsg?user={FREE_USER}&pass={FREE_PASS}&msg={message}"
    try:
        r = requests.get(url)
        if r.status_code == 200:
            print("SMS envoyé :", message)
        else:
            print("Erreur lors de l'envoi du SMS, code :", r.status_code)
    except Exception as e:
        print("Exception lors de l'envoi du SMS :", e)
