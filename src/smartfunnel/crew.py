from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

import sys
import os

# Uncomment the following line to use an example of a custom tool
# from smartfunnel.tools.custom_tool import MyCustomTool
# from smartfunnel.tools.FetchLatestVideosFromYouTubeChannelTool import FetchLatestVideosFromYouTubeChannelTool
# from smartfunnel.tools.AddVideoToVectorDBTool import AddVideoToVectorDBTool
# from smartfunnel.tools.QueryVectorDBTool import QueryVectorDBTool
# from smartfunnel.tools.FetchRelevantVideosFromYouTubeChannelTool import FetchRelevantVideosFromYouTubeChannelTool
# from smartfunnel.tools.FetchToAddInstagramAudioTool import FetchToAddInstagramAudioTool
# from FetchLatestVideosFromYouTubeChannelTool import FetchLatestVideosFromYouTubeChannelTool


from smartfunnel.tools.chroma_db_init import app_instance

from smartfunnel.tools.FetchRelevantVideosFromYouTubeChannelTool import FetchRelevantVideosFromYouTubeChannelTool
from smartfunnel.tools.AddVideoToVectorDBTool import AddVideoToVectorDBTool
from smartfunnel.tools.QueryVectorDBTool import QueryVectorDBTool

from smartfunnel.tools.FetchToAddInstagramAudioTool import FetchToAddInstagramAudioTool
from smartfunnel.tools.QueryInstagramDBTool import QueryInstagramDBTool

from smartfunnel.tools.PromptingRagTool import PromptingRagTool

from crewai_tools import SerperDevTool
from typing import List, Optional

from crewai import Agent, Crew, Process, Task
from crewai_tools import FirecrawlSearchTool
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
# Load environment variables
load_dotenv()

# from pydantic import BaseModel, Field
from typing import List, Optional
from crewai_tools.tools.base_tool import BaseTool

# from pydantic import BaseModel, Field
from typing import List, Optional

import streamlit as st
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

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

# from smartfunnel.tools.chroma_db_init import app_instance
# # from smartfunnel.tools.QueryInstagramDBTool import QueryInstagramDBTool
# # from smartfunnel.tools.FetchInstagramPostsTool import FetchInstagramPostsTool, set_instagram_credentials
# # from smartfunnel.tools.FetchInstagramPostsTool import AddPostsToVectorDBTool
# # from smartfunnel.tools.InstagramIntegratedTool import AddInstagramAudioTool, QueryDatabaseTool, FetchInstagramPostsTool
# from smartfunnel.tools.PromptingRagTool import PromptingRagTool
# from smartfunnel.tools.FetchToAddInstagramAudioTool import FetchToAddInstagramAudioTool
# from smartfunnel.tools.QueryInstagramDBTool import QueryInstagramDBTool
# # from smartfunnel.tools.FetchInstagramPostsTool import FetchInstagramPostsTool, AddPostsToVectorDBTool
# from smartfunnel.tools.QueryInstagramDBTool import QueryInstagramDBTool
# --- Tools ---
# fetch_latest_videos_tool = FetchLatestVideosFromYouTubeChannelTool()
fetch_relevant_videos_tool = FetchRelevantVideosFromYouTubeChannelTool()
add_video_to_vector_db_tool = AddVideoToVectorDBTool(app=app_instance)
fire_crawl_search_tool = FirecrawlSearchTool()
rag_tool = QueryVectorDBTool(app=app_instance)

from smartfunnel.tools.InputValidationTool import InputValidationTool
input_validation_tool = InputValidationTool()

from smartfunnel.tools.ResettingTool import ResetDatabaseTool
reset_database_tool = ResetDatabaseTool(app=app_instance)

# First set the Instagram credentials (do this once at the start)
# set_instagram_credentials("vladzieg", "Lommel1996+")

# Initialize tools
# fetch_instagram_posts_tool = FetchInstagramPostsTool()
# add_posts_to_vectordb_tool = AddInstagramAudioTool(app=app_instance)
# query_instagram_db_tool = QueryDatabaseTool(app=app_instance)

fetch_to_add_instagram_audio_tool = FetchToAddInstagramAudioTool(app=app_instance)
query_instagram_db_tool = QueryInstagramDBTool(app=app_instance)

from typing import List, Optional, Dict
from pydantic import BaseModel
from crewai import Agent, Crew, Process
# from crewai.tasks.conditional_task import ConditionalTask
# from crewai.tasks.task_output import TaskOutput


# def has_instagram_input(task_output: TaskOutput) -> bool:
#     """Check if Instagram username exists and is not empty"""
#     try:
#         # Access the raw output which should contain our validation results
#         if hasattr(task_output, 'raw'):
#             workflow_flags = task_output.raw.get('workflow_flags', {})
#             return workflow_flags.get('has_instagram', False)
#         return False
#     except Exception:
#         return False

# def has_youtube_input(task_output: TaskOutput) -> bool:
#     """Check if YouTube handle exists and is not empty"""
#     try:
#         # Access the raw output which should contain our validation results
#         if hasattr(task_output, 'raw'):
#             workflow_flags = task_output.raw.get('workflow_flags', {})
#             return workflow_flags.get('has_youtube', False)
#         return False
#     except Exception:
#         return False
    
# def has_instagram_input(inputs: Dict) -> bool:
#     """Check if Instagram username exists and is not empty"""
#     return bool(inputs.get('instagram_username'))

# def has_youtube_input(inputs: Dict) -> bool:
#     """Check if YouTube handle exists and is not empty"""
#     return bool(inputs.get('youtube_channel_handle'))

@CrewBase
class LatestAiDevelopmentCrew():
    """LatestAiDevelopment crew"""

    # @agent
    # def input_validation_agent(self) -> Agent:
    #     return Agent(
    #         tools=[InputValidationTool(result_as_answer=True)],
    #         verbose=True,
    #         allow_delegation=False,
    #         llm=ChatOpenAI(model="gpt-4o-mini"),
    #         config=self.agents_config['input_validation_agent']
    #     )

    # @agent
    # def starting_agent(self) -> Agent:
    #     return Agent(
    #         role="Input Validator",
    #         goal="Validate and process input parameters",
    #         backstory="I am responsible for validating input parameters and determining which tasks should run.",
    #         tools=[input_validation_tool],
    #         verbose=True,
    #         allow_delegation=False,
    #         llm=ChatOpenAI(model="gpt-4o-mini")
    #     )

    @agent
    def database_manager_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['database_manager_agent'],
            tools=[reset_database_tool],
            verbose=True,
            allow_delegation=False,
            llm=ChatOpenAI(model="gpt-4o-mini")
        )

    @agent
    def scrape_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['scrape_agent'],
            tools=[FetchRelevantVideosFromYouTubeChannelTool(result_as_answer=True)],  # Example of custom tool, loaded on the beginning of file
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
    
    # @agent
    # def fallback_agent(self) -> Agent:
    #     return Agent(
    #         config=self.agents_config['fallback_agent'],
    #         tools=[rag_tool, query_instagram_db_tool],
    #         verbose=True,
    #         allow_delegation=False,
    #         llm=ChatOpenAI(model="gpt-4o")
    #     )

    # Commented out Instagram agents
    # @agent
    # def scrape_agent_instagram(self) -> Agent:
    #     return Agent(
    #         config=self.agents_config['scrape_agent_instagram'],
    #         tools=[fetch_to_add_instagram_audio_tool],
    #         verbose=True,
    #         allow_delegation=False,
    #         llm=ChatOpenAI(model="gpt-4o-mini")
    #     )
    
    # @agent
    # def vector_db_agent_instagram(self) -> Agent:
    #     return Agent(
    #         config=self.agents_config['vector_db_agent_instagram'],
    #         tools=[fetch_to_add_instagram_audio_tool],
    #         verbose=True,
    #         allow_delegation=False,
    #         llm=ChatOpenAI(model="gpt-4o-mini")
    #     )

    @agent
    def fetch_to_add_instagram_audio_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['fetch_to_add_instagram_audio_agent'],
            tools=[FetchToAddInstagramAudioTool(app=app_instance, result_as_answer=True)],
            verbose=True,
            allow_delegation=False,
            llm=ChatOpenAI(model="gpt-4o-mini")
        )

    @agent
    def prompting_rag_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['prompting_rag_agent'],
            tools=[PromptingRagTool()],
            verbose=True,
            allow_delegation=False,
            llm=ChatOpenAI(model="gpt-4o-mini")
        )

    # @task
    # def starting_task(self) -> Task:
    #     return Task(
    #         description="""
    #         Validate the provided input parameters:
    #         1. Process the YouTube channel handle and Instagram username
    #         2. Return validated parameters and workflow flags
    #         3. Handle any null or missing values appropriately
    #         """,
    #         expected_output="""
    #         A JSON object containing validated parameters and workflow flags:
    #         """,
    #         agent=self.starting_agent(),
    #         tools=[InputValidationTool(result_as_answer=True)]
    #     )

    # @task
    # def starting_task(self) -> Task:
    #     """Initial task to validate inputs - this must be a regular Task, not ConditionalTask"""
    #     return Task(
    #         # description="Validate the input parameters and determine which workflows should run.",
    #         # expected_output="A structured output containing validated parameters.",
    #         agent=self.input_validation_agent(),  # Note the function call
    #         tools=[input_validation_tool]
    #     )

    @task
    def database_manager_task(self) -> Task:
        return Task(
            config=self.tasks_config['database_manager_task'],
            tools=[reset_database_tool]
        )

    @task
    def fetch_and_add_instagram_audio_task(self) -> Task:
        return Task(
            config=self.tasks_config['fetch_and_add_instagram_audio_task'],
            tools=[FetchToAddInstagramAudioTool(app=app_instance, result_as_answer=True)]
        )

    @task
    def find_instagram_information_task(self) -> Task:
        return Task(
            config=self.tasks_config['find_instagram_information_task'],
            tools=[query_instagram_db_tool],
            output_pydantic=ContentCreatorInfo
        )

    @task
    def follow_up_instagram_task(self) -> Task:
        return Task(
            config=self.tasks_config['follow_up_instagram_task'],
            tools=[query_instagram_db_tool],
            output_pydantic=ContentCreatorInfo
        )

    @task
    def scrape_youtube_channel_task(self) -> Task:
        return Task(
            config=self.tasks_config['scrape_youtube_channel_task'],
            tools=[FetchRelevantVideosFromYouTubeChannelTool(result_as_answer=True)]
        )

    @task
    def process_video_task(self) -> Task:
        return Task(
            config=self.tasks_config['process_video_task'],
            tools=[add_video_to_vector_db_tool]
        )
    
    @task
    def find_initial_information_task(self) -> Task:
        return Task(
            config=self.tasks_config['find_initial_information_task'],
            tools=[rag_tool],
            output_pydantic=ContentCreatorInfo
        )
    @task
    def follow_up_task(self) -> Task:
        return Task(
            config=self.tasks_config['follow_up_task'],
            # expected_output="Updated ContentCreatorInfo object with additional information",
            # agent=self.follow_up_agent(),
            tools=[rag_tool],
            output_pydantic=ContentCreatorInfo
        )

    # @task
    # def fallback_task(self) -> Task:
    #     return Task(
    #         config=self.tasks_config['fallback_task'],
    #         tools=[rag_tool, query_instagram_db_tool],
    #         output_pydantic=ContentCreatorInfo
    #     )

    @task
    def prompting_rag_task(self) -> Task:
        return Task(
            config=self.tasks_config['prompting_rag_task'],
            tools=[PromptingRagTool()],
            output_file="prompting_rag_task_output.txt",
            context=[self.find_initial_information_task(), self.follow_up_task(), self.find_instagram_information_task(), self.follow_up_instagram_task()]
        )

    # @task
    # def fetch_and_add_instagram_audio_task(self) -> Task:
    #     return Task(
    #         # description="Fetch and process Instagram audio content.",
    #         # expected_output="Processed Instagram audio data",
    #         agent=self.fetch_to_add_instagram_audio_agent(),  # Note the function call
    #         tools=[fetch_to_add_instagram_audio_tool],
    #         # condition=has_instagram_input
    #     )
    
    # @task
    # def find_instagram_information_task(self) -> Task:
    #     return Task(
    #         # description="Analyze Instagram profile information.",
    #         # expected_output="Analyzed Instagram profile data",
    #         agent=self.general_research_agent(),  # Note the function call
    #         tools=[query_instagram_db_tool],
    #         output_pydantic=ContentCreatorInfo,
    #         # condition=has_instagram_input
    #     )

    
    # @task
    # def follow_up_instagram_task(self) -> Task:
    #     return Task(
    #         # description="Analyze Instagram profile information.",
    #         # expected_output="Analyzed Instagram profile data",
    #         agent=self.general_research_agent(),  # Note the function call
    #         tools=[query_instagram_db_tool],
    #         output_pydantic=ContentCreatorInfo,
    #         # condition=has_instagram_input
    #     )

    # @task
    # def scrape_youtube_channel_task(self) -> Task:
    #     return Task(
    #         # description="Fetch and process YouTube channel information.",
    #         # expected_output="Processed YouTube channel data",
    #         agent=self.scrape_agent(),  # Note the function call
    #         tools=[fetch_relevant_videos_tool],
    #         # condition=has_youtube_input
    #     )
    
    # @task
    # def process_video_task(self) -> Task:
    #     return Task(
    #         # description="Process YouTube video data.",
    #         # expected_output="Processed YouTube video data",
    #         agent=self.vector_db_agent(),  # Note the function call
    #         tools=[add_video_to_vector_db_tool],
    #         # condition=has_youtube_input
    #     )

    # @task
    # def find_initial_information_task(self) -> Task:
    #     return Task(
    #         # description="Find initial information about the content creator.",
    #         # expected_output="Found initial information about the content creator",
    #         agent=self.general_research_agent(),  # Note the function call
    #         tools=[rag_tool],
    #         output_pydantic=ContentCreatorInfo,
    #         # condition=has_youtube_input
    #     )
    
    # @task
    # def follow_up_task(self) -> Task:
    #     return Task(
    #         # description="Find follow-up information about the content creator.",
    #         # expected_output="Found follow-up information about the content creator",
    #         agent=self.follow_up_agent(),  # Note the function call
    #         tools=[rag_tool],
    #         output_pydantic=ContentCreatorInfo,
    #         # condition=has_youtube_input
    #     )

    # # Regular tasks that always run
    # @task
    # def fallback_task(self) -> Task:
    #     return Task(
    #         # description="Process any remaining data and generate fallback information.",
    #         # expected_output="Fallback analysis results",
    #         agent=self.fallback_agent(),  # Note the function call
    #         output_pydantic=ContentCreatorInfo,
    #         tools=[rag_tool, query_instagram_db_tool]
    #     )

    # @task
    # def prompting_rag_task(self) -> Task:
    #     return Task(
    #         # description="Generate final RAG analysis.",
    #         # expected_output="Final RAG analysis report",
    #         agent=self.prompting_rag_agent(),  # Note the function call
    #         tools=[PromptingRagTool()],
    #         output_file="prompting_rag_task_output.txt"
    #     )

    @crew
    def crew(self) -> Crew:
        """Creates the LatestAiDevelopment crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            full_output=True
        )


	# @task
	# def fetch_and_add_instagram_audio_task(self) -> Task:
	# 	return Task(
	# 		config=self.tasks_config['fetch_and_add_instagram_audio_task'],
	# 		tools=[fetch_to_add_instagram_audio_tool],
	# 	)
	
	# @task
	# def find_instagram_information_task(self) -> Task:
	# 	return Task(
	# 		config=self.tasks_config['find_instagram_information_task'],
	# 		tools=[query_instagram_db_tool],
	# 		output_pydantic=ContentCreatorInfo,
	# 	)
	
	# @task
	# def follow_up_instagram_task(self) -> Task:
	# 	return Task(
	# 		config=self.tasks_config['follow_up_instagram_task'],
	# 		tools=[query_instagram_db_tool],
	# 		output_pydantic=ContentCreatorInfo,
	# 	)

	# @task
	# def scrape_youtube_channel_task(self) -> Task:
	# 	return Task(
	# 		config=self.tasks_config['scrape_youtube_channel_task'],
	# 		tools=[fetch_relevant_videos_tool],
	# 		# context="Use the FetchLatestVideosFromYouTubeChannelTool to fetch the latest videos from the YouTube channel.",
	# 	)
	
	# @task
	# def process_video_task(self) -> Task:
	# 	return Task(
	# 		config=self.tasks_config['process_video_task'],
	# 		tools=[add_video_to_vector_db_tool],
	# 		# context="Use the AddVideoToVectorDBTool to add the video to the vector database."
	# 	)

	# @task
	# def find_initial_information_task(self) -> Task:
	# 	return Task(
	# 		config=self.tasks_config['find_initial_information_task'],
	# 		# context="Use the RagTool to find information about the content creator.",
	# 		output_pydantic=ContentCreatorInfo,
	# 		tools=[rag_tool]
	# 	)
	
	# @task
	# def follow_up_task(self) -> Task:
	# 	return Task(
	# 		config=self.tasks_config['follow_up_task'],
	# 		output_pydantic=ContentCreatorInfo,
    #         # context="Use the RagTool to find information about the content creator.",
	# 		tools=[rag_tool]
	# 	)
	
	# @task
	# def fallback_task(self) -> Task:
	# 	return Task(
	# 		config=self.tasks_config['fallback_task'],
	# 		output_pydantic=ContentCreatorInfo,
	# 		tools=[rag_tool,query_instagram_db_tool],
	# 	)

	# @task
	# def prompting_rag_task(self) -> Task:
	# 	return Task(
	# 		config=self.tasks_config['prompting_rag_task'],
	# 		tools=[prompting_rag_tool],
	# 		# context={"content_creator_info": "fallback_task.output"},  # Changed this line
	# 		# context=["follow_up_task", "follow_up_instagram_task"],
	# 		output_file="prompting_rag_task_output.txt"
	# 	)

	# @crew
	# def crew(self) -> Crew:
	# 	"""Creates the LatestAiDevelopment crew"""
	# 	return Crew(
	# 		agents=self.agents, # Automatically created by the @agent decorator
	# 		tasks=self.tasks, # Automatically created by the @task decorator
	# 		process=Process.sequential,
	# 		verbose=True,
	# 		# manager_agent=self.manager_agent,
	# 		full_output=True
	# 		# process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
	# 	)