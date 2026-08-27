from typing import Literal, Optional

from pydantic import BaseModel, field_validator

from backend.models.collection import CollectionItemOut


class WebSearchRequest(BaseModel):
    engine: Literal["tavily", "exa"]
    query: str
    num_results: int = 10
    search_depth: Optional[str] = "basic"  # tavily only

    @field_validator("query")
    @classmethod
    def query_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Query cannot be empty.")
        return v


class WebSearchResult(BaseModel):
    url: str
    title: str = ""
    content: str = ""


class WebSearchResponse(BaseModel):
    results: list[WebSearchResult]


class ManualUrlAdd(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def url_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("URL cannot be empty.")
        return v


class SearchResultItem(BaseModel):
    url: str
    title: str = ""
    content: str


class AddSearchResults(BaseModel):
    items: list[SearchResultItem]

    @field_validator("items")
    @classmethod
    def items_not_empty(cls, v: list[SearchResultItem]) -> list[SearchResultItem]:
        if not v:
            raise ValueError("Select at least one result to add.")
        return v


class AddSearchResultsResponse(BaseModel):
    added: list[CollectionItemOut]
    skipped: list[str]  # URLs skipped because they already exist in the collection