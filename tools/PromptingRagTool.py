import ast
import json
import re

from typing import Type, List, Dict, Any, Union, Optional
from pydantic.v1 import BaseModel, Field
from crewai_tools.tools.base_tool import BaseTool
import openai
import os
import streamlit as st
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

# Update the _extract_content_creator_info method in PromptingRagTool
def _extract_content_creator_info(self, input_string: str) -> ContentCreatorInfo:
    """Extract ContentCreatorInfo using regex-based parsing with fallbacks."""
    try:
        cleaned_input = self._clean_input_string(input_string)

        # Try to extract all components
        try:
            life_events = self._extract_list_items(cleaned_input, "LifeEventObject")
            life_events_objects = [LifeEventObject(**item) for item in life_events] if life_events else [LifeEventObject.default()]
        except:
            life_events_objects = [LifeEventObject.default()]

        try:
            business_data = self._extract_business_object(cleaned_input)
            business_object = BusinessObject(**business_data) if business_data else BusinessObject.default()
        except:
            business_object = BusinessObject.default()

        try:
            values = self._extract_list_items(cleaned_input, "ValueObject")
            values_objects = [ValueObject(**item) for item in values] if values else [ValueObject.default()]
        except:
            values_objects = [ValueObject.default()]

        try:
            challenges = self._extract_list_items(cleaned_input, "ChallengeObject")
            challenges_objects = [ChallengeObject(**item) for item in challenges] if challenges else [ChallengeObject.default()]
        except:
            challenges_objects = [ChallengeObject.default()]

        try:
            achievements = self._extract_list_items(cleaned_input, "AchievementObject")
            achievements_objects = [AchievementObject(**item) for item in achievements] if achievements else [AchievementObject.default()]
        except:
            achievements_objects = [AchievementObject.default()]

        # Create ContentCreatorInfo with extracted or default values
        return ContentCreatorInfo(
            first_name=self._extract_field_value(cleaned_input, "first_name") or "",
            last_name=self._extract_field_value(cleaned_input, "last_name") or "",
            life_events=life_events_objects,
            business=business_object,
            values=values_objects,
            challenges=challenges_objects,
            achievements=achievements_objects
        )

    except Exception as e:
        # If everything fails, return default ContentCreatorInfo
        return ContentCreatorInfo.default()

DEFAULT_TEMPLATE = """[Persona]
Your name is Tony Jazz, and you are a man.

You are French and speak in the first person "I". 
You grew up on a small, quiet island called La Désirade, part of Guadeloupe. 
Life there was simple, with most people working in fishing or farming. 
From a young age, you found your passion in music, something that shaped your future.
you earned a degree in law. 
Your path started when you began to pursue music and creative work. 
You traveled between the Caribbean and France, splitting your time between the peaceful island and the more dynamic life in the Paris suburbs. 
Despite facing early setbacks, including struggling with jobs and finances, you kept pushing forward.
In 2008, you created a song in support of Barack Obama during his presidential campaign. 
In 2009, you were homeless, sleeping wherever you could. But through small jobs, including teaching guitar, you started to build your skills and connections.
You founded your own creative agency, "On Air," in 2010. But the journey wasn not smooth. 
You had to work hard to establish yourself, taking on many small projects and learning along the way. Slowly, your reputation grew, and so did your influence.
Today, you are much more than just a musician. You are a marketing strategist and an advocate for innovation. 
As the president of the Forum des Innovations de Bordeaux (FIB), you work with leaders like Alain Juppé to help young entrepreneurs and businesses in the region. 
You have been invited to speak at prestigious events like TEDx, the Young Leaders Summit at the White House, and the MEDays conference.
You have developed Money Boost, a comprehensive financial training program designed to help people achieve financial security, even on a tight budget.
You offer Access to free guides
Expert interviews and advice.
To continue selling this training, you have developed a [sales_process] where you engage directly with clients on Instagram to convince them to subscribe to a live session you organize.
To make the interactions on Instagram enjoyable with your clients, you personalize your messages by incorporating elements that define your personality, such as your [persona], [values].
Challenges you faced :
Growing up on a small island with limited opportunities.
Struggling in school and taking time to find your path.
Experiencing homelessness in 2009, which made survival your first priority.
Starting your career with small, low-paying jobs while trying to make a name for yourself.
Your achievements:
Founding your own creative agency, "On Air," in 2010.
Becoming a recognized marketing consultant and president of the Forum des Innovations de Bordeaux.
Speaking at top conferences like TEDx and MEDays.
Working closely with influential figures like Alain Juppé and contributing to regional innovation.
A self-made entrepreneur who overcame significant challenges.
You have become internationally recognized for your work in both creative fields and innovation.
You are humble and down-to-earth, staying true to your roots despite your achievements.
You actively support young entrepreneurs, helping them grow and succeed.
[values]
Value_1: Perseverance
Context: Use this value when sharing your personal journey or when talking about overcoming financial or personal challenges.
Description: Tony s story is about overcoming homelessness, financial struggles, and building multiple successful businesses. This journey illustrates resilience and determination, showing that anyone can rise from difficult situations to achieve great things.
Usage: Share your personal challenges and how perseverance helped you succeed, encouraging others to stay committed despite difficulties.
Value_2: Empowerment
Context: Use this value when offering your Money Boost program or speaking at public events.
Description: Through your Money Boost program, you empower participants to take control of their financial future, teaching them practical strategies to save, manage debt, and build wealth. You believe everyone has the potential to improve their financial situation.
-Usage: Share tools, strategies, and personal insights that empower clients to make informed financial decisions and improve their lives.
Value_3: Inclusiveness
Context: Use this value when discussing your financial education programs or interacting with diverse audiences.
Description: You provide accessible education and resources to people from all walks of life, whether they are just starting their financial journey or are experienced entrepreneurs. Your programs are designed to be easy to follow, ensuring that everyone can benefit.
Usage: Use simple, clear language in all your materials. Offer diverse formats like videos, interviews, and guides to make learning inclusive for everyone.
"""

class PromptingRagToolInput(BaseModel):
    """Input for PromptingRagTool."""
    input_string: str = Field(
        ..., 
        description="String containing the ContentCreatorInfo object representation"
    )
    template: str = Field(
        default=DEFAULT_TEMPLATE,
        description="The template to structure the output text"
    )


class PromptingRagToolOutput(BaseModel):
    """Output for PromptingRagTool."""
    text: str = Field(
        ..., description="The generated text following the template structure"
    )

class PromptingRagTool(BaseTool):
    name: str = "Prompting RAG Tool"
    description: str = (
        "Transforms ContentCreatorInfo into a persona-based text following "
        "a template structure using GPT-4-mini."
    )
    args_schema: Type[BaseModel] = PromptingRagToolInput
    return_schema: Type[BaseModel] = PromptingRagToolOutput


    def _extract_content_creator_info(self, input_string: str) -> ContentCreatorInfo:
        """Extract ContentCreatorInfo using robust parsing with proper validation."""
        try:
            cleaned_input = self._clean_input_string(input_string)
            
            # Initialize default objects
            extracted_data = {
                'first_name': "",
                'last_name': "",
                'life_events': [],
                'business': BusinessObject.default(),
                'values': [],
                'challenges': [],
                'achievements': []
            }

            # Extract basic fields
            extracted_data['first_name'] = self._extract_field_value(cleaned_input, 'first_name') or ""
            extracted_data['last_name'] = self._extract_field_value(cleaned_input, 'last_name') or ""

            # Extract and validate life events
            life_events_pattern = r'LifeEventObject\s*\(\s*name\s*=\s*["\']([^"\']*)["\'],\s*description\s*=\s*["\']([^"\']*)["\']'
            life_events_matches = re.finditer(life_events_pattern, cleaned_input, re.DOTALL)
            for match in life_events_matches:
                try:
                    event = LifeEventObject(
                        name=match.group(1).strip(),
                        description=match.group(2).strip()
                    )
                    extracted_data['life_events'].append(event)
                except Exception:
                    continue

            # Extract and validate business object
            business_pattern = r'BusinessObject\s*\(\s*name\s*=\s*["\']([^"\']*)["\'],\s*description\s*=\s*["\']([^"\']*)["\'],\s*genesis\s*=\s*["\']([^"\']*)["\']'
            business_match = re.search(business_pattern, cleaned_input, re.DOTALL)
            if business_match:
                try:
                    extracted_data['business'] = BusinessObject(
                        name=business_match.group(1).strip(),
                        description=business_match.group(2).strip(),
                        genesis=business_match.group(3).strip()
                    )
                except Exception:
                    pass

            # Extract and validate values
            values_pattern = r'ValueObject\s*\(\s*name\s*=\s*["\']([^"\']*)["\'],\s*origin\s*=\s*["\']([^"\']*)["\'],\s*impact_today\s*=\s*["\']([^"\']*)["\']'
            values_matches = re.finditer(values_pattern, cleaned_input, re.DOTALL)
            for match in values_matches:
                try:
                    value = ValueObject(
                        name=match.group(1).strip(),
                        origin=match.group(2).strip(),
                        impact_today=match.group(3).strip()
                    )
                    extracted_data['values'].append(value)
                except Exception:
                    continue

            # Extract and validate challenges
            challenges_pattern = r'ChallengeObject\s*\(\s*description\s*=\s*["\']([^"\']*)["\'],\s*learnings\s*=\s*["\']([^"\']*)["\']'
            challenges_matches = re.finditer(challenges_pattern, cleaned_input, re.DOTALL)
            for match in challenges_matches:
                try:
                    challenge = ChallengeObject(
                        description=match.group(1).strip(),
                        learnings=match.group(2).strip()
                    )
                    extracted_data['challenges'].append(challenge)
                except Exception:
                    continue

            # Extract and validate achievements
            achievements_pattern = r'AchievementObject\s*\(\s*description\s*=\s*["\']([^"\']*)["\']'
            achievements_matches = re.finditer(achievements_pattern, cleaned_input, re.DOTALL)
            for match in achievements_matches:
                try:
                    achievement = AchievementObject(
                        description=match.group(1).strip()
                    )
                    extracted_data['achievements'].append(achievement)
                except Exception:
                    continue

            # If no objects were found, use defaults
            if not extracted_data['life_events']:
                extracted_data['life_events'] = [LifeEventObject.default()]
            if not extracted_data['values']:
                extracted_data['values'] = [ValueObject.default()]
            if not extracted_data['challenges']:
                extracted_data['challenges'] = [ChallengeObject.default()]
            if not extracted_data['achievements']:
                extracted_data['achievements'] = [AchievementObject.default()]

            # Create and validate final ContentCreatorInfo object
            return ContentCreatorInfo(**extracted_data)

        except Exception as e:
            print(f"Error extracting content creator info: {str(e)}")
            return ContentCreatorInfo.default()


    def _extract_object(self, text: str, object_name: str, model_class: Type[BaseModel]) -> Union[Dict, List[Dict]]:
        """
        Generic function to extract any type of object or list of objects from text.
        
        Args:
            text: The input text to parse
            object_name: Name of the object to extract (e.g., "BusinessObject")
            model_class: The Pydantic model class for validation
        """
        try:
            # Check if it's a list of objects
            is_list = isinstance(model_class.__fields__.get('__root__', None), List)
            
            # Pattern for both single object and list of objects
            pattern = rf'{object_name}\s*\((.*?)\)'
            
            if is_list:
                # Extract all matches for lists
                matches = re.finditer(pattern, text, re.DOTALL)
                extracted_items = []
                
                for match in matches:
                    content = match.group(1)
                    item_dict = {}
                    
                    # Extract all fields defined in the model
                    for field_name, field in model_class.__fields__.items():
                        value = self._extract_field_value(content, field_name)
                        if value:  # Only add non-empty values
                            item_dict[field_name] = value
                    
                    if item_dict:  # Only add if we found any fields
                        extracted_items.append(item_dict)
                
                return extracted_items or [model_class.default().__dict__]
            else:
                # Extract single object
                match = re.search(pattern, text, re.DOTALL)
                if match:
                    content = match.group(1)
                    extracted_dict = {}
                    
                    # Extract all fields defined in the model
                    for field_name, field in model_class.__fields__.items():
                        value = self._extract_field_value(content, field_name)
                        if value:  # Only add non-empty values
                            extracted_dict[field_name] = value
                    
                    return extracted_dict or model_class.default().__dict__
                
                return model_class.default().__dict__
        except Exception as e:
            print(f"Error extracting {object_name}: {str(e)}")
            return model_class.default().__dict__

    def _extract_field_value(self, text: str, field_name: str) -> Optional[str]:
        """Extract field value with improved regex patterns."""
        try:
            patterns = [
                rf'{field_name}\s*=\s*"([^"]*)"',  # Double quotes
                rf"{field_name}\s*=\s*'([^']*)'",   # Single quotes
                rf'{field_name}\s*=\s*([^,\n\]}}]+)'  # No quotes
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.DOTALL)
                if match:
                    return match.group(1).strip()
            
            return None
        except Exception:
            return None

    def _extract_list_items(self, text: str, object_name: str) -> List[Dict]:
        """Extract items from a list of objects, return empty list if not found."""
        try:
            items = []
            pattern = rf'{object_name}\s*\((.*?)\)'
            matches = re.finditer(pattern, text, re.DOTALL)
            
            for match in matches:
                try:
                    item_dict = {}
                    content = match.group(1)
                    
                    # Extract fields based on object type
                    if object_name == "LifeEventObject":
                        item_dict["name"] = self._extract_field_value(content, "name")
                        item_dict["description"] = self._extract_field_value(content, "description")
                    elif object_name == "ValueObject":
                        item_dict["name"] = self._extract_field_value(content, "name")
                        item_dict["origin"] = self._extract_field_value(content, "origin")
                        item_dict["impact_today"] = self._extract_field_value(content, "impact_today")
                    elif object_name == "ChallengeObject":
                        item_dict["description"] = self._extract_field_value(content, "description")
                        item_dict["learnings"] = self._extract_field_value(content, "learnings")
                    elif object_name == "AchievementObject":
                        item_dict["description"] = self._extract_field_value(content, "description")
                    
                    if any(item_dict.values()):  # Only add if at least one field has a value
                        items.append(item_dict)
                except Exception:
                    continue  # Skip malformed items
                    
            return items
        except Exception:
            return []

    def _clean_input_string(self, input_string: str) -> str:
        """Clean and normalize the input string."""
        try:
            # Remove 'python' prefix if present
            input_string = re.sub(r'^python\s*', '', input_string)
            # Remove extra whitespace
            input_string = re.sub(r'\s+', ' ', input_string)
            # Remove escaped quotes
            input_string = input_string.replace('\\"', '"').replace("\\'", "'")
            # Remove extra closing parentheses
            input_string = re.sub(r'\)+$', ')', input_string)
            # Remove leading/trailing whitespace
            return input_string.strip()
        except Exception:
            return input_string

    def _run(self, **kwargs) -> dict:
        """Run the tool with the given inputs."""
        if not OPENAI_API_KEY:
        # if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable is not set")

        try:
            # Get the input string from kwargs
            input_string = kwargs.get('input_string', '')
            template = kwargs.get('template', DEFAULT_TEMPLATE)

            # If input_string is not provided, try to get it from the first positional argument
            if not input_string and len(kwargs) == 1:
                input_string = next(iter(kwargs.values()))

            if not input_string:
                return {"text": "No input provided"}

            # Extract ContentCreatorInfo from input string
            content_creator_info = self._extract_content_creator_info(input_string)

            creator_info_formatted = (
                f"Name: {content_creator_info.first_name} {content_creator_info.last_name}\n\n"
                f"Life Events:\n" + 
                "\n".join([f"- {event.name}: {event.description}" 
                          for event in content_creator_info.life_events]) + "\n\n"
                f"Business:\n"
                f"- Name: {content_creator_info.business.name}\n"
                f"- Description: {content_creator_info.business.description}\n"
                f"- Genesis: {content_creator_info.business.genesis}\n\n"
                f"Values:\n" +
                "\n".join([f"- {value.name}:\n  Origin: {value.origin}\n  Impact: {value.impact_today}" 
                          for value in content_creator_info.values]) + "\n\n"
                f"Challenges:\n" +
                "\n".join([f"- {challenge.description}:\n  Learnings: {challenge.learnings}" 
                          for challenge in content_creator_info.challenges]) + "\n\n"
                f"Achievements:\n" +
                "\n".join([f"- {achievement.description}" 
                          for achievement in content_creator_info.achievements])
            )

            system_prompt = """
            You are an expert in transforming creator information into persona-based narratives.
            Your task is to take the provided creator information and template, then generate 
            a new text that follows the same structure and style as the template but uses 
            the creator's information. Ensure you:
            1. Maintain a first-person perspective
            2. Derive the tone and style based on the creator's information
            3. Incorporate key details about the creator's journey, values, and achievements
            4. Create a cohesive narrative that flows naturally
            5. Keep similar length and structure as the template
            6. If the creator does not have an equivalent, do not mention it.
            7. Do NOT make up information.
            8. Do NOT use info from the template that is not in the creator's information.

            IMPORTANT: Write in the third person.
            IMPORTANT: Do not use the template as a starting point. Use the creator's information.
            IMPORTANT: Do not use info from the template that is not in the creator's information.
            IMPORTANT: Do not make up information.
            IMPORTANT: If the creator does not have an equivalent, do not mention it.
            IMPORTANT: The [life_events] section is a list of life events that the creator has lived through. Use it to personalize the [persona].
            IMPORTANT: The [achievements] section is a list of achievements that the creator has. Use it to personalize the [persona].
            IMPORTANT: The [business] section is the creator's business. Use it to personalize the [persona] section of the template.
            IMPORTANT: The [challenges] section is a list of challenges that the creator has faced. Use it to personalize the text.
            IMPORTANT: The [values] section is a list of values that the creator has. Use it to personalize the text.
            """

            user_prompt = f"""
            Template to follow:
            {template}

            Creator Information:
            {creator_info_formatted}

            Please transform this information into a new text that follows the template's 
            structure and style, but tells the creator's story. Keep the same type of story format, but adapt it to the creator's 
            actual experiences and journey.
            IMPORTANT: Write in the third person.
            IMPORTANT: Do not use the template as a starting point. Use the creator's information.
            IMPORTANT: Do not use info from the template that is not in the creator's information.
            IMPORTANT: Do not make up information.
            IMPORTANT: If the creator does not have an equivalent, do not mention it.
            IMPORTANT: The [life_events] section is a list of life events that the creator has lived through. Use it to personalize the [persona].
            IMPORTANT: The [achievements] section is a list of achievements that the creator has. Use it to personalize the [persona].
            IMPORTANT: The [business] section is the creator's business. Use it to personalize the [persona] section of the template.
            IMPORTANT: The [challenges] section is a list of challenges that the creator has faced. Use it to personalize the text.
            IMPORTANT: The [values] section is a list of values that the creator has. Use it to personalize the text.
            """

            try:
                response = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.6,
                    max_tokens=6000
                )

                generated_text = response.choices[0].message.content.strip()
                return {"text": generated_text}

            except Exception as e:
                return {"text": f"Error generating text with OpenAI: {str(e)}"}

        except Exception as e:
            return {"text": f"Error processing input: {str(e)}"}

    def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async version not implemented")
# import ast
# import json
# import re

# from typing import Type, List, Dict, Any, Union
# from pydantic.v1 import BaseModel, Field
# from crewai_tools.tools.base_tool import BaseTool
# import openai
# import os

# class LifeEventObject(BaseModel):
#     name: str
#     description: str

# class BusinessObject(BaseModel):
#     name: str
#     description: str
#     genesis: str

# class ValueObject(BaseModel):
#     name: str
#     origin: str
#     impact_today: str

# class ChallengeObject(BaseModel):
#     description: str
#     learnings: str

# class AchievementObject(BaseModel):
#     description: str

# class ContentCreatorInfo(BaseModel):
#     first_name: str
#     last_name: str
#     life_events: List[LifeEventObject]
#     business: BusinessObject
#     values: List[ValueObject]
#     challenges: List[ChallengeObject]
#     achievements: List[AchievementObject]

# DEFAULT_TEMPLATE = """[Persona]
# Your name is Tony Jazz, and you are a man.

# You are French and speak in the first person "I". 
# You grew up on a small, quiet island called La Désirade, part of Guadeloupe. 
# Life there was simple, with most people working in fishing or farming. 
# From a young age, you found your passion in music, something that shaped your future.
# you earned a degree in law. 
# Your path started when you began to pursue music and creative work. 
# You traveled between the Caribbean and France, splitting your time between the peaceful island and the more dynamic life in the Paris suburbs. 
# Despite facing early setbacks, including struggling with jobs and finances, you kept pushing forward.
# In 2008, you created a song in support of Barack Obama during his presidential campaign. 
# In 2009, you were homeless, sleeping wherever you could. But through small jobs, including teaching guitar, you started to build your skills and connections.
# You founded your own creative agency, "On Air," in 2010. But the journey wasn not smooth. 
# You had to work hard to establish yourself, taking on many small projects and learning along the way. Slowly, your reputation grew, and so did your influence.
# Today, you are much more than just a musician. You are a marketing strategist and an advocate for innovation. 
# As the president of the Forum des Innovations de Bordeaux (FIB), you work with leaders like Alain Juppé to help young entrepreneurs and businesses in the region. 
# You have been invited to speak at prestigious events like TEDx, the Young Leaders Summit at the White House, and the MEDays conference.
# You have developed Money Boost, a comprehensive financial training program designed to help people achieve financial security, even on a tight budget.
# You offer Access to free guides
# Expert interviews and advice.
# To continue selling this training, you have developed a [sales_process] where you engage directly with clients on Instagram to convince them to subscribe to a live session you organize.
# To make the interactions on Instagram enjoyable with your clients, you personalize your messages by incorporating elements that define your personality, such as your [persona], [values].
# Challenges you faced :
# Growing up on a small island with limited opportunities.
# Struggling in school and taking time to find your path.
# Experiencing homelessness in 2009, which made survival your first priority.
# Starting your career with small, low-paying jobs while trying to make a name for yourself.
# Your achievements:
# Founding your own creative agency, "On Air," in 2010.
# Becoming a recognized marketing consultant and president of the Forum des Innovations de Bordeaux.
# Speaking at top conferences like TEDx and MEDays.
# Working closely with influential figures like Alain Juppé and contributing to regional innovation.
# A self-made entrepreneur who overcame significant challenges.
# You have become internationally recognized for your work in both creative fields and innovation.
# You are humble and down-to-earth, staying true to your roots despite your achievements.
# You actively support young entrepreneurs, helping them grow and succeed.
# [values]
# Value_1: Perseverance
# Context: Use this value when sharing your personal journey or when talking about overcoming financial or personal challenges.
# Description: Tony s story is about overcoming homelessness, financial struggles, and building multiple successful businesses. This journey illustrates resilience and determination, showing that anyone can rise from difficult situations to achieve great things.
# Usage: Share your personal challenges and how perseverance helped you succeed, encouraging others to stay committed despite difficulties.
# Value_2: Empowerment
# Context: Use this value when offering your Money Boost program or speaking at public events.
# Description: Through your Money Boost program, you empower participants to take control of their financial future, teaching them practical strategies to save, manage debt, and build wealth. You believe everyone has the potential to improve their financial situation.
# -Usage: Share tools, strategies, and personal insights that empower clients to make informed financial decisions and improve their lives.
# Value_3: Inclusiveness
# Context: Use this value when discussing your financial education programs or interacting with diverse audiences.
# Description: You provide accessible education and resources to people from all walks of life, whether they are just starting their financial journey or are experienced entrepreneurs. Your programs are designed to be easy to follow, ensuring that everyone can benefit.
# Usage: Use simple, clear language in all your materials. Offer diverse formats like videos, interviews, and guides to make learning inclusive for everyone.
# """

# class PromptingRagToolInput(BaseModel):
#     """Input for PromptingRagTool."""
#     input_string: str = Field(
#         ..., 
#         description="String containing the ContentCreatorInfo object representation"
#     )
#     template: str = Field(
#         default=DEFAULT_TEMPLATE,
#         description="The template to structure the output text"
#     )

# class PromptingRagToolOutput(BaseModel):
#     """Output for PromptingRagTool."""
#     text: str = Field(
#         ..., description="The generated text following the template structure"
#     )

# class PromptingRagTool(BaseTool):
#     name: str = "Prompting RAG Tool"
#     description: str = (
#         "Transforms ContentCreatorInfo into a persona-based text following "
#         "a template structure using GPT-4-mini."
#     )
#     args_schema: Type[BaseModel] = PromptingRagToolInput
#     return_schema: Type[BaseModel] = PromptingRagToolOutput

#     def _extract_object_from_string(self, input_string: str) -> Dict:
#         """Extract nested object information from the string representation."""
#         def clean_string(s: str) -> str:
#             # Remove newlines and extra spaces
#             return ' '.join(s.split())

#         def extract_nested_objects(s: str) -> str:
#             # Replace LifeEventObject( with { and similar for other objects
#             s = re.sub(r'(\w+Object)\(', '{', s)
#             # Replace ContentCreatorInfo( with {
#             s = re.sub(r'ContentCreatorInfo\(', '{', s)
#             # Replace closing parentheses with }
#             s = re.sub(r'\)\s*(?=,|\s|$)', '}', s)
#             return s

#         try:
#             # Clean and prepare the string
#             cleaned = clean_string(input_string)
#             # Convert object notation to dictionary notation
#             dict_string = extract_nested_objects(cleaned)
#             # Evaluate the string to get a dictionary
#             result = ast.literal_eval(dict_string)
#             return result
#         except Exception as e:
#             raise ValueError(f"Failed to parse input string: {str(e)}")

#     def _run(self, input_string: str, template: str = DEFAULT_TEMPLATE) -> dict:
#         """Run the tool with the given inputs."""
#         if not os.getenv("OPENAI_API_KEY"):
#             raise ValueError("OPENAI_API_KEY environment variable is not set")

#         try:
#             # Extract data from input string
#             data_dict = self._extract_object_from_string(input_string)
            
#             # Convert to ContentCreatorInfo
#             content_creator_info = ContentCreatorInfo(
#                 first_name=data_dict.get('first_name', ''),
#                 last_name=data_dict.get('last_name', ''),
#                 life_events=[LifeEventObject(**event) for event in data_dict.get('life_events', [])],
#                 business=BusinessObject(**data_dict.get('business', {})),
#                 values=[ValueObject(**value) for value in data_dict.get('values', [])],
#                 challenges=[ChallengeObject(**challenge) for challenge in data_dict.get('challenges', [])],
#                 achievements=[AchievementObject(**achievement) for achievement in data_dict.get('achievements', [])]
#             )

#             system_prompt = """
#             You are an expert in transforming creator information into persona-based narratives.
#             Your task is to take the provided creator information and template, then generate 
#             a new text that follows the same structure and style as the template but uses 
#             the creator's information. Ensure you:
#             1. Maintain a first-person perspective
#             2. Derive the tone and style based on the creator's information
#             3. Incorporate key details about the creator's journey, values, and achievements
#             4. Create a cohesive narrative that flows naturally
#             5. Keep similar length and structure as the template
#             6. If the creator does not have an equivalent, do not mention it.
#             7. Do NOT make up information.
#             8. Do NOT use info from the template that is not in the creator's information.
#             """

#             creator_info_formatted = (
#                 f"Name: {content_creator_info.first_name} {content_creator_info.last_name}\n\n"
#                 f"Life Events:\n" + 
#                 "\n".join([f"- {event.name}: {event.description}" for event in content_creator_info.life_events]) + "\n\n"
#                 f"Business:\n"
#                 f"- Name: {content_creator_info.business.name}\n"
#                 f"- Description: {content_creator_info.business.description}\n"
#                 f"- Genesis: {content_creator_info.business.genesis}\n\n"
#                 f"Values:\n" +
#                 "\n".join([f"- {value.name}:\n  Origin: {value.origin}\n  Impact: {value.impact_today}" 
#                           for value in content_creator_info.values]) + "\n\n"
#                 f"Challenges:\n" +
#                 "\n".join([f"- {challenge.description}:\n  Learnings: {challenge.learnings}" 
#                           for challenge in content_creator_info.challenges]) + "\n\n"
#                 f"Achievements:\n" +
#                 "\n".join([f"- {achievement.description}" for achievement in content_creator_info.achievements])
#             )

#             user_prompt = f"""
#             Template to follow:
#             {template}

#             Creator Information:
#             {creator_info_formatted}

#             Please transform this information into a new text that follows the template's 
#             structure and style, but tells the creator's story. Keep the same type of story format, but adapt it to the creator's 
#             actual experiences and journey.
#             IMPORTANT: Write in the third person.
#             IMPORTANT: Do not use the template as a starting point. Use the creator's information.
#             IMPORTANT: Do not use info from the template that is not in the creator's information.
#             IMPORTANT: Do not make up information.
#             IMPORTANT: If the creator does not have an equivalent, do not mention it.
#             IMPORTANT: The [life_events] section is a list of life events that the creator has lived through. Use it to personalize the [persona].
#             IMPORTANT: The [achievements] section is a list of achievements that the creator has. Use it to personalize the [persona].
#             IMPORTANT: The [business] section is the creator's business. Use it to personalize the [persona] section of the template.
#             IMPORTANT: The [challenges] section is a list of challenges that the creator has faced. Use it to personalize the text.
#             IMPORTANT: The [values] section is a list of values that the creator has. Use it to personalize the text.
#             """

#             try:
#                 response = openai.chat.completions.create(
#                     model="gpt-4o-mini",
#                     messages=[
#                         {"role": "system", "content": system_prompt},
#                         {"role": "user", "content": user_prompt}
#                     ],
#                     temperature=0.6,
#                     max_tokens=6000
#                 )

#                 generated_text = response.choices[0].message.content.strip()
#                 return {"text": generated_text}

#             except Exception as e:
#                 raise Exception(f"Error generating text with OpenAI: {str(e)}")

#         except Exception as e:
#             raise Exception(f"Error in PromptingRagTool: {str(e)}")

#     def _arun(self, *args, **kwargs):
#         raise NotImplementedError("Async version not implemented")
# # class PromptingRagToolInput(BaseModel):
# #     input_data: str = Field(
# #         ..., 
# #         description="Raw input data that contains or represents the ContentCreatorInfo object. Can be a string, dictionary, or ContentCreatorInfo object."
# #     )
# #     # """Input for PromptingRagTool."""
# #     # input_data: Union[str, dict, ContentCreatorInfo] = Field(
# #     #     ..., 
# #     #     description="Raw input data that contains or represents the ContentCreatorInfo object. Can be a string, dictionary, or ContentCreatorInfo object."
# #     # )
# #     template: str = Field(
# #         default=DEFAULT_TEMPLATE,
# #         description="The template to structure the output text"
# #     )
# # # class PromptingRagToolInput(BaseModel):
# # #     """Input for PromptingRagTool."""
# # #     content_creator_info: ContentCreatorInfo = Field(
# # #         ..., description="The ContentCreatorInfo object containing creator's information"
# # #     )
# # #     template: str = Field(
# # #         default=DEFAULT_TEMPLATE,
# # #         description="The template to structure the output text"
# # #     )

# # class PromptingRagToolOutput(BaseModel):
# #     """Output for PromptingRagTool."""
# #     text: str = Field(
# #         ..., description="The generated text following the template structure"
# #     )

# # class PromptingRagTool(BaseTool):
# #     name: str = "Prompting RAG Tool"
# #     description: str = (
# #         "Transforms ContentCreatorInfo into a persona-based text following "
# #         "a template structure using GPT-4-mini."
# #     )
# #     args_schema: Type[BaseModel] = PromptingRagToolInput
# #     return_schema: Type[BaseModel] = PromptingRagToolOutput

# #     def _extract_content_creator_info(self, input_text: Union[str, dict, ContentCreatorInfo]) -> ContentCreatorInfo:

# #     # def _extract_content_creator_info(self, input_text: str) -> ContentCreatorInfo:
# #         """
# #         Extracts ContentCreatorInfo from input text using multiple fallback methods.
# #         """
# #         def clean_text(text: str) -> str:
# #             # Remove any non-printable characters and normalize whitespace
# #             text = re.sub(r'\s+', ' ', text)
# #             return text.strip()

# #         def extract_dict_string(text: str) -> str:
# #             # Look for dictionary-like structure
# #             dict_pattern = r'ContentCreatorInfo\s*\((.*?)\)'
# #             match = re.search(dict_pattern, text, re.DOTALL)
# #             if match:
# #                 return match.group(1)
# #             return text

# #         def parse_dict_string(text: str) -> dict:
# #             # Clean up the text
# #             text = clean_text(text)
# #             text = extract_dict_string(text)
            
# #             # Multiple parsing attempts
# #             try:
# #                 # Try direct ast.literal_eval first
# #                 return ast.literal_eval(text)
# #             except:
# #                 try:
# #                     # Try parsing as JSON
# #                     return json.loads(text)
# #                 except:
# #                     # Try extracting key-value pairs manually
# #                     pairs = {}
# #                     # Match patterns like "key=value" or "key: value"
# #                     pattern = r'(\w+)\s*[=:]\s*([^,\n]+)'
# #                     matches = re.findall(pattern, text)
# #                     for key, value in matches:
# #                         # Clean up the value
# #                         value = value.strip()
# #                         # Handle lists
# #                         if value.startswith('[') and value.endswith(']'):
# #                             try:
# #                                 pairs[key] = ast.literal_eval(value)
# #                             except:
# #                                 pairs[key] = value
# #                         else:
# #                             pairs[key] = value
# #                     return pairs

# #         def convert_to_content_creator_info(data: dict) -> ContentCreatorInfo:
# #             """Converts dictionary to ContentCreatorInfo with proper nested objects"""
# #             try:
# #                 # Handle life events
# #                 if 'life_events' in data:
# #                     life_events = []
# #                     for event in data['life_events']:
# #                         if isinstance(event, dict):
# #                             life_events.append(LifeEventObject(**event))
# #                         elif isinstance(event, str):
# #                             # Try to parse string as dict
# #                             try:
# #                                 event_dict = ast.literal_eval(event)
# #                                 life_events.append(LifeEventObject(**event_dict))
# #                             except:
# #                                 continue
# #                     data['life_events'] = life_events

# #                 # Handle business
# #                 if 'business' in data and isinstance(data['business'], dict):
# #                     data['business'] = BusinessObject(**data['business'])

# #                 # Handle values
# #                 if 'values' in data:
# #                     values = []
# #                     for value in data['values']:
# #                         if isinstance(value, dict):
# #                             values.append(ValueObject(**value))
# #                     data['values'] = values

# #                 # Handle challenges
# #                 if 'challenges' in data:
# #                     challenges = []
# #                     for challenge in data['challenges']:
# #                         if isinstance(challenge, dict):
# #                             challenges.append(ChallengeObject(**challenge))
# #                     data['challenges'] = challenges

# #                 # Handle achievements
# #                 if 'achievements' in data:
# #                     achievements = []
# #                     for achievement in data['achievements']:
# #                         if isinstance(achievement, dict):
# #                             achievements.append(AchievementObject(**achievement))
# #                     data['achievements'] = achievements

# #                 return ContentCreatorInfo(**data)
# #             except Exception as e:
# #                 raise ValueError(f"Failed to convert to ContentCreatorInfo: {str(e)}")

# #         try:
# #             # If input is already a ContentCreatorInfo object
# #             if isinstance(input_text, ContentCreatorInfo):
# #                 return input_text

# #             # If input is a dictionary
# #             if isinstance(input_text, dict):
# #                 return convert_to_content_creator_info(input_text)

# #             # If input is a string, try to parse it
# #             cleaned_text = clean_text(input_text)
# #             data_dict = parse_dict_string(cleaned_text)
# #             return convert_to_content_creator_info(data_dict)

# #         except Exception as e:
# #             raise ValueError(f"Failed to extract ContentCreatorInfo: {str(e)}")

# #     def _run(self, input_data: str, template: str = DEFAULT_TEMPLATE) -> dict:

# #     # def _run(self, input_data: Any, template: str = DEFAULT_TEMPLATE) -> dict:
# #         """Run the tool with the given inputs."""
# #         if not os.getenv("OPENAI_API_KEY"):
# #             raise ValueError("OPENAI_API_KEY environment variable is not set")
# #     # def _run(self, content_creator_info, template: str = DEFAULT_TEMPLATE) -> dict:
# #     #     """Run the tool with the given inputs."""
# #     #     if not os.getenv("OPENAI_API_KEY"):
# #     #         raise ValueError("OPENAI_API_KEY environment variable is not set")

# #         # Handle the input based on its type
# #         if isinstance(input_data, dict):
# #             try:
# #                 input_data = self._extract_content_creator_info(input_data)
# #                 # content_creator_info = self._extract_content_creator_info(input_data)
# #                 # content_creator_info = ContentCreatorInfo(**content_creator_info)
# #             except Exception as e:
# #                 raise ValueError(f"Invalid content_creator_info format: {str(e)}")
# #         elif isinstance(input_data, str):
# #             try:
# #                 # Try to evaluate the string as a dict if it's a string representation
# #                 import ast
# #                 input_data_dict = ast.literal_eval(input_data)
# #                 input_data = ContentCreatorInfo(**input_data_dict)
# #             except Exception as e:
# #                 raise ValueError(f"Could not parse content_creator_info string: {str(e)}")
# #         elif not isinstance(input_data, ContentCreatorInfo):
# #             raise ValueError("input_data must be a ContentCreatorInfo object, dict, or valid string representation")

# #         system_prompt = """
# #         You are an expert in transforming creator information into persona-based narratives.
# #         Your task is to take the provided creator information and template, then generate 
# #         a new text that follows the same structure and style as the template but uses 
# #         the creator's information. Ensure you:
# #         1. Maintain a first-person perspective
# #         2. Derive the tone and style based on the creator's information
# #         3. Incorporate key details about the creator's journey, values, and achievements
# #         4. Create a cohesive narrative that flows naturally
# #         5. Keep similar length and structure as the template
# #         6. If the creator does not have an equivalent, do not mention it.
# #         7. Do NOT make up information.
# #         8. Do NOT use info from the template that is not in the creator's information.
# #         """

# #         creator_info_formatted = (
# #             f"Name: {input_data.first_name} {input_data.last_name}\n\n"
# #             f"Life Events:\n" + 
# #             "\n".join([f"- {event.name}: {event.description}" for event in input_data.life_events]) + "\n\n"
# #             f"Business:\n"
# #             f"- Name: {input_data.business.name}\n"
# #             f"- Description: {input_data.business.description}\n"
# #             f"- Genesis: {input_data.business.genesis}\n\n"
# #             f"Values:\n" +
# #             "\n".join([f"- {value.name}:\n  Origin: {value.origin}\n  Impact: {value.impact_today}" 
# #                         for value in input_data.values]) + "\n\n"
# #             f"Challenges:\n" +
# #             "\n".join([f"- {challenge.description}:\n  Learnings: {challenge.learnings}" 
# #                         for challenge in input_data.challenges]) + "\n\n"
# #             f"Achievements:\n" +
# #             "\n".join([f"- {achievement.description}" for achievement in input_data.achievements])
# #         )
# #         # creator_info_formatted = (
# #         #     f"Name: {content_creator_info.first_name} {content_creator_info.last_name}\n\n"
# #         #     f"Life Events:\n" + 
# #         #     "\n".join([f"- {event.name}: {event.description}" for event in content_creator_info.life_events]) + "\n\n"
# #         #     f"Business:\n"
# #         #     f"- Name: {content_creator_info.business.name}\n"
# #         #     f"- Description: {content_creator_info.business.description}\n"
# #         #     f"- Genesis: {content_creator_info.business.genesis}\n\n"
# #         #     f"Values:\n" +
# #         #     "\n".join([f"- {value.name}:\n  Origin: {value.origin}\n  Impact: {value.impact_today}" 
# #         #               for value in content_creator_info.values]) + "\n\n"
# #         #     f"Challenges:\n" +
# #         #     "\n".join([f"- {challenge.description}:\n  Learnings: {challenge.learnings}" 
# #         #               for challenge in content_creator_info.challenges]) + "\n\n"
# #         #     f"Achievements:\n" +
# #         #     "\n".join([f"- {achievement.description}" for achievement in content_creator_info.achievements])
# #         # )

# #         user_prompt = f"""
# #         Template to follow:
# #         {template}

# #         Creator Information:
# #         {creator_info_formatted}

# #         Please transform this information into a new text that follows the template's 
# #         structure and style, but tells the creator's story. Keep the same type of story format, but adapt it to the creator's 
# #         actual experiences and journey.
# #         IMPORTANT: Write in the third person.
# #         IMPORTANT: Do not use the template as a starting point. Use the creator's information.
# #         IMPORTANT: Do not use info from the template that is not in the creator's information.
# #         IMPORTANT: Do not make up information.
# #         IMPORTANT: If the creator does not have an equivalent, do not mention it.
# #         IMPORTANT: The [life_events] section is a list of life events that the creator has lived through. Use it to personalize the [persona].
# #         IMPORTANT: The [achievements] section is a list of achievements that the creator has. Use it to personalize the [persona].
# #         IMPORTANT: The [business] section is the creator's business. Use it to personalize the [persona] section of the template.
# #         IMPORTANT: The [challenges] section is a list of challenges that the creator has faced. Use it to personalize the text.
# #         IMPORTANT: The [values] section is a list of values that the creator has. Use it to personalize the text.
# #         """

# #         try:
# #             response = openai.chat.completions.create(
# #                 model="gpt-4o-mini",
# #                 messages=[
# #                     {"role": "system", "content": system_prompt},
# #                     {"role": "user", "content": user_prompt}
# #                 ],
# #                 temperature=0.6,
# #                 max_tokens=6000
# #             )

# #             generated_text = response.choices[0].message.content.strip()
# #             return {"text": generated_text}

# #         except Exception as e:
# #             raise Exception(f"Error generating text with OpenAI: {str(e)}")

# #     def _arun(self, *args, **kwargs):
# #         raise NotImplementedError("Async version not implemented")
# # class PromptingRagTool(BaseTool):
# #     name: str = "Prompting RAG Tool"
# #     description: str = (
# #         "Transforms ContentCreatorInfo into a persona-based text following "
# #         "a template structure using GPT-4-mini."
# #     )
# #     args_schema: Type[BaseModel] = PromptingRagToolInput
# #     return_schema: Type[BaseModel] = PromptingRagToolOutput

# #     def _run(self, tool_input: Dict[str, Any], *args, **kwargs) -> dict:
# #         # Extract and validate inputs from the dictionary
# #         validated_input = PromptingRagToolInput(**tool_input)
# #         content_creator_info = validated_input.content_creator_info
# #         template = validated_input.template

# #         if not os.getenv("OPENAI_API_KEY"):
# #             raise ValueError("OPENAI_API_KEY environment variable is not set")

# #         system_prompt = """
# #         You are an expert in transforming creator information into persona-based narratives.
# #         Your task is to take the provided creator information and template, then generate 
# #         a new text that follows the same structure and style as the template but uses 
# #         the creator's information. Ensure you:
# #         1. Maintain a first-person perspective
# #         2. Derive the tone and style based on the creator's information
# #         3. Incorporate key details about the creator's journey, values, and achievements
# #         4. Create a cohesive narrative that flows naturally
# #         5. Keep similar length and structure as the template
# #         6. If the creator does not have an equivalent, do not mention it.
# #         7. Do NOT make up information.
# #         8. Do NOT use info from the template that is not in the creator's information.
# #         """

# #         creator_info_formatted = (
# #             f"Name: {content_creator_info.first_name} {content_creator_info.last_name}\n\n"
# #             f"Life Events:\n" + 
# #             "\n".join([f"- {event.name}: {event.description}" for event in content_creator_info.life_events]) + "\n\n"
# #             f"Business:\n"
# #             f"- Name: {content_creator_info.business.name}\n"
# #             f"- Description: {content_creator_info.business.description}\n"
# #             f"- Genesis: {content_creator_info.business.genesis}\n\n"
# #             f"Values:\n" +
# #             "\n".join([f"- {value.name}:\n  Origin: {value.origin}\n  Impact: {value.impact_today}" 
# #                       for value in content_creator_info.values]) + "\n\n"
# #             f"Challenges:\n" +
# #             "\n".join([f"- {challenge.description}:\n  Learnings: {challenge.learnings}" 
# #                       for challenge in content_creator_info.challenges]) + "\n\n"
# #             f"Achievements:\n" +
# #             "\n".join([f"- {achievement.description}" for achievement in content_creator_info.achievements])
# #         )

# #         user_prompt = f"""
# #         Template to follow:
# #         {template}

# #         Creator Information:
# #         {creator_info_formatted}

# #         Please transform this information into a new text that follows the template's 
# #         structure and style, but tells the creator's story. Keep the same type of 
# #         personal introduction and background story format, but adapt it to the creator's 
# #         actual experiences and journey.
# #         IMPORTANT: Do not use the template as a starting point. Use the creator's information.
# #         IMPORTANT: Do not use info from the template that is not in the creator's information.
# #         IMPORTANT: Do not make up information.
# #         IMPORTANT: If the creator does not have an equivalent, do not mention it.
# #         IMPORTANT: The [life_events] section is a list of life events that the creator has lived through. Use it to personalize the [persona].
# #         IMPORTANT: The [achievements] section is a list of achievements that the creator has. Use it to personalize the [persona].
# #         IMPORTANT: The [business] section is the creator's business. Use it to personalize the [persona] section of the template.
# #         IMPORTANT: The [challenges] section is a list of challenges that the creator has faced. Use it to personalize the text.
# #         IMPORTANT: The [values] section is a list of values that the creator has. Use it to personalize the text.
        
# #         """

# #         try:
# #             response = openai.chat.completions.create(
# #                 model="gpt-4o-mini",
# #                 messages=[
# #                     {"role": "system", "content": system_prompt},
# #                     {"role": "user", "content": user_prompt}
# #                 ],
# #                 temperature=0.6,
# #                 max_tokens=6000
# #             )

# #             generated_text = response.choices[0].message.content.strip()
# #             return {"text": generated_text}

# #         except Exception as e:
# #             raise Exception(f"Error generating text with OpenAI: {str(e)}")

# #     def _arun(self, *args, **kwargs):
# #         raise NotImplementedError("Async version not implemented")