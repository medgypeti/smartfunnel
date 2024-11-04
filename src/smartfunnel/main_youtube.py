#!/usr/bin/env python
import sys
import json
# from smartfunnel.crew import LatestAiDevelopmentCrew
import streamlit as st

from pydantic import BaseModel, Field
from typing import List, Optional

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
from smartfunnel.crew_youtube import YoutubeCrew

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
    life_events: Optional[List[LifeEventObject]] = Field(default_factory=list)
    business: Optional[BusinessObject] = None
    values: Optional[List[ValueObject]] = Field(default_factory=list)
    challenges: Optional[List[ChallengeObject]] = Field(default_factory=list)
    achievements: Optional[List[AchievementObject]] = Field(default_factory=list)
    first_name: Optional[str] = None
    last_name: Optional[str] = None

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
    
    def update(self, new_info):
        if isinstance(new_info, ContentCreatorInfo):
                        setattr(self, field, new_value)
        else:
            # Handle updating from other types of objects if needed
            pass


    
def save_output_to_markdown(crew_output, filename="creatorOutput.md"):
    """
    Save crew output to a markdown file with proper error handling.
    """
    try:
        with open(filename, "w", encoding="utf-8") as md_file:
            md_file.write("# Creator Analysis Output\n\n")
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

# def run():
#     """
#     Ask for YouTube and Instagram handles and process them.
#     """
#     try:
#         youtube_channel_handle = input("Please enter the YouTube channel handle to analyze:\n").strip()
        
#         inputs = {
#             "youtube_channel_handle": youtube_channel_handle
#         }
        
#         # Run the crew
#         result = YoutubeCrew().crew().kickoff(inputs=inputs)
        
#         # Save output to markdown
#         save_output_to_markdown(result)
#         print(result.tasks_output)
#         print("--------------------------------")
#         print(result.pydantic)
#         print("--------------------------------")
        
#         # Check and print the pydantic model
#         if isinstance(result.pydantic, ContentCreatorInfo):
#             populated_info = result.pydantic
#             print(populated_info)
#         else:
#             print("Unexpected output type")
            
#     except Exception as e:
#         print(f"An error occurred: {str(e)}")
#         sys.exit(1)

# if __name__ == "__main__":
#     run()


# ----------------------------------------------------------------------

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

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

instagram_info = """{"life_events":[{"name":"Childhood Bullying and Physical Assault","description":"During his school years, the author faced significant challenges including bullying and physical assault. One particularly traumatic incident involved a group of boys attacking him in the schoolyard, resulting in Elon being thrown down a concrete staircase, losing consciousness, and requiring urgent medical attention."},{"name":"Passion for Reading and Learning","description":""},{"name":"Family Dynamics and Parental Influence","description":""}],"business":{"name":"Antoine's Business","description":"Antoine's business utilizes a value-driven approach that emphasizes offering free resources to attract potential clients, leveraging technology and automation to enhance lead conversion, and executing a cross-channel marketing strategy to engage a broad audience. The business focuses on utilizing AI for initial client interactions and employing various sales channels to optimize conversion rates.","genesis":"The business was launched following an existential crisis that prompted Antoine to seek purpose through technological advancement. This realization of technology's potential to expand human consciousness inspired him to create a business that aligns with these values."},"values":[{"name":"Engagement","origin":"The author values audience engagement and actively seeks interaction.","impact_today":"Encourages audience interaction by offering valuable resources, fostering a sense of community."},{"name":"Transparency","origin":"The author builds trust by providing free, valuable resources.","impact_today":"Establishes credibility and trust among viewers by sharing knowledge openly."},{"name":"Efficiency","origin":"The author effectively uses automation and AI to enhance communication and conversion.","impact_today":"Improves conversion rates and ensures timely communication with prospects."},{"name":"Clear Communication","origin":"The author uses clear and direct calls to action to guide viewers.","impact_today":"Simplifies the process for viewers, making it easy for them to take the next step."},{"name":"Resilience","origin":"The author overcame significant challenges during childhood, including bullying.","impact_today":"Uses personal adversity as a catalyst for growth and motivation in his endeavors."},{"name":"Visionary Thinking","origin":"The author's fascination with technology and space was influenced by early reading habits.","impact_today":"Aims to push the boundaries of technology and create innovative solutions."},{"name":"Pursuit of Knowledge","origin":"The author experienced an existential crisis and seeks to advance human knowledge.","impact_today":"Focuses on projects that contribute to the broader advancement of human understanding."}],"challenges":[{"description":"During his school years, the author faced significant challenges including bullying and physical assault. One particularly traumatic incident involved a group of boys attacking him in the schoolyard, resulting in Elon being thrown down a concrete staircase, losing consciousness, and requiring urgent medical attention.","learnings":"When faced with adversity, channel your energy into a passion or hobby that provides solace and growth. Reading and learning can be powerful tools to overcome psychological challenges and broaden your perspective. Use difficult experiences as motivation to pursue your dreams and interests with greater determination."},{"description":"Elon Musk experienced a slight existential crisis, questioning the purpose of life and the meaning of things. This introspection led him to a profound realization about the role of advancing knowledge and technology.","learnings":"Embrace existential questions; they can lead to meaningful insights and motivations. Focus on projects and goals that contribute to the collective understanding and capabilities of humanity. Use your skills and resources to create solutions that address fundamental human challenges and improve quality of life."}],"achievements":[{"description":"Advancing Technology Beyond Imagination: The protagonist has made significant strides in advancing technology to a level that would have been considered magic in the past. This realization drives their ambition to push the boundaries of technology further."},{"description":"Business Growth and Strategy: The protagonist has successfully implemented strategies to significantly increase business revenue, potentially by 30% within a few weeks by applying specific business strategies."}],"first_name":"Elon","last_name":"Musk"}"""

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

def run():
    """
    Process YouTube and Instagram content and merge them.
    """
    try:
        # Get YouTube handle
        youtube_channel_handle = input("Please enter the YouTube channel handle to analyze:\n").strip()
        
        if not youtube_channel_handle:
            raise ValueError("YouTube channel handle cannot be empty")
            
        inputs = {
            "youtube_channel_handle": youtube_channel_handle
        }
        
        # Run the crew
        crew_result = YoutubeCrew().crew().kickoff(inputs=inputs)
        
        # Save output to markdown (keep your existing functionality)
        # save_output_to_markdown(crew_result)
        
        # Merge and validate content
        merged_model = merge_and_validate_content(crew_result, instagram_info)
        save_output_to_markdown(merged_model)
        
        # Print the merged model
        print("\nMerged Content Creator Info:")
        print(merged_model.json(indent=2))
        
        return merged_model
        
    except ValueError as e:
        print(f"Validation error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run()
