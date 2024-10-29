
from typing import Any, Type, List, Union
from datetime import datetime
from pydantic import BaseModel, Field
from crewai_tools.tools.base_tool import BaseTool
import instaloader
import logging
from dotenv import load_dotenv
import os
import time


import tempfile
import logging
from embedchain import App
from typing import Any, Type, List
from datetime import datetime
from pydantic import BaseModel, Field
from crewai_tools.tools.base_tool import BaseTool
import instaloader
import os
import requests
import io
from pydub import AudioSegment
from deepgram import Deepgram
from smartfunnel.tools.chroma_db_init import get_app_instance
app_instance = get_app_instance()

import streamlit as st
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
# Set up Deepgram
os.environ["DEEPGRAM_API_KEY"] = st.secrets["DEEPGRAM_API_KEY"]
# deepgram = Deepgram(DEEPGRAM_API_KEY)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PostInfo(BaseModel):
    """Instagram post information."""
    post_id: str
    caption: str
    timestamp: datetime
    likes: int
    url: str
    is_video: bool
    video_url: str = ""

    class Config:
        arbitrary_types_allowed = True

from typing import Any, Type, List
from datetime import datetime
from pydantic import BaseModel, Field
from crewai_tools.tools.base_tool import BaseTool
import instaloader
import logging
from dotenv import load_dotenv
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from typing import Any, Type, List
from datetime import datetime
from pydantic import BaseModel, Field
from crewai_tools.tools.base_tool import BaseTool
import instaloader
import logging
import os
import requests
import io
from pydub import AudioSegment
from embedchain import App

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FetchToAddInstagramAudioInput(BaseModel):
    """Input for FetchToAddInstagramAudio."""
    instagram_username: str = Field(..., description="The Instagram username to fetch posts from")

class FetchToAddInstagramAudioOutput(BaseModel):
    """Output containing results of fetch and audio processing."""
    processed_videos: List[str] = Field(default_factory=list, description="List of successfully processed video URLs")
    success: bool = Field(..., description="Whether the operation was successful")
    error_message: str = Field(default="", description="Error message if any operations failed")
    total_posts_found: int = Field(default=0, description="Total number of posts found")
    total_videos_processed: int = Field(default=0, description="Total number of videos processed")

from contextlib import contextmanager

@contextmanager
def temporary_file_manager(suffix='.wav'):
    """Context manager for handling temporary files."""
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, f'temp{suffix}')
    try:
        yield temp_path
    finally:
        # Clean up the file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        # Clean up the directory
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)

class FetchToAddInstagramAudioTool(BaseTool):
    """Tool that fetches Instagram posts and processes their audio for the vector database."""
    name: str = "Fetch and Process Instagram Audio"
    description: str = "Fetches Instagram posts and adds video audio to the vector database"
    args_schema: Type[BaseModel] = FetchToAddInstagramAudioInput
    insta_loader: Any = Field(default=None, exclude=True)
    app: Any = Field(default=None, exclude=True)
    is_initialized: bool = Field(default=False, exclude=True)
    session_file: str = Field(default="", exclude=True)

    def __init__(self, app: App, **data):
        super().__init__(**data)
        self.app = app
        self.session_file = os.path.join(tempfile.gettempdir(), "instagram_session")
        self.is_initialized = False

    def initialize_for_new_creator(self):
        """Reset the vector database before starting analysis for a new creator."""
        logger.info("Initializing vector database for new creator")
        if self.app is not None:
            self.app.reset()
            logger.info("Vector database reset successfully")
        else:
            logger.error("No app instance available for reset")
        self.is_initialized = True

    def _get_instaloader_instance(self):
        """Get or create a shared Instaloader instance with session management."""
        if not self.insta_loader:
            self.insta_loader = instaloader.Instaloader()
            try:
                username = os.getenv("INSTAGRAM_USERNAME", "the_smart_funnel")
                password = os.getenv("INSTAGRAM_PASSWORD", "Firescan2024+")

                # Try to load existing session
                if os.path.exists(self.session_file):
                    try:
                        self.insta_loader.load_session_from_file(username, self.session_file)
                        logger.info("Successfully loaded existing Instagram session")
                        return self.insta_loader
                    except Exception as e:
                        logger.warning(f"Failed to load existing session: {str(e)}")
                
                # Perform fresh login
                self.insta_loader.login(username, password)
                # Save session for future use
                self.insta_loader.save_session_to_file(self.session_file)
                logger.info("Successfully created new Instagram session")
                
            except Exception as e:
                logger.error(f"Failed to login to Instagram: {str(e)}")
                raise

        return self.insta_loader

    def _retry_operation(self, operation, max_retries=3, delay=5):
        """Generic retry mechanism for Instagram operations."""
        last_error = None
        for attempt in range(max_retries):
            try:
                return operation()
            except Exception as e:
                last_error = e
                if attempt + 1 < max_retries:
                    logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                    time.sleep(delay * (attempt + 1))
                    
                    if "login" in str(e).lower() or "429" in str(e):
                        self.insta_loader = None
                        self._get_instaloader_instance()
                        
        raise last_error

    def _process_video(self, video_url: str, post_metadata: dict) -> bool:
        with temporary_file_manager() as temp_audio_path:
            try:
                # Download video
                response = requests.get(video_url, timeout=30)
                if response.status_code != 200:
                    raise Exception(f"Failed to download video: Status code {response.status_code}")
                
                # Process video data
                video_buffer = io.BytesIO(response.content)
                audio = AudioSegment.from_file(video_buffer, format="mp4")
                
                # Export as WAV
                audio_buffer = io.BytesIO()
                audio.export(audio_buffer, format="wav")
                audio_buffer.seek(0)
                
                # Write to temporary file
                with open(temp_audio_path, 'wb') as f:
                    f.write(audio_buffer.getvalue())
                
                # Add to embedchain
                self.app.add(
                    temp_audio_path,
                    data_type="audio",
                    metadata=post_metadata
                )
                
                logger.info(f"Successfully processed video: {video_url}")
                return True
                
            except Exception as e:
                logger.error(f"Error processing video {video_url}: {str(e)}")
                return False
    
    def _run(self, instagram_username: str) -> FetchToAddInstagramAudioOutput:
        # Reset the database if not initialized
        if not self.is_initialized:
            self.initialize_for_new_creator()
            
        processed_videos = []
        errors = []
        total_posts = 0
        
        try:
            logger.info(f"Fetching posts for user: {instagram_username}")
            
            def get_profile():
                loader = self._get_instaloader_instance()
                return instaloader.Profile.from_username(loader.context, instagram_username)
            
            # Get profile with retry logic
            profile = self._retry_operation(get_profile)
            post_count = 0
            
            for post in profile.get_posts():
                total_posts += 1
                
                try:
                    if post.is_video and post.video_url:
                        post_metadata = {
                            "source": f"https://www.instagram.com/p/{post.shortcode}/",
                            "caption": post.caption if post.caption else "",
                            "timestamp": post.date_utc.isoformat(),
                            "likes": post.likes,
                            "post_id": post.shortcode
                        }
                        
                        if self._process_video(post.video_url, post_metadata):
                            processed_videos.append(post.video_url)
                    
                    post_count += 1
                    if post_count >= 4:
                        break
                        
                except Exception as post_error:
                    error_msg = f"Error processing post {post.shortcode}: {str(post_error)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    continue

            success = len(processed_videos) > 0
            error_message = "; ".join(errors) if errors else ""
            
            logger.info(f"Processed {len(processed_videos)} videos out of {total_posts} total posts")
            
            return FetchToAddInstagramAudioOutput(
                processed_videos=processed_videos,
                success=success,
                error_message=error_message,
                total_posts_found=total_posts,
                total_videos_processed=len(processed_videos)
            )

        except Exception as e:
            error_message = f"Error in fetch and process operation: {str(e)}"
            logger.error(error_message)
            return FetchToAddInstagramAudioOutput(
                processed_videos=[],
                success=False,
                error_message=error_message,
                total_posts_found=total_posts,
                total_videos_processed=0
            )

    def _handle_error(self, error: Exception) -> str:
        """Handle errors that occur during tool execution."""
        error_message = str(error)
        if "login" in error_message.lower():
            return "Failed to authenticate with Instagram. Please check your credentials."
        elif "not found" in error_message.lower():
            return f"Instagram profile not found. Please check the username."
        elif "rate limit" in error_message.lower():
            return "Instagram rate limit reached. Please try again later."
        else:
            return f"An error occurred: {error_message}"


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


from smartfunnel.tools.chroma_db_init import get_app_instance
app_instance = get_app_instance()
fetch_tool = FetchToAddInstagramAudioTool(app=app_instance)
fetch_tool.run(instagram_username="tonyjazz")
query_tool = QueryInstagramDBTool(app=app_instance)
# query_tool.run(query="What are the author's key achievements and successes?")
print(query_tool.run(query="What are the author's key achievements and successes?"))