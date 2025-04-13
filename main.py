from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import requests
import smtplib
import json
import os
import logging
from email.message import EmailMessage

# === Setup Logging ===
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/app.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# === Load Reference Table ===
REFERENCE_TABLE = []
try:
    with open("reference_table.json", "r") as f:
        REFERENCE_TABLE = json.load(f)
except FileNotFoundError:
    logging.error("reference_table.json not found!")
    raise Exception("reference_table.json not found!")

# === Configs (can be moved to a separate config.py or use dotenv) ===
SPLUNK_HEC_URL = os.getenv("SPLUNK_HEC_URL", "https://splunk-host:8088/services/collector")
SPLUNK_TOKEN = os.getenv("SPLUNK_TOKEN", "Your-Splunk-Token")
EMAIL_TO = os.getenv("EMAIL_TO", "someone@example.com")
EMAIL_FROM = os.getenv("EMAIL_FROM", "alerts@example.com")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.example.com")

# === FastAPI Init ===
app = FastAPI()

# === Pydantic Model ===
class AlertPayload(BaseModel):
    error: str
    error_code: int
    monitor_type: str

# === Helpers ===
def get_day_type():
    return "weekday" if datetime.now().weekday() < 5 else "weekend"

def find_destination(monitor_type: str, daytype: str):
    for row in REFERENCE_TABLE:
        if row["monitor_type"] == monitor_type and row["daytype"] == daytype:
            return row["destination"]
    return None

def load_email_template(file_path: str, data: dict) -> str:
    try:
        with open(file_path, "r") as f:
            template = f.read()
            for key, value in data.items():
                template = template.replace(f"{{{{{key}}}}}", str(value))
            return template
    except Exception as e:
        logging.error(f"Failed to load email template: {str(e)}")
        raise

def send_email(subject: str, body: str):
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = EMAIL_FROM
        msg["To"] = EMAIL_TO
        msg.set_content(body)

        with smtplib.SMTP(SMTP_SERVER) as server:
            server.send_message(msg)
        logging.info("Email sent successfully.")
    except Exception as e:
        logging.error(f"Email sending failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Email failed: {str(e)}")

def send_to_splunk(payload: dict):
    headers = {
        "Authorization": f"Splunk {SPLUNK_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "event": payload,
        "sourcetype": "_json"
    }
    try:
        response = requests.post(SPLUNK_HEC_URL, headers=headers, json=data)
        if response.status_code != 200:
            raise Exception(response.text)
        logging.info("Event sent to Splunk.")
    except Exception as e:
        logging.error(f"Splunk sending failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send to Splunk: {str(e)}")

# === API Endpoint ===
@app.post("/alert")
def handle_alert(payload: AlertPayload):
    daytype = get_day_type()
    destination = find_destination(payload.monitor_type, daytype)

    if not destination:
        logging.warning(f"No destination for monitor_type={payload.monitor_type}, daytype={daytype}")
        raise HTTPException(status_code=404, detail="No destination found for given monitor_type and daytype")

    # Create template context
    context = {
        "error": payload.error,
        "error_code": payload.error_code,
        "monitor_type": payload.monitor_type,
        "daytype": daytype,
        "timestamp": datetime.now().isoformat()
    }

    if destination == "email":
        body = load_email_template("templates/alert_email.txt", context)
        send_email(subject=f"[ALERT] {payload.monitor_type}", body=body)
    elif destination == "splunk":
        send_to_splunk(payload.dict())
    else:
        logging.error(f"Unsupported destination: {destination}")
        raise HTTPException(status_code=400, detail="Unsupported destination type")

    logging.info(f"Alert processed for {payload.monitor_type} -> {destination}")
    return {"status": "processed", "destination": destination}
