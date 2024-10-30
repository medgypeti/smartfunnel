from smartfunnel.sqlite_setup import ensure_pysqlite3
ensure_pysqlite3()  # Call this before any other imports

import streamlit as st
import sys
import json
from smartfunnel.crew import LatestAiDevelopmentCrew
import logging
from typing import Optional
from smartfunnel.tools.chroma_db_init import app_instance
from smartfunnel.tools.chroma_db_init import cleanup_old_db

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Streamlit configs
try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
except Exception as e:
    logger.warning(f"Error initializing Streamlit configs: {e}")


# Initialize Streamlit configs
try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
    
    # Reduce file watching using safer check
    import streamlit.runtime.scriptrunner as streamlit_runtime
    if streamlit_runtime.get_script_run_ctx():
        st.set_option('server.fileWatcherType', 'none')
except Exception as e:
    logger.warning(f"Error initializing Streamlit configs: {e}")

def validate_password(password: str) -> bool:
    """Validate password against stored secret"""
    try:
        return password == st.secrets["Answer"]
    except Exception as e:
        logger.error(f"Error accessing secrets: {e}")
        st.error("Error accessing secrets. Make sure secrets.toml is properly configured.")
        return False

def save_output_to_markdown(crew_output, filename: str = "creatorOutput.md") -> bool:
    """Save crew output to a markdown file"""
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
        logger.error(f"Error saving to markdown: {e}")
        st.error(f"Error saving to markdown file: {str(e)}")
        return False

def generate_markdown_content(crew_output) -> str:
    """Generate markdown content from crew output"""
    try:
        content = "# Creator Analysis Output\n\n"
        content += f"## Raw Output\n\n```\n{crew_output.raw}\n```\n\n"
        
        if crew_output.json_dict:
            content += f"## JSON Output\n\n```json\n{json.dumps(crew_output.json_dict, indent=2)}\n```\n\n"
        
        if crew_output.pydantic:
            content += f"## Pydantic Output\n\n```\n{crew_output.pydantic}\n```\n\n"
        
        content += f"## Tasks Output\n\n```\n{crew_output.tasks_output}\n```\n\n"
        content += f"## Token Usage\n\n```\n{crew_output.token_usage}\n```\n"
        
        return content
    except Exception as e:
        logger.error(f"Error generating markdown: {e}")
        raise


# def process_creator_data(youtube_handle: str, instagram_username: str) -> Optional[dict]:
#     """Process creator data and return results, handling empty inputs"""
#     try:
#         # Only include non-empty inputs
#         inputs = {}
#         if youtube_handle:
#             inputs["youtube_channel_handle"] = youtube_handle
#         if instagram_username:
#             inputs["instagram_username"] = instagram_username
            
#         if not inputs:
#             raise ValueError("At least one input (YouTube handle or Instagram username) is required")
        
#         crew_output = LatestAiDevelopmentCrew().crew().kickoff(inputs=inputs)
#         return crew_output
#     except Exception as e:
#         logger.error(f"Error processing creator data: {e}")
#         raise

def process_creator_data(youtube_handle: str, instagram_username: str) -> Optional[dict]:
    """Process creator data and return results"""
    try:
        inputs = {
            "youtube_channel_handle": youtube_handle,
            "instagram_username": instagram_username
        }
        
        # cleanup_old_db()

        crew_output = LatestAiDevelopmentCrew().crew().kickoff(inputs=inputs)
        return crew_output
    except Exception as e:
        logger.error(f"Error processing creator data: {e}")
        raise

def main():
    st.title("CrewAI Creator Analysis")
    
    # Create form for input
    with st.form("creator_form"):
        youtube_handle = st.text_input("YouTube Handle (optional)")
        instagram_username = st.text_input("Instagram Username (optional)")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Analyze")
    
    # Initialize session state
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False
    if 'crew_output' not in st.session_state:
        st.session_state.crew_output = None
    
    if submit_button:
        if not validate_password(password):
            st.error("Invalid password")
            return
            
        if not youtube_handle and not instagram_username:
            st.error("Please provide at least one input (YouTube handle or Instagram username)")
            return
            
        try:
            with st.spinner("Analyzing creator data..."):
                crew_output = process_creator_data(youtube_handle, instagram_username)
                
                # Update session state
                st.session_state.crew_output = crew_output
                st.session_state.analysis_complete = True
                
                # Save to file
                save_output_to_markdown(crew_output)
                
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            st.error(f"Analysis failed: {str(e)}")
# def main():
#     st.title("CrewAI Creator Analysis")
    
#     # Create form for input
#     with st.form("creator_form"):
#         youtube_handle = st.text_input("YouTube Handle")
#         instagram_username = st.text_input("Instagram Username")
#         password = st.text_input("Password", type="password")
#         submit_button = st.form_submit_button("Analyze")
    
#     # Initialize session state
#     if 'analysis_complete' not in st.session_state:
#         st.session_state.analysis_complete = False
#     if 'crew_output' not in st.session_state:
#         st.session_state.crew_output = None
    
#     if submit_button:
#         if not validate_password(password):
#             st.error("Invalid password")
#             return
            
#         try:
#             with st.spinner("Analyzing creator data..."):
#                 crew_output = process_creator_data(youtube_handle, instagram_username)
                
#                 # Update session state
#                 st.session_state.crew_output = crew_output
#                 st.session_state.analysis_complete = True
                
#                 # Save to file
#                 save_output_to_markdown(crew_output)
                
#         except Exception as e:
#             logger.error(f"Analysis failed: {e}")
#             st.error(f"Analysis failed: {str(e)}")
    
    # Display results
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
        try:
            markdown_content = generate_markdown_content(st.session_state.crew_output)
            st.download_button(
                label="Download Results",
                data=markdown_content,
                file_name="creatorOutput.md",
                mime="text/markdown"
            )
        except Exception as e:
            logger.error(f"Error creating download button: {e}")
            st.error("Error preparing download. Please try again.")

if __name__ == "__main__":
    main()
    
# from smartfunnel.sqlite_setup import ensure_pysqlite3
# ensure_pysqlite3()  # Call this before any other imports

# import streamlit as st
# import sys
# import json
# from smartfunnel.crew import LatestAiDevelopmentCrew

# import streamlit as st
# OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

# import streamlit as st

# # Reduce file watching
# if st._is_running_with_streamlit:
#     st.set_option('server.fileWatcherType', 'none')

# def validate_password(password):
#     """
#     Validate password against stored secret
#     """
#     try:
#         return password == st.secrets["Answer"]
#     except Exception as e:
#         st.error("Error accessing secrets. Make sure secrets.toml is properly configured.")
#         return False

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
#         password = st.text_input("Password", type="password")
#         submit_button = st.form_submit_button("Analyze")
    
#     # Initialize session state for storing results
#     if 'analysis_complete' not in st.session_state:
#         st.session_state.analysis_complete = False
#     if 'crew_output' not in st.session_state:
#         st.session_state.crew_output = None
    
#     if submit_button:
#         # First validate password
#         if validate_password(password):
#             try:
#                 # Show loading spinner while processing
#                 with st.spinner("Analyzing creator data..."):
#                     inputs = {
#                         "youtube_channel_handle": youtube_handle,
#                         "instagram_username": instagram_username
#                     }
                    
#                     # Run the crew
#                     crew_output = LatestAiDevelopmentCrew().crew().kickoff(inputs=inputs)
                    
#                     # Save output to session state
#                     st.session_state.crew_output = crew_output
#                     st.session_state.analysis_complete = True
                    
#                     # Save to file
#                     save_output_to_markdown(crew_output)
                    
#             except Exception as e:
#                 st.error(f"An error occurred: {str(e)}")
#         else:
#             st.error("Wrong password")
#             return
    
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