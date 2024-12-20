import streamlit as st
import sys
import json
from smartfunnel.crew import LatestAiDevelopmentCrew

def validate_password(password):
    """
    Validate password against stored secret
    """
    try:
        return password == st.secrets["Answer"]
    except Exception as e:
        st.error("Error accessing secrets. Make sure secrets.toml is properly configured.")
        return False

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
        st.error(f"Error saving to markdown file: {str(e)}")
        return False

def generate_markdown_content(crew_output):
    """
    Generate markdown content from crew output
    """
    content = "# Creator Analysis Output\n\n"
    content += f"## Raw Output\n\n```\n{crew_output.raw}\n```\n\n"
    
    if crew_output.json_dict:
        content += f"## JSON Output\n\n```json\n{json.dumps(crew_output.json_dict, indent=2)}\n```\n\n"
    
    if crew_output.pydantic:
        content += f"## Pydantic Output\n\n```\n{crew_output.pydantic}\n```\n\n"
    
    content += f"## Tasks Output\n\n```\n{crew_output.tasks_output}\n```\n\n"
    content += f"## Token Usage\n\n```\n{crew_output.token_usage}\n```\n"
    
    return content

def main():
    st.title("CrewAI Creator Analysis")
    
    # Create form for input
    with st.form("creator_form"):
        youtube_handle = st.text_input("YouTube Handle")
        instagram_username = st.text_input("Instagram Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Analyze")
    
    # Initialize session state for storing results
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False
    if 'crew_output' not in st.session_state:
        st.session_state.crew_output = None
    
    if submit_button:
        # First validate password
        if validate_password(password):
            try:
                # Show loading spinner while processing
                with st.spinner("Analyzing creator data..."):
                    inputs = {
                        "youtube_channel_handle": youtube_handle,
                        "instagram_username": instagram_username
                    }
                    
                    # Run the crew
                    crew_output = LatestAiDevelopmentCrew().crew().kickoff(inputs=inputs)
                    
                    # Save output to session state
                    st.session_state.crew_output = crew_output
                    st.session_state.analysis_complete = True
                    
                    # Save to file
                    save_output_to_markdown(crew_output)
                    
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
        else:
            st.error("Wrong password")
            return
    
    # Display results if analysis is complete
    if st.session_state.analysis_complete and st.session_state.crew_output is not None:
        st.success("Analysis completed successfully!")
        
        # Create tabs for different outputs
        tab1, tab2, tab3, tab4 = st.tabs(["Raw Output", "JSON Output", "Tasks Output", "Token Usage"])
        
        with tab1:
            st.code(st.session_state.crew_output.raw)
        
        with tab2:
            if st.session_state.crew_output.json_dict:
                st.json(st.session_state.crew_output.json_dict)
        
        with tab3:
            st.code(st.session_state.crew_output.tasks_output)
        
        with tab4:
            st.code(st.session_state.crew_output.token_usage)
        
        # Download button
        markdown_content = generate_markdown_content(st.session_state.crew_output)
        st.download_button(
            label="Download Results",
            data=markdown_content,
            file_name="creatorOutput.md",
            mime="text/markdown"
        )

if __name__ == "__main__":
    main()

# import streamlit as st
# import sys
# import json
# from smartfunnel.crew import LatestAiDevelopmentCrew

# def save_output_to_markdown(crew_output, filename="creatorOutput.md"):
#     """
#     Save crew output to a markdown file with proper error handling.
#     """
#     try:
#         with open(filename, "w", encoding="utf-8") as md_file:
#             md_file.write("# Creator Analysis Output\n\n")
#             md_file.write(f"## Raw Output\n\n```\n{crew_output.raw}\n```\n\n")
            
#             if crew_output.json_dict:
#                 md_file.write(f"## JSON Output\n\n```json\n{json.dumps(crew_output.json_dict, indent=2)}\n```\n\n")
            
#             if crew_output.pydantic:
#                 md_file.write(f"## Pydantic Output\n\n```\n{crew_output.pydantic}\n```\n\n")
            
#             md_file.write(f"## Tasks Output\n\n```\n{crew_output.tasks_output}\n```\n\n")
#             md_file.write(f"## Token Usage\n\n```\n{crew_output.token_usage}\n```\n")
            
#         return True
#     except Exception as e:
#         st.error(f"Error saving to markdown file: {str(e)}")
#         return False

# def generate_markdown_content(crew_output):
#     """
#     Generate markdown content from crew output
#     """
#     content = "# Creator Analysis Output\n\n"
#     content += f"## Raw Output\n\n```\n{crew_output.raw}\n```\n\n"
    
#     if crew_output.json_dict:
#         content += f"## JSON Output\n\n```json\n{json.dumps(crew_output.json_dict, indent=2)}\n```\n\n"
    
#     if crew_output.pydantic:
#         content += f"## Pydantic Output\n\n```\n{crew_output.pydantic}\n```\n\n"
    
#     content += f"## Tasks Output\n\n```\n{crew_output.tasks_output}\n```\n\n"
#     content += f"## Token Usage\n\n```\n{crew_output.token_usage}\n```\n"
    
#     return content

# def main():
#     st.title("CrewAI Creator Analysis")
    
#     # Create form for input
#     with st.form("creator_form"):
#         youtube_handle = st.text_input("YouTube Handle")
#         instagram_username = st.text_input("Instagram Username")
#         submit_button = st.form_submit_button("Analyze")
    
#     # Initialize session state for storing results
#     if 'analysis_complete' not in st.session_state:
#         st.session_state.analysis_complete = False
#     if 'crew_output' not in st.session_state:
#         st.session_state.crew_output = None
    
#     if submit_button:
#         try:
#             # Show loading spinner while processing
#             with st.spinner("Analyzing creator data..."):
#                 inputs = {
#                     "youtube_channel_handle": youtube_handle,
#                     "instagram_username": instagram_username
#                 }
                
#                 # Run the crew
#                 crew_output = LatestAiDevelopmentCrew().crew().kickoff(inputs=inputs)
                
#                 # Save output to session state
#                 st.session_state.crew_output = crew_output
#                 st.session_state.analysis_complete = True
                
#                 # Save to file
#                 save_output_to_markdown(crew_output)
                
#         except Exception as e:
#             st.error(f"An error occurred: {str(e)}")
    
#     # Display results if analysis is complete
#     if st.session_state.analysis_complete and st.session_state.crew_output is not None:
#         st.success("Analysis completed successfully!")
        
#         # Create tabs for different outputs
#         tab1, tab2, tab3, tab4 = st.tabs(["Raw Output", "JSON Output", "Tasks Output", "Token Usage"])
        
#         with tab1:
#             st.code(st.session_state.crew_output.raw)
        
#         with tab2:
#             if st.session_state.crew_output.json_dict:
#                 st.json(st.session_state.crew_output.json_dict)
        
#         with tab3:
#             st.code(st.session_state.crew_output.tasks_output)
        
#         with tab4:
#             st.code(st.session_state.crew_output.token_usage)
        
#         # Download button
#         markdown_content = generate_markdown_content(st.session_state.crew_output)
#         st.download_button(
#             label="Download Results",
#             data=markdown_content,
#             file_name="creatorOutput.md",
#             mime="text/markdown"
#         )

# if __name__ == "__main__":
#     main()