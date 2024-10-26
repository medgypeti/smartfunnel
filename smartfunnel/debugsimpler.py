
from typing import Any, Type, List
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

OPENAI_API_KEY = "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"

# Set up Deepgram
os.environ["DEEPGRAM_API_KEY"] = "46d16104048c4bd6b223b69c7bc05b2a3df4de75"
# deepgram = Deepgram(DEEPGRAM_API_KEY)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a temporary directory for ChromaDB
# db_path = tempfile.mkdtemp()
# logger.info(f"Created temporary directory for ChromaDB: {db_path}")

# # Configuration dictionary
# config = {
#     'app': {
#         'config': {
#             'name': 'full-stack-app'
#         }
#     },
#     'llm': {
#         'provider': 'openai',
#         'config': {
#             'model': 'gpt-4',
#             'temperature': 0.3,
#             'max_tokens': 8000,
#             'prompt': (
#                 "Reply to the $query by providing as much information about the protagonist in the video as possible.\n"
#                 "Be comprehensive, accurate and precise. Share as much information as possible.\n"
#                 "Everytime you answer a question, figure out why it matters to the audience, and why it matters to the protagonist, and where/how he developed this trait, and how he's using it in practice in his life and business. Be specific\n"
#                 "Always try to extract the actionable practical advice from the video.\n"
#                 "Always keep the storytelling part that's relevant to the query. Keep ALL the details of the story as accurate and precise as possible.\n"
#                 "For every reply, you should respond in sections, where each section is a single idea/concept/lesson/value/motivation/belief/etc.\n"
#                 "In each section, you should provide a clear claim, anecdote/story that was mentioned in the transcript to justify your claim.\n"
#                 "For every section, you should provide 1-3 hyper actionable and practical advice, tips that can be derived and executed from this insight.\n"
#                 "If you don't know the answer, just say that you don't know, don't try to make up an answer.\n"
#                 "Always end your reply with a summary of the main points you covered in the reply.\n"
#                 "Always translate the quotes back to English.\n"
#                 "$context\n\nQuery: $query\n\nHelpful Answer:"
#             ),
#             'system_prompt': (
#                 "Act as a potential customer of the author of the video. Interpret the answers based on what's in it for you. You want to learn practical advice that you can apply in your own personal or professional life. You know the importance of author's advice and takeaways, and real-lifestorytelling to absorb lessons."
#             ),
#             'api_key': OPENAI_API_KEY,
#         }
#     },
#     'vectordb': {
#         'provider': 'chroma',
#         'config': {
#             'dir': db_path,
#             'allow_reset': True
#         }
#     },
#     'embedder': {
#         'provider': 'openai',
#         'config': {
#             'model': 'text-embedding-ada-002',
#             'api_key': OPENAI_API_KEY,
#         }
#     },
# }

# def get_app_instance():
#     return App.from_config(config=config)

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
                username = os.getenv("INSTAGRAM_USERNAME", "vladzieg")
                password = os.getenv("INSTAGRAM_PASSWORD", "Lommel1996+")
                
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
                    if post_count >= 4:
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

class AddInstagramAudioInput(BaseModel):
    """Input for AddInstagramAudio."""
    posts: List[PostInfo] = Field(..., description="The Instagram posts to process")

class AddInstagramAudioOutput(BaseModel):
    """Output from AddInstagramAudio."""
    success: bool = Field(..., description="Whether the audio was successfully added to the vector DB")
    processed_posts: List[str] = Field(default_factory=list, description="List of successfully processed post IDs")
    error_message: str = Field(default="", description="Error message if any operations failed")

class AddInstagramAudioTool(BaseTool):
    """Tool that processes Instagram videos as audio and adds them to the vector database."""
    name: str = "Add Instagram Audio to Vector DB"
    description: str = "Adds Instagram video audio to the vector database using EmbedChain"
    args_schema: Type[BaseModel] = AddInstagramAudioInput
    app: Any = Field(default=None, exclude=True)

    def __init__(self, app: App, **data):
        super().__init__(**data)
        self.app = app
        
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

    def _run(self, posts: List[PostInfo]) -> AddInstagramAudioOutput:
        processed_posts = []
        errors = []

        # Filter video posts
        video_posts = [post for post in posts if post.is_video and post.video_url]
        
        for post in video_posts:
            temp_audio_path = None
            try:
                # Download video and convert to audio
                video_response = requests.get(post.video_url)
                video_buffer = io.BytesIO(video_response.content)
                audio = AudioSegment.from_file(video_buffer, format="mp4")
                
                # Export as WAV to memory
                audio_buffer = io.BytesIO()
                audio.export(audio_buffer, format="wav")
                audio_buffer.seek(0)
                
                # Save to temporary file
                temp_audio_path = self._process_audio(audio_buffer)
                
                # Add to embedchain with metadata
                self.app.add(
                    temp_audio_path,
                    data_type="audio",
                    metadata={
                        "source": post.url,
                        "caption": post.caption,
                        "timestamp": post.timestamp.isoformat(),
                        "likes": post.likes,
                        "post_id": post.post_id
                    }
                )
                
                processed_posts.append(post.post_id)
                logger.info(f"Successfully processed post: {post.post_id}")
                
            except Exception as e:
                error_msg = f"Error processing post {post.post_id}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
            finally:
                # Clean up temporary file
                if temp_audio_path:
                    self._cleanup_temp_file(temp_audio_path)
                
        return AddInstagramAudioOutput(
            success=len(processed_posts) > 0,
            processed_posts=processed_posts,
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
    name: str = "Query Database"
    description: str = "Queries the vector database containing processed Instagram content"
    args_schema: Type[BaseModel] = QueryDatabaseInput
    app: Any = Field(default=None, exclude=True)

    def __init__(self, app: App, **data):
        super().__init__(**data)
        self.app = app

    def _run(self, query: str) -> QueryDatabaseOutput:
        try:
            logger.info(f"Querying vector DB with: {query}")
            reply = self.app.query(
                f"""Please analyze the following query about the Instagram content: {query}
                Focus on providing specific examples and quotes from the posts."""
            )
            logger.info("Query completed successfully")
            
            if not reply or (isinstance(reply, str) and not reply.strip()):
                return QueryDatabaseOutput(
                    reply="No relevant content found in the processed posts.",
                    error_message="Empty response from database"
                )
            
            return QueryDatabaseOutput(reply=reply)
                
        except Exception as e:
            error_message = f"Failed to query vector DB: {str(e)}"
            logger.error(error_message)
            return QueryDatabaseOutput(
                reply="Error occurred",
                error_message=error_message
            )

from smartfunnel.tools.chroma_db_init import get_app_instance

def main():
    # Get app instance
    app_instance = get_app_instance()
    
    # Initialize tools with app instance
    fetch_tool = FetchInstagramPostsTool()
    process_tool = AddInstagramAudioTool(app=app_instance)
    query_tool = QueryDatabaseTool(app=app_instance)

    try:
        # Fetch posts
        instagram_username = "antoineblanco99"
        print(f"Fetching posts from {instagram_username}...")
        fetch_result = fetch_tool.run(instagram_username=instagram_username)
        
        if fetch_result.success:
            print(f"Successfully fetched {len(fetch_result.posts)} posts")
            
            # Process videos
            print("Processing videos...")
            process_results = process_tool.run(posts=fetch_result.posts)
            
            if process_results.success:
                print(f"Successfully processed {len(process_results.processed_posts)} posts")
                print("Processed posts IDs:", process_results.processed_posts)
                
                # Query the database
                print("\nQuerying database...")
                query = "Tell me about the content of these videos"
                query_result = query_tool.run(query=query)
                
                print("\nQuery Results:")
                print("-------------")
                if query_result.error_message:
                    print(f"Query error: {query_result.error_message}")
                else:
                    print(f"Response: {query_result.reply}")
            else:
                print(f"Processing failed: {process_results.error_message}")
        else:
            print(f"Fetching failed: {fetch_result.error_message}")

    except Exception as e:
        print(f"Error in main execution: {str(e)}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    main()