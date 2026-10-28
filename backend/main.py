import os
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import types
from schemas import ComplianceExtraction, VerificationResult
from rules_engine import run_statutory_audit

app = FastAPI(title="Vertical Compliance Foundation Engine", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "compliance-core"}

@app.post("/api/v1/audit-invoice", response_model=VerificationResult)
async def audit_invoice(file: UploadFile = File(...)):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured on server.")

    contents = await file.read()
    client = genai.Client(api_key=api_key)

    prompt = '''
    Extract all relevant statutory invoicing fields from this document.
    Determine whether the supply is inter-state or intra-state based on the states of the GSTINs.
    Extract every line item, taxable amounts, and tax breakdowns with complete fidelity.
    '''

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(data=contents, mime_type=file.content_type or "application/pdf"),
                prompt
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ComplianceExtraction,
                temperature=0.0
            )
        )
        extracted_data = ComplianceExtraction.model_validate_json(response.text)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"LLM extraction failed: {str(e)}")

    audit_report = run_statutory_audit(extracted_data)
    return audit_report
