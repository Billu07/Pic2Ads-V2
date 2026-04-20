from pydantic import BaseModel, Field


class ProductIntelInput(BaseModel):
    product_name: str = Field(min_length=1, max_length=200)
    product_image_url: str = Field(min_length=1, max_length=2000)


class ProductIntelOutput(BaseModel):
    category_primary: str
    category_sub: str
    price_tier: str
    primary_colors: list[str] = Field(default_factory=list, max_length=3)
    affordances: list[str] = Field(default_factory=list, max_length=6)
    visible_claims: list[str] = Field(default_factory=list, max_length=6)
    unknowns: list[str] = Field(default_factory=list, max_length=6)


class ProductIntelRunResponse(BaseModel):
    job_id: str
    cached: bool
    agent_name: str
    prompt_version: str
    output: ProductIntelOutput

