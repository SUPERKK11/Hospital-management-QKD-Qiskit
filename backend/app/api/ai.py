import os
import requests
from fastapi import APIRouter
from pydantic import BaseModel
from app.core.config import settings

router = APIRouter()

# --- CONFIG ---
HF_API_TOKEN = os.getenv("HF_TOKEN")
AI_URL = "https://router.huggingface.co/models/facebook/bart-large-mnli"

class DiagnosisRequest(BaseModel):
    diagnosis_text: str

@router.post("/predict-department")
async def predict_department(request: DiagnosisRequest):
    """
    Analyzes diagnosis text and suggests a hospital department.
    """
    if not HF_API_TOKEN:
        return {"recommended_department": "Error: HF_TOKEN missing in .env", "confidence": 0}

    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    candidate_labels = ["Cardiology", "Neurology", "Orthopedics", "General Medicine", "Pediatrics", "Dermatology", "Psychiatry"]
    payload = {"inputs": request.diagnosis_text, "parameters": {"candidate_labels": candidate_labels}}

    try:
        response = requests.post(AI_URL, headers=headers, json=payload)
        data = response.json()
        
        if "error" in data:
            return {"recommended_department": f"HF Error: {data['error']}", "confidence": 0}

        return {
            "recommended_department": data['labels'][0],
            "confidence": round(data['scores'][0] * 100, 1)
        }
    except Exception as e:
        print(f"❌ CRITICAL AI ERROR: {e}")
        return {"recommended_department": f"Backend Error: {str(e)}", "confidence": 0}