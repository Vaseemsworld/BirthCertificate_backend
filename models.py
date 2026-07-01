from datetime import date
from pydantic import BaseModel, Field, field_validator


class DragonCreate(BaseModel):
    child_name: str = Field(..., min_length=1, max_length=150)
    dob: date
    gender: str = Field(..., min_length=1, max_length=50)
    father_name: str = Field(..., min_length=1, max_length=150)
    mother_name: str = Field(..., min_length=1, max_length=150)
    place_of_birth: str = Field(..., min_length=1, max_length=200)
    signer_name: str = Field(..., min_length=1, max_length=150)

    @field_validator("dob")
    @classmethod
    def dob_not_in_future(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("Date of birth cannot be in the future")
        return v


class DragonOut(BaseModel):
    token: str
    registration_number: str
    child_name: str
    dob: date
    gender: str
    mother_name: str
    father_name: str
    place_of_birth: str
    signer_name: str
    created_at: str


class DragonCreateResponse(BaseModel):
    token: str
    registration_number: str
    record_url: str
    qr_code_base64: str
