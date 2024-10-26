from typing import Any, Type, List, Union
from datetime import datetime
from pydantic import BaseModel, Field
from crewai_tools.tools.base_tool import BaseTool
import instaloader
import logging
from dotenv import load_dotenv
import os

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
import streamlit as st

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
# OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
# Set up Deepgram
DEEPGRAM_API_KEY = st.secrets["DEEPGRAM_API_KEY"]
# DEEPGRAM_API_KEY = os.environ["DEEPGRAM_API_KEY"]
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

# class PostInfo(BaseModel):
#     """Instagram post information."""
#     post_id: str
#     caption: str
#     timestamp: datetime
#     likes: int
#     url: str
#     is_video: bool
#     video_url: str = ""

#     class Config:
#         arbitrary_types_allowed = True

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

class FetchToAddInstagramAudioTool(BaseTool):
    """Tool that fetches Instagram posts and processes their audio for the vector database."""
    name: str = "Fetch and Process Instagram Audio"
    description: str = "Fetches Instagram posts and adds video audio to the vector database"
    args_schema: Type[BaseModel] = FetchToAddInstagramAudioInput
    insta_loader: Any = Field(default=None, exclude=True)
    app: Any = Field(default=None, exclude=True)

    def __init__(self, app: App, **data):
        super().__init__(**data)
        self.app = app

    def _get_instaloader_instance(self):
        """Get or create a shared Instaloader instance."""
        if not self.insta_loader:
            self.insta_loader = instaloader.Instaloader()
            try:
                username = st.secrets["INSTAGRAM_USERNAME"]
                password = st.secrets["INSTAGRAM_PASSWORD"]
                # username = os.getenv("INSTAGRAM_USERNAME", "placeholder")
                # password = os.getenv("INSTAGRAM_PASSWORD", "placeholder")
                self.insta_loader.login(username, password)
                logger.info("Successfully logged in to Instagram")
            except Exception as e:
                logger.error(f"Failed to login to Instagram: {str(e)}")
                raise
        return self.insta_loader

    def _process_audio(self, audio_buffer: io.BytesIO) -> str:
        """Save audio to temporary file and return the path."""
        temp_path = f"temp_audio_{datetime.now().timestamp()}.wav"
        try:
            with open(temp_path, 'wb') as f:
                f.write(audio_buffer.getvalue())
            return temp_path
        except Exception as e:
            raise Exception(f"Error saving audio: {str(e)}")

    def _cleanup_temp_file(self, file_path: str):
        """Clean up temporary audio file."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.warning(f"Error cleaning up temporary file {file_path}: {str(e)}")

    def _process_video(self, video_url: str, post_metadata: dict) -> bool:
        """Process a single video and add it to the vector database."""
        temp_audio_path = None
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
            
            # Save to temporary file
            temp_audio_path = self._process_audio(audio_buffer)
            
            # Add to embedchain with metadata
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
        finally:
            if temp_audio_path:
                self._cleanup_temp_file(temp_audio_path)

    def _run(self, instagram_username: str) -> FetchToAddInstagramAudioOutput:
        processed_videos = []
        errors = []
        total_posts = 0
        
        try:
            logger.info(f"Fetching posts for user: {instagram_username}")
            
            # Get Instagram instance
            loader = self._get_instaloader_instance()
            
            # Get profile and posts
            profile = instaloader.Profile.from_username(loader.context, instagram_username)
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
                    if post_count >= 2:  # Limit to 6 posts as in original
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
