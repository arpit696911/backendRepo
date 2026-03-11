import os
from typing import Annotated
from io import StringIO, BytesIO

import pandas as pd
from dotenv import load_dotenv
from email_validator import validate_email, EmailNotValidError

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ai_service import generate_summary
from email_service import send_email


load_dotenv()

app = FastAPI(
    title="Sales Insight Automator",
    description="Upload a sales CSV/XLSX file and receive AI-generated insights by email.",
    version="1.0.0",
)

# -----------------------------
# CORS CONFIGURATION
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# FILE SIZE LIMIT
# -----------------------------
MAX_UPLOAD_SIZE_MB = 5
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024


@app.middleware("http")
async def upload_size_limit(request: Request, call_next):
    content_length = request.headers.get("content-length")

    if content_length:
        size = int(content_length)
        if size > MAX_UPLOAD_SIZE_BYTES:
            return JSONResponse(
                status_code=413,
                content={"detail": f"File too large. Max size {MAX_UPLOAD_SIZE_MB}MB"},
            )

    return await call_next(request)


# -----------------------------
# ANALYZE ENDPOINT
# -----------------------------
@app.post("/analyze")
async def analyze_sales(
    file: Annotated[UploadFile, File()],
    email: Annotated[str, Form()],
):
    # Validate email
    try:
        email = validate_email(email).email
    except EmailNotValidError as e:
        raise HTTPException(status_code=400, detail=str(e))

    filename = file.filename.lower()

    if not (filename.endswith(".csv") or filename.endswith(".xlsx")):
        raise HTTPException(
            status_code=400,
            detail="Only CSV or XLSX files are allowed",
        )

    # Parse file
    try:
        contents = await file.read()

        if filename.endswith(".csv"):
            df = pd.read_csv(StringIO(contents.decode("utf-8", errors="ignore")))
        else:
            df = pd.read_excel(BytesIO(contents))

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"File parsing error: {e}")

    if df.empty:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    # Generate AI summary
    try:
        summary = generate_summary(df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI summary failed: {e}")

    # Send email
    try:
        send_email(email, summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email sending failed: {e}")

    return {
        "message": "Analysis completed and email sent successfully",
        "email": email,
    }


# -----------------------------
# HEALTH CHECK
# -----------------------------
@app.get("/health")
async def health():
    return {"status": "ok"}