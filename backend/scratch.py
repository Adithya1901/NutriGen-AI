from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

response = client.post("/families/1/multi-daily-plan", json={
    "dates": ["2026-04-24"],
    "meals": ["Breakfast"],
    "budget": "Medium"
})

print("STATUS:", response.status_code)
print("BODY:", response.text)
