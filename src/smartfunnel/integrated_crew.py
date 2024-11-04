#!/usr/bin/env python
import sys
import json
import streamlit as st
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from smartfunnel.crew_youtube import YoutubeCrew
from smartfunnel.crew_instagram import InstagramCrew
from smartfunnel.crew_rag import RagCrew

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

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

def run():
    """
    Run the integrated crew analysis with comprehensive error handling.
    """
    try:
        # Get handles upfront - now optional
        youtube_channel_handle = input("Please enter the YouTube channel handle to analyze (or press Enter to skip):\n").strip()
        instagram_username = input("Please enter the Instagram handle to analyze (or press Enter to skip):\n").strip()
        
        # Make sure at least one handle is provided
        if not youtube_channel_handle and not instagram_username:
            raise ValueError("At least one handle (YouTube or Instagram) is required")
        
        # Initialize variables
        youtube_json = {}
        instagram_json = {}
        
        # Try YouTube analysis if handle provided
        if youtube_channel_handle:
            print("\n=== YouTube Analysis ===")
            try:
                youtube_result = YoutubeCrew().crew().kickoff(inputs={"youtube_channel_handle": youtube_channel_handle})
                if hasattr(youtube_result, 'pydantic'):
                    youtube_json = youtube_result.pydantic.dict()
                    print("YouTube Data Preview:")
                    print(f"- First Name: {youtube_json.get('first_name', 'Not found')}")
                    print(f"- Number of values: {len(youtube_json.get('values', []))}")
            except Exception as e:
                print(f"Warning: Error analyzing YouTube content: {str(e)}")
                youtube_json = {}  # Reset to empty dict if failed
        
        # Try Instagram analysis if handle provided
        if instagram_username:
            print("\n=== Instagram Analysis ===")
            try:
                instagram_result = InstagramCrew().crew().kickoff(inputs={"instagram_username": instagram_username})
                if hasattr(instagram_result, 'pydantic'):
                    instagram_json = instagram_result.pydantic.dict()
                    print("Instagram Data Preview:")
                    print(f"- First Name: {instagram_json.get('first_name', 'Not found')}")
                    print(f"- Number of values: {len(instagram_json.get('values', []))}")
            except Exception as e:
                print(f"Warning: Error analyzing Instagram content: {str(e)}")
                instagram_json = {}  # Reset to empty dict if failed
        
        # Status update
        print("\n=== Analysis Status ===")
        print(f"YouTube data available: {bool(youtube_json)}")
        print(f"Instagram data available: {bool(instagram_json)}")
        
        # If both analyses failed after attempting them, return empty model
        if youtube_channel_handle and instagram_username and not youtube_json and not instagram_json:
            print("All attempted analyses failed. Returning empty model.")
            return ContentCreatorInfo.create_empty()
        
        print("\n=== Merging Results ===")
        # Use whatever data we have
        merged_model = merge_and_validate_content(youtube_json, instagram_json)
        
        # Convert merged model to dict for RAG input
        print("\n=== Preparing RAG Input ===")
        merged_dict = merged_model.model_dump()
        
        # Print validation of merged data
        print(f"Number of values in merged data: {len(merged_dict.get('values', []))}")
        print(f"Number of life events in merged data: {len(merged_dict.get('life_events', []))}")
        
        # Convert to JSON string for RAG input
        merged_json = json.dumps(merged_dict)
        print("\n=== Passing to RAG Crew ===")
        
        # Pass to RAG Crew
        result_rag = RagCrew().crew().kickoff(inputs={"input_string": merged_json})
        print("\n=== RAG Processing Complete ===")
        
        return result_rag
        
    except ValueError as e:
        print(f"Validation error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run()