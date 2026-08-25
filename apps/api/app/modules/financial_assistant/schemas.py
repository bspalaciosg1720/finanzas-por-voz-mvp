from pydantic import BaseModel, ConfigDict, Field


class AssistantQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=3, max_length=300)


class AssistantAnswer(BaseModel):
    answer: str
    source: str
    disclaimer: str
