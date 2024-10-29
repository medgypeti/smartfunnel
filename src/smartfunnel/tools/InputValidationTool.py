# Import the classes from your original file
from pydantic.v1 import BaseModel, Field
from typing import Any, Type, List, Optional
from crewai_tools.tools.base_tool import BaseTool
import json

class InputValidationToolInput(BaseModel):
    """Input for InputValidationTool."""
    youtube_channel_handle: Optional[str] = Field(
        None, 
        description="The YouTube channel handle (e.g., '@channelhandle')"
    )
    instagram_username: Optional[str] = Field(
        None, 
        description="The Instagram username"
    )

class InputValidationToolOutput(BaseModel):
    """Output for InputValidationTool."""
    youtube_channel_handle: str = Field(
        ...,
        description="YouTube channel handle or 'None' if not provided"
    )
    instagram_username: str = Field(
        ...,
        description="Instagram username or 'None' if not provided"
    )
    has_youtube: bool = Field(
        ...,
        description="Whether YouTube input exists"
    )
    has_instagram: bool = Field(
        ...,
        description="Whether Instagram input exists"
    )

class InputValidationTool(BaseTool):
    name: str = "Input Validation Tool"
    description: str = (
        "Verifies if the provided input parameters exist. "
        "Returns the inputs if provided or 'None' if not provided."
    )
    args_schema: Type[BaseModel] = InputValidationToolInput
    return_schema: Type[BaseModel] = InputValidationToolOutput
    
    def _run(self, **kwargs) -> str:  # Changed return type to str
        try:
            # Handle both string and dictionary inputs
            if isinstance(kwargs, str):
                try:
                    inputs = json.loads(kwargs)
                except json.JSONDecodeError:
                    inputs = {}
            else:
                inputs = kwargs
            
            # Simply check if inputs exist and have content
            youtube_handle = inputs.get('youtube_channel_handle', '')
            instagram_user = inputs.get('instagram_username', '')
            
            # Basic existence check
            has_youtube = bool(youtube_handle and str(youtube_handle).strip())
            has_instagram = bool(instagram_user and str(instagram_user).strip())
            
            # Create the output object
            output = InputValidationToolOutput(
                youtube_channel_handle=youtube_handle.strip() if has_youtube else "None",
                instagram_username=instagram_user.strip() if has_instagram else "None",
                has_youtube=has_youtube,
                has_instagram=has_instagram
            )
            
            # Return the JSON string representation
            return output.json()
            
        except Exception as e:
            # Return error result as JSON string
            error_output = InputValidationToolOutput(
                youtube_channel_handle="None",
                instagram_username="None",
                has_youtube=False,
                has_instagram=False
            )
            return error_output.json()