from pydantic import BaseModel, Field


class KBArticle(BaseModel):
    """A single knowledge base article."""

    id: str = Field(description="Unique article identifier")
    title: str = Field(description="Article title")
    body: str = Field(description="Article content")


class KnowledgeBase(BaseModel):
    """Collection of knowledge base articles."""

    articles: list[KBArticle]
