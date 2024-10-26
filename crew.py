from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

import sys
import os

# Uncomment the following line to use an example of a custom tool
# from smartfunnel.tools.custom_tool import MyCustomTool
from smartfunnel.tools.FetchLatestVideosFromYouTubeChannelTool import FetchLatestVideosFromYouTubeChannelTool
from smartfunnel.tools.AddVideoToVectorDBTool import AddVideoToVectorDBTool
from smartfunnel.tools.QueryVectorDBTool import QueryVectorDBTool
from smartfunnel.tools.FetchRelevantVideosFromYouTubeChannelTool import FetchRelevantVideosFromYouTubeChannelTool
from smartfunnel.tools.FetchToAddInstagramAudioTool import FetchToAddInstagramAudioTool
from crewai_tools import SerperDevTool
from typing import List, Optional

from crewai import Agent, Crew, Process, Task
from crewai_tools import FirecrawlSearchTool
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
# Load environment variables
load_dotenv()

from pydantic import BaseModel, Field
from typing import List, Optional

from pydantic import BaseModel, Field
from typing import List, Optional

# class ValueObject(BaseModel):
#     name: str = Field(..., description="The name of the value, e.g., 'perseverance'")
#     origin: str = Field(..., description="The origin or development of the value, e.g., 'Developed this trait when joining the army and completing the program after 3 attempts'")
#     impact_today: str = Field(..., description="How the value impacts how the creator works today, e.g., 'When cold calling people, understands the power of numbers and having to go through a lot of setbacks to get a successful call'")

# class ChallengeObject(BaseModel):
#     description: str = Field(..., description="Description of the challenge, e.g., 'Experiencing homelessness in 2009'")
#     learnings: str = Field(..., description="The lessons the creator learned from the challenge, e.g., 'Made survival and ruthless prioritization his first priority'")

# class AchievementObject(BaseModel):
#     description: str = Field(..., description="Description of the achievement, e.g., 'Founding own creative agency \"On Air\"', 'Speaking at TEDx Conferences'")

# class LifeEventObject(BaseModel):
#     name: str = Field(..., description="Name or title of the life event, e.g., 'Childhood'")
#     description: str = Field(..., description="Description of the life event, e.g., 'Grew up on a quiet island called La Désirade, in Guadeloupe'")

# class BusinessObject(BaseModel):
#     name: str = Field(..., description="Name of the business, e.g., 'Agency \"On Air\"'")
#     description: str = Field(..., description="Description of the business, e.g., 'Marketing strategist to drive innovation in large corporates'")
#     genesis: str = Field(..., description="How the business started, e.g., 'Started as a freelancer, building out the skills to turn them into an agency in 2010'")

# class ContentCreatorInfo(BaseModel):
#     life_events: List[LifeEventObject] = Field(..., description="List of significant life events that shaped the creator's journey")
#     business: BusinessObject = Field(..., description="Information about the creator's business or primary professional venture")
#     values: List[ValueObject] = Field(..., description="List of the creator's core values that guide their work and life")
#     challenges: List[ChallengeObject] = Field(..., description="List of significant challenges faced by the creator and how they overcame them")
#     achievements: List[AchievementObject] = Field(..., description="List of the creator's notable achievements and milestones")

#     first_name: Optional[str] = Field(None, description="The first name of the content creator")
#     last_name: Optional[str] = Field(None, description="The last name of the content creator")

class ValueObject(BaseModel):
    name: str = Field(
        ..., 
        description="The name of the value, e.g., 'perseverance'"
    )
    origin: str = Field(
        ..., 
        description="The origin or development of the value, e.g., 'Developed this trait when joining the army and completing the program after 3 attempts'"
    )
    impact_today: str = Field(
        ..., 
        description="How the value impacts how the creator works today, e.g., 'When cold calling people, understands the power of numbers and having to go through a lot of setbacks to get a successful call'"
    )

    # Add default constructor for error handling
    @classmethod
    def default(cls) -> 'ValueObject':
        return cls(
            name="",
            origin="",
            impact_today=""
        )

class ChallengeObject(BaseModel):
    description: str = Field(
        ..., 
        description="Description of the challenge, e.g., 'Experiencing homelessness in 2009'"
    )
    learnings: str = Field(
        ..., 
        description="The lessons the creator learned from the challenge, e.g., 'Made survival and ruthless prioritization his first priority'"
    )

    @classmethod
    def default(cls) -> 'ChallengeObject':
        return cls(
            description="",
            learnings=""
        )

class AchievementObject(BaseModel):
    description: str = Field(
        ..., 
        description="Description of the achievement, e.g., 'Founding own creative agency \"On Air\"', 'Speaking at TEDx Conferences'"
    )

    @classmethod
    def default(cls) -> 'AchievementObject':
        return cls(
            description=""
        )

class LifeEventObject(BaseModel):
    name: str = Field(
        ..., 
        description="Name or title of the life event, e.g., 'Childhood'"
    )
    description: str = Field(
        ..., 
        description="Description of the life event, e.g., 'Grew up on a quiet island called La Désirade, in Guadeloupe'"
    )

    @classmethod
    def default(cls) -> 'LifeEventObject':
        return cls(
            name="",
            description=""
        )

class BusinessObject(BaseModel):
    name: str = Field(
        ..., 
        description="Name of the business, e.g., 'Agency \"On Air\"'"
    )
    description: str = Field(
        ..., 
        description="Description of the business, e.g., 'Marketing strategist to drive innovation in large corporates'"
    )
    genesis: str = Field(
        ..., 
        description="How the business started, e.g., 'Started as a freelancer, building out the skills to turn them into an agency in 2010'"
    )

    @classmethod
    def default(cls) -> 'BusinessObject':
        return cls(
            name="",
            description="",
            genesis=""
        )

class ContentCreatorInfo(BaseModel):
    life_events: List[LifeEventObject] = Field(
        ..., 
        description="List of significant life events that shaped the creator's journey"
    )
    business: BusinessObject = Field(
        ..., 
        description="Information about the creator's business or primary professional venture"
    )
    values: List[ValueObject] = Field(
        ..., 
        description="List of the creator's core values that guide their work and life"
    )
    challenges: List[ChallengeObject] = Field(
        ..., 
        description="List of significant challenges faced by the creator and how they overcame them"
    )
    achievements: List[AchievementObject] = Field(
        ..., 
        description="List of the creator's notable achievements and milestones"
    )
    first_name: Optional[str] = Field(
        None, 
        description="The first name of the content creator"
    )
    last_name: Optional[str] = Field(
        None, 
        description="The last name of the content creator"
    )

    @classmethod
    def default(cls) -> 'ContentCreatorInfo':
        return cls(
            first_name="",
            last_name="",
            life_events=[LifeEventObject.default()],
            business=BusinessObject.default(),
            values=[ValueObject.default()],
            challenges=[ChallengeObject.default()],
            achievements=[AchievementObject.default()]
        )

# Update the _extract_content_creator_info method in PromptingRagTool
# def _extract_content_creator_info(self, input_string: str) -> ContentCreatorInfo:
#     """Extract ContentCreatorInfo using regex-based parsing with fallbacks."""
#     try:
#         cleaned_input = self._clean_input_string(input_string)

#         # Try to extract all components
#         try:
#             life_events = self._extract_list_items(cleaned_input, "LifeEventObject")
#             life_events_objects = [LifeEventObject(**item) for item in life_events] if life_events else [LifeEventObject.default()]
#         except:
#             life_events_objects = [LifeEventObject.default()]

#         try:
#             business_data = self._extract_business_object(cleaned_input)
#             business_object = BusinessObject(**business_data) if business_data else BusinessObject.default()
#         except:
#             business_object = BusinessObject.default()

#         try:
#             values = self._extract_list_items(cleaned_input, "ValueObject")
#             values_objects = [ValueObject(**item) for item in values] if values else [ValueObject.default()]
#         except:
#             values_objects = [ValueObject.default()]

#         try:
#             challenges = self._extract_list_items(cleaned_input, "ChallengeObject")
#             challenges_objects = [ChallengeObject(**item) for item in challenges] if challenges else [ChallengeObject.default()]
#         except:
#             challenges_objects = [ChallengeObject.default()]

#         try:
#             achievements = self._extract_list_items(cleaned_input, "AchievementObject")
#             achievements_objects = [AchievementObject(**item) for item in achievements] if achievements else [AchievementObject.default()]
#         except:
#             achievements_objects = [AchievementObject.default()]

#         # Create ContentCreatorInfo with extracted or default values
#         return ContentCreatorInfo(
#             first_name=self._extract_field_value(cleaned_input, "first_name") or "",
#             last_name=self._extract_field_value(cleaned_input, "last_name") or "",
#             life_events=life_events_objects,
#             business=business_object,
#             values=values_objects,
#             challenges=challenges_objects,
#             achievements=achievements_objects
#         )

#     except Exception as e:
#         # If everything fails, return default ContentCreatorInfo
#         return ContentCreatorInfo.default()

from smartfunnel.tools.chroma_db_init import app_instance
# from smartfunnel.tools.QueryInstagramDBTool import QueryInstagramDBTool
# from smartfunnel.tools.FetchInstagramPostsTool import FetchInstagramPostsTool, set_instagram_credentials
# from smartfunnel.tools.FetchInstagramPostsTool import AddPostsToVectorDBTool
# from smartfunnel.tools.InstagramIntegratedTool import AddInstagramAudioTool, QueryDatabaseTool, FetchInstagramPostsTool
from smartfunnel.tools.PromptingRagTool import PromptingRagTool
from smartfunnel.tools.FetchToAddInstagramAudioTool import FetchToAddInstagramAudioTool
from smartfunnel.tools.QueryInstagramDBTool import QueryInstagramDBTool
# from smartfunnel.tools.FetchInstagramPostsTool import FetchInstagramPostsTool, AddPostsToVectorDBTool
from smartfunnel.tools.QueryInstagramDBTool import QueryInstagramDBTool
# --- Tools ---
# fetch_latest_videos_tool = FetchLatestVideosFromYouTubeChannelTool()
fetch_relevant_videos_tool = FetchRelevantVideosFromYouTubeChannelTool()
add_video_to_vector_db_tool = AddVideoToVectorDBTool(app=app_instance)
fire_crawl_search_tool = FirecrawlSearchTool()
rag_tool = QueryVectorDBTool(app=app_instance)

# First set the Instagram credentials (do this once at the start)
# set_instagram_credentials("vladzieg", "Lommel1996+")

# Initialize tools
# fetch_instagram_posts_tool = FetchInstagramPostsTool()
# add_posts_to_vectordb_tool = AddInstagramAudioTool(app=app_instance)
# query_instagram_db_tool = QueryDatabaseTool(app=app_instance)
prompting_rag_tool = PromptingRagTool()
fetch_to_add_instagram_audio_tool = FetchToAddInstagramAudioTool(app=app_instance)
query_instagram_db_tool = QueryInstagramDBTool(app=app_instance)
@CrewBase
class LatestAiDevelopmentCrew():
	"""LatestAiDevelopment crew"""

	@agent
	def scrape_agent(self) -> Agent:
		return Agent(
			config=self.agents_config['scrape_agent'],
			tools=[fetch_relevant_videos_tool], # Example of custom tool, loaded on the beginning of file
			verbose=True,
			allow_delegation=False,
			llm=ChatOpenAI(model="gpt-4o-mini")
		)
	@agent
	def vector_db_agent(self) -> Agent:
		return Agent(
			config=self.agents_config['vector_db_agent'],
			tools=[add_video_to_vector_db_tool],
			verbose=True,
			allow_delegation=False,
			llm=ChatOpenAI(model="gpt-4o-mini")
		)
	
	@agent
	def general_research_agent(self) -> Agent:
		return Agent(
			config=self.agents_config['general_research_agent'],
			tools=[rag_tool, query_instagram_db_tool],
			verbose=True,
			allow_delegation=False,
			llm=ChatOpenAI(model="gpt-4o-mini")
		)
	
	@agent
	def follow_up_agent(self) -> Agent:
		return Agent(
			config=self.agents_config['follow_up_agent'],
			tools=[rag_tool, query_instagram_db_tool],
			verbose=True,
			allow_delegation=False,
			llm=ChatOpenAI(model="gpt-4o-mini")
		)
	
	@agent
	def fallback_agent(self) -> Agent:
		return Agent(
			config=self.agents_config['fallback_agent'],
			tools=[rag_tool],
			verbose=True,
			allow_delegation=False,
			llm=ChatOpenAI(model="gpt-4o-mini")
		)
	
	# @agent
	# def scrape_agent_instagram(self) -> Agent:
	# 	return Agent(
	# 		config=self.agents_config['scrape_agent_instagram'],
	# 		tools=[fetch_to_add_instagram_audio_tool],
	# 		verbose=True,
	# 		allow_delegation=False,
	# 		llm=ChatOpenAI(model="gpt-4o-mini")
	# 	)
	
	# @agent
	# def vector_db_agent_instagram(self) -> Agent:
	# 	return Agent(
	# 		config=self.agents_config['vector_db_agent_instagram'],
	# 		tools=[fetch_to_add_instagram_audio_tool],
	# 		verbose=True,
	# 		allow_delegation=False,
	# 		llm=ChatOpenAI(model="gpt-4o-mini")
	# 	)


	@agent
	def fetch_to_add_instagram_audio_agent(self) -> Agent:
		return Agent(
			config=self.agents_config['fetch_to_add_instagram_audio_agent'],
			tools=[fetch_to_add_instagram_audio_tool],
			verbose=True,
			allow_delegation=False,
			llm=ChatOpenAI(model="gpt-4o-mini")
		)

	@agent
	def prompting_rag_agent(self) -> Agent:
		return Agent(
			config=self.agents_config['prompting_rag_agent'],
			tools=[prompting_rag_tool],
			verbose=True,
			allow_delegation=False,
			llm=ChatOpenAI(model="gpt-4o-mini")
		)
	
	# @task
	# def scrape_instagram_channel_task(self) -> Task:
	# 	return Task(
	# 		config=self.tasks_config['scrape_instagram_channel_task'],
	# 		tools=[fetch_instagram_posts_tool],
	# 	)
	
	# @task
	# def process_instagram_posts_task(self) -> Task:
	# 	return Task(
	# 		config=self.tasks_config['process_instagram_posts_task'],
	# 		tools=[add_posts_to_vectordb_tool],
	# 	)

	@task
	def fetch_and_add_instagram_audio_task(self) -> Task:
		return Task(
			config=self.tasks_config['fetch_and_add_instagram_audio_task'],
			tools=[fetch_to_add_instagram_audio_tool],
		)
	
	@task
	def find_instagram_information_task(self) -> Task:
		return Task(
			config=self.tasks_config['find_instagram_information_task'],
			tools=[query_instagram_db_tool],
			output_pydantic=ContentCreatorInfo,
		)
	
	@task
	def follow_up_instagram_task(self) -> Task:
		return Task(
			config=self.tasks_config['follow_up_instagram_task'],
			tools=[query_instagram_db_tool],
			output_pydantic=ContentCreatorInfo,
		)

	@task
	def scrape_youtube_channel_task(self) -> Task:
		return Task(
			config=self.tasks_config['scrape_youtube_channel_task'],
			tools=[fetch_relevant_videos_tool],
			# context="Use the FetchLatestVideosFromYouTubeChannelTool to fetch the latest videos from the YouTube channel.",
		)
	
	@task
	def process_video_task(self) -> Task:
		return Task(
			config=self.tasks_config['process_video_task'],
			tools=[add_video_to_vector_db_tool],
			# context="Use the AddVideoToVectorDBTool to add the video to the vector database."
		)

	@task
	def find_initial_information_task(self) -> Task:
		return Task(
			config=self.tasks_config['find_initial_information_task'],
			# context="Use the RagTool to find information about the content creator.",
			output_pydantic=ContentCreatorInfo,
			tools=[rag_tool]
		)
	
	@task
	def follow_up_task(self) -> Task:
		return Task(
			config=self.tasks_config['follow_up_task'],
			output_pydantic=ContentCreatorInfo,
            # context="Use the RagTool to find information about the content creator.",
			tools=[rag_tool]
		)
	
	@task
	def fallback_task(self) -> Task:
		return Task(
			config=self.tasks_config['fallback_task'],
			output_pydantic=ContentCreatorInfo,
			tools=[rag_tool,query_instagram_db_tool],
		)

	@task
	def prompting_rag_task(self) -> Task:
		return Task(
			config=self.tasks_config['prompting_rag_task'],
			tools=[prompting_rag_tool],
			# context={"content_creator_info": "fallback_task.output"},  # Changed this line
			# context=["fallback_task.output_pydantic"],
			output_file="prompting_rag_task_output.txt"
		)

	@crew
	def crew(self) -> Crew:
		"""Creates the LatestAiDevelopment crew"""
		return Crew(
			agents=self.agents, # Automatically created by the @agent decorator
			tasks=self.tasks, # Automatically created by the @task decorator
			process=Process.sequential,
			verbose=True,
			full_output=True
			# process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
		)