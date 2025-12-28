from pydantic import BaseModel, Field

class PaginatorData(BaseModel):
    limit: int = Field(6, ge=0, le=100)
    offset: int = Field(0, ge=0)
    