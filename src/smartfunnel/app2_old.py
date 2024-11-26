# from sqlite_setup import ensure_pysqlite3
# from sqlite_setup import ensure_pysqlite3
# ensure_pysqlite3()  # Call this before any other imports

import streamlit as st
import sys
import json
# from smartfunnel.crew import LatestAiDevelopmentCrew
import logging
from typing import Optional
from tools.chroma_db_init import app_instance
# from tools.chroma_db_init import cleanup_old_
# from smartfunnel.tools.chroma_db_init import app_instance
# from smartfunnel.tools.chroma_db_init import cleanup_old_db
import time
from datetime import datetime
import sys
import json
import streamlit as st
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from crew_youtube import YoutubeCrew
from crew_instagram import InstagramCrew
from crew_rag import RagCrew
#!/usr/bin/env python
import time
from datetime import datetime
import sys
import json
import streamlit as st
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from crew_youtube import YoutubeCrew
from crew_instagram import InstagramCrew
from crew_rag import RagCrew

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]  
# Initialize Streamlit configs
# try:
#     OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]  
#     # Reduce file watching using safer check
#     import streamlit.runtime.scriptrunner as streamlit_runtime
#     if streamlit_runtime.get_script_run_ctx():
#         st.set_option('server.fileWatcherType', 'none')
# except Exception as e:
#     logger.warning(f"Error initializing Streamlit configs: {e}")

class ValueObject(BaseModel):
    name: str = Field(
        ..., 
        description="The name of the value, e.g., 'perseverance'"
    )
    origin: str = Field(
        ..., 
        description="The origin or development of the value"
    )
    impact_today: str = Field(
        ..., 
        description="How the value impacts how the creator works today"
    )

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
        description="Description of the challenge"
    )
    learnings: str = Field(
        ..., 
        description="The lessons the creator learned from the challenge"
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
        description="Description of the achievement"
    )

    @classmethod
    def default(cls) -> 'AchievementObject':
        return cls(
            description=""
        )

class LifeEventObject(BaseModel):
    name: str = Field(
        ..., 
        description="Name or title of the life event"
    )
    description: str = Field(
        ..., 
        description="Description of the life event"
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
        description="Name of the business"
    )
    description: str = Field(
        ..., 
        description="Description of the business"
    )
    genesis: str = Field(
        ..., 
        description="How the business started"
    )

    @classmethod
    def default(cls) -> 'BusinessObject':
        return cls(
            name="",
            description="",
            genesis=""
        )

class ContentCreatorInfo(BaseModel):
    # Basic information about life events, stored as a list of LifeEventObject instances
    life_events: Optional[List[LifeEventObject]] = Field(default_factory=list)
    
    # Business information, stored as a single BusinessObject instance
    business: Optional[BusinessObject] = None
    
    # Core values of the content creator, stored as a list of ValueObject instances
    values: Optional[List[ValueObject]] = Field(default_factory=list)
    
    # Challenges faced by the creator, stored as a list of ChallengeObject instances
    challenges: Optional[List[ChallengeObject]] = Field(default_factory=list)
    
    # Notable achievements, stored as a list of AchievementObject instances
    achievements: Optional[List[AchievementObject]] = Field(default_factory=list)
    
    # Creator's first name
    first_name: Optional[str] = None
    
    # Creator's last name
    last_name: Optional[str] = None
    
    # Creator's full name - new field
    # This can be different from first_name + last_name in cases where creators use stage names
    full_name: Optional[str] = None
    
    # Creator's primary content language - new field
    # This helps identify the main audience and content focus
    main_language: Optional[str] = None

    @classmethod
    def create_empty(cls) -> 'ContentCreatorInfo':
        """Create a complete ContentCreatorInfo with default values."""
        return cls(
            first_name="Unknown",
            last_name="Unknown",
            full_name="Unknown",  # Default for new field
            main_language="Unknown",  # Default for new field
            life_events=[
                LifeEventObject(
                    name="Not specified",
                    description="No information available"
                )
            ],
            business=BusinessObject(
                name="Not specified",
                description="No information available",
                genesis="No information available"
            ),
            values=[
                ValueObject(
                    name="Not specified",
                    origin="No information available",
                    impact_today="No information available"
                )
            ],
            challenges=[
                ChallengeObject(
                    description="Not specified",
                    learnings="No information available"
                )
            ],
            achievements=[
                AchievementObject(
                    description="Not specified"
                )
            ]
        )
# class ContentCreatorInfo(BaseModel):
#     life_events: Optional[List[LifeEventObject]] = Field(default_factory=list)
#     business: Optional[BusinessObject] = None
#     values: Optional[List[ValueObject]] = Field(default_factory=list)
#     challenges: Optional[List[ChallengeObject]] = Field(default_factory=list)
#     achievements: Optional[List[AchievementObject]] = Field(default_factory=list)
#     first_name: Optional[str] = None
#     last_name: Optional[str] = None

#     @classmethod
#     def create_empty(cls) -> 'ContentCreatorInfo':
#         """Create a complete ContentCreatorInfo with default values."""
#         return cls(
#             first_name="Unknown",
#             last_name="Unknown",
#             life_events=[
#                 LifeEventObject(
#                     name="Not specified",
#                     description="No information available"
#                 )
#             ],
#             business=BusinessObject(
#                 name="Not specified",
#                 description="No information available",
#                 genesis="No information available"
#             ),
#             values=[
#                 ValueObject(
#                     name="Not specified",
#                     origin="No information available",
#                     impact_today="No information available"
#                 )
#             ],
#             challenges=[
#                 ChallengeObject(
#                     description="Not specified",
#                     learnings="No information available"
#                 )
#             ],
#             achievements=[
#                 AchievementObject(
#                     description="Not specified"
#                 )
#             ]
#         )
    
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import sys
import json
import streamlit as st
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from crew_youtube import YoutubeCrew
from crew_instagram import InstagramCrew


#  new version --------

def validate_password(password: str) -> bool:
    """Validate password against stored secret"""
    try:
        return password == st.secrets["Answer"]
    except Exception as e:
        logger.error(f"Error accessing secrets: {e}")
        st.error("Error accessing secrets. Make sure secrets.toml is properly configured.")
        return False

def convert_to_markdown(data: Dict) -> str:
    """
    Convert the analysis results to markdown format with enhanced structure and readability.
    Includes support for full_name and main_language fields while maintaining the original
    hierarchical organization.
    
    Args:
        data: Dictionary containing ContentCreatorInfo data
        
    Returns:
        str: Formatted markdown string containing the analysis report
    """
    # Start with the main title
    md = "# Creator Analysis Report\n\n"
    
    # Basic Information section with new fields
    md += "## Basic Information\n"
    md += f"- Full Name: {data.get('full_name', 'Unknown')}\n"
    md += f"- Main Language: {data.get('main_language', 'Unknown')}\n"
    
    # Include first and last name if they differ from full name
    first_name = data.get('first_name', 'Unknown')
    last_name = data.get('last_name', 'Unknown')
    if first_name != 'Unknown' or last_name != 'Unknown':
        md += f"- First Name: {first_name}\n"
        md += f"- Last Name: {last_name}\n"
    md += "\n"
    
    # Business Information section
    if data.get('business'):
        md += "## Business\n"
        md += f"### {data['business'].get('name', 'Unknown Business')}\n"
        md += f"{data['business'].get('description', '')}\n"
        md += f"**Genesis:** {data['business'].get('genesis', '')}\n\n"
    
    # Core Values section
    if data.get('values'):
        md += "## Core Values\n"
        for value in data['values']:
            md += f"### {value.get('name', '')}\n"
            md += f"**Origin:** {value.get('origin', '')}\n"
            md += f"**Impact Today:** {value.get('impact_today', '')}\n\n"
    
    # Life Events section
    if data.get('life_events'):
        md += "## Significant Life Events\n"
        for event in data['life_events']:
            md += f"### {event.get('name', '')}\n"
            md += f"{event.get('description', '')}\n\n"
    
    # Challenges and Learnings section
    if data.get('challenges'):
        md += "## Challenges and Learnings\n"
        for challenge in data['challenges']:
            md += f"### Challenge\n"
            md += f"{challenge.get('description', '')}\n"
            md += f"**Learnings:** {challenge.get('learnings', '')}\n\n"
    
    # Achievements section
    if data.get('achievements'):
        md += "## Achievements\n"
        for achievement in data['achievements']:
            md += f"- {achievement.get('description', '')}\n"
        md += "\n"
    
    # Add metadata section at the end
    md += "---\n"
    md += "## Report Metadata\n"
    md += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    md += f"Content Language: {data.get('main_language', 'Unknown')}\n"
    
    return md
# def convert_to_markdown(data: Dict) -> str:
#     """Convert the analysis results to markdown format"""
#     md = "# Creator Analysis Report\n\n"
    
#     # Basic Info
#     md += "## Basic Information\n"
#     md += f"- First Name: {data.get('first_name', 'Unknown')}\n"
#     md += f"- Last Name: {data.get('last_name', 'Unknown')}\n\n"
    
#     # Business
#     if data.get('business'):
#         md += "## Business\n"
#         md += f"### {data['business'].get('name', 'Unknown Business')}\n"
#         md += f"{data['business'].get('description', '')}\n"
#         md += f"**Genesis:** {data['business'].get('genesis', '')}\n\n"
    
#     # Values
#     if data.get('values'):
#         md += "## Core Values\n"
#         for value in data['values']:
#             md += f"### {value.get('name', '')}\n"
#             md += f"**Origin:** {value.get('origin', '')}\n"
#             md += f"**Impact Today:** {value.get('impact_today', '')}\n\n"
    
#     # Life Events
#     if data.get('life_events'):
#         md += "## Significant Life Events\n"
#         for event in data['life_events']:
#             md += f"### {event.get('name', '')}\n"
#             md += f"{event.get('description', '')}\n\n"
    
#     # Challenges
#     if data.get('challenges'):
#         md += "## Challenges and Learnings\n"
#         for challenge in data['challenges']:
#             md += f"### Challenge\n{challenge.get('description', '')}\n"
#             md += f"**Learnings:** {challenge.get('learnings', '')}\n\n"
    
#     # Achievements
#     if data.get('achievements'):
#         md += "## Achievements\n"
#         for achievement in data['achievements']:
#             md += f"- {achievement.get('description', '')}\n"
    
#     return md

#  new version --------

def merge_content_creator_info(info1: Dict[str, Any], info2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merges two ContentCreatorInfo dictionaries with proper default values.
    """
    def is_empty_or_none(value) -> bool:
        if value is None:
            return True
        if isinstance(value, (str, list, dict)) and not value:
            return True
        return False

    def merge_lists(list1: List, list2: List) -> List:
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

    # Initialize merged result
    merged = {}
    
    # Merge list fields with proper defaults
    default_value = {
        'name': 'Not specified',
        'origin': 'No information available',  # Added required field
        'impact_today': 'No information available'  # Added required field
    }
    
    default_challenge = {
        'description': 'No information available',
        'learnings': 'No information available'  # Added required field
    }
    
    default_achievement = {
        'description': 'No information available'
    }
    
    default_life_event = {
        'name': 'Not specified',
        'description': 'No information available'
    }
    
    # Merge list fields
    merged['values'] = merge_lists(
        info1.get('values', []),
        info2.get('values', [])
    ) or [default_value]
    
    merged['challenges'] = merge_lists(
        info1.get('challenges', []),
        info2.get('challenges', [])
    ) or [default_challenge]
    
    merged['achievements'] = merge_lists(
        info1.get('achievements', []),
        info2.get('achievements', [])
    ) or [default_achievement]
    
    merged['life_events'] = merge_lists(
        info1.get('life_events', []),
        info2.get('life_events', [])
    ) or [default_life_event]
    
    # Merge business object with defaults
    merged['business'] = {
        'name': 'Not specified',
        'description': 'No information available',
        'genesis': 'No information available'
    }
    
    if info1.get('business') or info2.get('business'):
        business1 = info1.get('business', {})
        business2 = info2.get('business', {})
        merged['business'] = {
            'name': business1.get('name', business2.get('name', 'Not specified')),
            'description': business1.get('description', business2.get('description', 'No information available')),
            'genesis': business1.get('genesis', business2.get('genesis', 'No information available'))
        }
    
    # Merge name fields
    merged['first_name'] = info1.get('first_name') or info2.get('first_name') or 'Unknown'
    merged['last_name'] = info1.get('last_name') or info2.get('last_name') or 'Unknown'
    
    return merged
# def merge_content_creator_info(info1: Dict[str, Any], info2: Dict[str, Any]) -> Dict[str, Any]:
#     """
#     Merges two ContentCreatorInfo dictionaries, combining lists and selecting the longest values
#     for unique fields. Handles empty/None values and ensures the final object is fully populated.
    
#     Args:
#         info1: First ContentCreatorInfo dictionary
#         info2: Second ContentCreatorInfo dictionary
        
#     Returns:
#         Dict[str, Any]: Merged ContentCreatorInfo dictionary
#     """
#     def is_empty_or_none(value) -> bool:
#         """Check if a value is empty or None"""
#         if value is None:
#             return True
#         if isinstance(value, (str, list, dict)) and not value:
#             return True
#         return False

#     def merge_lists(list1: List, list2: List) -> List:
#         """Merge two lists, removing duplicates based on 'name' or 'description'"""
#         if not list1:
#             return list2 or []
#         if not list2:
#             return list1 or []
            
#         merged = list1.copy()
#         existing_items = {
#             item.get('name', item.get('description', '')): True 
#             for item in merged
#         }
        
#         for item in list2:
#             identifier = item.get('name', item.get('description', ''))
#             if identifier and identifier not in existing_items:
#                 merged.append(item)
#                 existing_items[identifier] = True
                
#         return merged

#     def select_longest_object(obj1: Dict, obj2: Dict) -> Dict:
#         """Select the object with the longest description"""
#         if is_empty_or_none(obj1):
#             return obj2 or {}
#         if is_empty_or_none(obj2):
#             return obj1 or {}
            
#         # Compare lengths of descriptions
#         len1 = len(obj1.get('description', ''))
#         len2 = len(obj2.get('description', ''))
#         return obj1 if len1 >= len2 else obj2

#     # Initialize merged result
#     merged = {}
    
#     # Merge list fields
#     list_fields = ['life_events', 'values', 'challenges', 'achievements']
#     for field in list_fields:
#         merged[field] = merge_lists(
#             info1.get(field, []),
#             info2.get(field, [])
#         )
    
#     # Merge business object
#     merged['business'] = select_longest_object(
#         info1.get('business', {}),
#         info2.get('business', {})
#     )
    
#     # Merge name fields
#     merged['first_name'] = (
#         info1.get('first_name') or 
#         info2.get('first_name') or 
#         'Unknown'
#     )
#     merged['last_name'] = (
#         info1.get('last_name') or 
#         info2.get('last_name') or 
#         'Unknown'
#     )
    
#     # Ensure default values for empty lists
#     for field in list_fields:
#         if not merged[field]:
#             merged[field] = [{'name': 'Not specified', 'description': 'No information available'}]
            
#     # Ensure business object has required fields
#     if not merged['business']:
#         merged['business'] = {
#             'name': 'Not specified',
#             'description': 'No information available',
#             'genesis': 'No information available'
#         }
    
#     return merged


def ensure_dict(info: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Convert string input to dictionary if needed."""
    if isinstance(info, str):
        try:
            return json.loads(info.strip('"""').strip("'''"))
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")
    return info

def merge_and_validate_content(crew_result: Dict[str, Any], instagram_info: Dict[str, Any]) -> ContentCreatorInfo:
    """
    Merge crew result with Instagram info and validate the result.
    
    Args:
        crew_result: Result dictionary from the YouTube crew
        instagram_info: Result dictionary from Instagram crew
        
    Returns:
        ContentCreatorInfo: Validated merged content
    """
    try:
        # Merge the content
        merged_info = merge_content_creator_info(crew_result, instagram_info)
        
        # Create and return the ContentCreatorInfo model
        return ContentCreatorInfo(**merged_info)
    except Exception as e:
        print(f"Error during merge: {str(e)}")
        return ContentCreatorInfo.create_empty()


def run_analysis(youtube_handle: Optional[str], instagram_handle: Optional[str], full_name: Optional[str], main_language: Optional[str]) -> Dict[str, Any]:
    """
    Run analysis with improved progress feedback. The function expects initial_info to be merged
    with the results after it returns, preserving the original data flow pattern.
    """
    try:
        # Validate input
        if not youtube_handle and not instagram_handle:
            raise ValueError("At least one handle (YouTube or Instagram) is required")
        
        # Initialize containers for Streamlit UI
        progress_container = st.empty()
        status_container = st.empty()
        
        # Initialize result variables
        youtube_json = {}
        instagram_json = {}
        
        # YouTube Analysis Section
        if youtube_handle:
            with status_container.container():
                st.subheader("YouTube Analysis")
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("Initializing YouTube analysis...")
                progress_bar.progress(25)
                
                try:
                    youtube_result = YoutubeCrew().crew().kickoff(
                        inputs={"youtube_handle": youtube_handle}
                    )
                    progress_bar.progress(50)
                    status_text.text("Processing YouTube data...")
                    
                    if hasattr(youtube_result, 'pydantic'):
                        youtube_json = youtube_result.pydantic.dict()
                        progress_bar.progress(100)
                        status_text.text("YouTube analysis complete!")
                        st.write(f"✓ Found data for: {youtube_json.get('full_name', 'Unknown')}")
                        st.write(f"✓ Collected {len(youtube_json.get('values', []))} values")
                except Exception as e:
                    progress_bar.progress(100)
                    status_text.text(f"⚠️ YouTube analysis encountered an error: {str(e)}")
                    youtube_json = {}
        
        # Instagram Analysis Section
        if instagram_handle:
            with status_container.container():
                st.subheader("Instagram Analysis")
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("Initializing Instagram analysis...")
                progress_bar.progress(25)
                
                try:
                    instagram_result = InstagramCrew().crew().kickoff(
                        inputs={"instagram_handle": instagram_handle}
                    )
                    progress_bar.progress(50)
                    status_text.text("Processing Instagram data...")
                    
                    if hasattr(instagram_result, 'pydantic'):
                        instagram_json = instagram_result.pydantic.dict()
                        progress_bar.progress(100)
                        status_text.text("Instagram analysis complete!")
                        st.write(f"✓ Found data for: {instagram_json.get('full_name', 'Unknown')}")
                        st.write(f"✓ Collected {len(instagram_json.get('values', []))} values")
                except Exception as e:
                    progress_bar.progress(100)
                    status_text.text(f"⚠️ Instagram analysis encountered an error: {str(e)}")
                    instagram_json = {}
        
        # Merging Results Section
        with status_container.container():
            st.subheader("Merging Results")
            merge_progress = st.progress(0)
            merge_status = st.empty()
            
            # Handle failed analyses
            if youtube_handle and instagram_handle and not youtube_json and not instagram_json:
                merge_status.error("All attempted analyses failed. Returning empty model.")
                return ContentCreatorInfo.create_empty()
            
            merge_status.text("Merging available data...")
            merge_progress.progress(33)
            
            # Merge the available data
            merged_model = merge_and_validate_content(youtube_json, instagram_json)
            merge_progress.progress(66)
            
            # Convert merged model to proper format for RAG input
            merged_dict = merged_model.model_dump()
            
            # Format specifically for RAG input requirements
            rag_input = {
                "input_string": json.dumps(merged_dict)
            }
            
            merge_progress.progress(100)
            merge_status.text("✓ Merge complete!")
            
            st.write(f"✓ Combined {len(merged_dict.get('values', []))} values")
            st.write(f"✓ Combined {len(merged_dict.get('life_events', []))} life events")
        
        # RAG Processing Section
        with status_container.container():
            st.subheader("Final Analysis")
            rag_progress = st.progress(0)
            rag_status = st.empty()
            
            rag_status.text("Processing with RAG Crew...")
            rag_progress.progress(50)
            
            # Process with RAG using properly formatted input
            result_rag = RagCrew().crew().kickoff(inputs=rag_input)
            
            rag_progress.progress(100)
            rag_status.text("✓ Analysis complete!")
            
            return result_rag
        
    except ValueError as e:
        st.error(f"Validation error: {str(e)}")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        return None
# def run_analysis(youtube_handle: Optional[str], instagram_handle: Optional[str]) -> Dict[str, Any]:
#     """
#     Run analysis with improved progress feedback.
#     """
#     try:
#         # Make sure at least one handle is provided
#         if not youtube_handle and not instagram_handle:
#             raise ValueError("At least one handle (YouTube or Instagram) is required")
        
#         # Create a progress container
#         progress_container = st.empty()
#         status_container = st.empty()
        
#         # Initialize variables
#         youtube_json = {}
#         instagram_json = {}
        
#         # Try YouTube analysis if handle provided
#         if youtube_handle:
#             with status_container.container():
#                 st.subheader("YouTube Analysis")
#                 progress_bar = st.progress(0)
#                 status_text = st.empty()
                
#                 status_text.text("Initializing YouTube analysis...")
#                 progress_bar.progress(25)
                
#                 try:
#                     youtube_result = YoutubeCrew().crew().kickoff(inputs={"youtube_channel_handle": youtube_handle})
#                     progress_bar.progress(50)
#                     status_text.text("Processing YouTube data...")
                    
#                     if hasattr(youtube_result, 'pydantic'):
#                         youtube_json = youtube_result.pydantic.dict()
#                         progress_bar.progress(100)
#                         status_text.text("YouTube analysis complete!")
#                         st.write(f"✓ Found data for: {youtube_json.get('first_name', 'Unknown')} {youtube_json.get('last_name', 'Unknown')}")
#                         st.write(f"✓ Collected {len(youtube_json.get('values', []))} values")
#                 except Exception as e:
#                     progress_bar.progress(100)
#                     status_text.text(f"⚠️ YouTube analysis encountered an error: {str(e)}")
#                     youtube_json = {}
        
#         # Try Instagram analysis if handle provided
#         if instagram_handle:
#             with status_container.container():
#                 st.subheader("Instagram Analysis")
#                 progress_bar = st.progress(0)
#                 status_text = st.empty()
                
#                 status_text.text("Initializing Instagram analysis...")
#                 progress_bar.progress(25)
                
#                 try:
#                     instagram_result = InstagramCrew().crew().kickoff(inputs={"instagram_username": instagram_handle})
#                     progress_bar.progress(50)
#                     status_text.text("Processing Instagram data...")
                    
#                     if hasattr(instagram_result, 'pydantic'):
#                         instagram_json = instagram_result.pydantic.dict()
#                         progress_bar.progress(100)
#                         status_text.text("Instagram analysis complete!")
#                         st.write(f"✓ Found data for: {instagram_json.get('first_name', 'Unknown')} {instagram_json.get('last_name', 'Unknown')}")
#                         st.write(f"✓ Collected {len(instagram_json.get('values', []))} values")
#                 except Exception as e:
#                     progress_bar.progress(100)
#                     status_text.text(f"⚠️ Instagram analysis encountered an error: {str(e)}")
#                     instagram_json = {}
        
#         # Merging results
#         with status_container.container():
#             st.subheader("Merging Results")
#             merge_progress = st.progress(0)
#             merge_status = st.empty()
            
#             # If both analyses failed after attempting them, return empty model
#             if youtube_handle and instagram_handle and not youtube_json and not instagram_json:
#                 merge_status.error("All attempted analyses failed. Returning empty model.")
#                 return ContentCreatorInfo.create_empty()
            
#             merge_status.text("Merging available data...")
#             merge_progress.progress(33)
            
#             # Use whatever data we have
#             merged_model = merge_and_validate_content(youtube_json, instagram_json)
#             merge_progress.progress(66)
            
#             # Convert merged model to dict for RAG input
#             merged_dict = merged_model.model_dump()
#             merged_json = json.dumps(merged_dict)
            
#             merge_progress.progress(100)
#             merge_status.text("✓ Merge complete!")
            
#             st.write(f"✓ Combined {len(merged_dict.get('values', []))} values")
#             st.write(f"✓ Combined {len(merged_dict.get('life_events', []))} life events")
        
#         # RAG Processing
#         with status_container.container():
#             st.subheader("Final Analysis")
#             rag_progress = st.progress(0)
#             rag_status = st.empty()
            
#             rag_status.text("Processing with RAG Crew...")
#             rag_progress.progress(50)
            
#             result_rag = RagCrew().crew().kickoff(inputs={"input_string": merged_json})
            
#             rag_progress.progress(100)
#             rag_status.text("✓ Analysis complete!")
            
#             return result_rag
        
#     except ValueError as e:
#         st.error(f"Validation error: {str(e)}")
#         return None
#     except Exception as e:
#         st.error(f"An unexpected error occurred: {str(e)}")
#         return None


def main():
    """
    Main function for the Creator Analysis Tool. Handles user input collection,
    validation, analysis processing, and result presentation. Incorporates full_name
    and main_language fields while maintaining proper data flow through the analysis pipeline.
    """
    st.title("Creator Analysis Tool")
    
    # Password protection section
    password = st.text_input("Enter password", type="password")
    if not validate_password(password):
        st.warning("Please enter the correct password to proceed.")
        return
    
    # User input collection form
    with st.form("creator_analysis_form"):
        # New required fields for creator information
        full_name = st.text_input(
            "Content Creator's Full Name",
            help="Enter the complete name of the content creator"
        )
        main_language = st.text_input(
            "Content Creator's Main Language",
            help="Enter the primary language used by the creator (e.g., English, Spanish)"
        )
        
        # Optional social media handles
        youtube_handle = st.text_input(
            "YouTube Channel Handle (optional)",
            help="Enter the creator's YouTube handle without the @ symbol"
        )
        instagram_handle = st.text_input(
            "Instagram Handle (optional)",
            help="Enter the creator's Instagram handle without the @ symbol"
        )
        
        # Analysis trigger button
        analyze_button = st.form_submit_button("Analyze Creator")

    # Process analysis when button is clicked
    if analyze_button:
        # Validate required inputs
        if not youtube_handle and not instagram_handle:
            st.error("At least one handle (YouTube or Instagram) is required")
        elif not full_name:
            st.error("Content Creator's Full Name is required")
        elif not main_language:
            st.error("Content Creator's Main Language is required")
        else:
            # Begin analysis process
            with st.spinner("Analyzing creator content..."):
                try:
                    # Create initial info with the new required fields
                    initial_info = {
                        "youtube_handle": youtube_handle,
                        "instagram_handle": instagram_handle,
                        "full_name": full_name,
                        "main_language": main_language
                    }
                    
                    # Run the analysis pipeline
                    result = run_analysis(youtube_handle, instagram_handle, full_name, main_language)
                    
                    # Process and display results if analysis was successful
                    if result is not None:
                        # Update the result with the initial info
                        result_dict = result.model_dump()
                        result_dict.update(initial_info)
                        
                        # Create a new ContentCreatorInfo instance with the combined data
                        result = ContentCreatorInfo(**result_dict)
                        
                        # Show success message
                        st.success("Analysis complete!")
                        
                        # Display JSON results in expandable section
                        with st.expander("View Results", expanded=True):
                            st.json(result.model_dump())
                        
                        # Generate markdown report
                        markdown_content = convert_to_markdown(result.model_dump())
                        
                        # Provide download option for the report
                        st.download_button(
                            label="Download Report (Markdown)",
                            data=markdown_content,
                            file_name=f"creator_analysis_{full_name.replace(' ', '_').lower()}.md",
                            mime="text/markdown"
                        )
                    else:
                        st.error("Analysis failed to produce results. Please try again.")
                
                except Exception as e:
                    st.error(f"An error occurred during analysis: {str(e)}")
                    logger.error(f"Analysis error: {str(e)}", exc_info=True)

# def main():
#     st.title("Creator Analysis Tool")
    
#     # Password protection
#     password = st.text_input("Enter password", type="password")
#     if not validate_password(password):
#         st.warning("Please enter the correct password to proceed.")
#         return
    
#     with st.form("creator_analysis_form"):
#         youtube_handle = st.text_input("YouTube Channel Handle (optional)")
#         instagram_handle = st.text_input("Instagram Handle (optional)")
#         analyze_button = st.form_submit_button("Analyze Creator")

#     if analyze_button:
#         if not youtube_handle and not instagram_handle:
#             st.error("At least one handle (YouTube or Instagram) is required")
#         else:
#             with st.spinner("Analyzing creator content..."):
#                 result = run_analysis(youtube_handle, instagram_handle)
                
#                 if result is not None:
#                     st.success("Analysis complete!")
                    
#                     # Display results
#                     with st.expander("View Results", expanded=True):
#                         st.json(result.model_dump())
                    
#                     # Convert to markdown
#                     markdown_content = convert_to_markdown(result.model_dump())
                    
#                     # Download button for markdown
#                     st.download_button(
#                         label="Download Report (Markdown)",
#                         data=markdown_content,
#                         file_name="creator_analysis.md",
#                         mime="text/markdown"
#                     )

if __name__ == "__main__":
    main()