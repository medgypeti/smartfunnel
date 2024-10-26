from crewai_tools.tools.base_tool import BaseTool
from pydantic.v1 import BaseModel, Field
from typing import Any, Type
from embedchain import App
from youtube_transcript_api import YouTubeTranscriptApi
import logging
import re
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class AddVideoToVectorDBInput(BaseModel):
    video_url: str = Field(..., description="The URL of the YouTube video to add to the vector DB.")

class AddVideoToVectorDBOutput(BaseModel):
    success: bool = Field(..., description="Whether the video was successfully added to the vector DB.")
    error_message: str = Field(default="", description="Error message if the operation failed.")

class AddVideoToVectorDBTool(BaseTool):
    name: str = "Add Video to Vector DB"
    description: str = "Adds a YouTube video transcript to the vector database."
    args_schema: Type[AddVideoToVectorDBInput] = AddVideoToVectorDBInput
    app: Any = Field(default=None, exclude=True)

    def __init__(self, app: App, **data):
        super().__init__(**data)
        self.app = app

    def _extract_video_id(self, url: str) -> str:
        """Extract the video ID from a YouTube URL."""
        video_id_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
        if video_id_match:
            return video_id_match.group(1)
        else:
            raise ValueError("Could not extract video ID from URL")

    def _fetch_transcript(self, video_id: str) -> str:
        """Fetch the transcript for a given YouTube video ID."""
        try:
            # First, try to get the official transcript
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            return " ".join([entry['text'] for entry in transcript])
        except Exception as e:
            logger.warning(f"Failed to fetch official transcript: {str(e)}")
            
            # If official transcript fails, try to get auto-generated captions
            try:
                print("Trying to fetch auto-generated captions")
                # transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en-US', 'en'])
                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['fr-FR', 'fr'])
                return " ".join([entry['text'] for entry in transcript])
            except Exception as e:
                logger.warning(f"Failed to fetch auto-generated captions: {str(e)}")
                
                # If both methods fail, try to scrape the transcript
                print("Trying to scrape captions")
                return self._scrape_transcript(video_id)

    def _scrape_transcript(self, video_id: str) -> str:
        """Scrape the transcript from the YouTube video page."""
        url = f"https://www.youtube.com/watch?v={video_id}"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for the transcript in the page source
        transcript_element = soup.find('div', {'class': 'ytd-transcript-renderer'})
        if transcript_element:
            return transcript_element.get_text()
        else:
            raise Exception("Could not find transcript in the video page")

    def _run(self, video_url: str) -> AddVideoToVectorDBOutput:
        try:
            logger.info(f"Processing video: {video_url}")
            video_id = self._extract_video_id(video_url)
            transcript_text = self._fetch_transcript(video_id)
            
            logger.info(f"Adding transcript to vector DB for video ID: {video_id}")
            self.app.add(transcript_text, data_type="text", metadata={"source": video_url})
            logger.info("Transcript successfully added to vector DB")
            
            return AddVideoToVectorDBOutput(success=True)
        except Exception as e:
            error_message = f"Failed to add video transcript: {str(e)}"
            logger.error(error_message)
            return AddVideoToVectorDBOutput(success=False, error_message=error_message)

class QueryVectorDBInput(BaseModel):
    query: str = Field(..., description="The query to search the vector DB.")

class QueryVectorDBOutput(BaseModel):
    reply: str = Field(..., description="The reply from the query.")
    error_message: str = Field(default="", description="Error message if the operation failed.")

class QueryVectorDBTool(BaseTool):
    name: str = "Query Vector DB"
    description: str = "Queries the vector database with the given input."
    args_schema: Type[QueryVectorDBInput] = QueryVectorDBInput
    app: Any = Field(default=None, exclude=True)

    def __init__(self, app: App, **data):
        super().__init__(**data)
        self.app = app

    def _run(self, query: str) -> QueryVectorDBOutput:
        try:
            logger.info(f"Querying vector DB with: {query}")
            reply = self.app.query(query)
            logger.info(f"Query completed successfully")
            return QueryVectorDBOutput(reply=reply)
        except Exception as e:
            error_message = f"Failed to query vector DB: {str(e)}"
            logger.error(error_message)
            return QueryVectorDBOutput(reply="Error occurred", error_message=error_message)
        
import tempfile
import logging
from embedchain import App

OPENAI_API_KEY = "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"

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a temporary directory for ChromaDB
db_path = tempfile.mkdtemp()
logger.info(f"Created temporary directory for ChromaDB: {db_path}")

# Configuration dictionary
config = {
    'app': {
        'config': {
            'name': 'full-stack-app'
        }
    },
    'llm': {
        'provider': 'openai',
        'config': {
            'model': 'gpt-4o',
            'temperature': 0.3,
            'max_tokens': 4000,
            'prompt': (
                "Reply to the $query by providing as much information about the protagonist in the video as possible.\n"
                "Be comprehensive, accurate and precise. Share as much information as possible.\n"
                "Everytime you answer a question, figure out why it matters to the audience, and why it matters to the protagonist, and where/how he developed this trait, and how he's using it in practice in his life and business. Be specific\n"
                "Always try to extract the actionable practical advice from the video.\n"
                "Always keep the storytelling part that's relevant to the query. Keep the details of the story as accurate and precise as possible.\n"
                "For every reply, you should respond in sections, where each section is a single idea/concept/lesson/value/motivation/belief/etc.\n"
                "In each section, you should provide a clear claim, anecdote/story that was mentioned in the transcript to justify your claim.\n"
                "For every section, you should provide 1-3 hyper actionable and practical advice, tips that can be derived and executed from this insight.\n"
                # "For every information, back it up with a clear claim, anecdote/story that was mentioned in the transcript.\n"
                # "Each section can contain multiple paragraphs but it's important that each section contains a single idea/concept/lesson/value/motivation/belief/etc.\n"
                # "Return answer in bullet points.\n"
                "If you don't know the answer, just say that you don't know, don't try to make up an answer.\n"
                "Always end your reply with a summary of the main points you covered in the reply.\n"
                "Always translate the quotes back to English.\n"
                "$context\n\nQuery: $query\n\nHelpful Answer:"
            ),
            'system_prompt': (
                "Act as a potential customer of the author of the video. Interpret the answers based on what's in it for you. You want to learn practical advice that you can apply in your own personal or professional life. You know the importance of author's advice and takeaways, and real-lifestorytelling to absorb lessons."
            ),
            # 'prompt': (
            #     "You $query the information from the video transcript and reply with the relevant info.\n"
            #     "Answer in bullet points across multiple paragraphs.\n"
            #     "Be as comprehensive, accurate and precise as possible.\n"
            #     "Back up everything you say with real stories, anecdotes mentioned in the transcript.\n"
            #     "When applicable, you may refer paraphrase what the author said.\n"
            #     "For every information, give context on why it happened, when it happened, and it's impact on the author's life today.\n"
            #     "For every information, explain why it matters to the author, why it matters to the audience, how he develoepd this trait, and it's used in practice, and how it can be used to achieve their goals.\n"
            #     "Always try to extract the actionable practical advice from the comments.\n"
            #     "Each section can contain multiple paragraphs but it's important that each section contains a single idea/concept/lesson/value/motivation/belief/etc.\n"
            #     "Every bullet point should be based on actual information from the transcript and real-life events/examples mentioned in the scripts\n"
            #     "If you don't know the answer, just say that you don't know, don't try to make up an answer.\n"

            #     "Here is an example:"
            #     "Perseverance: The author developed this trait when he was a kid. He was determined to become a great basketball player, and he practiced every day for hours, even when he was injured. This trait helped him overcome many obstacles and achieve his goals.\n"
            #     "Practical advice: To develop perseverance, set clear goals and stay focused on them. Break down big goals into smaller ones and celebrate each small achievement. Stay disciplined and don't give up, even when faced with challenges.\n"
            #     "Here is another example:"
            #     "Grit: The author developed this trait when he was a teenager. He was determined to become a great musician, and he practiced every day for hours, even when he was tired and wanted to give up. This trait helped him overcome many obstacles and achieve his goals.\n"
            #     "Practical advice: To develop grit, set clear goals and stay focused on them. Break down big goals into smaller ones and celebrate each small achievement. Stay disciplined and don't give up, even when faced with challenges.\n"

            #     "$context\n\nQuery: $query\n\nHelpful Answer:"
            # ),
            # 'prompt': (
            #     "Get the information from the video transcript and answer the query.\n"
            #     "Everytime you answer a question, figure out why it matters to the audience, and why it matters to the author, and where/how he developed this trait, and how he's using it in practice in his life and business. Be specific\n"
            #     "Always try to extract the actionable practical advice from the video.\n"
            #     "What are the intrinsic motivations, core values, mental models that the author developed and that we can infer from the video?\n"
            #     "For every information, back it up with a clear claim, anecdote/story that was mentioned in the transcript.\n"
            #     "Return answer in bullet points.\n"
            #     "If you don't know the answer, just say that you don't know, don't try to make up an answer.\n"
            #     "$context\n\nQuery: $query\n\nHelpful Answer:"
            # ),
            # 'system_prompt': (
            #     "Act as a potential customer of the protagonist in the video. Interpret the answers of the protagonist based on what's in it for you. Your goal is to learn about the protagonist's story to apply his learnings to improve your professional career."
            #     # "You are the author of the video. You reply in the same tone as the author. You're a master storyteller and seller. You always tie an idea to a real story, anecdote, or life event from the transcript.\n"
            #     # "when you reply to the $query, focus on info that matters to the audience, and why it matters to understand the author.\n"
            #     # "For every information, give concrete info based on transcript on the context behind the info, and it's impact on the author's life today.\n"
            #     # "When you reply to the $query, focus on info that matters to the audience, and why it matters to understand the author.\n"
            # ),
            # 'system_prompt': (
            #     "Get the information from the video transcript and answer the $query.\n"
            #     # "when you reply to the $query, focus on info that matters to the audience, and why it matters to understand the author.\n"
            #     # "For every information, give concrete info based on transcript on the context behind the info, and it's impact on the author's life today.\n"
            #     # "When you reply to the $query, focus on info that matters to the audience, and why it matters to understand the author.\n"
            #     "Answer in bullet points across multiple paragraphs.\n"
            #     # "Each section of the bullet points should be a separate topic or theme from the video.\n"
            #     "Each section should be about either a value, intrinsic motivation, core belief, or mental model that the author developed.\n"
            #     "Per section, clearly, and accurately describe where, the context, period, life-event, or situation where the author first developed this trait/belief/character/etc. Be specific and use real info from the transcript.\n"
            #     "Per section, give 1-3 concrete actionable advice, tips that can be derived from this insight.\n"
            #     "Per section, back it up with a real anecdote, story, life event, biography, or background info about the author that explains why the author developed this trait and how it's relevant to the audience.\n"
            #     # "Per section, paraphrase section where the evidence of your claim lies.\n"
            #     # # "Specify how the author's learnings can be actioned, learnt, developed by someone else.\n"
            #     # # "To understand the author, infer, or explain the intrinsic motivations, core values, mental models behind the author.\n"
            #     # # "For every information, back it up with a clear anecdote, story, life event, biography, or background info about the author.\n"
            #     # # "Keep the original section of the transcript where the evidence of your claim lies.\n"
            #     # "IMPORTANT: Focus on the impact of storytelling, and the story of the author, and how it's relevant to the audience.\n"
            #     # "IMPORTANT: Always explain how the life events of the author shaped his life.\n"
            #     # "Return the answer in bullet points.\n"
            #     "If you don't know the answer, just say that you don't know, don't try to make up an answer.\n"
            # ),
            'api_key': OPENAI_API_KEY,
        }
    },
    'vectordb': {
        'provider': 'chroma',
        'config': {
            'dir': db_path,
            'allow_reset': True
        }
    },
    'embedder': {
        'provider': 'openai',
        'config': {
            'model': 'text-embedding-ada-002',
            'api_key': OPENAI_API_KEY,
        }
    },
}
# config = {
#     'app': {
#         'config': {
#             'name': 'full-stack-app'
#         }
#     },
#     'llm': {
#         'provider': 'openai',
#         'config': {
#             'model': 'gpt-4o-mini',
#             'temperature': 0.5,
#             'max_tokens': 5000,
#             # 'prompt': (
#             #     "Get the information from the video transcript and answer the query.\n"
#             #     "Everytime you answer a question, figure out why it matters to the audience, and why it matters to the author, and where/how he developed this trait, and how he's using it in practice in his life and business. Be specific\n"
#             #     "Always try to extract the actionable practical advice from the video.\n"
#             #     "What are the intrinsic motivations, core values, mental models that the author developed and that we can infer from the video?\n"
#             #     "For every information, back it up with a clear claim, anecdote/story that was mentioned in the transcript.\n"
#             #     "Return answer in bullet points.\n"
#             #     "If you don't know the answer, just say that you don't know, don't try to make up an answer.\n"
#             #     "$context\n\nQuery: $query\n\nHelpful Answer:"
#             # ),
#             'system_prompt': (
#                 "Get the information from the video transcript and answer the $query.\n"
#                 # "when you reply to the $query, focus on info that matters to the audience, and why it matters to understand the author.\n"
#                 # "For every information, give concrete info based on transcript on the context behind the info, and it's impact on the author's life today.\n"
#                 # "When you reply to the $query, focus on info that matters to the audience, and why it matters to understand the author.\n"
#                 "Answer in bullet points across multiple paragraphs.\n"
#                 # "Each section of the bullet points should be a separate topic or theme from the video.\n"
#                 "Each section should be about either a value, intrinsic motivation, core belief, or mental model that the author developed.\n"
#                 "Per section, clearly, and accurately describe where, the context, period, life-event, or situation where the author first developed this trait/belief/character/etc. Be specific and use real info from the transcript.\n"
#                 "Per section, give 1-3 concrete actionable advice, tips that can be derived from this insight.\n"
#                 "Per section, back it up with a real anecdote, story, life event, biography, or background info about the author that explains why the author developed this trait and how it's relevant to the audience.\n"
#                 # "Per section, paraphrase section where the evidence of your claim lies.\n"
#                 # # "Specify how the author's learnings can be actioned, learnt, developed by someone else.\n"
#                 # # "To understand the author, infer, or explain the intrinsic motivations, core values, mental models behind the author.\n"
#                 # # "For every information, back it up with a clear anecdote, story, life event, biography, or background info about the author.\n"
#                 # # "Keep the original section of the transcript where the evidence of your claim lies.\n"
#                 # "IMPORTANT: Focus on the impact of storytelling, and the story of the author, and how it's relevant to the audience.\n"
#                 # "IMPORTANT: Always explain how the life events of the author shaped his life.\n"
#                 # "Return the answer in bullet points.\n"
#                 "If you don't know the answer, just say that you don't know, don't try to make up an answer.\n"
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

def get_app_instance():
    return App.from_config(config=config)

app_instance = get_app_instance()

from smartfunnel.tools.chroma_db_init import app_instance

# --- Tools ---
add_video_to_vector_db_tool = AddVideoToVectorDBTool(app=app_instance)
rag_tool = QueryVectorDBTool(app=app_instance)

def main():
    # video_url = "https://www.youtube.com/watch?v=VeH7qKZr0WI&ab_channel=LexFridman"
    video_url = "https://www.youtube.com/watch?v=9yXYxD4TrEc&ab_channel=AntoineBlanco"
    # video_url = "https://www.youtube.com/watch?v=AfMu_7vQkPs&ab_channel=AntoineBlanco"
    # video_url = "https://www.youtube.com/watch?v=5z_YJ5k6kzw&t=2032s&ab_channel=AntoineBlanco"
    query = "What are the 8 specific tips mentioned in the video that I can apply to my business?"
    # Step 1: Add video to vector DB
    logger.info(f"Adding video to vector DB: {video_url}")
    add_result = add_video_to_vector_db_tool.run(video_url)
    if not add_result.success:
        logger.error(f"Failed to add video: {add_result.error_message}")
        return

    # Step 2: Query the vector DB
    logger.info(f"Querying vector DB with: {query}")
    query_result = rag_tool.run(query)

    # Print the result
    print(f"Reply: {query_result.reply}")
    if query_result.error_message:
        logger.error(f"Query error: {query_result.error_message}")

if __name__ == "__main__":
    main()