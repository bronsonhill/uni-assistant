"""
Refactored UI components for add_ai module.

This module provides UI elements and display functions for the AI Question Generator feature,
using the shared modules for code reuse with vector stores.
"""
import streamlit as st
import time
import os
import json
from typing import Dict, List, Any, Optional
from openai import OpenAI

# Import from shared modules
from features.content.shared.vector_store_manager import display_enhanced_kb_management, init_rag_manager
from features.content.shared.vector_store_utils import (
    create_vector_store,
    generate_questions_from_vector_store,
    add_selected_questions_to_data
)
from features.content.shared.ui_components import (
    render_questions_with_selection,
    display_file_upload_interface
)

def setup_openai_client():
    """Initialize and return the OpenAI client"""
    api_key = None
    try:
        # First check Streamlit secrets
        api_key = st.secrets["OPENAI_API_KEY"]
    except (KeyError, AttributeError):
        # Fallback to environment variable
        api_key = os.getenv("OPENAI_API_KEY")
        
    if not api_key:
        st.error("OpenAI API key not found. Please set it in your environment variables or contact support.")
        return None
        
    return OpenAI(api_key=api_key)

def init_session_state():
    """Initialize session state variables for the AI question generator"""
    # Generation state
    if "generation_subject" not in st.session_state:
        st.session_state.generation_subject = ""
    if "generation_week" not in st.session_state:
        st.session_state.generation_week = 1
    if "generation_in_progress" not in st.session_state:
        st.session_state.generation_in_progress = False
    if "generated_questions" not in st.session_state:
        st.session_state.generated_questions = []
    if "selected_questions" not in st.session_state:
        st.session_state.selected_questions = {}
    if "api_error" not in st.session_state:
        st.session_state.api_error = None
    if "file_uploaded" not in st.session_state:
        st.session_state.file_uploaded = False
    if "custom_questions" not in st.session_state:
        st.session_state.custom_questions = ""

def extract_vector_store_id(vector_store_data):
    """
    Extract the vector store ID from the data structure
    
    Args:
        vector_store_data: The vector store data (can be string, dict, etc.)
        
    Returns:
        The vector store ID as a string
    """
    if isinstance(vector_store_data, dict) and "id" in vector_store_data:
        return vector_store_data["id"]
    else:
        return str(vector_store_data)

def get_vector_store_id_for_subject_week(subject, week):
    """
    Get the vector store ID for a subject and week
    
    Args:
        subject: The subject
        week: The week number
        
    Returns:
        The vector store ID or None if not found
    """
    try:
        if "data" not in st.session_state:
            return None
            
        if subject not in st.session_state.data:
            return None
            
        if "vector_store_metadata" not in st.session_state.data[subject]:
            return None
            
        week_str = str(week)
        if week_str not in st.session_state.data[subject]["vector_store_metadata"]:
            return None
            
        # Extract the vector store ID
        vector_store_data = st.session_state.data[subject]["vector_store_metadata"][week_str]
        return extract_vector_store_id(vector_store_data)
        
    except Exception as e:
        print(f"Error getting vector store ID: {e}")
        return None

def process_uploaded_file(uploaded_file, subject: str, week: int, user_email: str, num_questions: int = 5):
    """
    Process the uploaded file and generate questions using both vector store and direct file content
    
    Args:
        uploaded_file: The streamlit uploaded file object (can be None if using custom text)
        subject: The subject for the questions
        week: The week number for the questions
        user_email: The user's email address
        num_questions: Number of questions to generate (default: 5)
    
    Returns:
        List of generated questions
    """
    st.session_state.generation_in_progress = True
    st.session_state.api_error = None
    st.session_state.num_questions = num_questions
    
    try:
        # Initialize OpenAI client
        client = setup_openai_client()
        if not client:
            st.session_state.api_error = "Could not initialize OpenAI client."
            st.session_state.generation_in_progress = False
            return []
        
        # If no file is uploaded but custom text is provided, generate directly from text
        if not uploaded_file and st.session_state.custom_questions.strip():
            # Define the question generation tool
            tools = [
                {
                    "type": "function",
                    "name": "generate_questions",
                    "description": "Generate study questions based on the provided text",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "questions": {
                                "type": "array",
                                "description": "List of generated questions with their answers",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "question": {
                                            "type": "string",
                                            "description": "The question text"
                                        },
                                        "answer": {
                                            "type": "string",
                                            "description": "The answer to the question"
                                        },
                                        "explanation": {
                                            "type": "string",
                                            "description": "Explanation of why the answer is correct"
                                        }
                                    },
                                    "required": ["question", "answer"]
                                }
                            }
                        },
                        "required": ["questions"]
                    }
                }
            ]
            
            # Create context from custom text
            context = f"""Generate {num_questions} study questions for the subject '{subject}', Week {week}.

Here is the content to generate questions from:
{st.session_state.custom_questions}

The questions should test understanding of key concepts, terminology, and applications from the provided text.
Include a mix of factual recall, understanding, and application questions."""
            
            # Call the OpenAI API with function definitions
            response = client.responses.create(
                model="gpt-4o",
                instructions=f"You are an expert question generator for educational content in {subject}. Generate {num_questions} high-quality study questions with answers based on the provided text.",
                input=context,
                tools=tools,
                tool_choice={"type": "function", "name": "generate_questions"}
            )
            
            # Extract questions from the function call
            questions = []
            if hasattr(response, 'output') and response.output:
                for item in response.output:
                    if item.type == "function_call":
                        try:
                            args = json.loads(item.arguments)
                            questions = args.get("questions", [])
                        except Exception as e:
                            print(f"Error parsing function call: {e}")
            
            st.session_state.generation_in_progress = False
            return questions
            
        # Handle uploaded file - support multiple files or single file
        if isinstance(uploaded_file, list):
            # Multiple files uploaded
            file_to_process = uploaded_file[0]  # Process the first file for now
        else:
            # Single file uploaded
            file_to_process = uploaded_file
            
        # Read file content
        file_bytes = file_to_process.getvalue()
        file_name = file_to_process.name
        file_type = file_name.split('.')[-1].lower()
        
        # Validate file type
        if file_type not in ["pdf", "txt"]:
            st.session_state.api_error = "Only PDF and TXT files are supported at this time."
            st.session_state.generation_in_progress = False
            return []
        
        # Initialize the RAG manager
        if not init_rag_manager(user_email):
            st.session_state.api_error = "Could not initialize RAG manager"
            st.session_state.generation_in_progress = False
            return []
        
        # Create a vector store for the subject and week
        vector_store_id = create_vector_store(subject, week, user_email, file_bytes, file_name)
        
        if not vector_store_id:
            st.session_state.api_error = "Could not create vector store for the uploaded file. Check the logs for details."
            st.session_state.generation_in_progress = False
            return []
            
        # First, upload the file to OpenAI to get direct access
        try:
            file_upload = client.files.create(
                file=file_bytes,
                purpose="user_data"
            )
            file_id = file_upload.id
            
            # Get the file content
            file_content = client.files.content(file_id).text
            
            # Define the question generation tool and file_search tool
            tools = [
                {
                    "type": "function",
                    "name": "generate_questions",
                    "description": "Generate study questions based on retrieved content",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "questions": {
                                "type": "array",
                                "description": "List of generated questions with their answers",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "question": {
                                            "type": "string",
                                            "description": "The question text"
                                        },
                                        "answer": {
                                            "type": "string",
                                            "description": "The answer to the question"
                                        },
                                        "explanation": {
                                            "type": "string",
                                            "description": "Explanation of why the answer is correct"
                                        }
                                    },
                                    "required": ["question", "answer"]
                                }
                            }
                        },
                        "required": ["questions"]
                    }
                },
                {
                    "type": "file_search",
                    "vector_store_ids": [vector_store_id],
                    "max_num_results": 10
                }
            ]
            
            # Add the user message with both direct content and vector search context
            context = f"""Generate {num_questions} study questions for the subject '{subject}', Week {week}.

Here is the direct content from the file:
{file_content}

Additionally, you can search the vector store for more context using the file_search tool.
The questions should test understanding of key concepts, terminology, and applications from the document.
Include a mix of factual recall, understanding, and application questions.
Make sure to use both the direct content and vector search results to generate comprehensive questions."""

            # Add custom questions if provided
            if st.session_state.custom_questions.strip():
                context += f"\n\nPlease also consider these specific questions or topics when generating questions:\n{st.session_state.custom_questions}"
            
            # Call the OpenAI API with function definitions and file_search tool
            response = client.responses.create(
                model="gpt-4o",
                instructions=f"You are an expert question generator for educational content in {subject}. Generate {num_questions} high-quality study questions with answers based on both the direct file content and vector search results.",
                input=context,
                tools=tools,
                tool_choice={"type": "function", "name": "generate_questions"}
            )
            
            # Extract questions from the function call
            questions = []
            if hasattr(response, 'output') and response.output:
                for item in response.output:
                    if item.type == "function_call":
                        try:
                            args = json.loads(item.arguments)
                            questions = args.get("questions", [])
                        except Exception as e:
                            print(f"Error parsing function call: {e}")
            
            # Clean up the uploaded file
            client.files.delete(file_id)
            
            st.session_state.generation_in_progress = False
            return questions
            
        except Exception as e:
            print(f"Error processing file content: {e}")
            # Fall back to vector store only if direct content processing fails
            return st.session_state.rag_manager.generate_questions_with_rag(
                subject=subject,
                week=str(week),
                num_questions=num_questions
            )
    
    except Exception as e:
        print(f"Error processing file: {e}")
        st.session_state.api_error = f"An error occurred: {str(e)}"
        st.session_state.generation_in_progress = False
        return []

def generate_questions_without_upload(subject: str, week: int, user_email: str, num_questions: int = 5, selected_files: List[str] = None):
    """
    Generate questions from existing vector store without uploading a new file
    
    Args:
        subject: The subject for the questions
        week: The week number for the questions
        user_email: The user's email address
        num_questions: Number of questions to generate (default: 5)
        selected_files: List of file IDs to use for context (default: None)
    
    Returns:
        List of generated questions
    """
    st.session_state.generation_in_progress = True
    st.session_state.api_error = None
    st.session_state.num_questions = num_questions
    
    try:
        # Initialize the RAG manager
        if not init_rag_manager(user_email):
            st.session_state.api_error = "Could not initialize RAG manager"
            st.session_state.generation_in_progress = False
            return []
        
        # Get vector store ID
        vector_store_id = get_vector_store_id_for_subject_week(subject, week)
        if not vector_store_id:
            st.session_state.api_error = "Could not find vector store for this subject and week"
            st.session_state.generation_in_progress = False
            return []
            
        # Initialize OpenAI client
        client = setup_openai_client()
        if not client:
            st.session_state.api_error = "Could not initialize OpenAI client."
            st.session_state.generation_in_progress = False
            return []
        
        # Define the question generation tool and file_search tool
        tools = [
            {
                "type": "function",
                "name": "generate_questions",
                "description": "Generate study questions based on retrieved content",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "questions": {
                            "type": "array",
                            "description": "List of generated questions with their answers",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "question": {
                                        "type": "string",
                                        "description": "The question text"
                                    },
                                    "answer": {
                                        "type": "string",
                                        "description": "The answer to the question"
                                    },
                                    "explanation": {
                                        "type": "string",
                                        "description": "Explanation of why the answer is correct"
                                    }
                                },
                                "required": ["question", "answer"]
                            }
                        }
                    },
                    "required": ["questions"]
                }
            },
            {
                "type": "file_search",
                "vector_store_ids": [vector_store_id],
                "max_num_results": 10
            }
        ]
        
        # Add the user message with vector search context
        context = f"""Generate {num_questions} study questions for the subject '{subject}', Week {week}.

You can search the vector store for context using the file_search tool.
The questions should test understanding of key concepts, terminology, and applications from the document.
Include a mix of factual recall, understanding, and application questions."""

        # Add custom questions if provided
        if st.session_state.custom_questions.strip():
            context += f"\n\nPlease also consider these specific questions or topics when generating questions:\n{st.session_state.custom_questions}"
        
        # Call the OpenAI API with function definitions and file_search tool
        response = client.responses.create(
            model="gpt-4o",
            instructions=f"You are an expert question generator for educational content in {subject}. Generate {num_questions} high-quality study questions with answers based on the vector search results.",
            input=context,
            tools=tools,
            tool_choice={"type": "function", "name": "generate_questions"}
        )
        
        # Extract questions from the function call
        questions = []
        if hasattr(response, 'output') and response.output:
            for item in response.output:
                if item.type == "function_call":
                    try:
                        args = json.loads(item.arguments)
                        questions = args.get("questions", [])
                    except Exception as e:
                        print(f"Error parsing function call: {e}")
        
        st.session_state.generation_in_progress = False
        return questions
        
    except Exception as e:
        print(f"Error generating questions: {e}")
        st.session_state.api_error = f"Error generating questions: {str(e)}"
        st.session_state.generation_in_progress = False
        return []

def on_generate_questions(subject: str, week: int, uploaded_file):
    """Callback for when the generate button is clicked"""
    # Process the file and generate questions
    with st.spinner("Processing file and generating questions..."):
        questions = process_uploaded_file(
            uploaded_file, 
            subject, 
            week, 
            st.session_state.email,
            num_questions=st.session_state.num_questions
        )
        st.session_state.generated_questions = questions
        st.session_state.selected_questions = {}
        
        # Show success or error message
        if st.session_state.api_error:
            st.error(st.session_state.api_error)
        elif questions:
            st.success(f"Generated {len(questions)} questions!")
        else:
            st.warning("No questions could be generated from this file.")

def display_file_upload(is_subscribed: bool):
    """Display the file upload interface for generating questions"""
    # Initialize data if user is logged in
    if "email" in st.session_state:
        if "data" not in st.session_state:
            from Home import load_data
            st.session_state.data = load_data(st.session_state.email)
    
    # Get the list of existing subjects from the user's data
    subject_options = []
    if "data" in st.session_state and st.session_state.data:
        # Just use the subjects from the user's data, no common subjects added
        subject_options = list(st.session_state.data.keys())
        
        # Sort alphabetically
        subject_options.sort()
    else:
        # Empty list if no data is available - will show "Create New" option only
        subject_options = []
    
    # Use the shared file upload interface with subject dropdown but without the generate button
    col1, col2 = st.columns(2)
    
    with col1:
        # Subject input 
        if subject_options:
            # Add "Create New" option to allow custom input
            all_options = subject_options.copy()
            if "Create New" not in all_options:
                all_options.append(" + New")
            
            selected_subject = st.selectbox(
                "Subject", 
                options=all_options,
                index=all_options.index(st.session_state.generation_subject) if st.session_state.generation_subject in all_options else 0,
                key="subject_input_select"
            )
            
            # If "Create New" is selected, show a text input
            if selected_subject == " + New":
                subject = st.text_input(
                    "New Subject Name", 
                    value="",
                    placeholder="e.g., Computer Science",
                    key="subject_input_custom"
                )
            else:
                subject = selected_subject
        else:
            # If no subject options provided, fall back to text input
            subject = st.text_input(
                "Subject", 
                value=st.session_state.generation_subject,
                placeholder="e.g., Computer Science",
                key="subject_input"
            )
    
    with col2:
        # Week input
        week = st.number_input(
            "Week", 
            min_value=1, 
            max_value=52,
            value=st.session_state.generation_week,
            key="week_input"
        )
    
    # Number of questions slider
    num_questions = st.slider(
        "Number of questions to generate",
        min_value=1,
        max_value=10,
        value=5,
        step=1,
        key="num_questions_slider"
    )
    
    # Save subject and week to session state
    st.session_state.generation_subject = subject
    st.session_state.generation_week = week
    st.session_state.num_questions = num_questions
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload a file (PDF or TXT)",
        type=["pdf", "txt"],
        key="file_upload",
        accept_multiple_files=False
    )
    
    # Add custom questions text area
    st.text_area(
        "Optional: Specify topics or questions to focus on from your uploaded content, or prompt AI to generate questions based on a specific topic or question.",
        key="custom_questions",
        help="Enter specific topics or questions you'd like to be covered in the generated questions. This will help guide the AI to focus on particular areas of interest."
    )
    
    # Set file uploaded flag
    file_uploaded = uploaded_file is not None
    st.session_state.file_uploaded = file_uploaded
    
    # Check if there's an existing vector store for this subject/week
    has_kb = False
    if subject and subject in st.session_state.data:
        if "vector_store_metadata" in st.session_state.data[subject]:
            if str(week) in st.session_state.data[subject]["vector_store_metadata"]:
                has_kb = True
    
    # Display two buttons side by side
    col1, col2 = st.columns(2)
    
    with col1:
        # Generate from Upload button - enabled if a file is uploaded or custom text is provided
        can_generate = file_uploaded or bool(st.session_state.custom_questions.strip())
        if st.button("Generate Questions", 
                    key="generate_from_upload_btn", 
                    use_container_width=True,
                    type="primary" if can_generate else "secondary"):
            if not subject:
                st.error("Please enter a subject.")
            elif can_generate:
                # Call the callback with the uploaded file info (can be None)
                on_generate_questions(subject, week, uploaded_file)
    
    with col2:
        # Generate from Previous Uploads button - enabled only if a vector store exists
        if st.button("Select from Knowledge Base", 
                    key="generate_from_previous_btn", 
                    use_container_width=True,
                    disabled=not has_kb,
                    type="primary" if has_kb else "secondary"):
            if not subject:
                st.error("Please enter a subject.")
            elif has_kb:
                # Initialize show_kb_selection in session state if not exists
                if "show_kb_selection" not in st.session_state:
                    st.session_state.show_kb_selection = True
                else:
                    st.session_state.show_kb_selection = not st.session_state.show_kb_selection
    
    # Display knowledge base selection UI if enabled
    if has_kb and st.session_state.get("show_kb_selection", False):
        # Get vector store ID
        vector_store_id = get_vector_store_id_for_subject_week(subject, week)
        if vector_store_id:
            # Get list of files in the vector store
            files = st.session_state.rag_manager.list_vector_store_files(vector_store_id)
            if files:
                # Initialize selected files in session state if not exists
                if "selected_file_ids" not in st.session_state:
                    st.session_state.selected_file_ids = []
                
                # Clean up selected file IDs - remove any that no longer exist
                available_file_ids = [f["id"] for f in files]
                st.session_state.selected_file_ids = [
                    file_id for file_id in st.session_state.selected_file_ids 
                    if file_id in available_file_ids
                ]
                
                # Create a container for file selection
                with st.container():
                    st.markdown("### Select Files for Context")
                    
                    # Create file options dictionary
                    file_options = {f["id"]: f["filename"] for f in files}
                    
                    # Create a row for Select All button and file count
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        if st.button("Select All", key="select_all_files"):
                            st.session_state.selected_file_ids = [f["id"] for f in files]
                    
                    with col2:
                        if st.session_state.selected_file_ids:
                            st.info(f"Selected {len(st.session_state.selected_file_ids)} file(s)")
                    
                    # Create multiselect with persistent state
                    selected_file_ids = st.multiselect(
                        "Choose files to use for context",
                        options=list(file_options.keys()),
                        default=st.session_state.selected_file_ids,
                        format_func=lambda x: file_options[x],
                        key="file_selection"
                    )
                    
                    # Update session state with current selection
                    st.session_state.selected_file_ids = selected_file_ids
                    
                    # Generate button for selected files
                    if st.button("Generate Questions", 
                               key="generate_from_selected",
                               use_container_width=True,
                               type="primary"):
                        with st.spinner("Generating additional questions..."):
                            questions = generate_questions_without_upload(
                                subject, 
                                week, 
                                st.session_state.email,
                                num_questions=st.session_state.num_questions,
                                selected_files=selected_file_ids
                            )
                            st.session_state.generated_questions = questions
                            st.session_state.selected_questions = {}
                            
                            # Show success or error message
                            if st.session_state.api_error:
                                st.error(st.session_state.api_error)
                            elif questions:
                                st.success(f"Generated {len(questions)} additional questions!")
                            else:
                                st.warning("No additional questions could be generated.")
                    elif not selected_file_ids:
                        st.warning("Please select at least one file to use for context.")

    # Button state explanation
    if not file_uploaded and not has_kb and not st.session_state.custom_questions.strip():
        st.info("Upload a file, enter custom text, or select a subject and week that has previous uploads to generate questions.")
    elif not file_uploaded and not has_kb:
        st.info("You can generate questions from your custom text input or upload a file to start building a knowledge base.")
    elif not file_uploaded:
        st.info("Previous uploads found for this subject and week. You can generate more questions from them, upload a new file, or use custom text input.")
    elif not has_kb:
        st.info("First time using this subject and week. Upload your file to start building a knowledge base or use custom text input.")

    # Add collapsible information section at the bottom
    with st.expander("💡 Tips for Generating Questions"):
        st.markdown("""
        ### Recommendations for Best Results
        
        - **Generate questions one file at a time** for the most focused and relevant questions
        - You can upload various materials such as:
          - Lecture slides
          - Transcripts
          - Reading materials
          - Course notes
        - Each file you upload is stored in your knowledge base
        - You can chat with an AI tutor about this content on the **Subject Tutor** page
        - For best results, use PDF files with clear text formatting
        
        Questions are generated based on the content's key concepts, so more specific materials will yield better questions!
        """)

def display_question_review():
    """Display the generated questions and allow selection"""
    # Check if we have generated questions
    if not st.session_state.generated_questions:
        return
    
    # Divider before questions
    st.divider()
    st.subheader("Review Generated Questions")
    st.write("Select the questions you want to add to your study collection.")
    
    # Reset selection if clicking reset
    if st.button("Reset Selection", key="reset_selection", use_container_width=True):
        st.session_state.selected_questions = {}
        st.rerun()
    
    # Use the shared questions renderer
    render_questions_with_selection(
        questions=st.session_state.generated_questions,
        selected_questions=st.session_state.selected_questions
    )
    
    # Show add button if questions are selected
    if st.session_state.selected_questions:
        st.success(f"{len(st.session_state.selected_questions)} questions selected.")
        
        if st.button("Add Selected Questions", key="add_selected", type="primary", use_container_width=True):
            subject = st.session_state.generation_subject
            week = st.session_state.generation_week
            
            if not subject:
                st.error("Please enter a subject.")
            else:
                # Add selected questions to data using the shared function
                st.session_state.data = add_selected_questions_to_data(
                    subject, 
                    week, 
                    st.session_state.selected_questions, 
                    st.session_state.email
                )
                
                # Show success message and clear selected questions
                st.success(f"Added {len(st.session_state.selected_questions)} questions to {subject}, Week {week}!")
                st.session_state.selected_questions = {}
                st.session_state.generated_questions = []
                
                # Show balloons
                st.balloons()
                
                # Rerun to update UI
                time.sleep(1)  # Brief pause for visual feedback
                st.rerun()

def display_kb_management():
    """Display the knowledge base management interface"""
    # Use the shared KB management from our shared module
    display_enhanced_kb_management()

def display_error_message(error_msg: str):
    """Display an error message"""
    st.error(error_msg) 