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

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for login credentials
INSTAGRAM_USERNAME = None
INSTAGRAM_PASSWORD = None

def set_instagram_credentials(username: str, password: str):
    """Set Instagram credentials globally"""
    global INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD
    INSTAGRAM_USERNAME = username
    INSTAGRAM_PASSWORD = password

class InstagramPost(BaseModel):
    """Model for Instagram post information."""
    post_id: str
    date: datetime
    caption: Optional[str]
    likes: int
    location: Optional[str]
    is_video: bool
    video_url: Optional[str]

class FetchInstagramPostsInput(BaseModel):
    """Input for FetchInstagramPosts."""
    instagram_username: str = Field(..., description="The Instagram username to fetch posts from.")
    days_back: int = Field(30, description="Number of days back to fetch posts from.")
    max_posts: int = Field(3, description="Maximum number of posts to fetch.")

class FetchInstagramPostsOutput(BaseModel):
    """Output for FetchInstagramPosts."""
    success: bool
    posts: List[InstagramPost] = []
    error_message: str = ""

class AddPostsToVectorDBInput(BaseModel):
    """Input for AddPostsToVectorDB."""
    posts: List[InstagramPost] = Field(..., description="List of Instagram posts to process")

class AddPostsToVectorDBOutput(BaseModel):
    """Output for AddPostsToVectorDB."""
    success: bool
    posts_processed: int = 0
    error_message: str = ""

class QueryInstagramDBInput(BaseModel):
    """Input for QueryInstagramDB."""
    query: str = Field(..., description="The query to search the Instagram content database")

class QueryInstagramDBOutput(BaseModel):
    """Output for QueryInstagramDB."""
    response: str = Field(..., description="The response from the query")
    error_message: str = Field(default="", description="Error message if the operation failed")
    success: bool = Field(..., description="Whether the operation was successful")

class CustomInstaloader(instaloader.Instaloader):
    """Custom Instaloader with rate limiting handling."""
    def do_sleep(self):
        sleep_duration = random.uniform(5, 15)
        time.sleep(sleep_duration)

    def _get_and_write_raw(self, *args, **kwargs):
        try:
            return super()._get_and_write_raw(*args, **kwargs)
        except instaloader.exceptions.ConnectionException as e:
            if "429" in str(e):
                logger.warning("Rate limit detected, sleeping for 60 seconds...")
                time.sleep(60)
                return super()._get_and_write_raw(*args, **kwargs)
            raise

class BaseInstagramTool(BaseTool):
    """Base class for Instagram tools with shared functionality"""
    
    model_config = {
        'arbitrary_types_allowed': True
    }

    def _get_session_filename(self, username: str) -> Path:
        machine_id = socket.gethostname()
        sessions_path = Path('instagram_sessions')
        sessions_path.mkdir(exist_ok=True)
        return sessions_path / f"{username}_{machine_id}_session"

    def _verify_session(self, L: CustomInstaloader, username: str) -> bool:
        try:
            profile = instaloader.Profile.from_username(L.context, username)
            next(profile.get_posts())
            return True
        except Exception as e:
            logger.warning(f"Session verification failed: {e}")
            return False

    def _login_to_instagram(self, L: CustomInstaloader, username: str, password: str) -> bool:
        try:
            session_file = self._get_session_filename(username)
            if session_file.exists():
                try:
                    L.load_session_from_file(username, str(session_file))
                    if self._verify_session(L, username):
                        return True
                    session_file.unlink(missing_ok=True)
                except Exception:
                    session_file.unlink(missing_ok=True)
            
            L.login(username, password)
            L.save_session_to_file(str(session_file))
            return self._verify_session(L, username)
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False

class FetchInstagramPostsTool(BaseInstagramTool):
    name: str = "Fetch Instagram Posts"
    description: str = "Fetches recent posts from an Instagram account."
    args_schema: Type[BaseModel] = FetchInstagramPostsInput
    return_schema: Type[BaseModel] = FetchInstagramPostsOutput
    _L: Optional[CustomInstaloader] = None

    def __init__(self):
        super().__init__()
        self._L = CustomInstaloader(
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            request_timeout=30
        )
        if not INSTAGRAM_USERNAME or not INSTAGRAM_PASSWORD:
            raise ValueError("Instagram credentials not set. Call set_instagram_credentials first.")
        if not self._login_to_instagram(self._L, INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD):
            raise Exception("Failed to login to Instagram")

    def _run(self, instagram_username: str, days_back: int = 30, max_posts: int = 3) -> FetchInstagramPostsOutput:
        try:
            logger.info(f"Fetching posts from profile: {instagram_username}")
            profile = instaloader.Profile.from_username(self._L.context, instagram_username)
            
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days_back)
            
            posts = []
            for post in profile.get_posts():
                if post.date.date() < start_date:
                    break
                if len(posts) >= max_posts:
                    break
                    
                if start_date <= post.date.date() <= end_date:
                    posts.append(InstagramPost(
                        post_id=post.shortcode,
                        date=post.date,
                        caption=post.caption,
                        likes=post.likes,
                        location=str(post.location) if post.location else None,
                        is_video=post.is_video,
                        video_url=post.video_url if post.is_video else None
                    ))
                time.sleep(random.uniform(2, 5))

            return FetchInstagramPostsOutput(success=True, posts=posts)
        except Exception as e:
            error_message = f"Error fetching Instagram posts: {str(e)}"
            logger.error(error_message)
            return FetchInstagramPostsOutput(success=False, error_message=error_message)

class AddPostsToVectorDBTool(BaseTool):
    name: str = "Add Posts to Vector DB"
    description: str = "Processes Instagram posts and adds their content to the vector database."
    args_schema: Type[BaseModel] = AddPostsToVectorDBInput
    return_schema: Type[BaseModel] = AddPostsToVectorDBOutput
    _app: Optional[App] = Field(default=None, exclude=True)

    model_config = {
        'arbitrary_types_allowed': True
    }

    def __init__(self, app: App):
        super().__init__()
        self._app = app

    def _process_post_description(self, post: InstagramPost) -> bool:
        try:
            description = f"""
Post Date: {post.date}
Caption: {post.caption if post.caption else 'No caption'}
Likes: {post.likes}
Location: {post.location if post.location else 'No location'}
"""
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=True) as temp_desc:
                temp_desc.write(description)
                temp_desc.flush()
                self._app.add(temp_desc.name, data_type="text_file")
                logger.info(f"Added description for post from {post.date}")
            return True
        except Exception as e:
            logger.error(f"Error processing description: {e}")
            return False

    def _process_video(self, video_url: str) -> bool:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(video_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=True) as temp_video:
                temp_video.write(response.content)
                temp_video.flush()
                
                video = VideoFileClip(temp_video.name)
                
                if video.audio is not None:
                    with tempfile.NamedTemporaryFile(suffix='.wav', delete=True) as temp_audio:
                        video.audio.write_audiofile(
                            temp_audio.name,
                            codec='pcm_s16le',
                            verbose=False,
                            logger=None
                        )
                        self._app.add(temp_audio.name, data_type="audio")
                        logger.info(f"Added audio from video")
                        
                video.close()
            return True
        except Exception as e:
            logger.error(f"Error processing video: {e}")
            return False

    def _run(self, posts: List[InstagramPost]) -> AddPostsToVectorDBOutput:
        try:
            posts_processed = 0
            content_processed = False
            
            for post in posts:
                logger.info(f"Processing post from {post.date}")
                
                if self._process_post_description(post):
                    content_processed = True
                
                if post.is_video and post.video_url:
                    if self._process_video(post.video_url):
                        posts_processed += 1
                        content_processed = True
                    time.sleep(random.uniform(5, 10))
                
                time.sleep(random.uniform(2, 5))

            if not content_processed:
                return AddPostsToVectorDBOutput(
                    success=True,
                    error_message="No content was processed from the posts",
                    posts_processed=0
                )

            return AddPostsToVectorDBOutput(success=True, posts_processed=posts_processed)
        except Exception as e:
            error_message = f"Error processing posts: {str(e)}"
            logger.error(error_message)
            return AddPostsToVectorDBOutput(
                success=False,
                error_message=error_message,
                posts_processed=posts_processed
            )
                
# from typing import List, Type
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
# from pydantic.v1 import BaseModel, Field
# from crewai_tools.tools.base_tool import BaseTool
# from embedchain import App

# # Set up logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# class FetchInstagramPostsInput(BaseModel):
#     """Input for FetchInstagramPosts."""
#     instagram_username: str = Field(..., description="The Instagram username to fetch posts from.")
#     days_back: int = Field(7, description="Number of days back to fetch posts from.")
#     max_posts: int = Field(3, description="Maximum number of posts to fetch.")

# class FetchInstagramPostsOutput(BaseModel):
#     """Output for FetchInstagramPosts."""
#     success: bool
#     error_message: str = ""
#     posts_processed: int = 0

# class CustomInstaloader(instaloader.Instaloader):
#     """Custom Instaloader with rate limiting handling."""
#     def do_sleep(self):
#         sleep_duration = random.uniform(5, 15)
#         time.sleep(sleep_duration)

#     def _get_and_write_raw(self, *args, **kwargs):
#         try:
#             return super()._get_and_write_raw(*args, **kwargs)
#         except instaloader.exceptions.ConnectionException as e:
#             if "429" in str(e):
#                 logger.warning("Rate limit detected, sleeping for 60 seconds...")
#                 time.sleep(60)
#                 return super()._get_and_write_raw(*args, **kwargs)
#             raise

# class FetchInstagramPostsTool(BaseTool):
#     name: str = "Fetch Instagram Posts"
#     description: str = "Fetches recent posts from an Instagram account and processes any video content into the vector database."
#     args_schema: Type[BaseModel] = FetchInstagramPostsInput
#     return_schema: Type[BaseModel] = FetchInstagramPostsOutput

#     def __init__(self, app: App, login_username: str, login_password: str):
#         super().__init__()
#         self._app = app
#         self._login_username = login_username
#         self._login_password = login_password
#         self._sessions_path = Path('instagram_sessions')
#         self._sessions_path.mkdir(exist_ok=True)
        
#         # Initialize Instaloader
#         self._L = CustomInstaloader(
#             download_videos=False,
#             download_video_thumbnails=False,
#             download_geotags=False,
#             download_comments=False,
#             save_metadata=False,
#             compress_json=False,
#             request_timeout=30
#         )
        
#         # Login during initialization
#         if not self._login_to_instagram():
#             raise Exception("Failed to login to Instagram")

#     def _get_session_filename(self) -> Path:
#         """Generate unique session filename."""
#         machine_id = socket.gethostname()
#         return self._sessions_path / f"{self._login_username}_{machine_id}_session"

#     def _verify_session(self) -> bool:
#         """Verify if the current session is valid."""
#         try:
#             profile = instaloader.Profile.from_username(self._L.context, self._login_username)
#             next(profile.get_posts())
#             return True
#         except Exception as e:
#             logger.warning(f"Session verification failed: {e}")
#             return False

#     def _login_to_instagram(self) -> bool:
#         """Handle Instagram login with session management."""
#         try:
#             session_file = self._get_session_filename()
            
#             if session_file.exists():
#                 try:
#                     self._L.load_session_from_file(self._login_username, str(session_file))
#                     if self._verify_session():
#                         return True
#                     session_file.unlink(missing_ok=True)
#                 except Exception:
#                     session_file.unlink(missing_ok=True)
            
#             self._L.login(self._login_username, self._login_password)
#             self._L.save_session_to_file(str(session_file))
            
#             return self._verify_session()
                
#         except Exception as e:
#             logger.error(f"Login failed: {e}")
#             return False

#     def _process_post_description(self, post) -> bool:
#         """Process post description and add to embedchain."""
#         try:
#             description = f"""
# Post Date: {post.date}
# Caption: {post.caption if post.caption else 'No caption'}
# Likes: {post.likes}
# Location: {post.location if post.location else 'No location'}
# """
#             with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=True) as temp_desc:
#                 temp_desc.write(description)
#                 temp_desc.flush()
#                 self._app.add(temp_desc.name, data_type="text_file")
#                 logger.info(f"Added description for post from {post.date}")
#             return True
#         except Exception as e:
#             logger.error(f"Error processing description: {e}")
#             return False

#     def _process_video(self, video_url: str) -> bool:
#         """Process video content and add to embedchain."""
#         try:
#             headers = {
#                 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
#             }
            
#             response = requests.get(video_url, headers=headers, timeout=30)
#             response.raise_for_status()
            
#             with tempfile.NamedTemporaryFile(suffix='.mp4', delete=True) as temp_video:
#                 temp_video.write(response.content)
#                 temp_video.flush()
                
#                 video = VideoFileClip(temp_video.name)
                
#                 if video.audio is not None:
#                     with tempfile.NamedTemporaryFile(suffix='.wav', delete=True) as temp_audio:
#                         video.audio.write_audiofile(
#                             temp_audio.name,
#                             codec='pcm_s16le',
#                             verbose=False,
#                             logger=None
#                         )
#                         self._app.add(temp_audio.name, data_type="audio")
#                         logger.info(f"Added audio from video")
                        
#                 video.close()
#             return True
            
#         except Exception as e:
#             logger.error(f"Error processing video: {e}")
#             return False

#     def _run(
#         self,
#         instagram_username: str,
#         days_back: int = 7,
#         max_posts: int = 3
#     ) -> FetchInstagramPostsOutput:
#         """Main execution method."""
#         try:
#             logger.info(f"Analyzing profile: {instagram_username}")
#             profile = instaloader.Profile.from_username(self._L.context, instagram_username)
            
#             end_date = datetime.now().date()
#             start_date = end_date - timedelta(days=days_back)
#             logger.info(f"Fetching posts from {start_date} to {end_date}")
            
#             posts_processed = 0
#             content_processed = False
            
#             for post in profile.get_posts():
#                 if post.date.date() < start_date:
#                     break
#                 if posts_processed >= max_posts:
#                     break
                    
#                 if start_date <= post.date.date() <= end_date:
#                     logger.info(f"Processing post from {post.date}")
                    
#                     # Process description
#                     if self._process_post_description(post):
#                         content_processed = True
                    
#                     # Process video if present
#                     if post.is_video and post.video_url:
#                         if self._process_video(post.video_url):
#                             posts_processed += 1
#                             content_processed = True
#                         time.sleep(random.uniform(5, 10))
                    
#                     time.sleep(random.uniform(2, 5))

#             if not content_processed:
#                 return FetchInstagramPostsOutput(
#                     success=True,
#                     error_message="No content was processed from the posts",
#                     posts_processed=0
#                 )

#             return FetchInstagramPostsOutput(
#                 success=True,
#                 posts_processed=posts_processed
#             )
            
#         except Exception as e:
#             error_message = f"Error processing Instagram posts: {str(e)}"
#             logger.error(error_message)
#             return FetchInstagramPostsOutput(
#                 success=False,
#                 error_message=error_message,
#                 posts_processed=posts_processed
#             )

# from crewai_tools.tools.base_tool import BaseTool
# from pydantic.v1 import BaseModel, Field, PrivateAttr
# from typing import Type
# import instaloader
# import logging
# import tempfile
# from datetime import datetime, timedelta
# import random
# import time
# from pathlib import Path
# import socket
# import itertools
# from moviepy.editor import VideoFileClip
# import requests
# from embedchain import App
# from typing import Any, Type

# class FetchInstagramDataInput(BaseModel):
#     instagram_username: str = Field(..., description="The Instagram username to fetch data from")
#     days_back: int = Field(default=7, description="Number of days of content to fetch")
#     max_posts: int = Field(default=3, description="Maximum number of posts to process")

# class FetchInstagramDataOutput(BaseModel):
#     success: bool = Field(..., description="Whether the operation was successful")
#     error_message: str = Field(default="", description="Error message if operation failed")
#     posts_processed: int = Field(default=0, description="Number of posts successfully processed")


# class FetchInstagramDataTool(BaseTool):
#     name: str = "Fetch Instagram Data"
#     description: str = "Fetches and processes Instagram posts, adding them to a vector database"
#     args_schema: Type[BaseModel] = FetchInstagramDataInput
#     return_schema: Type[BaseModel] = FetchInstagramDataOutput
#     app: Any = Field(default=None, exclude=True)
#     # class Config:
#     #     arbitrary_types_allowed = True

# class CustomInstaloader(instaloader.Instaloader):
#     def do_sleep(self):
#         sleep_duration = random.uniform(5, 15)
#         time.sleep(sleep_duration)

#     def _get_and_write_raw(self, *args, **kwargs):
#         try:
#             return super()._get_and_write_raw(*args, **kwargs)
#         except instaloader.exceptions.ConnectionException as e:
#             if "429" in str(e):
#                 time.sleep(60)
#                 return super()._get_and_write_raw(*args, **kwargs)
#             raise

#     def __init__(self, app: App, login_username: str, login_password: str, **data):
#         super().__init__(**data)
#         self.app = app
#         self.login_username = login_username
#         self.login_password = login_password
        
#         self._logger = logging.getLogger(__name__)
#         self._sessions_path = Path('instagram_sessions')
#         self._sessions_path.mkdir(exist_ok=True)
        
#         self._L = CustomInstaloader(
#             download_videos=False,
#             download_video_thumbnails=False,
#             download_geotags=False,
#             download_comments=False,
#             save_metadata=False,
#             compress_json=False,
#             request_timeout=30
#         )

#     def verify_session(self, username: str) -> bool:
#         try:
#             profile = instaloader.Profile.from_username(self._L.context, username)
#             next(itertools.islice(profile.get_posts(), 1), None)
#             return True
#         except Exception as e:
#             self._logger.warning(f"Session verification failed: {e}")
#             return False

#     def get_session_filename(self, username: str) -> Path:
#         machine_id = socket.gethostname()
#         return self._sessions_path / f"{username}_{machine_id}_session"

#     def login_to_instagram(self) -> bool:
#         try:
#             if not self.login_username or not self.login_password:
#                 raise ValueError("Login credentials not provided")
                
#             session_file = self.get_session_filename(self.login_username)
            
#             if session_file.exists():
#                 try:
#                     self._L.load_session_from_file(self.login_username, str(session_file))
#                     if self.verify_session(self.login_username):
#                         return True
#                     session_file.unlink(missing_ok=True)
#                 except Exception:
#                     session_file.unlink(missing_ok=True)
            
#             self._L.login(self.login_username, self.login_password)
#             self._L.save_session_to_file(str(session_file))
            
#             return self.verify_session(self.login_username)
                
#         except Exception as e:
#             self._logger.error(f"Login failed: {e}")
#             return False

#     def process_post_description(self, post) -> bool:
#         try:
#             description = f"""
# Post Date: {post.date}
# Caption: {post.caption if post.caption else 'No caption'}
# Likes: {post.likes}
# Location: {post.location if post.location else 'No location'}
# """
#             with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_desc:
#                 temp_desc.write(description)
#                 temp_desc.flush()
#                 self.app.add(temp_desc.name, data_type="text_file")
#             return True
                
#         except Exception as e:
#             self._logger.error(f"Error processing description: {e}")
#             return False

#     def process_video(self, video_url, post_date) -> bool:
#         try:
#             headers = {
#                 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
#             }
            
#             response = requests.get(video_url, headers=headers, timeout=30)
#             response.raise_for_status()
            
#             with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_video:
#                 temp_video.write(response.content)
#                 temp_video.flush()
                
#                 video = VideoFileClip(temp_video.name)
                
#                 if video.audio is not None:
#                     with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
#                         video.audio.write_audiofile(
#                             temp_audio.name,
#                             codec='pcm_s16le',
#                             verbose=False,
#                             logger=None
#                         )
#                         self.app.add(temp_audio.name, data_type="audio")
                        
#                 video.close()
#             return True
            
#         except Exception as e:
#             self._logger.error(f"Error processing video: {e}")
#             return False

#     def _run(self, **kwargs) -> FetchInstagramDataOutput:
#         """
#         Run the tool with the provided input parameters.
#         The method accepts kwargs that match the FetchInstagramDataInput model.
#         """
#         try:
#             # Convert input parameters to model
#             input_data = FetchInstagramDataInput(
#                 instagram_username=kwargs.get('instagram_handle', ''),  # Match the placeholder in YAML
#                 days_back=kwargs.get('days_back', 7),
#                 max_posts=kwargs.get('max_posts', 3)
#             )

#             if not self.login_to_instagram():
#                 return FetchInstagramDataOutput(
#                     success=False,
#                     error_message="Failed to login to Instagram",
#                     posts_processed=0
#                 )

#             profile = instaloader.Profile.from_username(self._L.context, input_data.instagram_username)
            
#             end_date = datetime.now().date()
#             start_date = end_date - timedelta(days=input_data.days_back)
            
#             posts_processed = 0
#             post_iterator = profile.get_posts()
            
#             for post in itertools.islice(post_iterator, 20):
#                 if post.date.date() < start_date:
#                     break
#                 if start_date <= post.date.date() <= end_date:
#                     if self.process_post_description(post):
#                         posts_processed += 1
                        
#                     if post.is_video:
#                         video_url = post.video_url
#                         if video_url:
#                             if self.process_video(video_url, post.date):
#                                 time.sleep(random.uniform(10, 20))
                                
#                     if posts_processed >= input_data.max_posts:
#                         break
                        
#                 time.sleep(random.uniform(2, 5))
                
#             return FetchInstagramDataOutput(
#                 success=True,
#                 posts_processed=posts_processed
#             )
            
#         except Exception as e:
#             self._logger.error(f"Error in _run: {str(e)}")
#             return FetchInstagramDataOutput(
#                 success=False,
#                 error_message=str(e),
#                 posts_processed=posts_processed if 'posts_processed' in locals() else 0
#             )