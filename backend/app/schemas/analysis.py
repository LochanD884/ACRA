from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl


class AnalysisCreate(BaseModel):
    thread_name: str | None = Field(default=None, min_length=1, max_length=120)
    repo_url: HttpUrl
    pr_number: int | None = Field(default=None, ge=1)
    github_token: str | None = None
    allow_git_clone: bool = False


class IssueOut(BaseModel):
    id: int
    file_path: str
    line_start: int | None
    line_end: int | None
    severity: str
    category: str
    message: str
    recommendation: str | None

    class Config:
        from_attributes = True


class AnalysisOut(BaseModel):
    id: int
    repo_url: str
    pr_number: int | None
    status: str
    progress: int
    summary: str | None
    quality_score: int | None
    extra_metadata: dict | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AnalysisDetail(AnalysisOut):
    issues: list[IssueOut] = []


class AnalysisList(BaseModel):
    items: list[AnalysisOut]
