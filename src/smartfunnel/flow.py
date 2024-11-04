from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

import sys
import os

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

fetch_relevant_videos_tool = FetchRelevantVideosFromYouTubeChannelTool()
add_video_to_vector_db_tool = AddVideoToVectorDBTool(app=app_instance)
fire_crawl_search_tool = FirecrawlSearchTool()
rag_tool = QueryVectorDBTool(app=app_instance)
fetch_to_add_instagram_audio_tool = FetchToAddInstagramAudioTool(app=app_instance)
query_instagram_db_tool = QueryInstagramDBTool(app=app_instance)


from smartfunnel.tools.InputValidationTool import InputValidationTool
input_validation_tool = InputValidationTool()

from smartfunnel.tools.ResettingTool import ResetDatabaseTool
reset_database_tool = ResetDatabaseTool(app=app_instance)

from typing import List, Optional, Dict
from pydantic import BaseModel
from crewai import Agent, Crew, Process

import asyncio
from typing import List

from crewai.flow.flow import Flow, listen, start, router, and_
from pydantic import BaseModel

from smartfunnel.crew_instagram import InstagramCrew
from smartfunnel.crew_rag import RagCrew
from smartfunnel.crew_youtube import YoutubeCrew

from smartfunnel.crew_instagram import ContentCreatorInfo, LifeEventObject, ValueObject, ChallengeObject, AchievementObject

# class ValueObject(BaseModel):
#     name: str = Field(
#         ..., 
#         description="The name of the value, e.g., 'perseverance'"
#     )
#     origin: str = Field(
#         ..., 
#         description="The origin or development of the value, e.g., 'Developed this trait when joining the army and completing the program after 3 attempts'"
#     )
#     impact_today: str = Field(
#         ..., 
#         description="How the value impacts how the creator works today, e.g., 'When cold calling people, understands the power of numbers and having to go through a lot of setbacks to get a successful call'"
#     )

#     # Add default constructor for error handling
#     @classmethod
#     def default(cls) -> 'ValueObject':
#         return cls(
#             name="",
#             origin="",
#             impact_today=""
#         )

# class ChallengeObject(BaseModel):
#     description: str = Field(
#         ..., 
#         description="Description of the challenge, e.g., 'Experiencing homelessness in 2009'"
#     )
#     learnings: str = Field(
#         ..., 
#         description="The lessons the creator learned from the challenge, e.g., 'Made survival and ruthless prioritization his first priority'"
#     )

#     @classmethod
#     def default(cls) -> 'ChallengeObject':
#         return cls(
#             description="",
#             learnings=""
#         )

# class AchievementObject(BaseModel):
#     description: str = Field(
#         ..., 
#         description="Description of the achievement, e.g., 'Founding own creative agency \"On Air\"', 'Speaking at TEDx Conferences'"
#     )

#     @classmethod
#     def default(cls) -> 'AchievementObject':
#         return cls(
#             description=""
#         )

# class LifeEventObject(BaseModel):
#     name: str = Field(
#         ..., 
#         description="Name or title of the life event, e.g., 'Childhood'"
#     )
#     description: str = Field(
#         ..., 
#         description="Description of the life event, e.g., 'Grew up on a quiet island called La Désirade, in Guadeloupe'"
#     )

#     @classmethod
#     def default(cls) -> 'LifeEventObject':
#         return cls(
#             name="",
#             description=""
#         )

# class BusinessObject(BaseModel):
#     name: str = Field(
#         ..., 
#         description="Name of the business, e.g., 'Agency \"On Air\"'"
#     )
#     description: str = Field(
#         ..., 
#         description="Description of the business, e.g., 'Marketing strategist to drive innovation in large corporates'"
#     )
#     genesis: str = Field(
#         ..., 
#         description="How the business started, e.g., 'Started as a freelancer, building out the skills to turn them into an agency in 2010'"
#     )

#     @classmethod
#     def default(cls) -> 'BusinessObject':
#         return cls(
#             name="",
#             description="",
#             genesis=""
#         )

# class ContentCreatorInfo(BaseModel):
#     life_events: List[LifeEventObject] = Field(
#         ..., 
#         description="List of significant life events that shaped the creator's journey"
#     )
#     business: BusinessObject = Field(
#         ..., 
#         description="Information about the creator's business or primary professional venture"
#     )
#     values: List[ValueObject] = Field(
#         ..., 
#         description="List of the creator's core values that guide their work and life"
#     )
#     challenges: List[ChallengeObject] = Field(
#         ..., 
#         description="List of significant challenges faced by the creator and how they overcame them"
#     )
#     achievements: List[AchievementObject] = Field(
#         ..., 
#         description="List of the creator's notable achievements and milestones"
#     )
#     first_name: Optional[str] = Field(
#         None, 
#         description="The first name of the content creator"
#     )
#     last_name: Optional[str] = Field(
#         None, 
#         description="The last name of the content creator"
#     )

#     @classmethod
#     def default(cls) -> 'ContentCreatorInfo':
#         return cls(
#             first_name="",
#             last_name="",
#             life_events=[LifeEventObject.default()],
#             business=BusinessObject.default(),
#             values=[ValueObject.default()],
#             challenges=[ChallengeObject.default()],
#             achievements=[AchievementObject.default()]
#         )

# # class ContentCreatorInfoState(BaseModel):
# #     content_creator_info: ClassVar[ContentCreatorInfo] = Field(
# #         ...,
# #         description="The content creator info"
# #     )
# class ContentCreatorInfo(BaseModel):
#     life_events: List[LifeEventObject] = Field(
#         ..., 
#         description="List of significant life events that shaped the creator's journey"
#     )
#     business: BusinessObject = Field(
#         ..., 
#         description="Information about the creator's business or primary professional venture"
#     )
#     values: List[ValueObject] = Field(
#         ..., 
#         description="List of the creator's core values that guide their work and life"
#     )
#     challenges: List[ChallengeObject] = Field(
#         ..., 
#         description="List of significant challenges faced by the creator and how they overcame them"
#     )
#     achievements: List[AchievementObject] = Field(
#         ..., 
#         description="List of the creator's notable achievements and milestones"
#     )
#     first_name: Optional[str] = Field(
#         None, 
#         description="The first name of the content creator"
#     )
#     last_name: Optional[str] = Field(
#         None, 
#         description="The last name of the content creator"
#     )


# from crewai.flow.flow import Flow, listen, start, router
# from pydantic import BaseModel
# from typing import Optional


# import asyncio
# from typing import Dict, Any
# from pydantic import BaseModel


# import asyncio
# from typing import Optional
# from crewai import Flow  # Assuming CrewAI supports async operations

# class MyFlow(Flow):
#     def __init__(self, youtube_params, instagram_params):
#         super().__init__()
#         self.youtube_params = youtube_params
#         self.instagram_params = instagram_params
#         self.youtube_result = None
#         self.instagram_result = None

#     @property
#     def state(self):
#         return self._state

#     @state.setter
#     def state(self, value):
#         self._state = value

#     def _process_crew_output(self, crew_output):
#         """Helper method to process crew outputs consistently"""
#         if hasattr(crew_output, 'pydantic'):
#             return crew_output.pydantic
#         elif hasattr(crew_output, 'raw'):
#             if isinstance(crew_output.raw, dict):
#                 return ContentCreatorInfo(**crew_output.raw)
#             return crew_output.raw
#         elif isinstance(crew_output, dict):
#             return ContentCreatorInfo(**crew_output)
#         return crew_output

#     @start()
#     def run_instagram_crew(self):
#         if not self.instagram_params.get("instagram_username"):
#             print("No Instagram username provided")
#             return None
#         result = InstagramCrew().crew().kickoff(inputs=self.instagram_params)
#         return result.pydantic if hasattr(result, 'pydantic') else None

#     @start()
#     def run_youtube_crew(self):
#         if not self.youtube_params.get("youtube_channel_handle"):
#             print("No YouTube handle provided")
#             return None
#         result = YoutubeCrew().crew().kickoff(inputs=self.youtube_params)
#         return result.pydantic if hasattr(result, 'pydantic') else None

#     def _merge_content_creator_info(self, youtube_info: Optional[ContentCreatorInfo], 
#                                   instagram_info: Optional[ContentCreatorInfo]) -> ContentCreatorInfo:
#     # def _merge_content_creator_info(self, youtube_info: Optional[ContentCreatorInfo], 
#     #                               instagram_info: Optional[ContentCreatorInfo]) -> ContentCreatorInfo:
#         # Create default empty objects
#         empty_life_event = LifeEventObject(name="", description="")
#         empty_value = ValueObject(name="", origin="", impact_today="")
#         empty_challenge = ChallengeObject(description="", learnings="")
#         empty_achievement = AchievementObject(description="")

#         # If both are None, return default
#         if youtube_info is None and instagram_info is None:
#             return ContentCreatorInfo(
#                 life_events=[empty_life_event],
#                 business=BusinessObject(name="", description="", genesis=""),
#                 values=[empty_value],
#                 challenges=[empty_challenge],
#                 achievements=[empty_achievement],
#                 first_name="",
#                 last_name=""
#             )

#         # If one is None, use the other
#         if youtube_info is None:
#             return instagram_info
#         if instagram_info is None:
#             return youtube_info

#         # Merge lists, removing duplicates and empty values
#         def merge_lists(list1, list2, is_empty_func):
#             # Convert to dictionary representation for comparison
#             seen = {}
#             merged = []
            
#             for item in list1 + list2:
#                 if not is_empty_func(item):
#                     item_dict = item.dict()
#                     key = str(sorted(item_dict.items()))
#                     if key not in seen:
#                         merged.append(item)
#                         seen[key] = True
            
#             return merged if merged else [empty_life_event]

#         # Helper functions to check for empty objects
#         is_empty_life_event = lambda x: not (x.name or x.description)
#         is_empty_value = lambda x: not (x.name or x.origin or x.impact_today)
#         is_empty_challenge = lambda x: not (x.description or x.learnings)
#         is_empty_achievement = lambda x: not x.description

#         # Create merged result
#         merged = ContentCreatorInfo(
#             life_events=merge_lists(
#                 youtube_info.life_events or [], 
#                 instagram_info.life_events or [], 
#                 is_empty_life_event
#             ),
#             business=BusinessObject(
#                 name=youtube_info.business.name or instagram_info.business.name or "",
#                 description=youtube_info.business.description or instagram_info.business.description or "",
#                 genesis=youtube_info.business.genesis or instagram_info.business.genesis or ""
#             ),
#             values=merge_lists(
#                 youtube_info.values or [], 
#                 instagram_info.values or [], 
#                 is_empty_value
#             ),
#             challenges=merge_lists(
#                 youtube_info.challenges or [], 
#                 instagram_info.challenges or [], 
#                 is_empty_challenge
#             ),
#             achievements=merge_lists(
#                 youtube_info.achievements or [], 
#                 instagram_info.achievements or [], 
#                 is_empty_achievement
#             ),
#             first_name=youtube_info.first_name or instagram_info.first_name or "",
#             last_name=youtube_info.last_name or instagram_info.last_name or ""
#         )

#         print(f"Merged life_events: {len(merged.life_events)}")
#         print(f"Merged values: {len(merged.values)}")
#         print(f"Merged challenges: {len(merged.challenges)}")
#         print(f"Merged achievements: {len(merged.achievements)}")

#         return merged

#     def _merge_with_defaults(self, info: ContentCreatorInfo, default_info: ContentCreatorInfo) -> ContentCreatorInfo:
#         """Helper method to merge a single info with defaults"""
#         return self._merge_content_creator_info(info, default_info)

#     # @listen(run_youtube_crew)
#     # @listen(run_instagram_crew)
#     @listen(and_(run_youtube_crew, run_instagram_crew))
#     def consolidate_results(self, result):
#         print(f"New result received: {result}")

#         # Determine which result we're dealing with based on existing data
#         if self.youtube_result is None:
#             print("Storing YouTube result")
#             self.youtube_result = result
#         elif self.instagram_result is None:
#             print("Storing Instagram result")
#             self.instagram_result = result
#         else:
#             print("Unexpected additional result received")
#             return

#         # Only proceed if we have both results
#         if self.youtube_result and self.instagram_result:
#             merged_info = self._merge_content_creator_info(
#                 self.youtube_result,
#                 self.instagram_result
#             )
#             print(f"Merged result: {merged_info}")
#             return RagCrew().crew().kickoff(inputs={"input_string": merged_info.json()})
#         else:
#             return "waiting_for_other_result"

# def kick_off():
#     youtube_params = {"youtube_channel_handle": "@clubvipfinance"}
#     instagram_params = {"instagram_username": "clubvipfinance"}

#     flow = MyFlow(youtube_params=youtube_params, instagram_params=instagram_params)
#     result = flow.kickoff()
#     print(result)

# if __name__ == "__main__":
#     kick_off()

from crewai.flow.flow import Flow, listen, start, and_
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from smartfunnel.crew_instagram import InstagramCrew
from smartfunnel.crew_youtube import YoutubeCrew
from smartfunnel.crew_rag import RagCrew
from smartfunnel.crew_instagram import (
    ContentCreatorInfo, LifeEventObject, ValueObject, 
    ChallengeObject, AchievementObject, BusinessObject
)


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

# class ContentCreatorInfoState(BaseModel):
#     content_creator_info: ClassVar[ContentCreatorInfo] = Field(
#         ...,
#         description="The content creator info"
#     )


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

# class MyFlow(Flow):
#     def __init__(self, youtube_params: Dict[str, str], instagram_params: Dict[str, str]):
#         super().__init__()
#         self.youtube_params = youtube_params
#         self.instagram_params = instagram_params
        
#         # Initialize with empty/default values
#         self._state = ContentCreatorInfo(
#             life_events=[LifeEventObject(name="", description="")],
#             business=BusinessObject(name="", description="", genesis=""),
#             values=[ValueObject(name="", origin="", impact_today="")],
#             challenges=[ChallengeObject(description="", learnings="")],
#             achievements=[AchievementObject(description="")],
#             first_name="",
#             last_name=""
#         )
        
#     @property
#     def state(self) -> ContentCreatorInfo:
#         return self._state
        
#     @state.setter
#     def state(self, value: ContentCreatorInfo):
#         self._state = value

#     @start()
#     def run_youtube_crew(self):
#         """Start YouTube crew and return its results."""
#         if not self.youtube_params.get("youtube_channel_handle"):
#             print("No YouTube handle provided")
#             return None
            
#         result = YoutubeCrew().crew().kickoff(inputs=self.youtube_params)
#         print("YouTube crew result type:", type(result))
#         if hasattr(result, 'json_dict'):
#             print("YouTube crew has json_dict output")
#             return result.json_dict
#         return None

#     @start()
#     def run_instagram_crew(self):
#         """Start Instagram crew and return its results."""
#         if not self.instagram_params.get("instagram_username"):
#             print("No Instagram username provided")
#             return None
            
#         result = InstagramCrew().crew().kickoff(inputs=self.instagram_params)
#         print("Instagram crew result type:", type(result))
#         if hasattr(result, 'json_dict'):
#             print("Instagram crew has json_dict output")
#             return result.json_dict
#         return None

#     # def _merge_content_creator_info(self, youtube_info: Optional[ContentCreatorInfo], 
#     #                               instagram_info: Optional[ContentCreatorInfo]) -> ContentCreatorInfo:
#     #     """Merge YouTube and Instagram information into a single ContentCreatorInfo object."""
#     #     if youtube_info is None and instagram_info is None:
#     #         return self._state  # Return current state if both inputs are None
#     #     if youtube_info is None:
#     #         return instagram_info
#     #     if instagram_info is None:
#     #         return youtube_info

#     #     def merge_lists(list1, list2, is_empty_func, default_constructor):
#     #         seen = {}
#     #         merged = []
            
#     #         for item in list1 + list2:
#     #             if not is_empty_func(item):
#     #                 item_dict = item.dict()
#     #                 key = str(sorted(item_dict.items()))
#     #                 if key not in seen:
#     #                     merged.append(item)
#     #                     seen[key] = True
            
#     #         return merged if merged else [default_constructor()]

#     #     # Define empty checks and default constructors for each type
#     #     is_empty_life_event = lambda x: not (x.name or x.description)
#     #     default_life_event = lambda: LifeEventObject(name="", description="")

#     #     is_empty_value = lambda x: not (x.name or x.origin or x.impact_today)
#     #     default_value = lambda: ValueObject(name="", origin="", impact_today="")

#     #     is_empty_challenge = lambda x: not (x.description or x.learnings)
#     #     default_challenge = lambda: ChallengeObject(description="", learnings="")

#     #     is_empty_achievement = lambda x: not x.description
#     #     default_achievement = lambda: AchievementObject(description="")

#     #     # Create merged result
#     #     merged = ContentCreatorInfo(
#     #         life_events=merge_lists(
#     #             youtube_info.life_events or [], 
#     #             instagram_info.life_events or [], 
#     #             is_empty_life_event,
#     #             default_life_event
#     #         ),
#     #         business=BusinessObject(
#     #             name=youtube_info.business.name or instagram_info.business.name or "",
#     #             description=youtube_info.business.description or instagram_info.business.description or "",
#     #             genesis=youtube_info.business.genesis or instagram_info.business.genesis or ""
#     #         ),
#     #         values=merge_lists(
#     #             youtube_info.values or [], 
#     #             instagram_info.values or [], 
#     #             is_empty_value,
#     #             default_value
#     #         ),
#     #         challenges=merge_lists(
#     #             youtube_info.challenges or [], 
#     #             instagram_info.challenges or [], 
#     #             is_empty_challenge,
#     #             default_challenge
#     #         ),
#     #         achievements=merge_lists(
#     #             youtube_info.achievements or [], 
#     #             instagram_info.achievements or [], 
#     #             is_empty_achievement,
#     #             default_achievement
#     #         ),
#     #         first_name=youtube_info.first_name or instagram_info.first_name or "",
#     #         last_name=youtube_info.last_name or instagram_info.last_name or ""
#     #     )

#     #     return merged

from crewai.flow.flow import Flow, listen, start, and_
from pydantic import BaseModel
from typing import Optional, Dict, Any, Union
import json

def merge_content_creator_info(info1: Dict[str, Any], info2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merges two ContentCreatorInfo dictionaries, combining lists and selecting the longest values
    for unique fields. Handles empty/None values and ensures the final object is fully populated.
    
    Args:
        info1: First ContentCreatorInfo dictionary
        info2: Second ContentCreatorInfo dictionary
        
    Returns:
        Dict[str, Any]: Merged ContentCreatorInfo dictionary
    """
    def is_empty_or_none(value) -> bool:
        """Check if a value is empty or None"""
        if value is None:
            return True
        if isinstance(value, (str, list, dict)) and not value:
            return True
        return False

    def merge_lists(list1: List, list2: List) -> List:
        """Merge two lists, removing duplicates based on 'name' or 'description'"""
        if not list1:
            return list2 or []
        if not list2:
            return list1 or []
            
        merged = list1.copy()
        existing_items = {
            item.get('name', item.get('description', '')): True 
            for item in merged
        }
        
        for item in list2:
            identifier = item.get('name', item.get('description', ''))
            if identifier and identifier not in existing_items:
                merged.append(item)
                existing_items[identifier] = True
                
        return merged

    def select_longest_object(obj1: Dict, obj2: Dict) -> Dict:
        """Select the object with the longest description"""
        if is_empty_or_none(obj1):
            return obj2 or {}
        if is_empty_or_none(obj2):
            return obj1 or {}
            
        # Compare lengths of descriptions
        len1 = len(obj1.get('description', ''))
        len2 = len(obj2.get('description', ''))
        return obj1 if len1 >= len2 else obj2

    # Initialize merged result
    merged = {}
    
    # Merge list fields
    list_fields = ['life_events', 'values', 'challenges', 'achievements']
    for field in list_fields:
        merged[field] = merge_lists(
            info1.get(field, []),
            info2.get(field, [])
        )
    
    # Merge business object
    merged['business'] = select_longest_object(
        info1.get('business', {}),
        info2.get('business', {})
    )
    
    # Merge name fields
    merged['first_name'] = (
        info1.get('first_name') or 
        info2.get('first_name') or 
        'Unknown'
    )
    merged['last_name'] = (
        info1.get('last_name') or 
        info2.get('last_name') or 
        'Unknown'
    )
    
    # Ensure default values for empty lists
    for field in list_fields:
        if not merged[field]:
            merged[field] = [{'name': 'Not specified', 'description': 'No information available'}]
            
    # Ensure business object has required fields
    if not merged['business']:
        merged['business'] = {
            'name': 'Not specified',
            'description': 'No information available',
            'genesis': 'No information available'
        }
    
    return merged

def ensure_dict(info: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Convert string input to dictionary if needed."""
    if isinstance(info, str):
        try:
            return json.loads(info.strip('"""').strip("'''"))
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")
    return info

def merge_and_validate_content(crew_result: Any, instagram_info: str) -> ContentCreatorInfo:
    """
    Merge crew result with Instagram info and validate the result.
    
    Args:
        crew_result: Result from the YouTube crew
        instagram_info: Instagram information as JSON string
        
    Returns:
        ContentCreatorInfo: Validated merged content
    """
    try:
        # Convert Instagram info to dict
        instagram_dict = ensure_dict(instagram_info)
        
        # Handle crew result based on its type
        if hasattr(crew_result, 'json_dict'):
            youtube_dict = crew_result.json_dict
        else:
            youtube_dict = ensure_dict(crew_result)
            
        # Merge the content
        merged_info = merge_content_creator_info(youtube_dict, instagram_dict)
        
        # Validate with Pydantic model
        return ContentCreatorInfo(**merged_info)
        
    except Exception as e:
        raise ValueError(f"Error merging content: {str(e)}")
    
def save_output_to_markdown(crew_output, filename="MergedCreatorOutput.md"):
    """
    Save crew output to a markdown file with proper error handling.
    """
    try:
        with open(filename, "w", encoding="utf-8") as md_file:
            md_file.write("# Merged Creator Analysis Output\n\n")
            md_file.write(f"## Raw Output\n\n```\n{crew_output.raw}\n```\n\n")
            
            if crew_output.json_dict:
                md_file.write(f"## JSON Output\n\n```json\n{json.dumps(crew_output.json_dict, indent=2)}\n```\n\n")
            
            if crew_output.pydantic:
                md_file.write(f"## Pydantic Output\n\n```\n{crew_output.pydantic}\n```\n\n")
            
            md_file.write(f"## Tasks Output\n\n```\n{crew_output.tasks_output}\n```\n\n")
            md_file.write(f"## Token Usage\n\n```\n{crew_output.token_usage}\n```\n")
            
        return True
    except Exception as e:
        print(f"Error saving to markdown file: {str(e)}")
        return False

from crewai.flow.flow import Flow, listen, start, and_
from typing import Dict, Any
import json

from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class ContentCreatorState(BaseModel):
    youtube_data: Optional[Dict[str, Any]] = None
    instagram_data: Optional[Dict[str, Any]] = None
    merged_data: Optional[Dict[str, Any]] = None
    rag_output: Optional[Dict[str, Any]] = None

def create_empty_content():
    """Create an empty ContentCreatorInfo structure with empty values"""
    return {
        "life_events": [],
        "business": {
            "name": "",
            "description": "",
            "genesis": ""
        },
        "values": [],
        "challenges": [],
        "achievements": [],
        "first_name": "",
        "last_name": ""
    }

def merge_content_creator_info(info1: Dict[str, Any], info2: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two content creator info dictionaries preserving all data"""
    # Start with default structure
    result = create_empty_content()
    
    def merge_lists(list1: List[Dict], list2: List[Dict], field: str) -> List[Dict]:
        """Merge two lists of dictionaries, avoiding duplicates"""
        if not list1 and not list2:
            return []
        
        merged = []
        seen = set()
        
        # Function to create identifier for deduplication
        def get_identifier(item: Dict) -> str:
            return item.get('name', '') + item.get('description', '')
        
        # Process both lists
        for item in (list1 or []) + (list2 or []):
            if not item:
                continue
            identifier = get_identifier(item)
            if identifier and identifier not in seen and any(item.values()):
                merged.append(item)
                seen.add(identifier)
        
        return merged

    # Merge list fields
    list_fields = ['life_events', 'values', 'challenges', 'achievements']
    for field in list_fields:
        result[field] = merge_lists(
            info1.get(field, []),
            info2.get(field, []),
            field
        )
    
    # Handle business object
    business1 = info1.get('business', {})
    business2 = info2.get('business', {})
    
    result['business'] = {
        'name': business1.get('name') or business2.get('name') or "",
        'description': business1.get('description') or business2.get('description') or "",
        'genesis': business1.get('genesis') or business2.get('genesis') or ""
    }
    
    # Handle name fields
    result['first_name'] = info1.get('first_name') or info2.get('first_name') or ""
    result['last_name'] = info1.get('last_name') or info2.get('last_name') or ""
    
    return result

class ContentCreatorState(BaseModel):
    youtube_data: Optional[Dict[str, Any]] = None
    instagram_data: Optional[Dict[str, Any]] = None
    merged_data: Optional[Dict[str, Any]] = None
    rag_output: Optional[Dict[str, Any]] = None

def create_empty_content():
    """Create an empty ContentCreatorInfo structure"""
    return {
        "life_events": [],
        "business": {
            "name": "",
            "description": "",
            "genesis": ""
        },
        "values": [],
        "challenges": [],
        "achievements": [],
        "first_name": "",
        "last_name": ""
    }

class ContentCreatorFlow(Flow[ContentCreatorState]):
    initial_state = ContentCreatorState

    def __init__(self, youtube_params: Dict[str, str], instagram_params: Dict[str, str]):
        super().__init__()
        self.youtube_params = youtube_params
        self.instagram_params = instagram_params

    @start()
    def fetch_youtube_data(self):
        """Start YouTube crew analysis"""
        print("Starting YouTube analysis...")
        if not self.youtube_params.get("youtube_channel_handle"):
            print("No YouTube handle provided")
            self.state.youtube_data = create_empty_content()
            return self.state.youtube_data
            
        try:
            result = YoutubeCrew().crew().kickoff(inputs=self.youtube_params)
            if hasattr(result, 'json_dict'):
                self.state.youtube_data = result.json_dict
                return result.json_dict
            return create_empty_content()
        except Exception as e:
            print(f"Error in YouTube analysis: {str(e)}")
            return create_empty_content()

    @start()
    def fetch_instagram_data(self):
        """Start Instagram crew analysis"""
        print("Starting Instagram analysis...")
        if not self.instagram_params.get("instagram_username"):
            print("No Instagram username provided")
            self.state.instagram_data = create_empty_content()
            return self.state.instagram_data
            
        try:
            result = InstagramCrew().crew().kickoff(inputs=self.instagram_params)
            if hasattr(result, 'json_dict'):
                self.state.instagram_data = result.json_dict
                return result.json_dict
            return create_empty_content()
        except Exception as e:
            print(f"Error in Instagram analysis: {str(e)}")
            return create_empty_content()

    @listen(and_(fetch_youtube_data, fetch_instagram_data))
    def merge_data(self):  # Remove parameters here
        """Merge YouTube and Instagram data"""
        print("Merging data from both sources...")
        
        # Get data from state
        youtube_data = self.state.youtube_data or create_empty_content()
        instagram_data = self.state.instagram_data or create_empty_content()
        
        merged = {
            "life_events": youtube_data.get("life_events", []) + instagram_data.get("life_events", []),
            "values": youtube_data.get("values", []) + instagram_data.get("values", []),
            "challenges": youtube_data.get("challenges", []) + instagram_data.get("challenges", []),
            "achievements": youtube_data.get("achievements", []) + instagram_data.get("achievements", []),
            "business": youtube_data.get("business") or instagram_data.get("business") or create_empty_content()["business"],
            "first_name": youtube_data.get("first_name") or instagram_data.get("first_name") or "",
            "last_name": youtube_data.get("last_name") or instagram_data.get("last_name") or ""
        }
        
        self.state.merged_data = merged
        return merged

    @listen(merge_data)
    def process_with_rag(self):  # Remove parameter here too
        """Process merged data with RAG crew"""
        print("Processing with RAG crew...")
        
        if not self.state.merged_data:
            print("No merged data available")
            return None

        try:
            result = RagCrew().crew().kickoff(
                inputs={"input_string": json.dumps(self.state.merged_data)}
            )
            if hasattr(result, 'json_dict'):
                self.state.rag_output = result.json_dict
            return result
        except Exception as e:
            print(f"Error in RAG processing: {str(e)}")
            return None

def run_analysis(youtube_handle: str = "", instagram_username: str = ""):
    """Run the content creator analysis flow"""
    flow = ContentCreatorFlow(
        youtube_params={"youtube_channel_handle": youtube_handle},
        instagram_params={"instagram_username": instagram_username}
    )
    return flow.kickoff()

if __name__ == "__main__":
    result = run_analysis(
        youtube_handle="@antoineblanco99",
        instagram_username=""
    )

# class ContentCreatorState(BaseModel):
#     youtube_data: Optional[Dict[str, Any]] = None
#     instagram_data: Optional[Dict[str, Any]] = None
#     merged_data: Optional[Dict[str, Any]] = None
#     rag_output: Optional[Dict[str, Any]] = None

# class ContentCreatorFlow(Flow[ContentCreatorState]):
#     initial_state = ContentCreatorState

#     def __init__(self, youtube_params: Dict[str, str], instagram_params: Dict[str, str]):
#         super().__init__()
#         self.youtube_params = youtube_params
#         self.instagram_params = instagram_params

#     @start()
#     def fetch_youtube_data(self):
#         """Start YouTube crew analysis"""
#         print("Starting YouTube analysis...")
#         if not self.youtube_params.get("youtube_channel_handle"):
#             print("No YouTube handle provided")
#             return None
            
#         result = YoutubeCrew().crew().kickoff(inputs=self.youtube_params)
#         if hasattr(result, 'json_dict'):
#             self.state.youtube_data = result.json_dict
#             return result.json_dict
#         return {}

#     @start()
#     def fetch_instagram_data(self):
#         """Start Instagram crew analysis"""
#         print("Starting Instagram analysis...")
#         if not self.instagram_params.get("instagram_username"):
#             print("No Instagram username provided")
#             return None
            
#         result = InstagramCrew().crew().kickoff(inputs=self.instagram_params)
#         if hasattr(result, 'json_dict'):
#             self.state.instagram_data = result.json_dict
#             return result.json_dict
#         return {}

#     @listen(and_(fetch_youtube_data, fetch_instagram_data))
#     def merge_data(self):
#         """Merge YouTube and Instagram data"""
#         print("Merging data from both sources...")

#         merged = merge_content_creator_info(
#             self.state.youtube_data or {},
#             self.state.instagram_data or {}
#         )
#         self.state.merged_data = merged
#         print(merged)
#         return merged

#     @listen(merge_data)
#     def process_with_rag(self):
#         """Process merged data with RAG crew"""
#         print("Processing with RAG crew...")
        
#         if not self.state.merged_data:
#             print("No merged data available")
#             return None

#         result = RagCrew().crew().kickoff(
#             inputs={"input_string": json.dumps(self.state.merged_data)}
#         )
        
#         if hasattr(result, 'json_dict'):
#             self.state.rag_output = result.json_dict
            
#         return result

# def run_analysis(youtube_handle: str = "", instagram_username: str = ""):
#     """Run the content creator analysis flow"""
#     flow = ContentCreatorFlow(
#         youtube_params={"youtube_channel_handle": youtube_handle},
#         instagram_params={"instagram_username": instagram_username}
#     )
#     return flow.kickoff()

# def plot_flow():
#     """Generate a plot of the flow"""
#     flow = ContentCreatorFlow(
#         youtube_params={"youtube_channel_handle": ""},
#         instagram_params={"instagram_username": ""}
#     )
#     flow.plot()

# if __name__ == "__main__":
#     result = run_analysis(
#         youtube_handle="@antoineblanco99",
#         instagram_username=""
#     )