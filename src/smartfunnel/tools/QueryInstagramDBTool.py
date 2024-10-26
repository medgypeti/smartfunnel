from typing import List, Type, Optional, Union
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
    query: str = Field(..., description="The query to search the Instagram content database")

class QueryInstagramDBOutput(BaseModel):
    """Output for QueryInstagramDB."""
    response: str = Field(..., description="The response from the query")
    error_message: str = Field(default="", description="Error message if the operation failed")
    success: bool = Field(..., description="Whether the operation was successful")

# class QueryInstagramDBInput(BaseModel):
#     query: str = Field(..., description="The query to search the Instagram content database")

# class QueryInstagramDBOutput(BaseModel):
#     response: str = Field(..., description="The response from the query")
#     error_message: str = Field(default="", description="Error message if the operation failed")
#     success: bool = Field(..., description="Whether the operation was successful")

class QueryInstagramDBTool(BaseTool):
    name: str = "Query Instagram DB"
    description: str = "Queries the Instagram content database with provided input"
    args_schema: Type[QueryInstagramDBInput] = QueryInstagramDBInput
    _app: Optional[App] = Field(default=None, exclude=True)
    
    model_config = {
        'arbitrary_types_allowed': True
    }
    
    def __init__(self, app: App):
        super().__init__()
        self._app = app
    
    def _run(self, query: Union[str, QueryInstagramDBInput], **kwargs) -> QueryInstagramDBOutput:
        try:
            query_text = query.query if isinstance(query, QueryInstagramDBInput) else query
            
            enhanced_query = f"""Please analyze the following query about the Instagram content: {query_text}
            Focus on providing specific examples and quotes from the posts."""
            
            response = self._app.query(enhanced_query)
            
            answer = response[0] if isinstance(response, tuple) else response
            
            if not answer or (isinstance(answer, str) and answer.strip() == ""):
                return QueryInstagramDBOutput(
                    response="No relevant content found in the processed posts.",
                    success=False,
                    error_message="No content found"
                )
            
            formatted_response = f"""
Answer: {answer}

Note: This response is based on the processed Instagram content."""
            
            return QueryInstagramDBOutput(response=formatted_response, success=True)
        except ValueError as ve:
            return QueryInstagramDBOutput(
                response="",
                success=False,
                error_message="No content has been added to the database yet."
            )
        except Exception as e:
            return QueryInstagramDBOutput(
                response="",
                success=False,
                error_message=str(e)
            )
# class QueryInstagramDBTool(BaseTool):
#     name: str = "Query Instagram DB"
#     description: str = "Queries the Instagram content database with provided input"
#     args_schema: Type[QueryInstagramDBInput] = QueryInstagramDBInput
#     app: App = Field(default=None, exclude=True)
    
#     # Private attributes
#     _logger: logging.Logger = PrivateAttr(default_factory=lambda: logging.getLogger(__name__))
    
#     model_config = {
#         'arbitrary_types_allowed': True
#     }
    
#     def __init__(self, app: App, **data):
#         super().__init__(**data)
#         self.app = app
    
#     def _run(self, query: Union[str, QueryInstagramDBInput], **kwargs) -> QueryInstagramDBOutput:
#         try:
#             # Handle both string and QueryInstagramDBInput inputs
#             if isinstance(query, str):
#                 query_text = query
#             else:
#                 query_text = query.query
                
#             # Add context to the query
#             enhanced_query = f"""Please analyze the following query about the Instagram content: {query_text}
#             Focus on providing specific examples and quotes from the posts."""
            
#             # Execute query
#             response = self.app.query(enhanced_query)
            
#             # Handle tuple response (new embedchain version returns (answer, context))
#             if isinstance(response, tuple):
#                 answer = response[0]
#             else:
#                 answer = response
                
#             if not answer or (isinstance(answer, str) and answer.strip() == ""):
#                 return QueryInstagramDBOutput(
#                     response="No relevant content found in the processed posts.",
#                     success=False,
#                     error_message="No content found"
#                 )
                
#             formatted_response = f"""
# Answer: {answer}

# Note: This response is based on the processed Instagram content."""
            
#             return QueryInstagramDBOutput(
#                 response=formatted_response,
#                 success=True
#             )
            
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
# from crewai_tools.tools.base_tool import BaseTool
# from pydantic.v1 import BaseModel, Field, PrivateAttr
# from typing import Type
# from embedchain import App
# import logging

# class QueryInstagramDBInput(BaseModel):
#     query: str = Field(..., description="The query to search the Instagram content database")

# class QueryInstagramDBOutput(BaseModel):
#     response: str = Field(..., description="The response from the query")
#     error_message: str = Field(default="", description="Error message if the operation failed")
#     success: bool = Field(..., description="Whether the operation was successful")

# class QueryInstagramDBTool(BaseTool):
#     name: str = "Query Instagram DB"
#     description: str = "Queries the Instagram content database with provided input"
#     args_schema: Type[QueryInstagramDBInput] = QueryInstagramDBInput
#     app: App = Field(default=None, exclude=True)

#     # Private attributes
#     _logger: logging.Logger = PrivateAttr(default_factory=lambda: logging.getLogger(__name__))

#     class Config:
#         arbitrary_types_allowed = True

#     def __init__(self, app: App, **data):
#         super().__init__(**data)
#         self.app = app

#     def _run(self, tool_input: QueryInstagramDBInput) -> QueryInstagramDBOutput:
#         try:
#             # Add context to the query
#             enhanced_query = f"""Please analyze the following query about the Instagram content: {tool_input.query}
#             Focus on providing specific examples and quotes from the posts."""
            
#             # Execute query
#             response = self.app.query(enhanced_query)
            
#             # Handle tuple response (new embedchain version returns (answer, context))
#             if isinstance(response, tuple):
#                 answer = response[0]
#             else:
#                 answer = response
                
#             if not answer or (isinstance(answer, str) and answer.strip() == ""):
#                 return QueryInstagramDBOutput(
#                     response="No relevant content found in the processed posts.",
#                     success=False,
#                     error_message="No content found"
#                 )
                
#             formatted_response = f"""
# Answer: {answer}

# Note: This response is based on the processed Instagram content."""
            
#             return QueryInstagramDBOutput(
#                 response=formatted_response,
#                 success=True
#             )
                
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