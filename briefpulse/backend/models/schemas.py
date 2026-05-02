from pydantic import BaseModel, Field


class BriefAnalyzeIn(BaseModel):
    client_name: str | None = None
    raw_brief: str = Field(..., min_length=3)


class ParsedBriefOut(BaseModel):
    sector: str | None = None
    target: str | None = None
    objective: str | None = None
    tone: str | None = None
    constraints: str | None = None
    competitors: list[str] = Field(default_factory=list)


class BriefAnalyzeOut(BaseModel):
    brief_id: int
    parsed_brief: ParsedBriefOut
    recommendations: list[dict]
