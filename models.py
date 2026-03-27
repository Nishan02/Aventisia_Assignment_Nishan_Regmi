from pydantic import BaseModel
from typing import Optional

class IssueCreate(BaseModel):
    title: str
    body: Optional[str] = None

class PullRequestCreate(BaseModel):
    title: str
    head: str  # The branch you are pulling FROM (e.g., "feature-branch")
    base: str  # The branch you are pulling INTO (e.g., "main")
    body: Optional[str] = None