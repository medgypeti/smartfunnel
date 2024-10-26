from typing import Any, Type, List, Union
from datetime import datetime
from pydantic import BaseModel, Field
from crewai_tools.tools.base_tool import BaseTool
import instaloader
import logging
from dotenv import load_dotenv
import os
import sys
import time
import requests
import io
from pydub import AudioSegment
from embedchain import App

OPENAI_API_KEY = "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"

# Set up Deepgram
os.environ["DEEPGRAM_API_KEY"] = "46d16104048c4bd6b223b69c7bc05b2a3df4de75"
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

class FetchInstagramPostsInput(BaseModel):
    """Input for FetchInstagramPosts."""
    instagram_username: str = Field(..., description="The Instagram username to fetch posts from")

class FetchInstagramPostsOutput(BaseModel):
    """Output containing list of Instagram posts."""
    posts: List[PostInfo]
    success: bool = True
    error_message: str = ""

class FetchInstagramPostsTool(BaseTool):
    """Tool that fetches Instagram posts from a specified account."""
    name: str = "Fetch Instagram Posts"
    description: str = "Fetches the latest posts from a specified Instagram account"
    args_schema: Type[BaseModel] = FetchInstagramPostsInput
    insta_loader: Any = Field(default=None, exclude=True)
    
    def _get_instaloader_instance(self):
        """Get or create a shared Instaloader instance."""
        if not self.insta_loader:
            self.insta_loader = instaloader.Instaloader()
            try:
                # Load Instagram credentials from environment variables
                username = os.getenv("INSTAGRAM_USERNAME", "the_smart_funnel")
                password = os.getenv("INSTAGRAM_PASSWORD", "Firescan2024+")
                
                self.insta_loader.login(username, password)
                logger.info("Successfully logged in to Instagram")
            except Exception as e:
                logger.error(f"Failed to login to Instagram: {str(e)}")
                raise
        return self.insta_loader

    def _run(self, instagram_username: str) -> FetchInstagramPostsOutput:
        try:
            logger.info(f"Fetching posts for user: {instagram_username}")
            
            # Get Instagram instance
            loader = self._get_instaloader_instance()
            
            # Get profile and posts
            profile = instaloader.Profile.from_username(loader.context, instagram_username)
            posts = []
            post_count = 0
            
            for post in profile.get_posts():
                try:
                    post_info = PostInfo(
                        post_id=post.shortcode,
                        caption=post.caption if post.caption else "",
                        timestamp=post.date_utc,
                        likes=post.likes,
                        url=f"https://www.instagram.com/p/{post.shortcode}/",
                        is_video=post.is_video,
                        video_url=post.video_url if post.is_video else ""
                    )
                    posts.append(post_info)
                    post_count += 1
                    logger.info(f"Processed post {post.shortcode}")

                    # Limit to 4 posts for testing
                    if post_count >= 1:
                        break
                        
                except Exception as post_error:
                    logger.error(f"Error processing individual post: {str(post_error)}")
                    continue

            if not posts:
                return FetchInstagramPostsOutput(
                    posts=[],
                    success=False,
                    error_message="No posts were successfully fetched"
                )

            logger.info(f"Successfully fetched {len(posts)} posts")
            return FetchInstagramPostsOutput(
                posts=posts,
                success=True,
                error_message=""
            )

        except Exception as e:
            error_message = f"Error fetching Instagram posts: {str(e)}"
            logger.error(error_message)
            return FetchInstagramPostsOutput(
                posts=[],
                success=False,
                error_message=error_message
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

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class AddInstagramAudioInput(BaseModel):
    """Input for AddInstagramAudio."""
    video_url: str = Field(..., description="The URL of the Instagram video to process")

class AddInstagramAudioOutput(BaseModel):
    """Output from AddInstagramAudio."""
    success: bool = Field(..., description="Whether the audio was successfully added to the vector DB")
    processed_posts: List[str] = Field(default_factory=list, description="List of successfully processed post IDs")
    transcription: str = Field(default="", description="Transcription of the audio if available")
    error_message: str = Field(default="", description="Error message if any operations failed")

class AddInstagramAudioTool(BaseTool):
    """Tool that processes Instagram videos as audio and adds them to the vector database."""
    name: str = "Add Instagram Audio to Vector DB"
    description: str = "Adds Instagram video audio to the vector database using EmbedChain"
    args_schema: Type[BaseModel] = AddInstagramAudioInput
    app: Any = Field(default=None, exclude=True)

    def __init__(self, app: Any, **data):
        super().__init__(**data)
        self.app = app
        logger.info("Initialized AddInstagramAudioTool with app instance")

    def _convert_video_to_audio_buffer(self, video_buffer: io.BytesIO) -> io.BytesIO:
        """Convert video buffer to audio buffer in WAV format."""
        try:
            logger.debug("Starting video to audio conversion")
            audio = AudioSegment.from_file(video_buffer, format="mp4")
            logger.debug(f"Audio duration: {len(audio)/1000:.2f} seconds")
            
            audio_buffer = io.BytesIO()
            audio.export(audio_buffer, format="wav")
            audio_buffer.seek(0)
            
            logger.debug(f"Successfully converted video to audio. Buffer size: {audio_buffer.getbuffer().nbytes} bytes")
            return audio_buffer
        except Exception as e:
            logger.error(f"Error in video to audio conversion: {str(e)}")
            raise

    def _get_transcription(self) -> str:
        """Get the most recent transcription by querying the database."""
        try:
            # Query for the most recently added content
            recent_content = self.app.query("What was the most recently added audio content? Please provide the full transcription.")
            logger.debug(f"Retrieved recent content from database: {recent_content[:200]}...")
            return recent_content
        except Exception as e:
            logger.error(f"Error retrieving transcription: {str(e)}")
            return ""

    def _run(self, video_url: str) -> AddInstagramAudioOutput:
        processed_posts = []
        errors = []
        transcription = ""

        try:
            logger.info(f"Starting to process video from URL: {video_url}")
            
            # Download video
            logger.debug("Downloading video...")
            video_response = requests.get(video_url, timeout=30)
            video_buffer = io.BytesIO(video_response.content)
            logger.debug(f"Downloaded video. Buffer size: {video_buffer.getbuffer().nbytes} bytes")
            
            # Convert to audio
            logger.debug("Converting video to audio...")
            audio_buffer = self._convert_video_to_audio_buffer(video_buffer)
            
            # Create metadata
            timestamp = datetime.now().isoformat()
            metadata = {
                "source": video_url,
                "type": "instagram_video",
                "processing_time": timestamp,
                "app_name": "full-stack-app"  # Use direct app name instead of accessing config
            }
            logger.debug(f"Created metadata: {metadata}")

            # Add audio to embedchain
            logger.info("Adding audio to embedchain...")
            response = self.app.add(
                audio_buffer,
                data_type="audio",
                metadata=metadata
            )
            logger.debug(f"Add response: {response}")
            
            # Wait briefly for processing
            logger.debug("Waiting for audio processing to complete...")
            time.sleep(2)
            
            # Get transcription
            logger.debug("Retrieving transcription...")
            transcription = self._get_transcription()
            logger.info(f"Transcription received: {transcription[:200]}...")
            
            processed_posts.append(video_url)
            logger.info(f"Successfully processed video: {video_url}")
            
            # Log data sources
            try:
                data_sources = self.app.get_data_sources()
                logger.debug(f"Current data sources: {data_sources}")
            except Exception as e:
                logger.warning(f"Could not retrieve data sources: {str(e)}")
            
        except Exception as e:
            error_msg = f"Error processing video {video_url}: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        return AddInstagramAudioOutput(
            success=len(processed_posts) > 0,
            processed_posts=processed_posts,
            transcription=transcription,
            error_message="; ".join(errors) if errors else ""
        )
class QueryDatabaseInput(BaseModel):
    """Input for QueryDatabase."""
    query: str = Field(..., description="The query to search the vector DB.")

class QueryDatabaseOutput(BaseModel):
    """Output from QueryDatabase."""
    reply: str = Field(..., description="The reply from the query")
    error_message: str = Field(default="", description="Error message if the operation failed")

class QueryDatabaseTool(BaseTool):
    """Tool for querying the video database."""
    name: str = "Query Database"
    description: str = "Queries the vector database containing processed Instagram content"
    args_schema: Type[BaseModel] = QueryDatabaseInput
    app: Any = Field(default=None, exclude=True)

    def __init__(self, app: App, **data):
        super().__init__(**data)
        self.app = app
        logger.info("Initialized QueryDatabaseTool with app instance")

    def _run(self, query: str) -> QueryDatabaseOutput:
        try:
            logger.info(f"Querying vector DB with: {query}")
            reply = self.app.query(query)
            logger.debug(f"Raw response from query: {reply[:200]}...")
            
            if not reply or (isinstance(reply, str) and not reply.strip()):
                logger.warning("No content found in database for query")
                return QueryDatabaseOutput(
                    reply="No relevant content found in the processed videos.",
                    error_message=""
                )
            
            return QueryDatabaseOutput(reply=reply)
            
        except Exception as e:
            error_message = f"Failed to query vector DB: {str(e)}"
            logger.error(error_message)
            return QueryDatabaseOutput(
                reply="Error occurred while querying the database",
                error_message=error_message
            )
        
# Test implementation
# Main execution
if __name__ == "__main__":
    from smartfunnel.tools.chroma_db_init import app_instance
    
    # Initialize tools with improved logging
    logger.info("Initializing tools...")
    
    fetch_tool = FetchInstagramPostsTool()
    logger.info("FetchInstagramPostsTool initialized")
    
    audio_tool = AddInstagramAudioTool(app=app_instance)
    logger.info("AddInstagramAudioTool initialized")
    
    query_tool = QueryDatabaseTool(app=app_instance)
    logger.info("QueryDatabaseTool initialized")
    
    # Fetch posts
    username = "antoineblanco99"
    logger.info(f"Fetching posts for user: {username}")
    result = fetch_tool._run(username)
    
    if result.success and result.posts:
        logger.info(f"Successfully fetched {len(result.posts)} posts")
        for post in result.posts:
            if post.is_video and post.video_url:
                logger.info(f"Processing video from post: {post.url}")
                audio_result = audio_tool._run(post.video_url)
                
                if audio_result.success:
                    logger.info("Successfully processed video")
                    print("\nTranscription:")
                    print("=" * 50)
                    print(audio_result.transcription)
                    print("=" * 50)
                else:
                    logger.error(f"Error processing video: {audio_result.error_message}")
    else:
        logger.error(f"Error fetching posts: {result.error_message}")
    
    # Query content
    logger.info("Querying database for content summary")
    query_result = query_tool._run("Summarize the content of the video in bullet points.")
    print("\nQuery Result:")
    print(query_result.reply)