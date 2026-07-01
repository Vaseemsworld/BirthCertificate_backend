import os
import base64
from datetime import date, datetime

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from database import supabase
from models import DragonCreate, DragonOut, DragonCreateResponse
from tokens import generate_token
from qr import generate_qr_base64
from registration import generate_registration_number

load_dotenv()

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")

app = FastAPI(title="Child Registration System API")

origins = [
    "http://localhost:5173",
    "https://birth-certificate-frontend-orpin.vercel.app",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _serialize(record: dict) -> dict:
    """Make sure date/datetime fields are JSON-friendly strings."""
    out = dict(record)
    if isinstance(out.get("dob"), (date, datetime)):
        out["dob"] = out["dob"].isoformat()
    if isinstance(out.get("created_at"), (date, datetime)):
        out["created_at"] = out["created_at"].isoformat()
    return out


@app.get("/")
def root():
    return {"status": "ok", "service": "Child Registration System"}


@app.post("/api/childs/", response_model=DragonCreateResponse)
def create_dragon(payload: DragonCreate):
    print("inside create dragon saregama opadenisa hfdjhfkjdh")
    data = payload.model_dump()
    print("DEBUG PAYLOAD:", data)
    data["dob"] = data["dob"].isoformat()

    token = generate_token()
    registration_no = generate_registration_number()

    # Retry a few times on the rare token collision
    last_error = None
    for _ in range(5):
        try:
            data["token"] = token
            data["registration_number"] = registration_no
            result = supabase.table("childs").insert(data).execute()
            if not result.data:
                raise RuntimeError("Insert returned no data")
            break
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            # if it's a unique violation, regenerate and retry; otherwise bail
            if "duplicate" in str(exc).lower() or "unique" in str(exc).lower():
                token = generate_token()
                registration_no = generate_registration_number()

                continue
            raise HTTPException(status_code=500, detail=f"Failed to save record: {exc}")
    else:
        raise HTTPException(
            status_code=500, detail=f"Failed to save record: {last_error}"
        )

    record_url = f"{FRONTEND_URL}/r/{token}"
    qr_b64 = generate_qr_base64(record_url)

    return DragonCreateResponse(
        token=token,
        record_url=record_url,
        qr_code_base64=qr_b64,
        registration_number=registration_no,
    )


@app.get("/api/childs/{token}", response_model=DragonOut)
def get_dragon(token: str):
    result = supabase.table("childs").select("*").eq("token", token).execute()
    if not result.data:
        raise HTTPException(
            status_code=404, detail="No Child found with this record number"
        )

    record = _serialize(result.data[0])
    return DragonOut(**record)


@app.get("/api/childs/{token}/qr")
def get_dragon_qr(token: str):
    # confirm the record exists before generating a code for it
    result = supabase.table("childs").select("token").eq("token", token).execute()
    if not result.data:
        raise HTTPException(
            status_code=404, detail="No Child found with this record number"
        )

    record_url = f"{FRONTEND_URL}/r/{token}"
    qr_b64 = generate_qr_base64(record_url)
    png_bytes = base64.b64decode(qr_b64)
    return Response(content=png_bytes, media_type="image/png")
