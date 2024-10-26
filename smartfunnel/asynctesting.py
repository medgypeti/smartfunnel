import json
import traceback
from typing import Any, Type, List, Union, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from crewai_tools.tools.base_tool import BaseTool
import instaloader
import logging
from dotenv import load_dotenv
import os
import asyncio
import aiohttp
from pydub import AudioSegment
import io
from embedchain import App
from concurrent.futures import ThreadPoolExecutor
from deepgram import Deepgram

# Original API keys
OPENAI_API_KEY = "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"
os.environ["DEEPGRAM_API_KEY"] = "46d16104048c4bd6b223b69c7bc05b2a3df4de75"

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Original PostInfo class
class PostInfo(BaseModel):
    """Instagram post information."""
    post_id: str
    caption: str
    timestamp: datetime
    likes: Optional[int] = Field(default=0)  # Make likes optional with default value 0
    url: str
    is_video: bool
    video_url: str = ""

    class Config:
        arbitrary_types_allowed = True

def _fetch_posts_sync(self, loader, username: str) -> List[PostInfo]:
    """Synchronous post fetching implementation."""
    profile = instaloader.Profile.from_username(loader.context, username)
    posts = []
    post_count = 0
    
    for post in profile.get_posts():
        try:
            post_info = PostInfo(
                post_id=post.shortcode,
                caption=post.caption if post.caption else "",
                timestamp=post.date_utc,
                likes=post.likes if post.likes is not None else 0,  # Handle None case
                url=f"https://www.instagram.com/p/{post.shortcode}/",
                is_video=post.is_video,
                video_url=post.video_url if post.is_video else ""
            )
            posts.append(post_info)
            post_count += 1
            logger.info(f"Processed post {post.shortcode}")

            if post_count >= 1:
                break
        except Exception as post_error:
            logger.error(f"Error processing individual post: {str(post_error)}")
            continue
            
    return posts

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

# Input/Output Models (unchanged)
class FetchInstagramPostsInput(BaseModel):
    """Input for FetchInstagramPosts."""
    instagram_username: str = Field(..., description="The Instagram username to fetch posts from")

class FetchInstagramPostsOutput(BaseModel):
    """Output containing list of Instagram posts."""
    posts: List[PostInfo]
    success: bool = True
    error_message: str = ""

class AddInstagramAudioInput(BaseModel):
    """Input for AddInstagramAudio."""
    video_url: str = Field(..., description="The URL of the Instagram video to process")

class AddInstagramAudioOutput(BaseModel):
    """Output from AddInstagramAudio."""
    success: bool = Field(..., description="Whether the audio was successfully added to the vector DB")
    processed_posts: List[str] = Field(default_factory=list, description="List of successfully processed post IDs")
    error_message: str = Field(default="", description="Error message if any operations failed")

# Async version of FetchInstagramPostsTool
class AsyncFetchInstagramPostsTool(BaseTool):
    """Tool that fetches Instagram posts from a specified account."""
    name: str = "Fetch Instagram Posts"  # Changed back to original name
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
                        likes=post.likes if post.likes is not None else 0,
                        url=f"https://www.instagram.com/p/{post.shortcode}/",
                        is_video=post.is_video,
                        video_url=post.video_url if post.is_video else ""
                    )
                    posts.append(post_info)
                    post_count += 1
                    logger.info(f"Processed post {post.shortcode}")

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


async def verify_audio_content(app_instance, video_url):
    """Verify and print the transcribed content of a processed video."""
    try:
        # Query specifically about the content that was just added
        verification_query = "Please show me the exact transcription of the most recently added video content."
        result = app_instance.query(verification_query)
        
        print("\n" + "="*50)
        print(f"Transcribed content for video {video_url}")
        print("="*50)
        print(f"First 500 characters: {result[:500]}")
        print("="*50 + "\n")
        
        return result
    except Exception as e:
        print(f"Error verifying audio content: {str(e)}")
        return None
    
# Async version of AddInstagramAudioTool
# class AsyncAddInstagramAudioTool(BaseTool):
#     name: str = "Add Instagram Audio to Vector DB"
#     description: str = "Adds Instagram video audio to the vector database using EmbedChain"
#     args_schema: Type[BaseModel] = AddInstagramAudioInput
#     app: Any = Field(default=None, exclude=True)
#     max_concurrent: int = Field(default=5, exclude=True)
#     semaphore: Any = Field(default=None, exclude=True)
#     logger: Any = Field(default=None, exclude=True)  # Add logger as a field

#     def __init__(self, app: App, max_concurrent: int = 5, **data):
#         super().__init__(**data)
#         self.app = app
#         self.max_concurrent = max_concurrent
#         self.semaphore = asyncio.Semaphore(max_concurrent)
#         self._setup_logger()
# class AsyncAddInstagramAudioTool(BaseTool):
#     name: str = "Add Instagram Audio to Vector DB"
#     description: str = "Adds Instagram video audio to the vector database using EmbedChain"
#     args_schema: Type[BaseModel] = AddInstagramAudioInput
#     app: Any = Field(default=None, exclude=True)
#     max_concurrent: int = Field(default=5, exclude=True)
#     semaphore: Any = Field(default=None, exclude=True)
#     logger: Any = Field(default=None, exclude=True)

#     def __init__(self, app: App, max_concurrent: int = 5, **data):
#         super().__init__(**data)
#         self.app = app
#         self.max_concurrent = max_concurrent
#         self.semaphore = asyncio.Semaphore(max_concurrent)
#         self._setup_logger()
        
#         # Initialize Deepgram
#         self.deepgram = Deepgram(os.environ["DEEPGRAM_API_KEY"])
class AsyncAddInstagramAudioTool(BaseTool):
    name: str = "Add Instagram Audio to Vector DB"
    description: str = "Adds Instagram video audio to the vector database using EmbedChain"
    args_schema: Type[BaseModel] = AddInstagramAudioInput
    app: Any = Field(default=None, exclude=True)
    max_concurrent: int = Field(default=5, exclude=True)
    semaphore: Any = Field(default=None, exclude=True)
    logger: Any = Field(default=None, exclude=True)

    def __init__(self, app: App, max_concurrent: int = 5, **data):
        super().__init__(**data)
        self.app = app
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self._setup_logger()

    async def verify_audio_content(self, temp_audio_path: str):
        """Verify the audio content was properly processed and stored."""
        try:
            print("\nVerifying audio content...")
            # Try a direct query about the audio that was just added
            test_queries = [
                "What was just said in this audio?",
                "Give me the exact transcription of the most recent audio.",
                "What topics were discussed in this audio?"
            ]
            
            for query in test_queries:
                print(f"\nTest query: {query}")
                print("-" * 50)
                try:
                    response = self.app.query(query)
                    print(f"Response: {response[:500]}..." if len(response) > 500 else response)
                except Exception as e:
                    print(f"Query failed: {str(e)}")
                print("-" * 50)

        except Exception as e:
            print(f"Verification error: {str(e)}")

    async def _download_and_process_video(self, video_url: str) -> bool:
        """Download and process a single video asynchronously."""
        temp_audio_path = None
        try:
            print(f"Starting processing for video: {video_url}")
            
            async with self.semaphore:
                async with aiohttp.ClientSession() as session:
                    print("Downloading video...")
                    async with session.get(video_url) as response:
                        if response.status != 200:
                            raise Exception(f"Failed to download video: {response.status}")
                        video_data = await response.read()
                        print(f"Downloaded video data size: {len(video_data)} bytes")
                
                # Process video data
                print("Converting video to audio...")
                video_buffer = io.BytesIO(video_data)
                audio = AudioSegment.from_file(video_buffer, format="mp4")
                print(f"Audio duration: {len(audio)/1000.0} seconds")
                
                # Export as WAV
                print("Exporting to WAV format...")
                audio_buffer = io.BytesIO()
                audio.export(audio_buffer, format="wav")
                audio_buffer.seek(0)
                
                # Save to temporary file
                temp_audio_path = f"temp_audio_{datetime.now().timestamp()}.wav"
                with open(temp_audio_path, 'wb') as f:
                    f.write(audio_buffer.getvalue())
                print(f"Saved temporary audio file: {temp_audio_path}")
                
                # Add to embedchain with direct audio processing
                print("Adding to embedchain database...")
                self.app.add(
                    temp_audio_path,
                    data_type="audio"
                )
                print("Successfully added to database")
                
                # Verify the content was properly processed
                await self.verify_audio_content(temp_audio_path)
                
                return True
            
        except Exception as e:
            print(f"Error processing video {video_url}: {str(e)}")
            return False
        finally:
            if temp_audio_path and os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
                print(f"Cleaned up temporary file: {temp_audio_path}")

    def _setup_logger(self):
        """Set up logging configuration."""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        
        # Add file handler if it doesn't exist
        if not logger.handlers:
            fh = logging.FileHandler('audio_processing.log')
            fh.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        
        self.logger = logger

    async def transcribe_audio(self, audio_path: str) -> str:
        """Transcribe audio file using Deepgram and return the transcript."""
        try:
            print(f"Starting transcription of {audio_path}")
            
            with open(audio_path, 'rb') as audio:
                source = {'buffer': audio, 'mimetype': 'audio/wav'}
                transcription = await self.deepgram.transcription.prerecorded(
                    source,
                    {
                        'smart_format': True,
                        'model': 'nova',
                        'language': 'en'
                    }
                )
                
                # Get the transcript
                transcript = transcription['results']['channels'][0]['alternatives'][0]['transcript']
                print("\n" + "="*50)
                print("TRANSCRIPTION OUTPUT:")
                print("="*50)
                print(transcript[:500] + "..." if len(transcript) > 500 else transcript)
                print("="*50 + "\n")
                
                return transcript
        except Exception as e:
            print(f"Transcription error: {str(e)}")
            raise

    async def verify_database_storage(self, transcript: str):
        """Verify that content was properly stored in the database."""
        try:
            print("\nVerifying database storage...")
            
            # Try to directly access the database
            try:
                collection_data = self.app.db.get()
                print(f"Database raw content: {collection_data}")
            except Exception as e:
                print(f"Could not access database directly: {str(e)}")

            # Try to query the content
            try:
                result = self.app.query("What was just added to the database?")
                print("\nQuery result after adding content:")
                print("="*50)
                print(result[:500] + "..." if len(result) > 500 else result)
                print("="*50)
            except Exception as e:
                print(f"Could not query database: {str(e)}")

        except Exception as e:
            print(f"Database verification error: {str(e)}")

    # async def _download_and_process_video(self, video_url: str) -> bool:
    #     """Download and process a single video asynchronously."""
    #     temp_audio_path = None
    #     try:
    #         print(f"Starting processing for video: {video_url}")
            
    #         async with self.semaphore:
    #             # Download and convert video (existing code remains the same until audio file creation)
                
    #             # After creating the WAV file
    #             print("Starting transcription...")
    #             transcript = await self.transcribe_audio(temp_audio_path)
                
    #             print("Adding to embedchain database...")
    #             # Add both audio and transcript
    #             self.app.add(
    #                 temp_audio_path,
    #                 data_type="audio",
    #                 metadata={
    #                     "source": video_url,
    #                     "type": "instagram_video",
    #                     "timestamp": str(datetime.now()),
    #                     "transcript": transcript  # Store transcript in metadata
    #                 }
    #             )
    #             print("Successfully added to database")
                
    #             # Verify storage
    #             await self.verify_database_storage(transcript)
                
    #             return True
            
    #     except Exception as e:
    #         print(f"Error processing video {video_url}: {str(e)}")
    #         return False
    #     finally:
    #         if temp_audio_path and os.path.exists(temp_audio_path):
    #             os.remove(temp_audio_path)
    #             print(f"Cleaned up temporary file: {temp_audio_path}")

    # async def _download_and_process_video(self, video_url: str) -> bool:
    #     """Download and process a single video asynchronously."""
    #     temp_audio_path = None
    #     try:
    #         print(f"Starting processing for video: {video_url}")
            
    #         async with self.semaphore:
    #             async with aiohttp.ClientSession() as session:
    #                 print("Downloading video...")
    #                 async with session.get(video_url) as response:
    #                     if response.status != 200:
    #                         raise Exception(f"Failed to download video: {response.status}")
    #                     video_data = await response.read()
    #                     print(f"Downloaded video data size: {len(video_data)} bytes")
                
    #             # Process video data
    #             print("Converting video to audio...")
    #             video_buffer = io.BytesIO(video_data)
    #             audio = AudioSegment.from_file(video_buffer, format="mp4")
    #             print(f"Audio duration: {len(audio)/1000.0} seconds")
                
    #             # Export as WAV
    #             print("Exporting to WAV format...")
    #             audio_buffer = io.BytesIO()
    #             audio.export(audio_buffer, format="wav")
    #             audio_buffer.seek(0)
                
    #             # Save to temporary file
    #             temp_audio_path = f"temp_audio_{datetime.now().timestamp()}.wav"
    #             with open(temp_audio_path, 'wb') as f:
    #                 f.write(audio_buffer.getvalue())
    #             print(f"Saved temporary audio file: {temp_audio_path}")
                
    #             # Add to embedchain
    #             print("Adding to embedchain database...")
    #             self.app.add(
    #                 temp_audio_path,
    #                 data_type="audio",
    #                 metadata={
    #                     "source": video_url,
    #                     "type": "instagram_video",
    #                     "timestamp": str(datetime.now())
    #                 }
    #             )
    #             print("Successfully added to database")
                
    #             # Verify the transcribed content
    #             print("Verifying transcribed content...")
    #             await verify_audio_content(self.app, video_url)
                
    #             return True
            
    #     except Exception as e:
    #         print(f"Error processing video {video_url}: {str(e)}")
    #         return False
    #     finally:
    #         if temp_audio_path and os.path.exists(temp_audio_path):
    #             os.remove(temp_audio_path)
    #             print(f"Cleaned up temporary file: {temp_audio_path}")

    def _run(self, video_url: str) -> AddInstagramAudioOutput:
        """Synchronous wrapper for async processing required by BaseTool."""
        try:
            print(f"Starting synchronous run for video: {video_url}")  # Fallback logging
            # Create new event loop for async operation
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = loop.run_until_complete(self._download_and_process_video(video_url))
            loop.close()
            
            if success:
                print(f"Successfully processed video: {video_url}")  # Fallback logging
                return AddInstagramAudioOutput(
                    success=True,
                    processed_posts=[video_url],
                    error_message=""
                )
            else:
                print(f"Failed to process video: {video_url}")  # Fallback logging
                return AddInstagramAudioOutput(
                    success=False,
                    processed_posts=[],
                    error_message=f"Failed to process video: {video_url}"
                )
        except Exception as e:
            error_msg = f"Error processing video: {str(e)}"
            print(error_msg)  # Fallback logging
            return AddInstagramAudioOutput(
                success=False,
                processed_posts=[],
                error_message=error_msg
            )

    # async def _download_and_process_video(self, video_url: str) -> bool:
    #     """Download and process a single video asynchronously."""
    #     temp_audio_path = None
    #     try:
    #         print(f"Starting processing for video: {video_url}")  # Fallback logging
            
    #         async with self.semaphore:
    #             async with aiohttp.ClientSession() as session:
    #                 print("Downloading video...")  # Fallback logging
    #                 async with session.get(video_url) as response:
    #                     if response.status != 200:
    #                         raise Exception(f"Failed to download video: {response.status}")
    #                     video_data = await response.read()
    #                     print(f"Downloaded video data size: {len(video_data)} bytes")  # Fallback logging
                
    #             # Process video data
    #             print("Converting video to audio...")  # Fallback logging
    #             video_buffer = io.BytesIO(video_data)
    #             audio = AudioSegment.from_file(video_buffer, format="mp4")
    #             print(f"Audio duration: {len(audio)/1000.0} seconds")  # Fallback logging
                
    #             # Export as WAV
    #             print("Exporting to WAV format...")  # Fallback logging
    #             audio_buffer = io.BytesIO()
    #             audio.export(audio_buffer, format="wav")
    #             audio_buffer.seek(0)
                
    #             # Save to temporary file
    #             temp_audio_path = f"temp_audio_{datetime.now().timestamp()}.wav"
    #             with open(temp_audio_path, 'wb') as f:
    #                 f.write(audio_buffer.getvalue())
    #             print(f"Saved temporary audio file: {temp_audio_path}")  # Fallback logging
                
    #             # Add to embedchain
    #             print("Adding to embedchain database...")  # Fallback logging
    #             self.app.add(
    #                 temp_audio_path,
    #                 data_type="audio",
    #                 metadata={
    #                     "source": video_url,
    #                     "type": "instagram_video",
    #                     "timestamp": str(datetime.now())
    #                 }
    #             )
    #             print("Successfully added to database")  # Fallback logging
                
    #             return True
            
    #     except Exception as e:
    #         print(f"Error processing video {video_url}: {str(e)}")  # Fallback logging
    #         return False
    #     finally:
    #         if temp_audio_path and os.path.exists(temp_audio_path):
    #             os.remove(temp_audio_path)
    #             print(f"Cleaned up temporary file: {temp_audio_path}")  # Fallback logging

async def process_posts_concurrently(app_instance, posts: List[PostInfo], max_concurrent: int = 5):
    """Process multiple posts concurrently."""
    print(f"Starting concurrent processing of {len(posts)} posts")  # Fallback logging
    
    audio_tool = AsyncAddInstagramAudioTool(app=app_instance, max_concurrent=max_concurrent)
    tasks = []
    
    for post in posts:
        if post.is_video and post.video_url:
            print(f"Queuing video: {post.video_url}")  # Fallback logging
            task = audio_tool._download_and_process_video(post.video_url)
            tasks.append((post.video_url, task))
    
    processed_urls = []
    if tasks:
        print(f"Processing {len(tasks)} videos concurrently")  # Fallback logging
        for video_url, task in tasks:
            try:
                success = await task
                if success:
                    processed_urls.append(video_url)
                    print(f"Successfully processed video: {video_url}")  # Fallback logging
                else:
                    print(f"Failed to process video: {video_url}")  # Fallback logging
            except Exception as e:
                print(f"Error processing video {video_url}: {str(e)}")  # Fallback logging
                continue
    
    print(f"Completed processing. Success count: {len(processed_urls)}")  # Fallback logging
    return processed_urls

async def verify_database_content(app_instance, processed_urls):
    """Verify that content was properly added to the database."""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting database content verification")
        
        # Get collection info
        try:
            # This might need to be adjusted based on your embedchain version/setup
            collection_info = app_instance.db.get_collection_info()
            logger.debug(f"Database collection info: {collection_info}")
        except Exception as e:
            logger.error(f"Error getting collection info: {str(e)}")
        
        # Test query
        logger.info("Executing test query...")
        test_query = "What is mentioned in these videos?"
        result = app_instance.query(test_query)
        
        logger.debug(f"Query result type: {type(result)}")
        logger.debug(f"Query result length: {len(result) if result else 0}")
        logger.debug(f"Query result preview: {result[:500] if result else 'No result'}")
        
        if not result or result.strip() == "":
            logger.warning("Database query returned empty result")
            return False
            
        logger.info("Database verification successful")
        return True
    except Exception as e:
        logger.error(f"Error verifying database content: {str(e)}")
        return False
# class AsyncAddInstagramAudioTool(BaseTool):
#     name: str = "Add Instagram Audio to Vector DB"
#     description: str = "Adds Instagram video audio to the vector database using EmbedChain"
#     args_schema: Type[BaseModel] = AddInstagramAudioInput
#     app: Any = Field(default=None, exclude=True)

#     def __init__(self, app: App, max_concurrent: int = 5, **data):
#         super().__init__(**data)
#         self.app = app
#         self.semaphore = asyncio.Semaphore(max_concurrent)
        
#     async def _download_and_process_video(self, video_url: str) -> bool:
#         """Download and process a single video asynchronously."""
#         temp_audio_path = None
#         try:
#             async with aiohttp.ClientSession() as session:
#                 async with session.get(video_url) as response:
#                     if response.status != 200:
#                         raise Exception(f"Failed to download video: {response.status}")
#                     video_data = await response.read()
            
#             # Process video data
#             video_buffer = io.BytesIO(video_data)
#             audio = AudioSegment.from_file(video_buffer, format="mp4")
            
#             # Export as WAV
#             audio_buffer = io.BytesIO()
#             audio.export(audio_buffer, format="wav")
#             audio_buffer.seek(0)
            
#             # Save to temporary file
#             temp_audio_path = f"temp_audio_{datetime.now().timestamp()}.wav"
#             with open(temp_audio_path, 'wb') as f:
#                 f.write(audio_buffer.getvalue())
            
#             # Add to embedchain
#             self.app.add(
#                 temp_audio_path,
#                 data_type="audio",
#                 metadata={"source": video_url}
#             )
            
#             return True
            
#         except Exception as e:
#             logger.error(f"Error processing video {video_url}: {str(e)}")
#             return False
#         finally:
#             if temp_audio_path and os.path.exists(temp_audio_path):
#                 os.remove(temp_audio_path)

#     def _run(self, video_url: str) -> AddInstagramAudioOutput:
#         try:
#             success = asyncio.run(self._download_and_process_video(video_url))
#             return AddInstagramAudioOutput(
#                 success=success,
#                 processed_posts=[video_url] if success else [],
#                 error_message="" if success else f"Failed to process {video_url}"
#             )
#         except Exception as e:
#             error_message = f"Error processing video: {str(e)}"
#             logger.error(error_message)
#             return AddInstagramAudioOutput(
#                 success=False,
#                 processed_posts=[],
#                 error_message=error_message
#             )
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
    logger: Any = Field(default=None, exclude=True)  # Add logger as a field with exclude=True


    def __init__(self, app: App, **data):
        super().__init__(**data)
        self.app = app
        # self.logger = logging.getLogger(__name__)
        self._setup_logger()


    def _setup_logger(self):
        """Set up logging configuration."""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        
        # Add file handler if it doesn't exist
        if not logger.handlers:
            fh = logging.FileHandler('query_tool.log')
            fh.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        
        self.logger = logger

    def _run(self, query: str) -> QueryDatabaseOutput:
        try:
            # self.logger.info(f"Querying vector DB with: {query}")
            
            # Modify the query prompt to be more specific
            formatted_query = f"""
            Based on the Instagram video content in the database, please analyze and respond to this query:
            {query}
            
            Please provide:
            1. Relevant information from the videos
            2. Specific examples or quotes if available
            3. Any relevant context or patterns observed
            
            If no relevant information is found, please indicate that clearly.
            """
            
            # Set longer response time and more detailed context
            response = self.app.query(
                formatted_query,
                temperature=0.3,  # Lower temperature for more focused responses
                top_k=5  # Increase number of relevant chunks to consider
            )
            
            self.logger.info("Query completed successfully")
            self.logger.debug(f"Raw response: {response[:200]}...")  # Log first 200 chars
            
            if not response or (isinstance(response, str) and not response.strip()):
                return QueryDatabaseOutput(
                    reply="No relevant content found in the processed videos. The database may be empty or the query may need to be reformulated.",
                    error_message="Empty response from database"
                )
            
            return QueryDatabaseOutput(reply=response)
                
        except Exception as e:
            error_message = f"Failed to query vector DB: {str(e)}"
            self.logger.error(error_message)
            self.logger.error(traceback.format_exc())
            return QueryDatabaseOutput(
                reply="Error occurred while querying the database",
                error_message=error_message
            )
# class QueryDatabaseTool(BaseTool):
#     name: str = "Query Database"
#     description: str = "Queries the vector database containing processed Instagram content"
#     args_schema: Type[BaseModel] = QueryDatabaseInput
#     app: Any = Field(default=None, exclude=True)

#     def __init__(self, app: App, **data):
#         super().__init__(**data)
#         self.app = app

#     def _run(self, query: str) -> QueryDatabaseOutput:
#         try:
#             logger.info(f"Querying vector DB with: {query}")
#             reply = self.app.query(
#                 f"""Please analyze the following query about the Instagram content: {query}
#                 Focus on providing specific examples and quotes from the posts."""
#             )
#             logger.info("Query completed successfully")
            
#             if not reply or (isinstance(reply, str) and not reply.strip()):
#                 return QueryDatabaseOutput(
#                     reply="No relevant content found in the processed posts.",
#                     error_message="Empty response from database"
#                 )
            
#             return QueryDatabaseOutput(reply=reply)
                
#         except Exception as e:
#             error_message = f"Failed to query vector DB: {str(e)}"
#             logger.error(error_message)
#             return QueryDatabaseOutput(
#                 reply="Error occurred",
#                 error_message=error_message
#             )

# async def main_async():
#     logger = logging.getLogger(__name__)
    
#     # Get app instance
#     from smartfunnel.tools.chroma_db_init import get_app_instance
#     app_instance = get_app_instance()
    
#     # Initialize tools
#     fetch_tool = AsyncFetchInstagramPostsTool()
#     query_tool = QueryDatabaseTool(app=app_instance)
    
#     try:
#         instagram_username = "antoineblanco99"
#         logger.info(f"Fetching posts from {instagram_username}...")
#         fetch_result = fetch_tool.run(instagram_username=instagram_username)
        
#         if fetch_result.success:
#             logger.info(f"Successfully fetched {len(fetch_result.posts)} posts")
        
#         if fetch_result.success:
#             logger.info(f"Successfully fetched {len(fetch_result.posts)} posts")
#             video_posts = [p for p in fetch_result.posts if p.is_video]
#             logger.debug(f"Found {len(video_posts)} video posts")
            
#             for i, post in enumerate(video_posts):
#                 logger.debug(f"Video {i+1}/{len(video_posts)}:")
#                 logger.debug(f"  ID: {post.post_id}")
#                 logger.debug(f"  URL: {post.video_url}")
#                 logger.debug(f"  Caption preview: {post.caption[:100]}")
            
#             logger.info("Processing videos...")
#             processed_urls = await process_posts_concurrently(
#                 app_instance,
#                 fetch_result.posts,
#                 max_concurrent=5
#             )
            
#             if processed_urls:
#                 logger.info(f"Successfully processed {len(processed_urls)} videos")
#                 logger.debug("Processed URLs:")
#                 for url in processed_urls:
#                     logger.debug(f"  {url}")
                
#                 # Verify content immediately after processing
#                 logger.info("Verifying immediate database content...")
#                 test_query = "What is the main topic of these videos?"
#                 immediate_test = app_instance.query(test_query)
#                 logger.debug(f"Immediate test query result: {immediate_test[:500] if immediate_test else 'None'}")
                
#                 # Wait a moment for any async operations to complete
#                 await asyncio.sleep(2)
                
#                 # Proceed with regular queries
#                 queries = [
#                     "Tell me about the content of these videos",
#                     # ... other queries ...
#                 ]
                
#                 for query in queries:
#                     logger.info(f"Executing query: {query}")
#                     query_result = query_tool.run(query=query)
#                     logger.debug(f"Query result: {query_result.reply[:500]}")
#                     print(f"\nQuery: {query}")
#                     print("-" * 50)
#                     print(f"Response: {query_result.reply}\n")
#             else:
#                 logger.warning("No videos were successfully processed")
#         else:
#             logger.error(f"Fetching failed: {fetch_result.error_message}")
            
#     except Exception as e:
#         logger.error(f"Error in main execution: {str(e)}")
#         import traceback
#         logger.error(traceback.format_exc())

# def main():
#     """Entry point for the script."""
#     asyncio.run(main_async())

# if __name__ == "__main__":
#     main()

# async def main_async():
#     logger = logging.getLogger(__name__)
#     logger.setLevel(logging.DEBUG)
    
#     try:
#         # Get app instance
#         from smartfunnel.tools.chroma_db_init import get_app_instance
#         app_instance = get_app_instance()
        
#         # Initialize tools
#         fetch_tool = AsyncFetchInstagramPostsTool()
#         query_tool = QueryDatabaseTool(app=app_instance)
        
#         # Fetch and process posts
#         instagram_username = "antoineblanco99"
#         logger.info(f"Fetching posts from {instagram_username}...")
#         fetch_result = fetch_tool.run(instagram_username=instagram_username)
        
#         if fetch_result.success:
#             logger.info(f"Successfully fetched {len(fetch_result.posts)} posts")
#             video_posts = [p for p in fetch_result.posts if p.is_video]
#             logger.debug(f"Found {len(video_posts)} video posts")
            
#             # Process videos
#             processed_urls = await process_posts_concurrently(
#                 app_instance,
#                 fetch_result.posts,
#                 max_concurrent=5
#             )

#             if processed_urls:
#                 logger.info(f"Successfully processed {len(processed_urls)} videos")
                
#                 # Wait for database to fully process
#                 await asyncio.sleep(5)
                
#                 print("\nFinal Database Verification:")
#                 print("="*50)
                
#                 # Try different methods to verify database content
#                 app_instance = get_app_instance()
                
#                 try:
#                     # Method 1: Direct database access
#                     collection_data = app_instance.db.get()
#                     print("Database contents:")
#                     print(json.dumps(collection_data, indent=2))
#                 except Exception as e:
#                     print(f"Could not access database directly: {str(e)}")
                
#                 # Method 2: List all stored documents
#                 try:
#                     docs = app_instance.db.list()
#                     print("\nStored documents:")
#                     for doc in docs:
#                         print(f"Document ID: {doc.id}")
#                         print(f"Content preview: {doc.page_content[:200]}...")
#                         print("-"*30)
#                 except Exception as e:
#                     print(f"Could not list documents: {str(e)}")

#             # if processed_urls:
#             #     logger.info(f"Successfully processed {len(processed_urls)} videos")
                
#             #     # Wait for database to fully process
#             #     await asyncio.sleep(5)
                
#             #     # Verify database content is accessible
#             #     logger.info("Verifying database content...")
                
#                 # Test queries with increasingly specific focus
#                 test_queries = [
#                     "What are the main topics discussed in these videos?",
#                     "What specific examples or quotes can you find from any of the videos?",
#                     "Are there any recurring themes or patterns in the video content?",
#                     "What is the overall tone or style of these videos?",
#                 ]
                
#                 for query in test_queries:
#                     logger.info(f"\nExecuting test query: {query}")
#                     query_result = query_tool.run(query=query)
                    
#                     logger.info("-" * 50)
#                     logger.info(f"Query: {query}")
#                     logger.info(f"Response: {query_result.reply}")
#                     logger.info("-" * 50)
                    
#                     # Wait briefly between queries
#                     await asyncio.sleep(1)
                
#                 # Verify database size and content
#                 try:
#                     collection_info = app_instance.db.get_collection_info()
#                     logger.info(f"Database collection info: {collection_info}")
#                 except Exception as e:
#                     logger.error(f"Error getting collection info: {str(e)}")
#             else:
#                 logger.warning("No videos were successfully processed")
#         else:
#             logger.error(f"Fetching failed: {fetch_result.error_message}")
            
#     except Exception as e:
#         logger.error(f"Error in main execution: {str(e)}")
#         logger.error(traceback.format_exc())

# def main():
#     """Entry point for the script."""
#     asyncio.run(main_async())

# if __name__ == "__main__":
#     main()

async def main_async():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    
    try:
        # Get app instance
        from smartfunnel.tools.chroma_db_init import get_app_instance
        app_instance = get_app_instance()
        
        # Initialize tools
        fetch_tool = AsyncFetchInstagramPostsTool()
        query_tool = QueryDatabaseTool(app=app_instance)
        
        # Fetch and process posts
        instagram_username = "antoineblanco99"
        logger.info(f"Fetching posts from {instagram_username}...")
        fetch_result = fetch_tool.run(instagram_username=instagram_username)
        
        if fetch_result.success:
            logger.info(f"Successfully fetched {len(fetch_result.posts)} posts")
            video_posts = [p for p in fetch_result.posts if p.is_video]
            logger.debug(f"Found {len(video_posts)} video posts")
            
            # Process videos
            processed_urls = await process_posts_concurrently(
                app_instance,
                fetch_result.posts,
                max_concurrent=5
            )
            
            if processed_urls:
                logger.info(f"Successfully processed {len(processed_urls)} videos")
                
                # Wait for database to fully process
                await asyncio.sleep(5)
                
                # Test the database content with specific queries
                test_queries = [
                    "What was discussed in these videos?",
                    "Give me the exact transcription of any of the videos.",
                    "What are the main points mentioned in any of the videos?",
                    "Tell me any specific quotes from the videos."
                ]
                
                print("\nTesting database content:")
                print("=" * 50)
                for query in test_queries:
                    try:
                        print(f"\nQuery: {query}")
                        response = app_instance.query(query)
                        print(f"Response: {response[:500]}..." if len(response) > 500 else response)
                    except Exception as e:
                        print(f"Query failed: {str(e)}")
                    print("-" * 50)
            else:
                logger.warning("No videos were successfully processed")
        else:
            logger.error(f"Fetching failed: {fetch_result.error_message}")
            
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        logger.error(traceback.format_exc())

def main():
    """Entry point for the script."""
    asyncio.run(main_async())

if __name__ == "__main__":
    main()