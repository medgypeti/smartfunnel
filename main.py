#!/usr/bin/env python
import sys
import json
from smartfunnel.crew import LatestAiDevelopmentCrew

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

def print_output(crew_output):
    print(f"Raw Output: {crew_output.raw}")
    print(f"Pydantic Output: {crew_output.pydantic}")
    print(f"Tasks Output: {crew_output.tasks_output}")
    print(f"Token Usage: {crew_output.token_usage}")

def run():
    """
    Ask for YouTube and Instagram handles and process them.
    """
    try:
        youtube_channel_handle = input("Please enter the YouTube handle to analyze:\n").strip()
        instagram_username = input("Please enter the Instagram Username to analyze:\n").strip()
        
        # Create inputs dictionary with proper string values (not sets)
        inputs = {
            "youtube_channel_handle": youtube_channel_handle,
            "instagram_username": instagram_username  # Remove the set creation
        }
        
        # Run the crew
        crew_output = LatestAiDevelopmentCrew().crew().kickoff(inputs=inputs)
        
        # Save and print output
        if save_output_to_markdown(crew_output):
            print("\nOutput has been saved to creatorOutput.md")
        print_output(crew_output)
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run()

