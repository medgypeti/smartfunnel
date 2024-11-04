from smartfunnel.sqlite_setup import ensure_pysqlite3
ensure_pysqlite3()  # Call this before any other imports

import streamlit as st
import sys
import json
# from smartfunnel.crew import LatestAiDevelopmentCrew
import logging
from typing import Optional
from smartfunnel.tools.chroma_db_init import app_instance
from smartfunnel.tools.chroma_db_init import cleanup_old_db
import time
from datetime import datetime
import sys
import json
import streamlit as st
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from smartfunnel.crew_youtube import YoutubeCrew
from smartfunnel.crew_instagram import InstagramCrew
from smartfunnel.crew_rag import RagCrew
#!/usr/bin/env python
import time
from datetime import datetime
import sys
import json
import streamlit as st
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from smartfunnel.crew_youtube import YoutubeCrew
from smartfunnel.crew_instagram import InstagramCrew
from smartfunnel.crew_rag import RagCrew

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Streamlit configs
try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
    
    # Reduce file watching using safer check
    import streamlit.runtime.scriptrunner as streamlit_runtime
    if streamlit_runtime.get_script_run_ctx():
        st.set_option('server.fileWatcherType', 'none')
except Exception as e:
    logger.warning(f"Error initializing Streamlit configs: {e}")
    
    # Reduce file watching using safer check
import streamlit.runtime.scriptrunner as streamlit_runtime
    if streamlit_runtime.get_script_run_ctx():
        st.set_option('server.fileWatcherType', 'none')
except Exception as e:
    logger.warning(f"Error initializing Streamlit configs: {e}")

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
    life_events: Optional[List[LifeEventObject]] = Field(default_factory=list)
    business: Optional[BusinessObject] = None
    values: Optional[List[ValueObject]] = Field(default_factory=list)
    challenges: Optional[List[ChallengeObject]] = Field(default_factory=list)
    achievements: Optional[List[AchievementObject]] = Field(default_factory=list)
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    @classmethod
    def create_empty(cls) -> 'ContentCreatorInfo':
        """Create a complete ContentCreatorInfo with default values."""
        return cls(
            first_name="Unknown",
            last_name="Unknown",
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
from smartfunnel.crew_youtube import YoutubeCrew
from smartfunnel.crew_instagram import InstagramCrew

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

def run_analysis(youtube_handle: Optional[str], instagram_handle: Optional[str]) -> Dict[str, Any]:
    """
    Identical to original run() function but with Streamlit inputs.
    """
    try:
        # Make sure at least one handle is provided
        if not youtube_handle and not instagram_handle:
            raise ValueError("At least one handle (YouTube or Instagram) is required")
        
        # Initialize variables
        youtube_json = {}
        instagram_json = {}
        
        # Try YouTube analysis if handle provided
        if youtube_handle:
            st.write("\n=== YouTube Analysis ===")
            try:
                youtube_result = YoutubeCrew().crew().kickoff(inputs={"youtube_channel_handle": youtube_handle})
                if hasattr(youtube_result, 'pydantic'):
                    youtube_json = youtube_result.pydantic.dict()
                    st.write("YouTube Data Preview:")
                    st.write(f"- First Name: {youtube_json.get('first_name', 'Not found')}")
                    st.write(f"- Number of values: {len(youtube_json.get('values', []))}")
            except Exception as e:
                st.write(f"Warning: Error analyzing YouTube content: {str(e)}")
                youtube_json = {}  # Reset to empty dict if failed
        
        # Try Instagram analysis if handle provided
        if instagram_handle:
            st.write("\n=== Instagram Analysis ===")
            try:
                instagram_result = InstagramCrew().crew().kickoff(inputs={"instagram_username": instagram_handle})
                if hasattr(instagram_result, 'pydantic'):
                    instagram_json = instagram_result.pydantic.dict()
                    st.write("Instagram Data Preview:")
                    st.write(f"- First Name: {instagram_json.get('first_name', 'Not found')}")
                    st.write(f"- Number of values: {len(instagram_json.get('values', []))}")
            except Exception as e:
                st.write(f"Warning: Error analyzing Instagram content: {str(e)}")
                instagram_json = {}  # Reset to empty dict if failed
        
        # Status update
        st.write("\n=== Analysis Status ===")
        st.write(f"YouTube data available: {bool(youtube_json)}")
        st.write(f"Instagram data available: {bool(instagram_json)}")
        
        # If both analyses failed after attempting them, return empty model
        if youtube_handle and instagram_handle and not youtube_json and not instagram_json:
            st.write("All attempted analyses failed. Returning empty model.")
            return ContentCreatorInfo.create_empty()
        
        st.write("\n=== Merging Results ===")
        # Use whatever data we have
        merged_model = merge_and_validate_content(youtube_json, instagram_json)
        
        # Convert merged model to dict for RAG input
        st.write("\n=== Preparing RAG Input ===")
        merged_dict = merged_model.model_dump()
        
        # Print validation of merged data
        st.write(f"Number of values in merged data: {len(merged_dict.get('values', []))}")
        st.write(f"Number of life events in merged data: {len(merged_dict.get('life_events', []))}")
        
        # Convert to JSON string for RAG input
        merged_json = json.dumps(merged_dict)
        st.write("\n=== Passing to RAG Crew ===")
        
        # Pass to RAG Crew
        result_rag = RagCrew().crew().kickoff(inputs={"input_string": merged_json})
        st.write("\n=== RAG Processing Complete ===")
        
        return result_rag
        
    except ValueError as e:
        st.error(f"Validation error: {str(e)}")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        return None

def main():
    st.title("Creator Analysis Tool")
    
    with st.form("creator_analysis_form"):
        youtube_handle = st.text_input("YouTube Channel Handle (optional)")
        instagram_handle = st.text_input("Instagram Handle (optional)")
        analyze_button = st.form_submit_button("Analyze Creator")

    if analyze_button:
        if not youtube_handle and not instagram_handle:
            st.error("At least one handle (YouTube or Instagram) is required")
        else:
            result = run_analysis(youtube_handle, instagram_handle)
            
            if result is not None:
                # Display the results exactly as they are
                st.json(result.model_dump())

if __name__ == "__main__":
    main()
    
# def run_analysis(youtube_handle: Optional[str], instagram_handle: Optional[str]) -> Dict[str, Any]:
#     """
#     Runs the integrated analysis with robust error handling and proper input formatting for RAG.
#     """
#     if not youtube_handle and not instagram_handle:
#         st.error("At least one handle (YouTube or Instagram) is required")
#         return ContentCreatorInfo.create_empty()

#     youtube_json = {}
#     instagram_json = {}
    
#     progress_bar = st.progress(0)
#     status_text = st.empty()
    
#     # Try YouTube analysis if handle provided
#     if youtube_handle:
#         status_text.text("=== YouTube Analysis ===")
#         try:
#             youtube_result = YoutubeCrew().crew().kickoff(inputs={"youtube_channel_handle": youtube_handle})
#             if hasattr(youtube_result, 'pydantic'):
#                 youtube_json = youtube_result.pydantic.dict()
#                 with st.expander("YouTube Data Preview", expanded=True):
#                     st.write("YouTube Data Preview:")
#                     st.write(f"- First Name: {youtube_json.get('first_name', 'Not found')}")
#                     st.write(f"- Number of values: {len(youtube_json.get('values', []))}")
#         except Exception as e:
#             st.warning(f"Warning: Error analyzing YouTube content: {str(e)}")
#             youtube_json = {}
#         progress_bar.progress(0.4)
    
#     # Try Instagram analysis if handle provided
#     if instagram_handle:
#         status_text.text("=== Instagram Analysis ===")
#         try:
#             instagram_result = InstagramCrew().crew().kickoff(inputs={"instagram_username": instagram_handle})
#             if hasattr(instagram_result, 'pydantic'):
#                 instagram_json = instagram_result.pydantic.dict()
#                 with st.expander("Instagram Data Preview", expanded=True):
#                     st.write("Instagram Data Preview:")
#                     st.write(f"- First Name: {instagram_json.get('first_name', 'Not found')}")
#                     st.write(f"- Number of values: {len(instagram_json.get('values', []))}")
#         except Exception as e:
#             st.warning(f"Warning: Error analyzing Instagram content: {str(e)}")
#             instagram_json = {}
#         progress_bar.progress(0.7)
    
#     # Status update
#     status_text.text("=== Analysis Status ===")
#     st.write(f"YouTube data available: {bool(youtube_json)}")
#     st.write(f"Instagram data available: {bool(instagram_json)}")
    
#     # If both analyses failed after attempting them, return empty model
#     if youtube_handle and instagram_handle and not youtube_json and not instagram_json:
#         st.warning("All attempted analyses failed. Returning empty model.")
#         progress_bar.empty()
#         status_text.empty()
#         return ContentCreatorInfo.create_empty()
    
#     status_text.text("=== Merging Results ===")
#     merged_model = merge_and_validate_content(youtube_json, instagram_json)
#     merged_dict = merged_model.model_dump()
    
#     status_text.text("=== Preparing RAG Input ===")
#     # Convert to proper format for RAG input
#     input_for_rag = {"input_string": json.dumps(merged_dict)}
    
#     status_text.text("=== Passing to RAG Crew ===")
#     try:
#         result_rag = RagCrew().crew().kickoff(inputs=input_for_rag)
#         if result_rag is None:
#             st.error("RAG analysis failed to produce results")
#             return ContentCreatorInfo.create_empty()
#     except Exception as e:
#         st.error(f"Error in RAG processing: {str(e)}")
#         return ContentCreatorInfo.create_empty()
    
#     progress_bar.progress(1.0)
#     status_text.text("=== RAG Processing Complete ===")
    
#     # Clean up
#     status_text.empty()
#     progress_bar.empty()
    
#     return result_rag

# def main():
#     # Initialize session state
#     if 'analysis_history' not in st.session_state:
#         st.session_state.analysis_history = []
#     if 'last_run_time' not in st.session_state:
#         st.session_state.last_run_time = None

#     # Page configuration
#     st.set_page_config(page_title="Creator Analysis Tool", page_icon="🎯", layout="wide")
#     st.title("🎯 Creator Analysis Tool")
    
#     # Create input form
#     with st.form("creator_analysis_form"):
#         col1, col2 = st.columns(2)
        
#         with col1:
#             youtube_handle = st.text_input(
#                 "YouTube Channel Handle",
#                 placeholder="Enter YouTube handle (optional)",
#                 help="Enter the YouTube channel handle without the @ symbol"
#             )
        
#         with col2:
#             instagram_handle = st.text_input(
#                 "Instagram Handle",
#                 placeholder="Enter Instagram handle (optional)",
#                 help="Enter the Instagram username without the @ symbol"
#             )
        
#         analyze_button = st.form_submit_button("Analyze Creator", use_container_width=True)

#     # Handle form submission
#     if analyze_button:
#         if not youtube_handle and not instagram_handle:
#             st.warning("Please enter at least one handle (YouTube or Instagram)")
#         else:
#             with st.spinner("Analyzing creator content..."):
#                 result = run_analysis(youtube_handle, instagram_handle)
                
#                 if result and hasattr(result, 'pydantic'):
#                     try:
#                         # Store analysis record
#                         analysis_record = {
#                             "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#                             "youtube_handle": youtube_handle,
#                             "instagram_handle": instagram_handle,
#                             "execution_time": st.session_state.last_run_time
#                         }
#                         st.session_state.analysis_history.append(analysis_record)
                        
#                         # Show success message
#                         st.success(f"Analysis completed in {st.session_state.last_run_time:.2f} seconds!")
                        
#                         # Get result dictionary safely
#                         result_dict = result.pydantic.dict()
                        
#                         # Display results
#                         st.header("Analysis Results")
                        
#                         # Creator name
#                         st.subheader("Creator Information")
#                         st.write(f"**Name:** {result_dict.get('first_name', '')} {result_dict.get('last_name', '')}")
                        
#                         # Display sections
#                         sections = {
#                             'values': 'Core Values',
#                             'business': 'Business Details',
#                             'challenges': 'Challenges & Learnings',
#                             'achievements': 'Key Achievements',
#                             'life_events': 'Significant Life Events'
#                         }
                        
#                         for section, title in sections.items():
#                             data = result_dict.get(section)
#                             if data:
#                                 with st.expander(title, expanded=True):
#                                     if isinstance(data, list):
#                                         for item in data:
#                                             if section == 'values':
#                                                 st.markdown(f"##### {item['name']}")
#                                                 st.markdown(f"**Origin:** {item['origin']}")
#                                                 st.markdown(f"**Impact Today:** {item['impact_today']}")
#                                                 st.markdown("---")
#                                             elif section == 'challenges':
#                                                 st.markdown(f"**Challenge:** {item['description']}")
#                                                 st.markdown(f"**Learnings:** {item['learnings']}")
#                                                 st.markdown("---")
#                                             elif section == 'life_events':
#                                                 st.markdown(f"##### {item['name']}")
#                                                 st.markdown(item['description'])
#                                                 st.markdown("---")
#                                             else:
#                                                 st.markdown(f"- {item['description']}")
#                                     else:  # For business section
#                                         st.markdown(f"**{data['name']}**")
#                                         st.markdown(f"**Description:** {data['description']}")
#                                         st.markdown(f"**Genesis:** {data.get('genesis', 'Not available')}")
#                     except Exception as e:
#                         st.error(f"Error processing results: {str(e)}")
#                 else:
#                     st.error("Analysis failed to produce valid results")

#     # Display analysis history
#     if st.session_state.analysis_history:
#         st.header("Recent Analyses")
#         for analysis in reversed(st.session_state.analysis_history[-5:]):
#             with st.expander(f"Analysis from {analysis['timestamp']}", expanded=False):
#                 st.write(f"**YouTube Handle:** {analysis['youtube_handle'] or 'N/A'}")
#                 st.write(f"**Instagram Handle:** {analysis['instagram_handle'] or 'N/A'}")
#                 st.write(f"**Execution Time:** {analysis['execution_time']:.2f} seconds")
