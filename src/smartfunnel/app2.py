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
    Run analysis that captures both the consolidated creator info and the RAG text analysis.
    The function processes YouTube and Instagram data first, consolidates it, then runs the RAG analysis
    to provide additional insights in text form.
    """
    try:
        # Initialize our results container to store both structured and text analysis
        results = {
            'consolidated_info': None,  # Will store the merged YouTube/Instagram structured data
            'text_analysis': None,      # Will store the RAG crew's text analysis
            'raw_data': {              # Store raw data for reference
                'youtube': None,
                'instagram': None
            }
        }

        # Initialize result variables
        youtube_json = {}
        instagram_json = {}
        
        # YouTube Analysis Section
        if youtube_handle:
            with st.container():
                st.subheader("YouTube Analysis")
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    youtube_inputs = {
                        "youtube_handle": youtube_handle,
                        "full_name": full_name,
                        "main_language": main_language
                    }
                    
                    youtube_crew = YoutubeCrew()
                    youtube_result = youtube_crew.crew().kickoff(inputs=youtube_inputs)
                    results['raw_data']['youtube'] = youtube_result
                    
                    if youtube_result and hasattr(youtube_result, 'pydantic'):
                        youtube_json = youtube_result.pydantic.model_dump()
                        progress_bar.progress(100)
                        status_text.text("YouTube analysis complete!")
                        st.write(f"✓ Found YouTube data for: {youtube_json.get('full_name', 'Unknown')}")
                except Exception as e:
                    st.error(f"YouTube analysis error: {str(e)}")
        
        # Instagram Analysis Section
        if instagram_handle:
            with st.container():
                st.subheader("Instagram Analysis")
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    instagram_inputs = {
                        "instagram_handle": instagram_handle,
                        "full_name": full_name,
                        "main_language": main_language
                    }
                    
                    instagram_crew = InstagramCrew()
                    instagram_result = instagram_crew.crew().kickoff(inputs=instagram_inputs)
                    results['raw_data']['instagram'] = instagram_result
                    
                    if instagram_result and hasattr(instagram_result, 'pydantic'):
                        instagram_json = instagram_result.pydantic.model_dump()
                        progress_bar.progress(100)
                        status_text.text("Instagram analysis complete!")
                        st.write(f"✓ Found Instagram data for: {instagram_json.get('full_name', 'Unknown')}")
                except Exception as e:
                    st.error(f"Instagram analysis error: {str(e)}")
        
        # Merge results if we have any data
        if not youtube_json and not instagram_json:
            st.warning("No data was collected from either YouTube or Instagram analysis")
            results['consolidated_info'] = ContentCreatorInfo.create_empty()
            return results
            
        # Merging Results Section
        with st.container():
            st.subheader("Merging Results")
            merge_status = st.empty()
            
            try:
                # Merge available data
                merged_model = merge_and_validate_content(youtube_json, instagram_json)
                merged_dict = merged_model.model_dump()
                merged_dict.update({
                    "full_name": full_name,
                    "main_language": main_language
                })
                
                # Store consolidated info
                results['consolidated_info'] = ContentCreatorInfo(**merged_dict)
                merge_status.text("✓ Merge complete!")
                
                # Prepare input for RAG analysis
                rag_input = {
                    "input_string": json.dumps(merged_dict)
                }
                
                # RAG Analysis Section
                with st.container():
                    st.subheader("Detailed Analysis")
                    rag_progress = st.progress(0)
                    rag_status = st.empty()
                    
                    try:
                        rag_status.text("Generating detailed analysis...")
                        rag_progress.progress(50)
                        
                        # Run RAG analysis
                        rag_crew = RagCrew()
                        rag_result = rag_crew.crew().kickoff(inputs=rag_input)
                        
                        # Store the text analysis directly from the raw output
                        if rag_result and hasattr(rag_result, 'raw'):
                            results['text_analysis'] = rag_result.raw
                            rag_progress.progress(100)
                            rag_status.text("✓ Detailed analysis complete!")
                        else:
                            rag_status.warning("Analysis completed but produced no detailed insights")
                            
                    except Exception as e:
                        rag_status.error(f"Detailed analysis error: {str(e)}")
                        logger.error(f"RAG analysis error details: {str(e)}", exc_info=True)
                
                return results
                
            except Exception as e:
                st.error(f"Error during merge: {str(e)}")
                return None
        
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        return None

def display_analysis_results(results: Dict[str, Any]) -> None:
    """
    Display both the consolidated structured data and the detailed text analysis.
    This function presents results in a clear, organized manner with proper sections
    for different types of information.
    """
    if not results:
        st.error("No results to display")
        return
    
    # Display the detailed text analysis first
    if results.get('text_analysis'):
        st.subheader("Detailed Analysis")
        with st.expander("View Detailed Analysis", expanded=True):
            st.write(results['text_analysis'])
    
    # Display consolidated structured data
    st.subheader("Consolidated Creator Information")
    if results.get('consolidated_info'):
        with st.expander("View Structured Data", expanded=True):
            consolidated_dict = results['consolidated_info'].model_dump()
            st.json(consolidated_dict)
    
    # Display raw data in a collapsed section
    st.subheader("Raw Data")
    with st.expander("View Raw Data", expanded=False):
        raw_data = results.get('raw_data', {})
        
        st.write("### YouTube Data")
        youtube_raw = raw_data.get('youtube')
        if youtube_raw and hasattr(youtube_raw, 'pydantic'):
            st.json(youtube_raw.pydantic.model_dump())
        else:
            st.write("No YouTube data available")
        
        st.write("### Instagram Data")
        instagram_raw = raw_data.get('instagram')
        if instagram_raw and hasattr(instagram_raw, 'pydantic'):
            st.json(instagram_raw.pydantic.model_dump())
        else:
            st.write("No Instagram data available")
# def run_analysis(youtube_handle: Optional[str], instagram_handle: Optional[str], full_name: Optional[str], main_language: Optional[str]) -> Dict[str, Any]:
#     """
#     Run analysis with improved error handling and proper CrewOutput processing.
#     This function now ensures the RagCrew runs and its results are captured.
#     """
#     try:
#         # Initialize our results container with all potential outputs
#         results = {
#             'youtube_raw': None,
#             'instagram_raw': None,
#             'rag_raw': None,
#             'merged_content': None,
#             'consolidated_info': None,
#             'final_analysis': None  # This will store the RAG analysis results
#         }

#         # Initialize result variables
#         youtube_json = {}
#         instagram_json = {}
        
#         # YouTube Analysis Section
#         if youtube_handle:
#             with st.container():
#                 st.subheader("YouTube Analysis")
#                 progress_bar = st.progress(0)
#                 status_text = st.empty()
                
#                 try:
#                     youtube_inputs = {
#                         "youtube_handle": youtube_handle,
#                         "full_name": full_name,
#                         "main_language": main_language
#                     }
                    
#                     youtube_crew = YoutubeCrew()
#                     youtube_result = youtube_crew.crew().kickoff(inputs=youtube_inputs)
#                     results['youtube_raw'] = youtube_result
                    
#                     if youtube_result and hasattr(youtube_result, 'pydantic'):
#                         youtube_json = youtube_result.pydantic.model_dump()
#                         progress_bar.progress(100)
#                         status_text.text("YouTube analysis complete!")
#                         st.write(f"✓ Found YouTube data for: {youtube_json.get('full_name', 'Unknown')}")
#                 except Exception as e:
#                     st.error(f"YouTube analysis error: {str(e)}")
        
#         # Instagram Analysis Section
#         if instagram_handle:
#             with st.container():
#                 st.subheader("Instagram Analysis")
#                 progress_bar = st.progress(0)
#                 status_text = st.empty()
                
#                 try:
#                     instagram_inputs = {
#                         "instagram_handle": instagram_handle,
#                         "full_name": full_name,
#                         "main_language": main_language
#                     }
                    
#                     instagram_crew = InstagramCrew()
#                     instagram_result = instagram_crew.crew().kickoff(inputs=instagram_inputs)
#                     results['instagram_raw'] = instagram_result
                    
#                     if instagram_result and hasattr(instagram_result, 'pydantic'):
#                         instagram_json = instagram_result.pydantic.model_dump()
#                         progress_bar.progress(100)
#                         status_text.text("Instagram analysis complete!")
#                         st.write(f"✓ Found Instagram data for: {instagram_json.get('full_name', 'Unknown')}")
#                 except Exception as e:
#                     st.error(f"Instagram analysis error: {str(e)}")
        
#         # Merge results if we have any data
#         if not youtube_json and not instagram_json:
#             st.warning("No data was collected from either YouTube or Instagram analysis")
#             return ContentCreatorInfo.create_empty()
            
#         # Merging Results Section
#         with st.container():
#             st.subheader("Merging Results")
#             merge_status = st.empty()
            
#             try:
#                 # Merge available data
#                 merged_model = merge_and_validate_content(youtube_json, instagram_json)
                
#                 # Add the original input information
#                 merged_dict = merged_model.model_dump()
#                 merged_dict.update({
#                     "full_name": full_name,
#                     "main_language": main_language
#                 })
                
#                 # Store merged content
#                 results['merged_content'] = merged_dict
                
#                 # Create consolidated ContentCreatorInfo
#                 consolidated_info = ContentCreatorInfo(**merged_dict)
#                 results['consolidated_info'] = consolidated_info
                
#                 merge_status.text("✓ Merge complete!")
                
#                 # Prepare input for RAG analysis
#                 rag_input = {
#                     "input_string": json.dumps(merged_dict)
#                 }
                
#                 # RAG Analysis Section
#                 with st.container():
#                     st.subheader("RAG Analysis")
#                     rag_progress = st.progress(0)
#                     rag_status = st.empty()
                    
#                     try:
#                         rag_status.text("Running RAG analysis...")
#                         rag_progress.progress(50)
                        
#                         rag_crew = RagCrew()
#                         rag_result = rag_crew.crew().kickoff(inputs=rag_input)
#                         results['rag_raw'] = rag_result
                        
#                         if rag_result and hasattr(rag_result, 'pydantic'):
#                             # Store the final analysis
#                             results['final_analysis'] = rag_result.pydantic.model_dump()
#                             rag_progress.progress(100)
#                             rag_status.text("✓ RAG analysis complete!")
#                         else:
#                             rag_status.warning("RAG analysis completed but returned no results")
#                     except Exception as e:
#                         rag_status.error(f"RAG analysis error: {str(e)}")
                
#                 return results
                
#             except Exception as e:
#                 st.error(f"Error during merge: {str(e)}")
#                 return None
        
#     except Exception as e:
#         st.error(f"An unexpected error occurred: {str(e)}")
#         return None

# def display_analysis_results(results: Dict[str, Any]) -> None:
#     """
#     Display analysis results including RAG output with proper error handling and formatting.
#     """
#     if not results:
#         st.error("No results to display")
#         return
    
#     # Display final RAG analysis results first (if available)
#     st.subheader("Final Analysis Results")
#     if results.get('final_analysis'):
#         with st.expander("View Final Analysis", expanded=True):
#             st.json(results['final_analysis'])
    
#     # Display consolidated results
#     st.subheader("Consolidated Data")
#     if results.get('consolidated_info'):
#         with st.expander("View Consolidated Results", expanded=True):
#             consolidated_dict = results['consolidated_info'].model_dump()
#             st.json(consolidated_dict)
    
#     # Display raw outputs in a separate section
#     st.subheader("Raw Analysis Data")
#     with st.expander("View Raw Data", expanded=False):
#         # YouTube raw data
#         st.write("### YouTube Analysis")
#         if results.get('youtube_raw') and hasattr(results['youtube_raw'], 'pydantic'):
#             try:
#                 youtube_data = results['youtube_raw'].pydantic.model_dump()
#                 st.json(youtube_data)
#             except Exception:
#                 st.write("No YouTube data available")
#         else:
#             st.write("No YouTube data available")
            
#         # Instagram raw data
#         st.write("### Instagram Analysis")
#         if results.get('instagram_raw') and hasattr(results['instagram_raw'], 'pydantic'):
#             try:
#                 instagram_data = results['instagram_raw'].pydantic.model_dump()
#                 st.json(instagram_data)
#             except Exception:
#                 st.write("No Instagram data available")
#         else:
#             st.write("No Instagram data available")
            
#         # RAG raw data
#         st.write("### RAG Analysis")
#         if results.get('rag_raw') and hasattr(results['rag_raw'], 'pydantic'):
#             try:
#                 rag_data = results['rag_raw'].pydantic.model_dump()
#                 st.json(rag_data)
#             except Exception:
#                 st.write("No RAG analysis data available")
#         else:
#             st.write("No RAG analysis data available")

def main():
    """
    Main function with updated result handling.
    """
    st.title("Creator Analysis Tool")
    
    # Password protection
    password = st.text_input("Enter password", type="password")
    if not validate_password(password):
        st.warning("Please enter the correct password to proceed.")
        return
    
    with st.form("creator_analysis_form"):
        full_name = st.text_input(
            "Content Creator's Full Name",
            help="Enter the complete name of the content creator"
        )
        main_language = st.text_input(
            "Content Creator's Main Language",
            help="Enter the primary language used by the creator"
        )
        youtube_handle = st.text_input(
            "YouTube Channel Handle (optional)",
            help="Enter the creator's YouTube handle without the @ symbol"
        )
        instagram_handle = st.text_input(
            "Instagram Handle (optional)",
            help="Enter the creator's Instagram handle without the @ symbol"
        )
        analyze_button = st.form_submit_button("Analyze Creator")

    if analyze_button:
        if not youtube_handle and not instagram_handle:
            st.error("At least one handle (YouTube or Instagram) is required")
        elif not full_name:
            st.error("Content Creator's Full Name is required")
        elif not main_language:
            st.error("Content Creator's Main Language is required")
        else:
            with st.spinner("Analyzing creator content..."):
                try:
                    # Run analysis
                    results = run_analysis(youtube_handle, instagram_handle, full_name, main_language)
                    
                    if results:
                        st.success("Analysis complete!")
                        
                        # Display results using the new display function
                        display_analysis_results(results)
                        
                        # Generate markdown report
                        if results.get('consolidated_info'):
                            markdown_content = convert_to_markdown(
                                results['consolidated_info'].model_dump()
                            )
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

if __name__ == "__main__":
    main()