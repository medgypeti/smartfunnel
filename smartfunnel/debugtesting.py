from typing import Any, Type
from smartfunnel.tools.chroma_db_init import get_app_instance
app_instance = get_app_instance()


#  limits and start of fetching instagram posts ----------------------------

from typing import List, Type
from datetime import datetime
from pydantic import BaseModel, Field
from crewai_tools.tools.base_tool import BaseTool
import instaloader
import os
from dotenv import load_dotenv

def get_instaloader_instance():
    """Get or create a shared Instaloader instance."""
    if not hasattr(get_instaloader_instance, 'instance'):
        L = instaloader.Instaloader()
        username = "vladzieg"  # Use your credentials
        password = "Lommel1996+"
        try:
            L.login(username, password)
            logger.info("Successfully logged in to Instagram")
            get_instaloader_instance.instance = L
        except Exception as e:
            logger.error(f"Failed to login to Instagram: {str(e)}")
            raise
    return get_instaloader_instance.instance

class PostInfo(BaseModel):
    """Instagram post information."""
    post_id: str
    caption: str
    timestamp: datetime
    likes: int
    url: str
    is_video: bool
    video_url: str

    class Config:
        arbitrary_types_allowed = True

class FetchInstagramPostsInput(BaseModel):
    """Input for FetchInstagramPosts."""
    instagram_username: str = Field(..., description="The Instagram username to fetch posts from")

    class Config:
        arbitrary_types_allowed = True

class FetchInstagramPostsOutput(BaseModel):
    """Output containing list of Instagram posts."""
    posts: List[PostInfo]

    class Config:
        arbitrary_types_allowed = True

class FetchInstagramPostsTool(BaseTool):
    """Tool that fetches Instagram posts from a specified account."""
    name: str = "Fetch Instagram Posts"
    description: str = "Fetches the latest posts from a specified Instagram account"
    args_schema: Type[BaseModel] = FetchInstagramPostsInput
    insta_loader: Any = Field(default=None, exclude=True)
    
    def _run(self, instagram_username: str) -> FetchInstagramPostsOutput:
        try:
            # Initialize and login to Instagram
            self.insta_loader = instaloader.Instaloader()
            self.insta_loader.login("vladzieg", "Lommel1996+")
            
            # Get profile and posts
            profile = instaloader.Profile.from_username(self.insta_loader.context, instagram_username)
            posts = []
            
            for post in profile.get_posts():
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
                
                if len(posts) >= 4:
                    break

            return FetchInstagramPostsOutput(posts=posts)

        except Exception as e:
            raise Exception(f"Error fetching Instagram posts: {str(e)}")

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
        
#  limits and start of audio processing -----------------------------------

from crewai_tools.tools.base_tool import BaseTool
from pydantic.v1 import BaseModel, Field
from typing import Any, Type, List
import instaloader
import logging
import os
import requests
import io
from pydub import AudioSegment
from datetime import datetime

logger = logging.getLogger(__name__)

class AddInstagramAudioOutput(BaseModel):
    """Output from AddInstagramAudio."""
    success: bool = Field(..., description="Whether the audio was successfully added to the vector DB")
    processed_posts: List[str] = Field(default_factory=list, description="List of successfully processed post IDs")
    error_message: str = Field(default="", description="Error message if any operations failed")

    class Config:
        arbitrary_types_allowed = True

class AddInstagramAudioInput(BaseModel):
    """Input for AddInstagramAudio."""
    posts_output: FetchInstagramPostsOutput = Field(..., description="The Instagram posts to process")

    class Config:
        arbitrary_types_allowed = True

class AddInstagramAudioTool(BaseTool):
    """Tool that processes Instagram videos as audio and adds them to the vector database."""
    name: str = "Add Instagram Audio to Vector DB"
    description: str = "Adds Instagram video audio to the vector database"
    args_schema: Type[BaseModel] = AddInstagramAudioInput
    app: Any = Field(default=None, exclude=True)

    def _run(self, posts_output: FetchInstagramPostsOutput) -> AddInstagramAudioOutput:
        processed_posts = []
        errors = []

        # Filter video posts
        video_posts = [post for post in posts_output.posts if post.is_video and post.video_url]
        
        for post in video_posts:
            try:
                # Download video and convert to audio
                video_response = requests.get(post.video_url)
                video_buffer = io.BytesIO(video_response.content)
                audio = AudioSegment.from_file(video_buffer, format="mp4")
                
                # Export as WAV to memory
                audio_buffer = io.BytesIO()
                audio.export(audio_buffer, format="wav")
                audio_buffer.seek(0)
                
                # Add to embedchain
                self.app.add(
                    audio_buffer,
                    data_type="audio",
                    metadata={
                        "source": post.url,
                        "caption": post.caption,
                        "timestamp": post.timestamp.isoformat(),
                        "likes": post.likes
                    }
                )
                
                processed_posts.append(post.post_id)
                logger.info(f"Successfully processed post: {post.post_id}")
                
            except Exception as e:
                error_msg = f"Error processing post {post.post_id}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                continue

        return AddInstagramAudioOutput(
            success=len(processed_posts) > 0,
            processed_posts=processed_posts,
            error_message="; ".join(errors) if errors else ""
        )
    
#  limits and start of querying the database -------------------------------

from typing import Type, Any
from pydantic.v1 import BaseModel, Field
from crewai_tools.tools.base_tool import BaseTool
import logging

logger = logging.getLogger(__name__)

class QueryDatabaseInput(BaseModel):
    """Input for QueryDatabase."""
    query: str = Field(
        ..., description="The query to run against the database"
    )
    class Config:
        arbitrary_types_allowed = True

class QueryDatabaseOutput(BaseModel):
    """Output from QueryDatabase."""
    answer: str = Field(..., description="The response from the database")
    success: bool = Field(..., description="Whether the query was successful")

    class Config:
        arbitrary_types_allowed = True
        
class QueryDatabaseTool(BaseTool):
    name: str = "Query Database"
    description: str = "Queries the vector database"
    args_schema: Type[QueryDatabaseInput] = QueryDatabaseInput
    app: Any = Field(default=None, exclude=True)

    def _run(self, query: str) -> QueryDatabaseOutput:
        try:
            response = self.app.query(
                f"""Please analyze the following query about the Instagram content: {query}
                Focus on providing specific examples and quotes from the posts."""
            )
            
            if not response or (isinstance(response, str) and not response.strip()):
                return QueryDatabaseOutput(
                    answer="No relevant content found in the processed posts.",
                    success=False
                )
            
            return QueryDatabaseOutput(
                answer=f"Answer: {response}\n\nNote: This response is based on the processed Instagram content.",
                success=True
            )
                
        except Exception as e:
            return QueryDatabaseOutput(
                answer=f"Error querying database: {str(e)}",
                success=False
            )

# Get your app instance
from smartfunnel.tools.chroma_db_init import get_app_instance
app_instance = get_app_instance()

# Fetch posts
instagram_tool = FetchInstagramPostsTool()
posts_output = instagram_tool.run(instagram_username="antoineblanco99")

# Process videos
processor_tool = AddInstagramAudioTool(app=app_instance)
process_results = processor_tool.run(posts_output=posts_output)

# Query if successful
if process_results.success:
    query_tool = QueryDatabaseTool(app=app_instance)
    query_result = query_tool.run(query="Tell me about the content of these videos")
    print(query_result.answer if query_result.success else f"Query failed: {query_result.answer}")
else:
    print(f"Processing failed: {process_results.error_message}")