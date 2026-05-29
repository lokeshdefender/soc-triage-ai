from groq import Groq
import json
import os
from dotenv import load_dotenv

import streamlit as st

load_dotenv()

# Works locally with .env AND on Streamlit Cloud with secrets
api_key = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
client = Groq(api_key=api_key)

def load_prompt():
    with open("prompts/triage_prompt.txt", "r") as f:
        return f.read()

def triage_alert(alert: dict) -> dict:
    system_prompt = load_prompt()
    alert_json = json.dumps(alert, indent=2)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Triage this alert:\n\n{alert_json}"}
        ],
        temperature=0.1
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown code fences if model wraps in ```json
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    return json.loads(raw)

def triage_all(alerts: list) -> list:
    results = []
    for alert in alerts:
        try:
            triage = triage_alert(alert)
            triage["alert_id"] = alert.get("alert_id", "N/A")
            triage["original_type"] = alert.get("alert_type", "N/A")
            triage["hostname"] = alert.get("hostname", "N/A")
            results.append(triage)
            print(f"  ✓ Triaged {alert.get('alert_id')}")
        except Exception as e:
            print(f"  ✗ Error on {alert.get('alert_id')}: {str(e)}")
            results.append({
                "alert_id": alert.get("alert_id", "N/A"),
                "error": str(e),
                "severity": "ERROR"
            })
    return results

if __name__ == "__main__":
    with open("sample_alerts/alerts.json") as f:
        alerts = json.load(f)

    print(f"Triaging {len(alerts)} alerts...\n")
    results = triage_all(alerts)

    print("\n--- TRIAGE RESULTS ---\n")
    for r in results:
        print(f"[{r.get('severity')}] {r.get('alert_id')} — {r.get('summary')}")
        print(f"  Action: {r.get('recommended_action')}\n")