from typing import List, Type, Optional, Union, Dict
from datetime import datetime, timedelta
import tempfile
import random
import time
import logging
from pathlib import Path
import socket
import instaloader
import requests
from moviepy.editor import VideoFileClip
from pydantic.v1 import BaseModel, Field, PrivateAttr
from crewai_tools.tools.base_tool import BaseTool
from embedchain import App
# from crewai_tools.tools.base_tool import BaseTool
# from pydantic.v1 import BaseModel, Field, PrivateAttr
# from typing import Type, Union
# from embedchain import App
# import logging

class QueryInstagramDBInput(BaseModel):
    """Input for QueryInstagramDB."""
    query: str = Field(
        ..., 
        description="The query to search the instagram content added to the database",
        example="How do the author's values impact their work?"
    )

class QueryInstagramDBOutput(BaseModel):
    """Output for QueryInstagramDB."""
    response: str = Field(..., description="The response from the query")
    error_message: str = Field(default="", description="Error message if the operation failed")
    success: bool = Field(..., description="Whether the operation was successful")

class QueryInstagramDBTool(BaseTool):
    name: str = "Query Instagram DB"
    description: str = """Queries the Instagram content database with provided input query.
    Example: 'How do the author's values impact their work?'"""
    args_schema: Type[BaseModel] = QueryInstagramDBInput
    
    _app: Optional[App] = PrivateAttr(default=None)

    def __init__(self, app: App):
        super().__init__()
        self._app = app

    def _run(self, query: Union[str, Dict, QueryInstagramDBInput]) -> QueryInstagramDBOutput:
        try:
            # Convert string input to QueryInstagramDBInput
            if isinstance(query, str):
                query = QueryInstagramDBInput(query=query)
            # Convert dict input to QueryInstagramDBInput
            elif isinstance(query, dict):
                query = QueryInstagramDBInput(**query)
            # At this point, query should be QueryInstagramDBInput
            if not isinstance(query, QueryInstagramDBInput):
                raise ValueError("Invalid query format")

            query_str = query.query
            if not query_str.strip():
                raise ValueError("Query string cannot be empty")

            # Rest of your code remains the same
            enhanced_query = f"""Please analyze the following query about the Instagram content: {query_str}
            Focus on providing specific examples and quotes from the posts."""

            response = self._app.query(enhanced_query)
            answer = response[0] if isinstance(response, tuple) else response

            if not answer or (isinstance(answer, str) and answer.strip() == ""):
                return QueryInstagramDBOutput(
                    response="No relevant content found in the processed posts.",
                    success=False,
                    error_message="No content found"
                )

            formatted_response = f"""Answer: {answer}\n\nNote: This response is based on the processed Instagram content."""
            return QueryInstagramDBOutput(response=formatted_response, success=True)

        except Exception as e:
            logging.error(f"Error in QueryInstagramDBTool: {str(e)}")
            return QueryInstagramDBOutput(
                response="",
                success=False,
                error_message=str(e)
            )
# class QueryInstagramDBInput(BaseModel):
#     """Input for QueryInstagramDB."""
#     query: str = Field(..., description="The query to search the vector database")

# class QueryInstagramDBOutput(BaseModel):
#     """Output for QueryInstagramDB."""
#     response: str = Field(..., description="The response from the query")
#     error_message: str = Field(default="", description="Error message if the operation failed")
#     success: bool = Field(..., description="Whether the operation was successful")

# class QueryInstagramDBTool(BaseTool):
#     name: str = "Query Instagram DB"
#     description: str = "Queries the Instagram content database with provided input query: 'The query to search the vector database'"
#     args_schema: Type[BaseModel] = QueryInstagramDBInput
    
#     _app: Optional[App] = PrivateAttr(default=None)

#     def __init__(self, app: App):
#         super().__init__()
#         self._app = app

#     def _run(self, query: str, **kwargs) -> QueryInstagramDBOutput:
#         try:
#             # Enhance the query with specific instructions
#             enhanced_query = f"""Please analyze the following query about the Instagram content: {query}
#             Focus on providing specific examples and quotes from the posts."""

#             # Query the database
#             response = self._app.query(enhanced_query)

#             # Handle tuple response
#             answer = response[0] if isinstance(response, tuple) else response

#             # Check for empty response
#             if not answer or (isinstance(answer, str) and answer.strip() == ""):
#                 return QueryInstagramDBOutput(
#                     response="No relevant content found in the processed posts.",
#                     success=False,
#                     error_message="No content found"
#                 )

#             # Format the response
#             formatted_response = f"""Answer: {answer}\n\nNote: This response is based on the processed Instagram content."""

#             return QueryInstagramDBOutput(response=formatted_response, success=True)

#         except ValueError as ve:
#             return QueryInstagramDBOutput(
#                 response="",
#                 success=False,
#                 error_message="No content has been added to the database yet."
#             )
#         except Exception as e:
#             return QueryInstagramDBOutput(
#                 response="",
#                 success=False,
#                 error_message=str(e)
#             )

# class QueryInstagramDBInput(BaseModel):
#     """Input for QueryInstagramDB."""
#     query: str = Field(..., description="The query to search the vector database")

# class QueryInstagramDBOutput(BaseModel):
#     """Output for QueryInstagramDB."""
#     response: str = Field(..., description="The response from the query")
#     error_message: str = Field(default="", description="Error message if the operation failed")
#     success: bool = Field(..., description="Whether the operation was successful")

# class QueryInstagramDBTool(BaseTool):
#     name: str = "Query Instagram DB"
#     description: str = "Queries the Instagram content database with provided input"
#     args_schema: Type[QueryInstagramDBInput] = QueryInstagramDBInput
#     _app: Optional[App] = Field(default=None, exclude=True)
    
#     model_config = {
#         'arbitrary_types_allowed': True
#     }
    
#     def __init__(self, app: App):
#         super().__init__()
#         self._app = app
    
#     def _run(self, query: Union[str, QueryInstagramDBInput], **kwargs) -> QueryInstagramDBOutput:
#         try:
#             query_text = query.query if isinstance(query, QueryInstagramDBInput) else query
            
#             enhanced_query = f"""Please analyze the following query about the Instagram content: {query_text}
#             Focus on providing specific examples and quotes from the posts."""
            
#             response = self._app.query(enhanced_query)
            
#             answer = response[0] if isinstance(response, tuple) else response
            
#             if not answer or (isinstance(answer, str) and answer.strip() == ""):
#                 return QueryInstagramDBOutput(
#                     response="No relevant content found in the processed posts.",
#                     success=False,
#                     error_message="No content found"
#                 )
            
#             formatted_response = f"""
# Answer: {answer}

# Note: This response is based on the processed Instagram content."""
            
#             return QueryInstagramDBOutput(response=formatted_response, success=True)
#         except ValueError as ve:
#             return QueryInstagramDBOutput(
#                 response="",
#                 success=False,
#                 error_message="No content has been added to the database yet."
#             )
#         except Exception as e:
#             return QueryInstagramDBOutput(
#                 response="",
#                 success=False,
#                 error_message=str(e)
#             )
