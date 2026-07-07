from typing import Literal
from pydantic import BaseModel, Field, field_validator


class CheckRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=20000)

    @field_validator("text")
    @classmethod
    def text_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text must not be blank or whitespace only")
        return v


class RiskItem(BaseModel):
    clause: str
    severity: str
    severity_label: str
    reason: str


class CheckResponse(BaseModel):
    id: int
    cached: bool
    risks: list[RiskItem]
