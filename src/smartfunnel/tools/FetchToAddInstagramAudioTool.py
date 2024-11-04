from typing import Any, Type, List, Union
from datetime import datetime
from pydantic import BaseModel, Field
from crewai_tools.tools.base_tool import BaseTool
import instaloader
import logging
import os
import time
import tempfile
import requests
import io
from pydub import AudioSegment
from embedchain import App
from groq import Groq
# import streamlit as st
from contextlib import contextmanager
from deepgram import DeepgramClient, PrerecordedOptions

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


from typing import Any, Type, List, Union, Dict
from datetime import datetime
from pydantic import BaseModel, Field
from crewai_tools.tools.base_tool import BaseTool
import instaloader
import logging
import os
import time
import tempfile
import requests
import io
import json
from pydub import AudioSegment
from embedchain import App
from groq import Groq
import streamlit as st
from contextlib import contextmanager
from deepgram import DeepgramClient, PrerecordedOptions

# Configuration
class Config:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    INSTAGRAM_USERNAME = st.secrets["INSTAGRAM_USERNAME"]
    INSTAGRAM_PASSWORD = st.secrets["INSTAGRAM_PASSWORD"]
    DEEPGRAM_API_KEY = st.secrets["DEEPGRAM_API_KEY"]

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeepgramResponse(BaseModel):
    """Model for Deepgram response data."""
    transcript: str
    confidence: float
    words: List[Dict]
    duration: float
    start_times: List[float]
    end_times: List[float]

class TranscriptionResult:
    """Wrapper for transcription results."""
    def __init__(self, text: str, metadata: Dict):
        self.text = text
        self.metadata = metadata

def parse_deepgram_response(response_data: Dict) -> TranscriptionResult:
    """
    Parse Deepgram response and extract relevant information.
    Updated to match Deepgram's JSON structure.
    """
    try:
        # Extract basic metadata
        metadata = {
            "duration": response_data["metadata"]["duration"],
            "channels": response_data["metadata"]["channels"],
            "models": response_data["metadata"]["models"],
            "created": response_data["metadata"]["created"],
            "request_id": response_data["metadata"]["request_id"]
        }

        # Get model info from the first model
        if response_data["metadata"]["model_info"]:
            first_model = list(response_data["metadata"]["model_info"].values())[0]
            metadata["model_info"] = {
                "name": first_model["name"],
                "version": first_model["version"],
                "arch": first_model["arch"]
            }
        
        # Extract transcript from results structure
        transcript = response_data["results"]["channels"][0]["alternatives"][0]["transcript"]
        confidence = response_data["results"]["channels"][0]["alternatives"][0]["confidence"]
        
        # Add confidence to metadata
        metadata["confidence"] = confidence
        
        return TranscriptionResult(transcript, metadata)
    except KeyError as e:
        logger.error(f"Error parsing Deepgram response: {str(e)}")
        raise ValueError("Invalid Deepgram response format")

class PostInfo(BaseModel):
    """Instagram post information with relevance score."""
    post_id: str
    caption: str
    timestamp: datetime
    likes: int
    url: str
    is_video: bool
    video_url: str = ""
    relevance_score: float = 0.0
    transcription: str = ""

    class Config:
        arbitrary_types_allowed = True

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

class VideoDownloadError(Exception):
    """Custom exception for video download failures."""
    pass

@contextmanager
def temporary_file_manager(suffix='.wav'):
    """Context manager for handling temporary files."""
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, f'temp{suffix}')
    try:
        yield temp_path
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)

class FetchToAddInstagramAudioTool(BaseTool):
    name: str = "Fetch and Process Instagram Audio"
    description: str = "Fetches Instagram posts, ranks them, transcribes audio, and adds to vector database"
    args_schema: Type[BaseModel] = FetchToAddInstagramAudioInput
    insta_loader: Any = Field(default=None, exclude=True)
    app: Any = Field(default=None, exclude=True)
    is_initialized: bool = Field(default=False, exclude=True)
    session_file: str = Field(default="", exclude=True)
    groq_client: Any = Field(default=None, exclude=True)
    deepgram_client: Any = Field(default=None, exclude=True)

    def __init__(self, app: App, **data):
        super().__init__(**data)
        self.app = app
        self.session_file = os.path.join(tempfile.gettempdir(), "instagram_session")
        self.is_initialized = False
        # Initialize clients with direct API keys
        self.groq_client = Groq(api_key=Config.GROQ_API_KEY)
        self.deepgram_client = DeepgramClient(Config.DEEPGRAM_API_KEY)

    def _get_instaloader_instance(self):
        """Get or create a shared Instaloader instance with session management."""
        if not self.insta_loader:
            self.insta_loader = instaloader.Instaloader()
            try:
                username = Config.INSTAGRAM_USERNAME
                password = Config.INSTAGRAM_PASSWORD

                if os.path.exists(self.session_file):
                    try:
                        self.insta_loader.load_session_from_file(username, self.session_file)
                        logger.info("Successfully loaded existing Instagram session")
                        return self.insta_loader
                    except Exception as e:
                        logger.warning(f"Failed to load existing session: {str(e)}")
                
                self.insta_loader.login(username, password)
                self.insta_loader.save_session_to_file(self.session_file)
                logger.info("Successfully created new Instagram session")
                
            except Exception as e:
                logger.error(f"Failed to login to Instagram: {str(e)}")
                raise

        return self.insta_loader

    def initialize_for_new_creator(self):
        """Reset the vector database before starting analysis for a new creator."""
        logger.info("Initializing vector database for new creator")
        if self.app is not None:
            self.app.reset()
            logger.info("Vector database reset successfully")
        else:
            logger.error("No app instance available for reset")
        self.is_initialized = True

    def _retry_operation(self, operation, max_retries=3, delay=5):
        """Generic retry mechanism for Instagram operations."""
        last_error = None
        for attempt in range(max_retries):
            try:
                return operation()
            except instaloader.exceptions.ProfileNotExistsException:
                logger.error("Profile does not exist")
                return None
            except Exception as e:
                last_error = e
                if attempt + 1 < max_retries:
                    logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                    time.sleep(delay * (attempt + 1))
                    
                    if "login" in str(e).lower() or "429" in str(e):
                        self.insta_loader = None
                        self._get_instaloader_instance()
                    
        raise last_error

    def _download_video_with_retry(self, video_url: str, max_retries=3) -> bytes:
        """Download video content with retry mechanism."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    video_url, 
                    headers=headers, 
                    timeout=30,
                    allow_redirects=True
                )
                
                if response.status_code == 200:
                    return response.content
                elif response.status_code == 500:
                    logger.warning(f"500 error on attempt {attempt + 1}, trying alternative URL format")
                    alt_url = video_url.split('?')[0]
                    alt_response = requests.get(
                        alt_url,
                        headers=headers,
                        timeout=30,
                        allow_redirects=True
                    )
                    if alt_response.status_code == 200:
                        return alt_response.content
                
                logger.error(f"Attempt {attempt + 1} failed with status code: {response.status_code}")
                
            except requests.RequestException as e:
                logger.error(f"Attempt {attempt + 1} failed with error: {str(e)}")
                
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                
        raise VideoDownloadError(f"Failed to download video after {max_retries} attempts")

    def _get_video_url(self, post, max_retries=3):
        """Get video URL with fallback options."""
        for attempt in range(max_retries):
            try:
                if hasattr(post, 'video_url'):
                    return post.video_url
                post_json = post._node
                if 'video_url' in post_json:
                    return post_json['video_url']
                if 'video_resources' in post_json:
                    return post_json['video_resources'][0]['src']
            except Exception as e:
                logger.error(f"Error getting video URL on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                
        raise ValueError("Could not extract video URL")

    def _transcribe_video_url(self, video_url: str) -> TranscriptionResult:
        """
        Transcribe video directly from URL using Deepgram.
        """
        try:
            # Configure Deepgram options
            options = PrerecordedOptions(
                model="nova-2",
                language="fr",
                smart_format=True,
            )
            
            # Create the URL payload
            payload = {
                "url": video_url
            }
            
            logger.info(f"Sending URL to Deepgram for transcription: {video_url}")
            
            # Send to Deepgram using transcribe_url
            response = self.deepgram_client.listen.prerecorded.v("1").transcribe_url(
                payload,
                options
            )
            
            # Get response as dictionary
            response_dict = json.loads(response.to_json())
            
            # Debug log
            logger.info(f"Raw Deepgram response: {json.dumps(response_dict, indent=2)}")
            
            # Extract metadata
            metadata = {
                "duration": response_dict.get("metadata", {}).get("duration", 0),
                "channels": response_dict.get("metadata", {}).get("channels", 1),
                "created": response_dict.get("metadata", {}).get("created", ""),
                "request_id": response_dict.get("metadata", {}).get("request_id", "")
            }
            
            # Extract transcript and confidence
            results = response_dict.get("results", {})
            channels = results.get("channels", [{}])
            alternatives = channels[0].get("alternatives", [{}])
            transcript = alternatives[0].get("transcript", "")
            confidence = alternatives[0].get("confidence", 0.0)
            
            # Add confidence to metadata
            metadata["confidence"] = confidence
            
            # Log success or warning
            if transcript:
                logger.info(f"Transcription successful: {len(transcript)} characters")
            else:
                logger.warning("No transcript returned from Deepgram")
            
            return TranscriptionResult(transcript, metadata)

        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            raise

    def _process_video(self, post: Union[Any, PostInfo], post_metadata: dict) -> bool:
        """
        Process a single video: get URL and transcribe directly.
        """
        try:
            # Handle both PostInfo objects and raw instaloader Post objects
            if isinstance(post, PostInfo):
                video_url = post.video_url
            else:
                video_url = self._get_video_url(post)
                
            logger.info(f"Processing video from URL: {video_url}")
            
            try:
                # Transcribe directly from URL
                transcription_result = self._transcribe_video_url(video_url)
                
                # Print transcription details
                print("\n" + "="*50)
                print(f"Transcription for post: {post_metadata['post_id']}")
                print(f"Post URL: {post_metadata['source']}")
                print("\nTranscribed Content:")
                print("-"*50)
                print(transcription_result.text or "NO TRANSCRIPT FOUND")
                print("-"*50)
                print(f"Confidence Score: {transcription_result.metadata.get('confidence', 0.0):.2f}")
                print(f"Duration: {transcription_result.metadata.get('duration', 0.0):.2f} seconds")
                print("="*50 + "\n")
                
                if not transcription_result.text:
                    logger.warning("Empty transcript returned from Deepgram")
                    return False
                
                # Add to vector database
                enhanced_metadata = {
                    **post_metadata,
                    "data_type": "text",
                    "processing_timestamp": datetime.now().isoformat(),
                    "source_platform": "instagram",
                    "content_type": "video_transcription",
                    "audio_duration": transcription_result.metadata.get("duration", 0.0),
                    "transcription_confidence": transcription_result.metadata.get("confidence", 0.0),
                    "video_url": video_url,
                    "transcription_timestamp": transcription_result.metadata.get("created", ""),
                    "request_id": transcription_result.metadata.get("request_id", "")
                }
                
                self.app.add(
                    transcription_result.text,
                    data_type="text",
                    metadata=enhanced_metadata
                )
                
                logger.info(f"Successfully processed video for post {post_metadata['post_id']}")
                return True
                
            except Exception as e:
                logger.error(f"Transcription failed for post {post_metadata['post_id']}: {str(e)}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing video for post {post_metadata['post_id']}: {str(e)}")
            return False
        
    def _analyze_post_relevance(self, post: PostInfo) -> float:
        """
        Analyze post caption for personal story relevance using Groq LLM.
        Returns a relevance score from 0 to 10.
        """
        try:
            prompt = f"""
            Rate the following Instagram post caption on a scale of 1-10 based on how much it reveals about the creator's personal story, journey, or experiences.
            A score of 1 means it's purely promotional or unrelated to personal stories.
            A score of 10 means it's a deep, meaningful personal story or reflection.

            Caption: {post.caption}

            Only respond with a single number between 1 and 10. No other text.
            """

            response = self.groq_client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=5
            )

            score = float(response.choices[0].message.content.strip())
            return min(max(score, 1), 10)  # Ensure score is between 1 and 10

        except Exception as e:
            logger.error(f"Error analyzing post relevance: {str(e)}")
            return 0.0

    def _fetch_and_rank_posts(self, profile: Any, max_posts: int = 30) -> List[PostInfo]:
        """
        Fetch posts and rank them based on personal story relevance.
        """
        all_posts = []
        post_count = 0

        try:
            for post in profile.get_posts():
                if post_count >= max_posts:
                    break

                post_info = PostInfo(
                    post_id=post.shortcode,
                    caption=post.caption if post.caption else "",
                    timestamp=post.date_utc,
                    likes=post.likes,
                    url=f"https://www.instagram.com/p/{post.shortcode}/",
                    is_video=post.is_video,
                    video_url=self._get_video_url(post) if post.is_video else ""
                )

                # Analyze post relevance
                post_info.relevance_score = self._analyze_post_relevance(post_info)
                all_posts.append(post_info)
                post_count += 1

                # Add small delay to avoid rate limiting
                time.sleep(0.5)

        except Exception as e:
            logger.error(f"Error fetching posts: {str(e)}")

        # Sort posts by relevance score and return top ones
        ranked_posts = sorted(all_posts, key=lambda x: x.relevance_score, reverse=True)
        return ranked_posts[:40]  # Return top 40 most relevant posts

    def _run(self, instagram_username: str) -> str:
        if not self.is_initialized:
            self.initialize_for_new_creator()
            
        try:
            logger.info(f"Fetching posts for user: {instagram_username}")
            profile = self._retry_operation(lambda: instaloader.Profile.from_username(
                self._get_instaloader_instance().context, 
                instagram_username
            ))
            
            if profile is None:
                return "Instagram profile not found"

            # Fetch and rank posts
            ranked_posts = self._fetch_and_rank_posts(profile)
            
            processed_videos = []
            errors = []
            total_relevant_posts = len(ranked_posts)
            video_posts = [post for post in ranked_posts if post.is_video]
            
            for post in video_posts:
                try:
                    post_metadata = {
                        "source": post.url,
                        "caption": post.caption,
                        "timestamp": post.timestamp.isoformat(),
                        "likes": post.likes,
                        "post_id": post.post_id,
                        "relevance_score": post.relevance_score
                    }
                    
                    if self._process_video(post, post_metadata):
                        processed_videos.append(post.post_id)
                        
                except Exception as post_error:
                    error_msg = f"Error processing post {post.post_id}: {str(post_error)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    continue

            success = len(processed_videos) > 0
            error_message = "; ".join(errors) if errors else ""
            
            summary = f"Analyzed {total_relevant_posts} posts from top 200 posts.\n"
            summary += f"Found {len(video_posts)} video posts among relevant content.\n"
            summary += f"Successfully processed and transcribed {len(processed_videos)} videos.\n"
            
            if ranked_posts:
                avg_score = sum(p.relevance_score for p in ranked_posts) / len(ranked_posts)
                max_score = max(p.relevance_score for p in ranked_posts)
                summary += f"Average relevance score: {avg_score:.1f}\n"
                summary += f"Highest relevance score: {max_score:.1f}\n"
            
            if errors:
                summary += f"Errors encountered: {error_message}"

            return summary

        except Exception as e:
            error_message = f"Error in fetch and process operation: {str(e)}"
            logger.error(error_message)
            return error_message

#  Transslating French

# from typing import Any, Type, List, Union
# from datetime import datetime
# from pydantic import BaseModel, Field
# from crewai_tools.tools.base_tool import BaseTool
# import instaloader
# import logging
# import os
# import time
# import tempfile
# import requests
# import io
# from pydub import AudioSegment
# from embedchain import App
# from groq import Groq
# import streamlit as st
# from contextlib import contextmanager



# # Set up logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# class PostInfo(BaseModel):
#     """Instagram post information with relevance score."""
#     post_id: str
#     caption: str
#     timestamp: datetime
#     likes: int
#     url: str
#     is_video: bool
#     video_url: str = ""
#     relevance_score: float = 0.0

#     class Config:
#         arbitrary_types_allowed = True

# class FetchToAddInstagramAudioInput(BaseModel):
#     """Input for FetchToAddInstagramAudio."""
#     instagram_username: str = Field(..., description="The Instagram username to fetch posts from")

# class FetchToAddInstagramAudioOutput(BaseModel):
#     """Output containing results of fetch and audio processing."""
#     processed_videos: List[str] = Field(default_factory=list, description="List of successfully processed video URLs")
#     success: bool = Field(..., description="Whether the operation was successful")
#     error_message: str = Field(default="", description="Error message if any operations failed")
#     total_posts_found: int = Field(default=0, description="Total number of posts found")
#     total_videos_processed: int = Field(default=0, description="Total number of videos processed")

# class VideoDownloadError(Exception):
#     """Custom exception for video download failures."""
#     pass

# @contextmanager
# def temporary_file_manager(suffix='.wav'):
#     """Context manager for handling temporary files."""
#     temp_dir = tempfile.mkdtemp()
#     temp_path = os.path.join(temp_dir, f'temp{suffix}')
#     try:
#         yield temp_path
#     finally:
#         if os.path.exists(temp_path):
#             os.remove(temp_path)
#         if os.path.exists(temp_dir):
#             os.rmdir(temp_dir)

# class FetchToAddInstagramAudioTool(BaseTool):
#     name: str = "Fetch and Process Instagram Audio"
#     description: str = "Fetches Instagram posts, ranks them by personal story relevance, and adds video audio to the vector database"
#     args_schema: Type[BaseModel] = FetchToAddInstagramAudioInput
#     insta_loader: Any = Field(default=None, exclude=True)
#     app: Any = Field(default=None, exclude=True)
#     is_initialized: bool = Field(default=False, exclude=True)
#     session_file: str = Field(default="", exclude=True)
#     groq_client: Any = Field(default=None, exclude=True)

#     def __init__(self, app: App, **data):
#         super().__init__(**data)
#         self.app = app
#         self.session_file = os.path.join(tempfile.gettempdir(), "instagram_session")
#         self.is_initialized = False
#         self.groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

#     def initialize_for_new_creator(self):
#         """Reset the vector database before starting analysis for a new creator."""
#         logger.info("Initializing vector database for new creator")
#         if self.app is not None:
#             self.app.reset()
#             logger.info("Vector database reset successfully")
#         else:
#             logger.error("No app instance available for reset")
#         self.is_initialized = True

#     def _get_instaloader_instance(self):
#         """Get or create a shared Instaloader instance with session management."""
#         if not self.insta_loader:
#             self.insta_loader = instaloader.Instaloader()
#             try:
#                 username = st.secrets["INSTAGRAM_USERNAME"]
#                 password = st.secrets["INSTAGRAM_PASSWORD"]

#                 if os.path.exists(self.session_file):
#                     try:
#                         self.insta_loader.load_session_from_file(username, self.session_file)
#                         logger.info("Successfully loaded existing Instagram session")
#                         return self.insta_loader
#                     except Exception as e:
#                         logger.warning(f"Failed to load existing session: {str(e)}")
                
#                 self.insta_loader.login(username, password)
#                 self.insta_loader.save_session_to_file(self.session_file)
#                 logger.info("Successfully created new Instagram session")
                
#             except Exception as e:
#                 logger.error(f"Failed to login to Instagram: {str(e)}")
#                 raise

#         return self.insta_loader

#     def _retry_operation(self, operation, max_retries=3, delay=5):
#         """Generic retry mechanism for Instagram operations."""
#         last_error = None
#         for attempt in range(max_retries):
#             try:
#                 return operation()
#             except instaloader.exceptions.ProfileNotExistsException:
#                 logger.error("Profile does not exist")
#                 return None
#             except Exception as e:
#                 last_error = e
#                 if attempt + 1 < max_retries:
#                     logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
#                     time.sleep(delay * (attempt + 1))
                    
#                     if "login" in str(e).lower() or "429" in str(e):
#                         self.insta_loader = None
#                         self._get_instaloader_instance()
                    
#         raise last_error

#     def _download_video_with_retry(self, video_url: str, max_retries=3) -> bytes:
#         """Download video content with retry mechanism."""
#         headers = {
#             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
#         }
        
#         for attempt in range(max_retries):
#             try:
#                 response = requests.get(
#                     video_url, 
#                     headers=headers, 
#                     timeout=30,
#                     allow_redirects=True
#                 )
                
#                 if response.status_code == 200:
#                     return response.content
#                 elif response.status_code == 500:
#                     logger.warning(f"500 error on attempt {attempt + 1}, trying alternative URL format")
#                     alt_url = video_url.split('?')[0]
#                     alt_response = requests.get(
#                         alt_url,
#                         headers=headers,
#                         timeout=30,
#                         allow_redirects=True
#                     )
#                     if alt_response.status_code == 200:
#                         return alt_response.content
                
#                 logger.error(f"Attempt {attempt + 1} failed with status code: {response.status_code}")
                
#             except requests.RequestException as e:
#                 logger.error(f"Attempt {attempt + 1} failed with error: {str(e)}")
                
#             if attempt < max_retries - 1:
#                 time.sleep(2 ** attempt)
                
#         raise VideoDownloadError(f"Failed to download video after {max_retries} attempts")

#     def _get_video_url(self, post, max_retries=3):
#         """Get video URL with fallback options."""
#         for attempt in range(max_retries):
#             try:
#                 if hasattr(post, 'video_url'):
#                     return post.video_url
#                 post_json = post._node
#                 if 'video_url' in post_json:
#                     return post_json['video_url']
#                 if 'video_resources' in post_json:
#                     return post_json['video_resources'][0]['src']
#             except Exception as e:
#                 logger.error(f"Error getting video URL on attempt {attempt + 1}: {str(e)}")
#                 if attempt < max_retries - 1:
#                     time.sleep(2 ** attempt)
#                     continue
                
#         raise ValueError("Could not extract video URL")

#     def _process_video(self, post: Union[Any, PostInfo], post_metadata: dict) -> bool:
#             """
#             Process a single video with enhanced error handling.
#             Extracts audio and adds it to embedchain vector database.
#             """
#             try:
#                 # Handle both PostInfo objects and raw instaloader Post objects
#                 if isinstance(post, PostInfo):
#                     video_url = post.video_url
#                 else:
#                     video_url = self._get_video_url(post)
                    
#                 video_content = self._download_video_with_retry(video_url)
                
#                 with temporary_file_manager() as temp_audio_path:
#                     # Convert video to audio
#                     video_buffer = io.BytesIO(video_content)
#                     audio = AudioSegment.from_file(video_buffer, format="mp4")
                    
#                     # Export as WAV for better compatibility
#                     audio_buffer = io.BytesIO()
#                     audio.export(audio_buffer, format="wav")
#                     audio_buffer.seek(0)
                    
#                     # Save to temporary file
#                     with open(temp_audio_path, 'wb') as f:
#                         f.write(audio_buffer.getvalue())
                    
#                     # Add to embedchain with enhanced metadata
#                     enhanced_metadata = {
#                         **post_metadata,
#                         "data_type": "audio",
#                         "processing_timestamp": datetime.now().isoformat(),
#                         "source_platform": "instagram",
#                         "content_type": "video_audio"
#                     }
                    
#                     # Use embedchain's add method to process and store the audio
#                     self.app.add(
#                         temp_audio_path,
#                         data_type="audio",
#                         metadata=enhanced_metadata
#                     )
                    
#                     logger.info(f"Successfully added audio to vector database for post {post_metadata['post_id']}")
#                     return True
                    
#             except VideoDownloadError as e:
#                 logger.error(f"Failed to download video for post {post_metadata['post_id']}: {str(e)}")
#                 return False
#             except Exception as e:
#                 logger.error(f"Error processing video for post {post_metadata['post_id']}: {str(e)}")
#                 return False

#     def _analyze_post_relevance(self, post: PostInfo) -> float:
#         """
#         Analyze post caption for personal story relevance using Groq LLM.
#         Returns a relevance score from 0 to 10.
#         """
#         try:
#             prompt = f"""
#             Rate the following Instagram post caption on a scale of 1-10 based on how much it reveals about the creator's personal story, journey, or experiences.
#             A score of 1 means it's purely promotional or unrelated to personal stories.
#             A score of 10 means it's a deep, meaningful personal story or reflection.

#             Caption: {post.caption}

#             Only respond with a single number between 1 and 10. No other text.
#             """

#             response = self.groq_client.chat.completions.create(
#                 model="llama-3.1-70b-versatile",
#                 messages=[{"role": "user", "content": prompt}],
#                 temperature=0.1,
#                 max_tokens=5
#             )

#             score = float(response.choices[0].message.content.strip())
#             return min(max(score, 1), 10)  # Ensure score is between 1 and 10

#         except Exception as e:
#             logger.error(f"Error analyzing post relevance: {str(e)}")
#             return 0.0

#     def _fetch_and_rank_posts(self, profile: Any, max_posts: int = 5) -> List[PostInfo]:
#         """
#         Fetch posts and rank them based on personal story relevance.
#         """
#         all_posts = []
#         post_count = 0

#         try:
#             for post in profile.get_posts():
#                 if post_count >= max_posts:
#                     break

#                 post_info = PostInfo(
#                     post_id=post.shortcode,
#                     caption=post.caption if post.caption else "",
#                     timestamp=post.date_utc,
#                     likes=post.likes,
#                     url=f"https://www.instagram.com/p/{post.shortcode}/",
#                     is_video=post.is_video,
#                     video_url=self._get_video_url(post) if post.is_video else ""
#                 )

#                 # Analyze post relevance
#                 post_info.relevance_score = self._analyze_post_relevance(post_info)
#                 all_posts.append(post_info)
#                 post_count += 1

#                 # Add small delay to avoid rate limiting
#                 time.sleep(0.5)

#         except Exception as e:
#             logger.error(f"Error fetching posts: {str(e)}")

#         # Sort posts by relevance score and return top ones
#         ranked_posts = sorted(all_posts, key=lambda x: x.relevance_score, reverse=True)
#         return ranked_posts[:30]  # Return top 40 most relevant posts

#     def _run(self, instagram_username: str) -> str:
#         if not self.is_initialized:
#             self.initialize_for_new_creator()
            
#         try:
#             logger.info(f"Fetching posts for user: {instagram_username}")
#             profile = self._retry_operation(lambda: instaloader.Profile.from_username(
#                 self._get_instaloader_instance().context, 
#                 instagram_username
#             ))
            
#             if profile is None:
#                 return "Instagram profile not found"

#             # Fetch and rank posts
#             ranked_posts = self._fetch_and_rank_posts(profile)
            
#             processed_videos = []
#             errors = []
#             total_relevant_posts = len(ranked_posts)
#             video_posts = [post for post in ranked_posts if post.is_video]
            
#             for post in video_posts:
#                 try:
#                     post_metadata = {
#                         "source": post.url,
#                         "caption": post.caption,
#                         "timestamp": post.timestamp.isoformat(),
#                         "likes": post.likes,
#                         "post_id": post.post_id,
#                         "relevance_score": post.relevance_score
#                     }
                    
#                     if self._process_video(post, post_metadata):
#                         processed_videos.append(post.post_id)
                        
#                 except Exception as post_error:
#                     error_msg = f"Error processing post {post.post_id}: {str(post_error)}"
#                     logger.error(error_msg)
#                     errors.append(error_msg)
#                     continue

#             success = len(processed_videos) > 0
#             error_message = "; ".join(errors) if errors else ""
            
#             summary = f"Analyzed {total_relevant_posts} posts from top 200 posts.\n"
#             summary += f"Found {len(video_posts)} video posts among relevant content.\n"
#             summary += f"Successfully processed {len(processed_videos)} videos.\n"
            
#             # Add some stats about the relevance scores
#             if ranked_posts:
#                 avg_score = sum(p.relevance_score for p in ranked_posts) / len(ranked_posts)
#                 max_score = max(p.relevance_score for p in ranked_posts)
#                 summary += f"Average relevance score: {avg_score:.1f}\n"
#                 summary += f"Highest relevance score: {max_score:.1f}\n"
            
#             if errors:
#                 summary += f"Errors encountered: {error_message}"

#             return summary

#         except Exception as e:
#             error_message = f"Error in fetch and process operation: {str(e)}"
#             logger.error(error_message)
#             return error_message
# --- new functionality

# from typing import Any, Type, List, Union
# from datetime import datetime
# from pydantic import BaseModel, Field
# from crewai_tools.tools.base_tool import BaseTool
# import instaloader
# import logging
# from dotenv import load_dotenv
# import os
# import time


# import tempfile
# import logging
# from embedchain import App
# from typing import Any, Type, List
# from datetime import datetime
# from pydantic import BaseModel, Field
# from crewai_tools.tools.base_tool import BaseTool
# import instaloader
# import os
# import requests
# import io
# from pydub import AudioSegment
# from deepgram import Deepgram
# from smartfunnel.tools.chroma_db_init import get_app_instance
# app_instance = get_app_instance()

# import streamlit as st
# OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
# # Set up Deepgram
# os.environ["DEEPGRAM_API_KEY"] = st.secrets["DEEPGRAM_API_KEY"]
# # deepgram = Deepgram(DEEPGRAM_API_KEY)

# # Set up logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

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

# from typing import Any, Type, List
# from datetime import datetime
# from pydantic import BaseModel, Field
# from crewai_tools.tools.base_tool import BaseTool
# import instaloader
# import logging
# from dotenv import load_dotenv
# import os

# # Set up logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# from typing import Any, Type, List
# from datetime import datetime
# from pydantic import BaseModel, Field
# from crewai_tools.tools.base_tool import BaseTool
# import instaloader
# import logging
# import os
# import requests
# import io
# from pydub import AudioSegment
# from embedchain import App

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# class FetchToAddInstagramAudioInput(BaseModel):
#     """Input for FetchToAddInstagramAudio."""
#     instagram_username: str = Field(..., description="The Instagram username to fetch posts from")

# class FetchToAddInstagramAudioOutput(BaseModel):
#     """Output containing results of fetch and audio processing."""
#     processed_videos: List[str] = Field(default_factory=list, description="List of successfully processed video URLs")
#     success: bool = Field(..., description="Whether the operation was successful")
#     error_message: str = Field(default="", description="Error message if any operations failed")
#     total_posts_found: int = Field(default=0, description="Total number of posts found")
#     total_videos_processed: int = Field(default=0, description="Total number of videos processed")

# from contextlib import contextmanager

# class VideoDownloadError(Exception):
#     """Custom exception for video download failures."""
#     pass

# @contextmanager
# def temporary_file_manager(suffix='.wav'):
#     """Context manager for handling temporary files."""
#     temp_dir = tempfile.mkdtemp()
#     temp_path = os.path.join(temp_dir, f'temp{suffix}')
#     try:
#         yield temp_path
#     finally:
#         if os.path.exists(temp_path):
#             os.remove(temp_path)
#         if os.path.exists(temp_dir):
#             os.rmdir(temp_dir)

# class FetchToAddInstagramAudioTool(BaseTool):
#     name: str = "Fetch and Process Instagram Audio"
#     description: str = "Fetches Instagram posts and adds video audio to the vector database"
#     args_schema: Type[BaseModel] = FetchToAddInstagramAudioInput
#     insta_loader: Any = Field(default=None, exclude=True)
#     app: Any = Field(default=None, exclude=True)
#     is_initialized: bool = Field(default=False, exclude=True)
#     session_file: str = Field(default="", exclude=True)

#     def __init__(self, app: App, **data):
#         super().__init__(**data)
#         self.app = app
#         self.session_file = os.path.join(tempfile.gettempdir(), "instagram_session")
#         self.is_initialized = False

#     def initialize_for_new_creator(self):
#         """Reset the vector database before starting analysis for a new creator."""
#         logger.info("Initializing vector database for new creator")
#         if self.app is not None:
#             self.app.reset()
#             logger.info("Vector database reset successfully")
#         else:
#             logger.error("No app instance available for reset")
#         self.is_initialized = True

#     def _get_instaloader_instance(self):
#         """Get or create a shared Instaloader instance with session management."""
#         if not self.insta_loader:
#             self.insta_loader = instaloader.Instaloader()
#             try:
#                 username = st.secrets["INSTAGRAM_USERNAME"]
#                 password = st.secrets["INSTAGRAM_PASSWORD"]

#                 if os.path.exists(self.session_file):
#                     try:
#                         self.insta_loader.load_session_from_file(username, self.session_file)
#                         logger.info("Successfully loaded existing Instagram session")
#                         return self.insta_loader
#                     except Exception as e:
#                         logger.warning(f"Failed to load existing session: {str(e)}")
                
#                 self.insta_loader.login(username, password)
#                 self.insta_loader.save_session_to_file(self.session_file)
#                 logger.info("Successfully created new Instagram session")
                
#             except Exception as e:
#                 logger.error(f"Failed to login to Instagram: {str(e)}")
#                 raise

#         return self.insta_loader
    
#     def _retry_operation(self, operation, max_retries=3, delay=5):
#         """Generic retry mechanism for Instagram operations."""
#         last_error = None
#         for attempt in range(max_retries):
#             try:
#                 return operation()
#             except instaloader.exceptions.ProfileNotExistsException:
#                 logger.error("Profile does not exist")
#                 return None
#             except Exception as e:
#                 last_error = e
#                 if attempt + 1 < max_retries:
#                     logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
#                     time.sleep(delay * (attempt + 1))
                    
#                     if "login" in str(e).lower() or "429" in str(e):
#                         self.insta_loader = None
#                         self._get_instaloader_instance()
                        
#         raise last_error

#     def _download_video_with_retry(self, video_url: str, max_retries=3) -> bytes:
#         """Download video content with retry mechanism."""
#         headers = {
#             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
#         }
        
#         for attempt in range(max_retries):
#             try:
#                 response = requests.get(
#                     video_url, 
#                     headers=headers, 
#                     timeout=30,
#                     allow_redirects=True
#                 )
                
#                 if response.status_code == 200:
#                     return response.content
#                 elif response.status_code == 500:
#                     logger.warning(f"500 error on attempt {attempt + 1}, trying alternative URL format")
#                     # Try alternative URL format
#                     alt_url = video_url.split('?')[0]
#                     alt_response = requests.get(
#                         alt_url,
#                         headers=headers,
#                         timeout=30,
#                         allow_redirects=True
#                     )
#                     if alt_response.status_code == 200:
#                         return alt_response.content
                
#                 logger.error(f"Attempt {attempt + 1} failed with status code: {response.status_code}")
                
#             except requests.RequestException as e:
#                 logger.error(f"Attempt {attempt + 1} failed with error: {str(e)}")
                
#             if attempt < max_retries - 1:
#                 time.sleep(2 ** attempt)  # Exponential backoff
                
#         raise VideoDownloadError(f"Failed to download video after {max_retries} attempts")

#     def _get_video_url(self, post, max_retries=3):
#         """Get video URL with fallback options."""
#         for attempt in range(max_retries):
#             try:
#                 if hasattr(post, 'video_url'):
#                     return post.video_url
#                 # Fallback to manual extraction if needed
#                 post_json = post._node
#                 if 'video_url' in post_json:
#                     return post_json['video_url']
#                 if 'video_resources' in post_json:
#                     return post_json['video_resources'][0]['src']
#             except Exception as e:
#                 logger.error(f"Error getting video URL on attempt {attempt + 1}: {str(e)}")
#                 if attempt < max_retries - 1:
#                     time.sleep(2 ** attempt)
#                     continue
                
#         raise ValueError("Could not extract video URL")

#     def _process_video(self, post: Any, post_metadata: dict) -> bool:
#         """Process a single video with enhanced error handling."""
#         try:
#             video_url = self._get_video_url(post)
#             video_content = self._download_video_with_retry(video_url)
            
#             with temporary_file_manager() as temp_audio_path:
#                 video_buffer = io.BytesIO(video_content)
#                 audio = AudioSegment.from_file(video_buffer, format="mp4")
                
#                 audio_buffer = io.BytesIO()
#                 audio.export(audio_buffer, format="wav")
#                 audio_buffer.seek(0)
                
#                 with open(temp_audio_path, 'wb') as f:
#                     f.write(audio_buffer.getvalue())
                
#                 self.app.add(
#                     temp_audio_path,
#                     data_type="audio",
#                     metadata=post_metadata
#                 )
                
#                 logger.info(f"Successfully processed video for post {post_metadata['post_id']}")
#                 return True
                
#         except VideoDownloadError as e:
#             logger.error(f"Failed to download video for post {post_metadata['post_id']}: {str(e)}")
#             return False
#         except Exception as e:
#             logger.error(f"Error processing video for post {post_metadata['post_id']}: {str(e)}")
#             return False

#     def _run(self, instagram_username: str) -> str:
#         if not self.is_initialized:
#             self.initialize_for_new_creator()
            
#         try:
#             logger.info(f"Fetching posts for user: {instagram_username}")
#             profile = self._retry_operation(lambda: instaloader.Profile.from_username(
#                 self._get_instaloader_instance().context, 
#                 instagram_username
#             ))
            
#             if profile is None:
#                 return "Instagram profile not found"
                
#             processed_videos = []
#             errors = []
#             total_posts = 0
#             post_count = 0
            
#             for post in profile.get_posts():
#                 total_posts += 1
                
#                 try:
#                     if post.is_video:
#                         post_metadata = {
#                             "source": f"https://www.instagram.com/p/{post.shortcode}/",
#                             "caption": post.caption if post.caption else "",
#                             "timestamp": post.date_utc.isoformat(),
#                             "likes": post.likes,
#                             "post_id": post.shortcode
#                         }
                        
#                         if self._process_video(post, post_metadata):
#                             processed_videos.append(post.shortcode)
                    
#                     post_count += 1
#                     if post_count >= 3:  # Limit to 40 posts
#                         break
                        
#                 except Exception as post_error:
#                     error_msg = f"Error processing post {post.shortcode}: {str(post_error)}"
#                     logger.error(error_msg)
#                     errors.append(error_msg)
#                     continue

#             success = len(processed_videos) > 0
#             error_message = "; ".join(errors) if errors else ""
            
#             return f"Successfully processed {len(processed_videos)} videos out of {total_posts} total posts. Errors: {error_message if errors else 'None'}"

#         except Exception as e:
#             error_message = f"Error in fetch and process operation: {str(e)}"
#             logger.error(error_message)
#             return error_message


#  New functionality ---

# @contextmanager
# def temporary_file_manager(suffix='.wav'):
#     """Context manager for handling temporary files."""
#     temp_dir = tempfile.mkdtemp()
#     temp_path = os.path.join(temp_dir, f'temp{suffix}')
#     try:
#         yield temp_path
#     finally:
#         # Clean up the file
#         if os.path.exists(temp_path):
#             os.remove(temp_path)
#         # Clean up the directory
#         if os.path.exists(temp_dir):
#             os.rmdir(temp_dir)

# class FetchToAddInstagramAudioTool(BaseTool):
#     """Tool that fetches Instagram posts and processes their audio for the vector database."""
#     name: str = "Fetch and Process Instagram Audio"
#     description: str = "Fetches Instagram posts and adds video audio to the vector database"
#     args_schema: Type[BaseModel] = FetchToAddInstagramAudioInput
#     insta_loader: Any = Field(default=None, exclude=True)
#     app: Any = Field(default=None, exclude=True)
#     is_initialized: bool = Field(default=False, exclude=True)
#     session_file: str = Field(default="", exclude=True)

#     def __init__(self, app: App, **data):
#         super().__init__(**data)
#         self.app = app
#         self.session_file = os.path.join(tempfile.gettempdir(), "instagram_session")
#         self.is_initialized = False

#     def initialize_for_new_creator(self):
#         """Reset the vector database before starting analysis for a new creator."""
#         logger.info("Initializing vector database for new creator")
#         if self.app is not None:
#             self.app.reset()
#             logger.info("Vector database reset successfully")
#         else:
#             logger.error("No app instance available for reset")
#         self.is_initialized = True

#     def _get_instaloader_instance(self):
#         """Get or create a shared Instaloader instance with session management."""
#         if not self.insta_loader:
#             self.insta_loader = instaloader.Instaloader()
#             try:
#                 username = st.secrets["INSTAGRAM_USERNAME"]
#                 password = st.secrets["INSTAGRAM_PASSWORD"]

#                 if os.path.exists(self.session_file):
#                     try:
#                         self.insta_loader.load_session_from_file(username, self.session_file)
#                         logger.info("Successfully loaded existing Instagram session")
#                         return self.insta_loader
#                     except Exception as e:
#                         logger.warning(f"Failed to load existing session: {str(e)}")
                
#                 self.insta_loader.login(username, password)
#                 self.insta_loader.save_session_to_file(self.session_file)
#                 logger.info("Successfully created new Instagram session")
                
#             except Exception as e:
#                 logger.error(f"Failed to login to Instagram: {str(e)}")
#                 raise

#         return self.insta_loader

#     def _retry_operation(self, operation, max_retries=3, delay=5):
#         """Generic retry mechanism for Instagram operations."""
#         last_error = None
#         for attempt in range(max_retries):
#             try:
#                 return operation()
#             except instaloader.exceptions.ProfileNotExistsException:
#                 logger.error("Profile does not exist")
#                 return None
#             except Exception as e:
#                 last_error = e
#                 if attempt + 1 < max_retries:
#                     logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
#                     time.sleep(delay * (attempt + 1))
                    
#                     if "login" in str(e).lower() or "429" in str(e):
#                         self.insta_loader = None
#                         self._get_instaloader_instance()
                        
#         raise last_error

#     def _process_video(self, video_url: str, post_metadata: dict) -> bool:
#         with temporary_file_manager() as temp_audio_path:
#             try:
#                 response = requests.get(video_url, timeout=30)
#                 if response.status_code != 200:
#                     raise Exception(f"Failed to download video: Status code {response.status_code}")
                
#                 video_buffer = io.BytesIO(response.content)
#                 audio = AudioSegment.from_file(video_buffer, format="mp4")
                
#                 audio_buffer = io.BytesIO()
#                 audio.export(audio_buffer, format="wav")
#                 audio_buffer.seek(0)
                
#                 with open(temp_audio_path, 'wb') as f:
#                     f.write(audio_buffer.getvalue())
                
#                 self.app.add(
#                     temp_audio_path,
#                     data_type="audio",
#                     metadata=post_metadata
#                 )
                
#                 logger.info(f"Successfully processed video: {video_url}")
#                 return True
                
#             except Exception as e:
#                 logger.error(f"Error processing video {video_url}: {str(e)}")
#                 return False

#     def _run(self, instagram_username: str) -> str:
#         if not self.is_initialized:
#             self.initialize_for_new_creator()
            
#         try:
#             logger.info(f"Fetching posts for user: {instagram_username}")
            
#             def get_profile():
#                 loader = self._get_instaloader_instance()
#                 return instaloader.Profile.from_username(loader.context, instagram_username)
            
#             profile = self._retry_operation(get_profile)
#             if profile is None:
#                 return "Instagram profile not found"
                
#             processed_videos = []
#             errors = []
#             total_posts = 0
#             post_count = 0
            
#             for post in profile.get_posts():
#                 total_posts += 1
                
#                 try:
#                     if post.is_video and post.video_url:
#                         post_metadata = {
#                             "source": f"https://www.instagram.com/p/{post.shortcode}/",
#                             "caption": post.caption if post.caption else "",
#                             "timestamp": post.date_utc.isoformat(),
#                             "likes": post.likes,
#                             "post_id": post.shortcode
#                         }
                        
#                         if self._process_video(post.video_url, post_metadata):
#                             processed_videos.append(post.video_url)
                    
#                     post_count += 1
#                     if post_count >= 40:
#                         break
                        
#                 except Exception as post_error:
#                     error_msg = f"Error processing post {post.shortcode}: {str(post_error)}"
#                     logger.error(error_msg)
#                     errors.append(error_msg)
#                     continue

#             success = len(processed_videos) > 0
#             error_message = "; ".join(errors) if errors else ""
            
#             result = {
#                 "processed_videos": processed_videos,
#                 "success": success,
#                 "error_message": error_message,
#                 "total_posts_found": total_posts,
#                 "total_videos_processed": len(processed_videos)
#             }
            
#             return f"Successfully processed {len(processed_videos)} videos out of {total_posts} total posts"

#         except Exception as e:
#             error_message = f"Error in fetch and process operation: {str(e)}"
#             logger.error(error_message)
#             return error_message    