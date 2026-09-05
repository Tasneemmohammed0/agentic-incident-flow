from pydantic import BaseModel, Field


class KBArticle(BaseModel):
    """A single knowledge base article."""

    id: int
    text: str


class KnowledgeBase(BaseModel):
    """Collection of knowledge base articles."""

    articles: list[KBArticle]
