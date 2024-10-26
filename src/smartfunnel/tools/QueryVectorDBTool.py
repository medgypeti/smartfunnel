from crewai_tools.tools.base_tool import BaseTool
from pydantic.v1 import BaseModel, Field
from typing import Any, Type
from embedchain import App
import logging

logger = logging.getLogger(__name__)

class QueryVectorDBInput(BaseModel):
    query: str = Field(..., description="The query to search the vector DB.")

class QueryVectorDBOutput(BaseModel):
    reply: str = Field(..., description="The reply from the query.")
    error_message: str = Field(default="", description="Error message if the operation failed.")

class QueryVectorDBTool(BaseTool):
    name: str = "Query Vector DB"
    description: str = "Queries the vector database with the given input."
    args_schema: Type[QueryVectorDBInput] = QueryVectorDBInput
    app: Any = Field(default=None, exclude=True)

    def __init__(self, app: App, **data):
        super().__init__(**data)
        self.app = app

    def _run(self, query: str) -> QueryVectorDBOutput:
        try:
            logger.info(f"Querying vector DB with: {query}")
            reply = self.app.query(query)
            logger.info(f"Query completed successfully")
            return QueryVectorDBOutput(reply=reply)
        except Exception as e:
            error_message = f"Failed to query vector DB: {str(e)}"
            logger.error(error_message)
            return QueryVectorDBOutput(reply="Error occurred", error_message=error_message)