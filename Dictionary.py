from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class Dictionary(BaseModel):
    name: str = Field(include=True)
    url: str = Field(include=True)
    answer: str = Field(include=True)
    keywords: list[str] = Field(include=False)
    is_run: bool = Field(default=True, include=False)


dictionary_list: list[Dictionary] = []
