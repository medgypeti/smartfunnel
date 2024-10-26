import tempfile
import logging
from embedchain import App
from embedchain.chunkers.common_chunker import CommonChunker
from embedchain.config.add_config import ChunkerConfig
import streamlit as st

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a temporary directory for ChromaDB
db_path = tempfile.mkdtemp()
logger.info(f"Created temporary directory for ChromaDB: {db_path}")

config = {
    'app': {
        'config': {
            'name': 'full-stack-app'
        }
    },
        'llm': {
        'provider': 'openai',
        'config': {
            'model': 'gpt-4o',
            'temperature': 0.3,
            # 'max_tokens': 2000,
            'prompt': (
                "The following context is primarily in French.\n"
                "If the query is in English, translate it to French before searching.\n"
                "Once you find relevant information in French, translate it back to English before answering.\n\n"
                # "Provide relevant answers back in the query's language."
                "Be comprehensive, accurate and precise. Share as much information as possible.\n"
                "Everytime you answer a question, figure out why it matters to the audience, and why it matters to the protagonist, and where/how he developed this trait, and how he's using it in practice in his life and business. Be specific\n"
                "Always try to extract the actionable practical advice from the content.\n"
                "Give the context within which every story is set.\n"
                "Always keep the storytelling part that's relevant to the query. Keep ALL the details of the story as accurate and precise as possible.\n"
                "For every reply, you should respond in sections, where each section is a single idea/concept/lesson/value/motivation/belief/etc.\n"
                "In each section, you should provide a clear claim, backstory/context, anecdote/story that you can retrieve from the content to exemplify your claim.\n"
                "For every section, you should provide 1-3 hyper actionable and practical advice, tips that can be derived and executed from this insight.\n"
                "IMPORTANT: If you don't know the answer, don't try to make up an answer. Don't try to give a generic answer. Don't try to give generic best practices.\n"
                "Always end your reply with a summary of the main points you covered in the reply.\n"
                "Always translate the quotes back to English.\n"
                "Act as a potential customer of the protagonist. Interpret the answers based on what's in it for you. You want to learn practical advice that you can apply in your own personal or professional life. You know the importance of author's advice and takeaways, and real-lifestorytelling to absorb lessons."
                "$context\n\nQuery: $query\n\nHelpful Answer:"
            ),
            'system_prompt': (
                "Act as a translator and answer finder for a multilingual audience.\n"
                "If a question is in a different language from the content, translate the query to match the content language.\n"
                "Provide relevant answers back in the query's language."
                "Be comprehensive, accurate and precise. Share as much information as possible.\n"
                "Everytime you answer a question, figure out why it matters to the audience, and why it matters to the protagonist, and where/how he developed this trait, and how he's using it in practice in his life and business. Be specific\n"
                "Always try to extract the actionable practical advice from the content.\n"
                "Give the context within which every story is set.\n"
                "Always keep the storytelling part that's relevant to the query. Keep ALL the details of the story as accurate and precise as possible.\n"
                "For every reply, you should respond in sections, where each section is a single idea/concept/lesson/value/motivation/belief/etc.\n"
                "In each section, you should provide a clear claim, backstory/context, anecdote/story that you can retrieve from the content to exemplify your claim.\n"
                "For every section, you should provide 1-3 hyper actionable and practical advice, tips that can be derived and executed from this insight.\n"
                "IMPORTANT: If you don't know the answer, don't try to make up an answer. Don't try to give a generic answer. Don't try to give generic best practices.\n"
                "Always end your reply with a summary of the main points you covered in the reply.\n"
                "Always translate the quotes back to English.\n"
                "Act as a potential customer of the protagonist. Interpret the answers based on what's in it for you. You want to learn practical advice that you can apply in your own personal or professional life. You know the importance of author's advice and takeaways, and real-lifestorytelling to absorb lessons."
                # "IMPORTANT: If you don't know the answer, LEAVE IT BLANK, and move on. Don't try to make up an answer. Don't try to give a generic answer. Don't try to give generic best practices.\n"
            ),
            'api_key': OPENAI_API_KEY,
        }
    },
    'vectordb': {
        'provider': 'chroma',
        'config': {
            'dir': db_path,
            'allow_reset': True
        }
    },
    'embedder': {
        'provider': 'openai',
        'config': {
            'model': 'text-embedding-ada-002',
            'api_key': OPENAI_API_KEY,
        }
    },
    'chunker': {
        'chunk_size': 3000,
        'chunk_overlap': 1000,
        'length_function': 'len',
        'min_chunk_size': 1001
    },
}

def get_app_instance():
    return App.from_config(config=config)

app_instance = get_app_instance()


# import tempfile
# import logging
# from embedchain import App


# # Set up logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Create a temporary directory for ChromaDB
# db_path = tempfile.mkdtemp()
# logger.info(f"Created temporary directory for ChromaDB: {db_path}")

# # Configuration dictionary
# # config = {
# #     'app': {
# #         'config': {
# #             'name': 'full-stack-app'
# #         }
# #     },
# #     'llm': {
# #         'provider': 'openai',
# #         'config': {
# #             'model': 'gpt-4o',
# #             'temperature': 0.4,
# #             'max_tokens': 10000,
# #             'prompt': (
# #                 "$context contains all the information available to you.\n\n"
# #                 "Reply to the $query by retrieving as much information as possible from the context.\n"
# #                 "Be comprehensive, accurate and precise. Share as much information as possible.\n"
# #                 "Everytime you answer a question, figure out why it matters to the audience, and why it matters to the protagonist, and where/how he developed this trait, and how he's using it in practice in his life and business. Be specific\n"
# #                 "Always try to extract the actionable practical advice from the video.\n"
# #                 "Give the context within which every story is set.\n"
# #                 "Always keep the storytelling part that's relevant to the query. Keep ALL the details of the story as accurate and precise as possible.\n"
# #                 "For every reply, you should respond in sections, where each section is a single idea/concept/lesson/value/motivation/belief/etc.\n"
# #                 "In each section, you should provide a clear claim, backstory/context, anecdote/story that was mentioned in the transcript to exemplify your claim.\n"
# #                 "For every section, you should provide 1-3 hyper actionable and practical advice, tips that can be derived and executed from this insight.\n"
# #                 "IMPORTANT: If you don't know the answer, LEAVE IT BLANK, and move on. Don't try to make up an answer. Don't try to give a generic answer. Don't try to give generic best practices.\n"
# #                 "Always end your reply with a summary of the main points.\n"
# #                 "Make sure English.\n"
# #                 # "$context\n\nQuery: $query\n\nHelpful Answer:"
# #             ),
# #             'system_prompt': (
# #                 "Act as a potential customer of the author of the video. Interpret the answers based on what's in it for you. You want to learn practical advice that you can apply in your own personal or professional life. You know the importance of author's advice and takeaways, and real-lifestorytelling to absorb lessons."
# #                 "IMPORTANT: If you don't know the answer, LEAVE IT BLANK, and move on. Don't try to make up an answer. Don't try to give a generic answer. Don't try to give generic best practices.\n"
# #             ),
# #             'api_key': OPENAI_API_KEY,
# #         }
# #     },
# #     'vectordb': {
# #         'provider': 'chroma',
# #         'config': {
# #             'dir': db_path,
# #             'allow_reset': True
# #         }
# #     },
# #     'embedder': {
# #         'provider': 'openai',
# #         'config': {
# #             'model': 'text-embedding-ada-002',
# #             'api_key': OPENAI_API_KEY,
# #         }
# #     },
# # }
# config = {
#     'app': {
#         'config': {
#             'name': 'full-stack-app'
#         }
#     },
#     'llm': {
#         'provider': 'openai',
#         'config': {
#             'model': 'gpt-4o',
#             'temperature': 0.3,
#             'max_tokens': 10000,
#             'prompt': (
#                 "Reply to the $query by providing as much information about the protagonist in the video as possible.\n"
#                 "Be comprehensive, accurate and precise. Share as much information as possible.\n"
#                 "Everytime you answer a question, figure out why it matters to the audience, and why it matters to the protagonist, and where/how he developed this trait, and how he's using it in practice in his life and business. Be specific\n"
#                 "Always try to extract the actionable practical advice from the video.\n"
#                 "Give the context within which every story is set.\n"
#                 "Always keep the storytelling part that's relevant to the query. Keep ALL the details of the story as accurate and precise as possible.\n"
#                 "For every reply, you should respond in sections, where each section is a single idea/concept/lesson/value/motivation/belief/etc.\n"
#                 "In each section, you should provide a clear claim, backstory/context, anecdote/story that was mentioned in the transcript to exemplify your claim.\n"
#                 "For every section, you should provide 1-3 hyper actionable and practical advice, tips that can be derived and executed from this insight.\n"
#                 "IMPORTANT: If you don't know the answer, LEAVE IT BLANK, and move on. Don't try to make up an answer. Don't try to give a generic answer. Don't try to give generic best practices.\n"
#                 "Always end your reply with a summary of the main points you covered in the reply.\n"
#                 "Always translate the quotes back to English.\n"
#                 "$context\n\nQuery: $query\n\nHelpful Answer:"
#             ),
#             'system_prompt': (
#                 "Act as a potential customer of the author of the video. Interpret the answers based on what's in it for you. You want to learn practical advice that you can apply in your own personal or professional life. You know the importance of author's advice and takeaways, and real-lifestorytelling to absorb lessons."
#                 "IMPORTANT: If you don't know the answer, LEAVE IT BLANK, and move on. Don't try to make up an answer. Don't try to give a generic answer. Don't try to give generic best practices.\n"
#             ),
#             'api_key': OPENAI_API_KEY,
#         }
#     },
#     'vectordb': {
#         'provider': 'chroma',
#         'config': {
#             'dir': db_path,
#             # 'allow_reset': True
#         }
#     },
#     'embedder': {
#         'provider': 'openai',
#         'config': {
#             'model': 'text-embedding-ada-002',
#             'api_key': OPENAI_API_KEY,
#         }
#     },
# }

# def get_app_instance():
#     return App.from_config(config=config)

# app_instance = get_app_instance()

