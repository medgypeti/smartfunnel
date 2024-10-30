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

class QueryInstagramDBInput(BaseModel):
    """Input for QueryInstagramDB."""
    query: str = Field(
        ..., 
        description="The query to search the instagram content added to the database"
    )
    instagram_username: Optional[str] = Field(
        default=None,
        description="The Instagram username to query content for"
    )

class QueryInstagramDBOutput(BaseModel):
    """Output for QueryInstagramDB."""
    response: str = Field(..., description="The response from the query")
    error_message: str = Field(default="", description="Error message if the operation failed")
    success: bool = Field(..., description="Whether the operation was successful")

class QueryInstagramDBTool(BaseTool):
    name: str = "Query Instagram DB"
    description: str = """Queries the Instagram content database with provided input query."""
    args_schema: Type[BaseModel] = QueryInstagramDBInput
    
    _app: Optional[App] = PrivateAttr(default=None)
    _insta_loader: Optional[instaloader.Instaloader] = PrivateAttr(default=None)

    def __init__(self, app: App):
        super().__init__()
        self._app = app
        self._insta_loader = instaloader.Instaloader()

    def _check_profile_exists(self, username: str) -> bool:
        """Check if an Instagram profile exists."""
        if not username:
            return True
        try:
            if username.startswith('@'):
                username = username[1:]
            profile = instaloader.Profile.from_username(self._insta_loader.context, username)
            return True
        except instaloader.exceptions.ProfileNotExistsException:
            return False
        except Exception as e:
            logging.error(f"Error checking profile existence: {str(e)}")
            return False

    def _run(self, input_data: Union[str, Dict]) -> str:
        try:
            # Handle string input
            if isinstance(input_data, str):
                query = input_data
                instagram_username = None
            # Handle dictionary input
            elif isinstance(input_data, dict):
                # Remove tool name if present
                input_data.pop('name', None)
                query = input_data.get('query')
                instagram_username = input_data.get('instagram_username')
                
                if not query:
                    return "Error: Query is required"
            else:
                return "Error: Invalid input format"

            # Check profile existence
            if instagram_username and not self._check_profile_exists(instagram_username):
                return f"Error: Instagram profile not found: {instagram_username}"

            # Create the enhanced query
            if instagram_username:
                enhanced_query = f"""Please analyze the following query about the Instagram content from {instagram_username}: {query}
                Focus on providing specific examples and quotes from the posts."""
            else:
                enhanced_query = f"""Please analyze the following query about the Instagram content: {query}
                Focus on providing specific examples and quotes from the posts."""

            # Query the database
            try:
                response = self._app.query(enhanced_query)
                answer = response[0] if isinstance(response, tuple) else response

                if not answer or (isinstance(answer, str) and answer.strip() == ""):
                    return "No relevant content found in the processed posts."

                formatted_response = f"""Answer: {answer}\n\nNote: This response is based on the processed Instagram content{
                    f' from {instagram_username}' if instagram_username else ''}."""
                
                return formatted_response

            except Exception as e:
                return f"Error querying database: {str(e)}"

        except Exception as e:
            logging.error(f"Error in QueryInstagramDBTool: {str(e)}")
            return f"Error processing request: {str(e)}"

# from typing import List, Type, Optional, Union, Dict
# from datetime import datetime, timedelta
# import tempfile
# import random
# import time
# import logging
# from pathlib import Path
# import socket
# import instaloader
# import requests
# from moviepy.editor import VideoFileClip
# from pydantic.v1 import BaseModel, Field, PrivateAttr
# from crewai_tools.tools.base_tool import BaseTool
# from embedchain import App
# # from crewai_tools.tools.base_tool import BaseTool
# # from pydantic.v1 import BaseModel, Field, PrivateAttr
# # from typing import Type, Union
# # from embedchain import App
# # import logging

# class QueryInstagramDBInput(BaseModel):
#     """Input for QueryInstagramDB."""
#     query: str = Field(
#         ..., 
#         description="The query to search the instagram content added to the database",
#         example="How do the author's values impact their work?"
#     )

# class QueryInstagramDBOutput(BaseModel):
#     """Output for QueryInstagramDB."""
#     response: str = Field(..., description="The response from the query")
#     error_message: str = Field(default="", description="Error message if the operation failed")
#     success: bool = Field(..., description="Whether the operation was successful")

# class QueryInstagramDBTool(BaseTool):
#     name: str = "Query Instagram DB"
#     description: str = """Queries the Instagram content database with provided input query.
#     Example: 'How do the author's values impact their work?'"""
#     args_schema: Type[BaseModel] = QueryInstagramDBInput
    
#     _app: Optional[App] = PrivateAttr(default=None)

#     def __init__(self, app: App):
#         super().__init__()
#         self._app = app

#     def _run(self, query: Union[str, Dict, QueryInstagramDBInput]) -> QueryInstagramDBOutput:
#         try:
#             # Convert string input to QueryInstagramDBInput
#             if isinstance(query, str):
#                 query = QueryInstagramDBInput(query=query)
#             # Convert dict input to QueryInstagramDBInput
#             elif isinstance(query, dict):
#                 query = QueryInstagramDBInput(**query)
#             # At this point, query should be QueryInstagramDBInput
#             if not isinstance(query, QueryInstagramDBInput):
#                 raise ValueError("Invalid query format")

#             query_str = query.query
#             if not query_str.strip():
#                 raise ValueError("Query string cannot be empty")

#             # Rest of your code remains the same
#             enhanced_query = f"""Please analyze the following query about the Instagram content: {query_str}
#             Focus on providing specific examples and quotes from the posts."""

#             response = self._app.query(enhanced_query)
#             answer = response[0] if isinstance(response, tuple) else response

#             if not answer or (isinstance(answer, str) and answer.strip() == ""):
#                 return QueryInstagramDBOutput(
#                     response="No relevant content found in the processed posts.",
#                     success=False,
#                     error_message="No content found"
#                 )

#             formatted_response = f"""Answer: {answer}\n\nNote: This response is based on the processed Instagram content."""
#             return QueryInstagramDBOutput(response=formatted_response, success=True)

#         except Exception as e:
#             logging.error(f"Error in QueryInstagramDBTool: {str(e)}")
#             return QueryInstagramDBOutput(
#                 response="",
#                 success=False,
#                 error_message=str(e)
#             )
