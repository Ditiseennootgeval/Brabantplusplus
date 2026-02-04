import requests
import re
import json
import os
from bs4 import BeautifulSoup
from datetime import datetime
import pytz
import smtplib
from email.message import EmailMessage

BASE_URL = "https://www.brabantplus.nl"
SEARCH_WORD = "Roeptoetgat"
STATE_FILE = "state.json"

# Email config (via GitHub Secrets)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_FROM = os.environ["EMAIL_FROM"]
EMAIL_TO = os.environ["EMAIL_TO"]
EMAIL_PASSWORD = os.environ["EMAIL_PASSWORD"]

tz = pytz.timezone("Europe/Amsterdam")
now = datetime.now(tz)

# Alleen zoeken tussen 08:00 en 21:00
if not (8 <= now.hour < 21):
    print("Buiten zoektijd")
    exit(0)

today = now.strftime("%Y-%m-%d")

# Status lezen
state = {}
if os.path.exists(STATE_FILE):
    with open(STATE_FILE) as f:
        state = json.load(f)

if state.get("found_date") == today:
    print("Vandaag al gevonden, stoppen")
    exit(0)

def send_email(programma, seizoen, aflevering, url):
    msg = EmailMessage()
    msg["Subject"] = "Roeptoetgat gevonden!"
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    msg.set_content(
        f"""Het woord Roeptoetgat is gevonden.

Programma: {programma}
Seizoen: {seizoen}
Aflevering: {aflevering}
URL: {url}
"""
    )

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as s:
        s.starttls()
        s.login(EMAIL_FROM, EMAIL_PASSWORD)
        s.send_message(msg)

def crawl():
    visited = set()
    to_visit = [BASE_URL]

    while to_visit:
        url = to_visit.pop()
        if url in visited:
            continue

        visited.add(url)
        print("Bezoek:", url)

        try:
            r = requests.get(url, timeout=10)
        except:
            continue

        if SEARCH_WORD.lower() in r.text.lower():
            soup = BeautifulSoup(r.text, "html.parser")
            text = soup.get_text(" ")

            programma = re.search(r"(Brabant Nieuws|.+?)", text)
            seizoen = re.search(r"Seizoen\s*(\d{4})", text)
            aflevering = re.search(r"Aflevering\s*(\d+)", text)

            send_email(
                programma.group(1) if programma else "Onbekend",
                seizoen.group(1) if seizoen else "Onbekend",
                aflevering.group(1) if aflevering else "Onbekend",
                url
            )

            with open(STATE_FILE, "w") as f:
                json.dump({"found_date": today}, f)

            print("Gevonden! Stoppen voor vandaag.")
            exit(0)

        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True):
            link = a["href"]
            if link.startswith("/"):
                link = BASE_URL + link
            if link.startswith(BASE_URL):
                to_visit.append(link)

crawl()

