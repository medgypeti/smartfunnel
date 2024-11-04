#!/usr/bin/env python
import sys
import json
# from smartfunnel.crew import LatestAiDevelopmentCrew
from smartfunnel.crew_instagram import InstagramCrew
import streamlit as st

from pydantic import BaseModel, Field
from typing import List, Optional

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
            for field in self.__fields__:
                new_value = getattr(new_info, field)
                if new_value is not None:
                    if isinstance(new_value, list):
                        current_value = getattr(self, field, [])
                        current_value.extend(new_value)
                        setattr(self, field, current_value)
                    else:
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

def run():
    """
    Ask for YouTube and Instagram handles and process them.
    """
    try:
        instagram_username = input("Please enter the Instagram username to analyze:\n").strip()
        
        inputs = {
            "instagram_username": instagram_username
        }
        
        # Run the crew
        result = InstagramCrew().crew().kickoff(inputs=inputs)
        
        # Save output to markdown
        save_output_to_markdown(result)
        print(result.tasks_output)
        print(result.pydantic)
        
        # Check and print the pydantic model
        if isinstance(result.pydantic, ContentCreatorInfo):
            populated_info = result.pydantic
            print(populated_info)
        else:
            print("Unexpected output type")
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run()

# def run():
#     """
#     Ask for YouTube and Instagram handles and process them.
#     """
#     try:
#         # youtube_channel_handle = input("Please enter the YouTube handle to analyze:\n").strip()
#         instagram_username = input("Please enter the Instagram username to analyze:\n").strip()
        
#         # Create inputs dictionary with proper string values (not sets)
#         inputs = {
#             # "youtube_channel_handle": youtube_channel_handle
#             "instagram_username": instagram_username  # Remove the set creation
#         }
        
#         # Run the crew
#         crew_output = InstagramCrew().crew().kickoff(inputs=inputs)
        
#         save_output_to_markdown(crew_output)

#         # Save and print output
#         # if save_output_to_markdown(crew_output):
#         #     print("\nOutput has been saved to creatorOutput.md")
#         # print_output(crew_output)

#         # Collect outputs from all tasks
#         all_outputs = []
#         for task_output in crew_output.tasks_output:
#             if task_output.pydantic:
#                 all_outputs.append(task_output.pydantic)

#         # Combine the outputs into a single ContentCreatorInfo object
#         consolidated_info = ContentCreatorInfo.default()
#         for output in all_outputs:
#             # Assuming ContentCreatorInfo has methods to update its fields
#             consolidated_info.update(output)
#         # Now consolidated_info contains information from all tasks
#         print("--------------------------------")
#         print("--------------------------------")
#         print(consolidated_info)
#         print("--------------------------------")
#         print("--------------------------------")
        
#     except Exception as e:
#         print(f"An error occurred: {str(e)}")
#         sys.exit(1)

# if __name__ == "__main__":
#     run()
