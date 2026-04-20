from pydantic import BaseModel, Field


class GenerateAdInput(BaseModel):
    job_id: str = Field(min_length=1)
    mode: str = Field(pattern=r"^(ugc|pro_arc|tv)$")


class GenerateAdResult(BaseModel):
    job_id: str
    status: str
    message: str


class RenderUnitInput(BaseModel):
    job_id: str = Field(min_length=1)
    unit_sequence: int = Field(ge=0)


class RenderUnitResult(BaseModel):
    job_id: str
    unit_sequence: int
    status: str

