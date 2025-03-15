import streamlit as st
import sys
import os
import time
import datetime
import json

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import functions
from Home import load_data, save_data, add_question, get_user_email
from rag_manager import RAGManager
import users

# Import st-paywall directly instead of custom paywall module
try:
    from st_paywall import add_auth
except ImportError:
    # Fallback if there's an issue with st_paywall
    def add_auth(required=False, login_button_text="Login", login_button_color="primary", login_sidebar=False):
        if "email" not in st.session_state:
            st.session_state.email = "test@example.com"  # Fallback to test user
        return True  # Always return subscribed in fallback mode

# Premium feature helper functions
def show_premium_benefits():
    """Show the benefits of premium subscription to encourage sign-up"""
    st.markdown("### 🌟 Upgrade to Premium for these benefits:")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("✅ **Unlimited AI-generated questions**")
        st.markdown("✅ **Advanced question filtering**")
        st.markdown("✅ **Detailed progress analytics**")
    
    with col2:
        st.markdown("✅ **Priority support**")
        st.markdown("✅ **Assessment extraction from documents**")
        st.markdown("✅ **Export/import functionality**")
    
    st.markdown("---")

def run():
    """Main AI question generation page content - this gets run by the navigation system"""
    # Check subscription status - required for this premium feature
    # Use st-paywall's add_auth directly instead of check_subscription
    is_subscribed = add_auth(required=True)
    user_email = st.session_state.get("email")
    
    # If user is not subscribed, the add_auth function will redirect them
    # The code below will only execute for subscribed users
    
    # Double-check subscription status in our own database
    if user_email and not users.check_subscription_active(user_email):
        st.warning("Your subscription appears to be inactive. Please contact support if this is incorrect.")
        show_premium_benefits()
        st.stop()
        
    # Get the most reliable user email
    user_email = get_user_email() or user_email
    
    # Make sure we have the user's email in all the right places
    if user_email:
        st.session_state.user_email = user_email
    
    # Load data if not already in session state
    if "data" not in st.session_state:
        st.session_state.data = load_data(user_email)
    
    # Initialize the study material manager 
    if "rag_manager" not in st.session_state or not hasattr(st.session_state.rag_manager, 'delete_vector_store'):
        try:
            # Reinitialize if we don't have the expected methods
            print("Initializing RAGManager with all required methods")
            st.session_state.rag_manager = RAGManager()
            # Load any existing study materials from data
            st.session_state.rag_manager.load_vector_stores_from_data(st.session_state.data, user_email)
        except Exception as e:
            print(f"Error initializing RAGManager: {e}")
            st.session_state.rag_manager = None
    
    rag_manager = st.session_state.rag_manager
    
    # Debug vector store info
    if rag_manager and hasattr(rag_manager, 'vector_stores'):
        st.session_state.debug_vector_stores = rag_manager.vector_stores
    
    # Initialize AI question generation specific session state
    if "generated_questions" not in st.session_state:
        st.session_state.generated_questions = []
    if "generation_in_progress" not in st.session_state:
        st.session_state.generation_in_progress = False
    if "selected_questions" not in st.session_state:
        st.session_state.selected_questions = []
    if "generation_subject" not in st.session_state:
        st.session_state.generation_subject = ""
    if "generation_week" not in st.session_state:
        st.session_state.generation_week = ""
    if "api_error" not in st.session_state:
        st.session_state.api_error = None
    if "uploaded_files" not in st.session_state:
        st.session_state.uploaded_files = {}
    if "delete_vector_store_id" not in st.session_state:
        st.session_state.delete_vector_store_id = None
    if "delete_vector_store_subject" not in st.session_state:
        st.session_state.delete_vector_store_subject = None
    if "delete_vector_store_week" not in st.session_state:
        st.session_state.delete_vector_store_week = None
    
    st.title("🤖 AI-Generated Questions")
    
    if rag_manager is None:
        st.error("Could not initialize the RAG Manager. Make sure you have the required dependencies installed.")
        st.info("Run: `pip install sentence-transformers chromadb pdfplumber`")
        st.stop()
    
    st.markdown("""
    Upload your lecture notes or course materials, and let AI generate study questions for you. 
    The system will build a knowledge base for each subject and week, allowing for more relevant questions.
    
    The files you upload will also be available to the assistant chat bot making it more knowledgeable and tailored to your subject content.
    """)
    
    # Helper functions
    def process_uploaded_file():
        """Process the uploaded file and generate questions"""
        st.session_state.generation_in_progress = True
        st.session_state.api_error = None
        
        try:
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
                st.error("Only PDF and TXT files are supported at this time.")
                st.session_state.generation_in_progress = False
                return
            
            # Check if OpenAI API key is set
            api_key = None
            try:
                # First check Streamlit secrets
                api_key = st.secrets["OPENAI_API_KEY"]
            except (KeyError, AttributeError):
                # Fallback to environment variable
                api_key = os.getenv("OPENAI_API_KEY")
                
            if not api_key:
                st.session_state.api_error = "OpenAI API key not found. Please set it in .streamlit/secrets.toml or as an environment variable."
                st.session_state.generation_in_progress = False
                return
            
            # Get existing questions for this subject/week if any
            existing_questions = []
            subject = st.session_state.generation_subject
            week = st.session_state.generation_week
            if (subject in st.session_state.data and 
                week in st.session_state.data[subject] and
                week != "vector_store_metadata"):
                existing_questions = st.session_state.data[subject][week]
            
            # Keep track of files uploaded for this subject/week
            if subject not in st.session_state.uploaded_files:
                st.session_state.uploaded_files[subject] = {}
            if week not in st.session_state.uploaded_files[subject]:
                st.session_state.uploaded_files[subject][week] = []
            
            # Add to the list of files uploaded for this subject/week if not already there
            file_entry = {"name": file_name, "type": file_type, "timestamp": datetime.datetime.now().isoformat()}
            if file_entry not in st.session_state.uploaded_files[subject][week]:
                st.session_state.uploaded_files[subject][week].append(file_entry)
            
            # Generate questions using RAG approach and get updated data with vector store info
            questions, updated_data = st.session_state.rag_manager.generate_questions_from_file(
                file_bytes=file_bytes,
                file_type=file_type,
                file_name=file_name,
                subject=subject,
                week=week,
                num_questions=st.session_state.num_questions,
                existing_questions=existing_questions,
                data=st.session_state.data,
                email=user_email
            )
            
            # Update data with vector store metadata
            st.session_state.data = updated_data
            
            # Save the updated data with vector store metadata to persist vector store IDs
            save_data(st.session_state.data, user_email)
            
            # Make sure our rag_manager is updated with the latest vector store info
            print("Reloading vector stores from updated data with user email")
            st.session_state.rag_manager.load_vector_stores_from_data(st.session_state.data, user_email)
            
            # Debug updated vector store info
            if hasattr(st.session_state.rag_manager, 'vector_stores'):
                st.session_state.debug_vector_stores = st.session_state.rag_manager.vector_stores
            
            st.session_state.generated_questions = questions
            st.session_state.selected_questions = [True] * len(questions)
            
        except Exception as e:
            st.session_state.api_error = str(e)
        
        st.session_state.generation_in_progress = False
    
    def generate_without_upload():
        """Generate questions from existing knowledge base without uploading new files"""
        st.session_state.generation_in_progress = True
        st.session_state.api_error = None
        
        try:
            # Get existing questions for this subject/week if any
            existing_questions = []
            subject = st.session_state.generation_subject
            week = st.session_state.generation_week
            
            print(f"generate_without_upload: subject={subject}, week={week}, user_email={user_email}")
            
            if (subject in st.session_state.data and 
                week in st.session_state.data[subject] and
                week != "vector_store_metadata"):
                existing_questions = st.session_state.data[subject][week]
            
            # Check if we have a vector store for this subject/week
            store_key = f"{subject}_{week}" if not user_email else f"{subject}_{week}_{user_email}"
            print(f"Looking for vector store with key: {store_key}")
            print(f"Available vector stores: {list(st.session_state.rag_manager.vector_stores.keys())}")
            
            if store_key not in st.session_state.rag_manager.vector_stores:
                print(f"Vector store with key {store_key} not found, trying to load it")
                # Try to load it from metadata if available
                if (subject in st.session_state.data and 
                    "vector_store_metadata" in st.session_state.data[subject] and 
                    week in st.session_state.data[subject]["vector_store_metadata"]):
                    
                    # Try to load the vector store
                    vector_store = st.session_state.rag_manager.get_or_create_vector_store(subject, week, user_email)
                    print(f"Loaded vector store for {store_key}: {vector_store}")
                else:
                    raise ValueError(f"No vector store found for {subject} Week {week}. Please upload content first.")
            
            # Generate questions from existing knowledge base
            questions = st.session_state.rag_manager.generate_questions_with_rag(
                subject=subject,
                week=week,
                num_questions=st.session_state.num_questions,
                existing_questions=existing_questions,
                email=user_email
            )
            
            st.session_state.generated_questions = questions
            st.session_state.selected_questions = [True] * len(questions)
            
        except Exception as e:
            st.session_state.api_error = str(e)
        
        st.session_state.generation_in_progress = False
    
    def add_selected_questions():
        """Add selected questions to the database"""
        selected_count = 0
        
        # Make sure we have the latest user email
        current_email = get_user_email() or user_email
        print(f"Adding selected questions for user: {current_email}")
        
        for i, selected in enumerate(st.session_state.selected_questions):
            if selected and i < len(st.session_state.generated_questions):
                q = st.session_state.generated_questions[i]
                st.session_state.data = add_question(
                    st.session_state.data,
                    st.session_state.generation_subject,
                    int(st.session_state.generation_week),
                    q["question"],
                    q["answer"],
                    current_email  # Use the most up-to-date email
                )
                selected_count += 1
        
        if selected_count > 0:
            save_data(st.session_state.data, current_email)
            st.success(f"Added {selected_count} questions successfully!")
            # Clear generated questions
            st.session_state.generated_questions = []
            st.session_state.selected_questions = []
        else:
            st.warning("No questions selected to add.")
    
    # Main interface
    tab1, tab2 = st.tabs(["Generate Questions", "Manage Knowledge Base"])
    
    with tab1:
        col1, col2 = st.columns(2)
    
        with col1:
            st.subheader("Course Material")
            
            # Subject selection
            all_subjects = list(st.session_state.data.keys())
            
            # Allow adding a new subject
            new_subject = st.checkbox("Add a new subject")
            
            if new_subject:
                subject = st.text_input("Enter new subject name:")
                st.session_state.generation_subject = subject
            else:
                subject = st.selectbox(
                    "Select subject",
                    options=all_subjects if all_subjects else [""],
                    index=0 if all_subjects else None,
                    key="subject_select"
                )
                st.session_state.generation_subject = subject
            
            # Week selection - only show weeks that have vector stores
            week_options = []
            if subject and subject in st.session_state.data:
                # Filter out non-week keys (like "vector_store_metadata")
                week_options = [w for w in st.session_state.data[subject].keys() 
                              if w != "vector_store_metadata" and w.isdigit()]
                week_options = sorted(week_options, key=int)
            
            # Allow adding a new week
            new_week = st.checkbox("Add a new week")
            
            if new_week:
                week = st.text_input("Enter week number:", value="1")
                st.session_state.generation_week = week
            else:
                week = st.selectbox(
                    "Select week",
                    options=week_options if week_options else ["1"],
                    index=0 if week_options else None,
                    key="week_select"
                )
                st.session_state.generation_week = week
            
            # Number of questions to generate
            st.session_state.num_questions = st.slider(
                "Number of questions to generate",
                min_value=1,
                max_value=10,
                value=5
            )
            
            # Upload files section
            st.subheader("Upload New Material")
            
            # File uploader - use a fixed key to avoid session state issues
            # Add cache cleanup to ensure it works with the XSRF changes
            if "file_uploader_key" not in st.session_state:
                st.session_state.file_uploader_key = "file_uploader_fixed"
                
            uploaded_file = st.file_uploader(
                "Upload a PDF or text file", 
                type=["pdf", "txt", "png", "jpg"],
                accept_multiple_files=True,
                key=st.session_state.file_uploader_key,
                help="The file will be processed and added to the knowledge base"
            )
            
            # Check if course materials exist for this subject/week
            has_materials = False
            store_key = f"{subject}_{week}" if not user_email else f"{subject}_{week}_{user_email}"
            print(f"Looking for vector store with key: {store_key} for user: {user_email}")
            
            # First check if it's in our session state rag_manager
            if hasattr(st.session_state, 'rag_manager') and hasattr(st.session_state.rag_manager, 'vector_stores'):
                has_materials = store_key in st.session_state.rag_manager.vector_stores
            
            # Also check if it's in the data's metadata
            if (not has_materials and subject in st.session_state.data and 
                "vector_store_metadata" in st.session_state.data[subject] and 
                week in st.session_state.data[subject]["vector_store_metadata"]):
                has_materials = True
                
                # If we found it in metadata but not in rag_manager, let's try to load it
                if store_key not in st.session_state.rag_manager.vector_stores:
                    print(f"Loading vector store for key {store_key} with user_email {user_email}")
                    st.session_state.rag_manager.get_or_create_vector_store(subject, week, user_email)
            
            # Display existing uploaded files for this subject/week
            if (subject in st.session_state.uploaded_files and 
                week in st.session_state.uploaded_files[subject] and 
                st.session_state.uploaded_files[subject][week]):
                
                with st.expander("Previously uploaded files for this subject/week"):
                    for i, file_entry in enumerate(st.session_state.uploaded_files[subject][week]):
                        st.write(f"{i+1}. {file_entry['name']} ({file_entry['type']}) - {file_entry['timestamp']}")
            
            # Show the "Generate from Existing Materials" button if there are course materials
            if has_materials:
                st.write("📚 **Course materials available for this subject/week!**")
                
                # Option to generate from existing materials
                generate_existing_btn = st.button(
                    "Generate Questions from Existing Materials",
                    type="secondary",
                    disabled=not subject or not week or st.session_state.generation_in_progress
                )
                
                if generate_existing_btn:
                    generate_without_upload()
            elif subject and week:
                st.info("No course materials found for this subject/week. Upload files to create one.")
                
                # Debug expander to help troubleshoot
                with st.expander("Technical Details"):
                    st.write("This information is for troubleshooting course material issues:")
                    
                    # Show what we know about this subject and week
                    st.write(f"**Looking for materials**: {subject} / Week {week}")
                    st.write(f"**Store key**: {store_key}")
                    
                    # Check if subject exists in data
                    if subject in st.session_state.data:
                        st.write(f"✅ Subject '{subject}' found in data")
                        
                        # Check if metadata exists
                        if "vector_store_metadata" in st.session_state.data[subject]:
                            st.write("✅ vector_store_metadata found for this subject")
                            
                            # List all weeks in vector_store_metadata
                            weeks_with_stores = list(st.session_state.data[subject]["vector_store_metadata"].keys())
                            st.write(f"Weeks with vector stores: {', '.join(weeks_with_stores)}")
                            
                            # Check if this week exists
                            if week in st.session_state.data[subject]["vector_store_metadata"]:
                                st.write(f"✅ Week {week} found in vector_store_metadata")
                                vector_store_id = st.session_state.data[subject]["vector_store_metadata"][week].get("id", "Unknown")
                                st.write(f"Vector Store ID: {vector_store_id}")
                            else:
                                st.write(f"❌ Week {week} not found in vector_store_metadata")
                        else:
                            st.write("❌ No vector_store_metadata found for this subject")
                    else:
                        st.write(f"❌ Subject '{subject}' not found in data")
                    
                    # Check rag_manager
                    if hasattr(st.session_state, 'rag_manager') and hasattr(st.session_state.rag_manager, 'vector_stores'):
                        st.write("✅ RAG Manager initialized")
                        store_keys = list(st.session_state.rag_manager.vector_stores.keys())
                        st.write(f"Vector stores in RAG Manager: {', '.join(store_keys)}")
                        
                        if store_key in st.session_state.rag_manager.vector_stores:
                            st.write(f"✅ Store key '{store_key}' found in RAG Manager")
                            st.write(f"Vector store info: {st.session_state.rag_manager.vector_stores[store_key]}")
                        else:
                            st.write(f"❌ Store key '{store_key}' not found in RAG Manager")
                    else:
                        st.write("❌ RAG Manager not properly initialized")
            
            # Generate button for new upload
            # Check if files are uploaded - handle both single file and list cases
            files_uploaded = uploaded_file is not None
            if isinstance(uploaded_file, list):
                files_uploaded = len(uploaded_file) > 0
                
            generate_btn = st.button(
                "Upload & Generate Questions",
                type="primary",
                disabled=not files_uploaded or not subject or not week or st.session_state.generation_in_progress
            )
            
            if generate_btn:
                process_uploaded_file()
    
        with col2:
            st.subheader("Preview Generated Questions")
            
            if st.session_state.generation_in_progress:
                st.info("Generating questions... This may take a moment.")
                with st.spinner("Processing document and generating questions using RAG..."):
                    # Show indeterminate spinner instead of a progress bar
                    pass
            
            elif st.session_state.api_error:
                st.error(f"Error generating questions: {st.session_state.api_error}")
            
            elif st.session_state.generated_questions:
                st.success(f"Generated {len(st.session_state.generated_questions)} questions!")
                
                # Display each question with a checkbox
                for i, q in enumerate(st.session_state.generated_questions):
                    question_container = st.container(border=True)
                    with question_container:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"### Question {i+1}")
                        with col2:
                            st.session_state.selected_questions[i] = st.checkbox(
                                "Include",
                                value=st.session_state.selected_questions[i],
                                key=f"select_q_{i}"
                            )
                        
                        st.markdown(f"**Q: {q['question']}**")
                        with st.expander("View Answer"):
                            st.markdown(q['answer'])
                        
                        # Allow editing before adding
                        if st.button("Edit", key=f"edit_{i}"):
                            st.session_state.generated_questions[i]["question"] = st.text_area(
                                "Edit Question",
                                value=q["question"],
                                height=100,
                                key=f"edit_q_{i}"
                            )
                            st.session_state.generated_questions[i]["answer"] = st.text_area(
                                "Edit Answer",
                                value=q["answer"],
                                height=200,
                                key=f"edit_a_{i}"
                            )
                
                # Add selected questions button
                st.button(
                    "Add Selected Questions",
                    type="primary",
                    on_click=add_selected_questions
                )
            
            else:
                st.info("Upload a file or use existing knowledge base to generate questions.")
                
                # Show example of what it can do
                with st.expander("See example questions"):
                    st.markdown("""
                    ### Example Question 1
                    **Q: What is the difference between a compiler and an interpreter?**
                    
                    A: A compiler translates the entire source code into machine code before execution, creating an executable file that can be run independently. An interpreter, on the other hand, reads and executes the code line by line during runtime without creating a separate executable. Compilers generally produce faster-running applications since optimization happens ahead of time, while interpreters offer more flexibility for debugging and cross-platform compatibility.
                    
                    ### Example Question 2
                    **Q: Explain the principle of locality and how it affects cache design.**
                    
                    A: The principle of locality refers to the tendency of programs to access the same or nearby memory locations repeatedly over short periods. There are two main types: temporal locality (recently accessed items are likely to be accessed again soon) and spatial locality (items near recently accessed ones are likely to be accessed soon). Cache design leverages this principle by storing recently accessed data and adjacent data in fast memory. Effective cache designs use block/line fetching for spatial locality and maintain recently used data for temporal locality, significantly improving performance since cache access is much faster than main memory access.
                    """)
    
    with tab2:
        st.subheader("Knowledge Base Management")
        
        # Display all subjects and weeks with knowledge bases
        st.write("The following subject/week combinations have knowledge bases:")
        
        # Look for vector store metadata in the data
        has_vector_stores = False
        vector_store_info = []
        
        # Session state for managing active vector store
        if "active_vector_store" not in st.session_state:
            st.session_state.active_vector_store = None
        if "active_subject" not in st.session_state:
            st.session_state.active_subject = None
        if "active_week" not in st.session_state:
            st.session_state.active_week = None
        if "vector_store_files" not in st.session_state:
            st.session_state.vector_store_files = []
            
        # First, check in session_state.data which is the source of truth
        for subject in st.session_state.data:
            if isinstance(st.session_state.data[subject], dict) and "vector_store_metadata" in st.session_state.data[subject]:
                has_vector_stores = True
                
                # Display each subject and its vector stores
                st.write(f"**{subject}**")
                for week in st.session_state.data[subject]["vector_store_metadata"]:
                    vector_store_id = st.session_state.data[subject]["vector_store_metadata"][week].get("id", "Unknown")
                    vector_store_name = st.session_state.data[subject]["vector_store_metadata"][week].get("name", "Unknown")
                    
                    vector_store_info.append({
                        "subject": subject,
                        "week": week,
                        "id": vector_store_id,
                        "name": vector_store_name
                    })
                    
                    # Create columns for each vector store entry
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        # Show files if we have them tracked
                        if subject in st.session_state.uploaded_files and week in st.session_state.uploaded_files[subject]:
                            st.write(f"- Week {week}: {len(st.session_state.uploaded_files[subject][week])} tracked uploads")
                        else:
                            st.write(f"- Week {week}: Vector store exists but uploads not tracked locally")
                    
                    with col2:
                        # Create columns for buttons
                        btn_col1, btn_col2 = st.columns(2)
                        
                        with btn_col1:
                            # Button to manage this vector store
                            if st.button(f"Manage Files", key=f"manage_{subject}_{week}", use_container_width=True):
                                st.session_state.active_vector_store = vector_store_id
                                st.session_state.active_subject = subject
                                st.session_state.active_week = week
                                
                                # Fetch files for this vector store
                                st.session_state.vector_store_files = st.session_state.rag_manager.list_vector_store_files(vector_store_id)
                                st.rerun()
                                
                        with btn_col2:
                            # Button to delete the entire vector store
                            if st.button("🗑️ Delete", key=f"delete_store_{subject}_{week}", type="secondary", use_container_width=True):
                                # Set the vector store to delete in session state
                                st.session_state.delete_vector_store_id = vector_store_id
                                st.session_state.delete_vector_store_subject = subject
                                st.session_state.delete_vector_store_week = week
                                st.rerun()
        
        if not has_vector_stores:
            st.info("No knowledge bases created yet. Upload course materials to create knowledge bases.")
        
        # Handle delete confirmation if there's a pending deletion
        if st.session_state.delete_vector_store_id is not None:
            # Create a confirmation dialog
            with st.container(border=True):
                st.warning(f"⚠️ Are you sure you want to delete the entire knowledge base for **{st.session_state.delete_vector_store_subject} - Week {st.session_state.delete_vector_store_week}**?")
                st.write("This will permanently delete all files and the vector store. This action cannot be undone.")
                
                # Show confirmation buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✓ Yes, Delete Everything", type="primary", key="confirm_delete"):
                        try:
                            # Check if method exists
                            if not hasattr(st.session_state.rag_manager, 'delete_vector_store'):
                                # Reload the RAGManager to get the latest methods
                                print("RAGManager missing delete_vector_store method, reloading...")
                                
                                # Force reload by recreating the RAGManager instance
                                from rag_manager import RAGManager
                                st.session_state.rag_manager = RAGManager()
                                st.session_state.rag_manager.load_vector_stores_from_data(st.session_state.data, user_email)
                                
                                # Check again after reload
                                if not hasattr(st.session_state.rag_manager, 'delete_vector_store'):
                                    raise AttributeError("Method 'delete_vector_store' still missing after reload")
                            
                            # Delete the vector store
                            success = st.session_state.rag_manager.delete_vector_store(st.session_state.delete_vector_store_id)
                            
                            if success:
                                # Check if method exists
                                if not hasattr(st.session_state.rag_manager, 'remove_vector_store_from_data'):
                                    # Implement here if missing
                                    print("Implementing remove_vector_store_from_data inline")
                                    
                                    # Simple implementation to remove from data
                                    subject = st.session_state.delete_vector_store_subject
                                    week = st.session_state.delete_vector_store_week
                                    if subject in st.session_state.data and "vector_store_metadata" in st.session_state.data[subject]:
                                        if week in st.session_state.data[subject]["vector_store_metadata"]:
                                            # Remove the week
                                            st.session_state.data[subject]["vector_store_metadata"].pop(week)
                                            # If empty metadata, remove it
                                            if not st.session_state.data[subject]["vector_store_metadata"]:
                                                st.session_state.data[subject].pop("vector_store_metadata")
                                else:
                                    # Update the data by removing the vector store metadata
                                    st.session_state.data = st.session_state.rag_manager.remove_vector_store_from_data(
                                        st.session_state.data,
                                        st.session_state.delete_vector_store_subject,
                                        st.session_state.delete_vector_store_week,
                                        user_email
                                    )
                        except Exception as e:
                            st.error(f"Error deleting vector store: {e}")
                            print(f"Error in delete confirmation: {e}")
                            success = False
                        
                        if success:
                            # Save updated data
                            save_data(st.session_state.data, user_email)
                            
                            # Remove from uploaded_files tracking if present
                            subject = st.session_state.delete_vector_store_subject
                            week = st.session_state.delete_vector_store_week
                            if subject in st.session_state.uploaded_files and week in st.session_state.uploaded_files[subject]:
                                del st.session_state.uploaded_files[subject][week]
                                if not st.session_state.uploaded_files[subject]:
                                    del st.session_state.uploaded_files[subject]
                            
                            # Show success message
                            st.success(f"Knowledge base for {subject} - Week {week} deleted successfully!")
                        else:
                            st.error("Failed to delete knowledge base. Please try again.")
                        
                        # Clear the delete confirmation state
                        st.session_state.delete_vector_store_id = None
                        st.session_state.delete_vector_store_subject = None
                        st.session_state.delete_vector_store_week = None
                        st.rerun()
                
                with col2:
                    if st.button("✗ Cancel", key="cancel_delete"):
                        # Clear the delete confirmation state
                        st.session_state.delete_vector_store_id = None
                        st.session_state.delete_vector_store_subject = None
                        st.session_state.delete_vector_store_week = None
                        st.rerun()
            
        # Display active vector store management interface if one is selected
        if st.session_state.active_vector_store:
            st.markdown("---")
            
            # Create a back button
            if st.button("← Back to Knowledge Base List"):
                st.session_state.active_vector_store = None
                st.session_state.active_subject = None
                st.session_state.active_week = None
                st.session_state.vector_store_files = []
                st.rerun()
                
            st.subheader(f"Managing {st.session_state.active_subject} - Week {st.session_state.active_week}")
            st.write(f"Vector Store ID: `{st.session_state.active_vector_store}`")
            
            # Create tabs for different functions
            file_tab, upload_tab = st.tabs(["Files in Vector Store", "Add New Files"])
            
            with file_tab:
                # Show files in the vector store with options to delete
                st.write("Files currently in this vector store:")
                
                # Refresh button
                if st.button("Refresh File List"):
                    st.session_state.vector_store_files = st.session_state.rag_manager.list_vector_store_files(st.session_state.active_vector_store)
                    st.success("File list refreshed")
                
                if not st.session_state.vector_store_files:
                    st.info("No files found in this vector store.")
                else:
                    # Display files in a table with action buttons
                    for i, file in enumerate(st.session_state.vector_store_files):
                        st.markdown(f"### File {i+1}")
                        file_container = st.container(border=True)
                        
                        with file_container:
                            # Format the created_at timestamp
                            created_at = datetime.datetime.fromtimestamp(file["created_at"]) if isinstance(file["created_at"], (int, float)) else "Unknown"
                            filename = file.get("filename", "Unknown")
                            
                            # Main file info
                            st.write(f"**Filename**: {filename}")
                            st.write(f"**ID**: `{file['id']}`")
                            st.write(f"**Created**: {created_at}, **Status**: {file['status'] or 'Unknown'}")
                            
                            # Action buttons in columns
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                # View button (show info about file)
                                if st.button("File Info", key=f"view_file_{i}"):
                                    file_id = file["id"]
                                    # Store minimal file info in session state
                                    st.session_state.current_file_data = {
                                        "content_type": "info",
                                        "text_content": "OpenAI doesn't allow direct downloading of files uploaded to vector stores for assistants. Files are securely stored by OpenAI and used for retrieving relevant information during question generation."
                                    }
                                    st.session_state.current_file_name = filename
                                    st.session_state.current_file_id = file_id
                                    st.rerun()
                            
                            with col2:
                                # Rename button
                                if st.button("Rename", key=f"rename_file_{i}"):
                                    # Set session state to show rename dialog
                                    st.session_state.rename_file_id = file["id"]
                                    st.session_state.rename_file_index = i
                                    st.session_state.rename_file_current_name = filename
                                    st.rerun()
                            
                            with col3:
                                # Delete button
                                if st.button("Delete File", key=f"delete_file_{i}"):
                                    with st.spinner("Deleting file..."):
                                        success = st.session_state.rag_manager.delete_vector_store_file(
                                            st.session_state.active_vector_store, 
                                            file["id"]
                                        )
                                        
                                        if success:
                                            st.success("File deleted successfully!")
                                            # Remove from the list
                                            st.session_state.vector_store_files = [f for f in st.session_state.vector_store_files if f["id"] != file["id"]]
                                            st.rerun()
                                        else:
                                            st.error("Failed to delete file. Please try again.")
                            
                            # Show rename dialog if this is the file being renamed
                            if hasattr(st.session_state, "rename_file_id") and st.session_state.rename_file_id == file["id"]:
                                st.write("---")
                                st.write("**Rename File**")
                                new_filename = st.text_input(
                                    "New filename:", 
                                    value=st.session_state.rename_file_current_name,
                                    key=f"new_filename_{i}"
                                )
                                
                                rename_col1, rename_col2 = st.columns(2)
                                with rename_col1:
                                    if st.button("Save", key=f"save_rename_{i}"):
                                        # Update filename in session state tracking
                                        subject = st.session_state.active_subject
                                        week = st.session_state.active_week
                                        old_name = st.session_state.rename_file_current_name
                                        
                                        # Find and update the file entry in uploaded_files
                                        if (subject in st.session_state.uploaded_files and 
                                            week in st.session_state.uploaded_files[subject]):
                                            for file_entry in st.session_state.uploaded_files[subject][week]:
                                                if file_entry["name"] == old_name:
                                                    # Update the filename
                                                    file_entry["name"] = new_filename
                                                    file_entry["renamed_at"] = datetime.datetime.now().isoformat()
                                                    break
                                        
                                        # Update in the current list
                                        st.session_state.vector_store_files[st.session_state.rename_file_index]["filename"] = new_filename
                                        
                                        # Clear rename state
                                        del st.session_state.rename_file_id
                                        del st.session_state.rename_file_index
                                        del st.session_state.rename_file_current_name
                                        
                                        st.success(f"File renamed to: {new_filename}")
                                        st.rerun()
                                
                                with rename_col2:
                                    if st.button("Cancel", key=f"cancel_rename_{i}"):
                                        # Clear rename state
                                        del st.session_state.rename_file_id
                                        del st.session_state.rename_file_index
                                        del st.session_state.rename_file_current_name
                                        st.rerun()
                    
                    # Display file content if viewing
                    if hasattr(st.session_state, "current_file_data") and st.session_state.current_file_data:
                        st.markdown("---")
                        st.subheader(f"Content of: {st.session_state.current_file_name}")
                        
                        content_container = st.container(border=True)
                        with content_container:
                            content_data = st.session_state.current_file_data
                            content_type = content_data.get("content_type", "text")
                            
                            # Add a download button
                            file_id = st.session_state.current_file_id
                            file_name = st.session_state.current_file_name
                            
                            if content_type == "info":
                                # Just display the text information
                                st.info(content_data.get("text_content", "No information available"))
                                
                                # Show a notice about the original file name
                                st.write(f"**Original Filename**: {file_name}")
                                
                                # Show the file ID
                                st.write(f"**File ID**: `{file_id}`")
                                
                                # Explain that the content is used for question generation
                                st.write("This file is stored securely by OpenAI and is used to generate relevant questions based on your course material.")
                            elif content_type == "text":
                                # Text content can be displayed directly
                                st.text_area(
                                    "File Content", 
                                    value=content_data.get("text_content", "No content available"),
                                    height=400,
                                    disabled=True
                                )
                            elif content_type == "pdf":
                                # For PDFs, offer download
                                st.info("PDF files can be downloaded for viewing")
                                
                                # Create a download button for the PDF content
                                st.download_button(
                                    label="Download PDF",
                                    data=content_data.get("content", b""),
                                    file_name=file_name if file_name.lower().endswith(".pdf") else f"{file_name}.pdf",
                                    mime="application/pdf"
                                )
                            else:
                                # Binary content
                                st.info("Binary files can be downloaded for viewing")
                                st.download_button(
                                    label="Download File",
                                    data=content_data.get("content", b""),
                                    file_name=file_name,
                                    mime="application/octet-stream"
                                )
                            
                            # Action buttons
                            action_col1, action_col2 = st.columns(2)
                            
                            with action_col1:
                                if st.button("Close", key="close_file_content"):
                                    del st.session_state.current_file_data
                                    del st.session_state.current_file_name
                                    del st.session_state.current_file_id
                                    st.rerun()
            
            with upload_tab:
                st.write("Upload a new file to this vector store:")
                
                # File uploader for adding new files
                uploaded_file = st.file_uploader(
                    "Upload a PDF or text file", 
                    type=["pdf", "txt"],
                    key=f"upload_to_vector_store_{st.session_state.active_vector_store}",
                    help="The file will be processed and added to the knowledge base"
                )
                
                if uploaded_file:
                    if st.button("Add File to Vector Store", type="primary"):
                        with st.spinner("Adding file to vector store..."):
                            try:
                                # Read file content
                                file_bytes = uploaded_file.getvalue()
                                file_name = uploaded_file.name
                                file_type = file_name.split('.')[-1].lower()
                                
                                # Add to the vector store
                                file_batch = st.session_state.rag_manager.add_file_to_vector_store(
                                    vector_store_id=st.session_state.active_vector_store,
                                    file_bytes=file_bytes,
                                    file_name=file_name
                                )
                                
                                # Track the file in our local data structure
                                subject = st.session_state.active_subject
                                week = st.session_state.active_week
                                
                                if subject not in st.session_state.uploaded_files:
                                    st.session_state.uploaded_files[subject] = {}
                                if week not in st.session_state.uploaded_files[subject]:
                                    st.session_state.uploaded_files[subject][week] = []
                                
                                # Add to the list of files uploaded for this subject/week
                                file_entry = {"name": file_name, "type": file_type, "timestamp": datetime.datetime.now().isoformat()}
                                st.session_state.uploaded_files[subject][week].append(file_entry)
                                
                                st.success(f"File added successfully! Batch ID: {file_batch['id']}")
                                
                                # Refresh file list
                                st.session_state.vector_store_files = st.session_state.rag_manager.list_vector_store_files(st.session_state.active_vector_store)
                                
                            except Exception as e:
                                st.error(f"Error adding file to vector store: {str(e)}")
                else:
                    st.info("Please upload a file to add to the vector store.")
        
        st.markdown("""
        ### About Knowledge Bases
        
        This feature creates and maintains persistent knowledge bases for each subject/week combination. 
        
        **Benefits:**
        - Files are processed and stored in a vector database
        - Content is preserved between sessions
        - Question generation improves as more content is added
        - Questions are more relevant to the specific course material
        
        **How it works:**
        1. When you upload a file, it's processed and added to the knowledge base
        2. The knowledge base is stored in MongoDB for persistence across sessions
        3. Questions are generated using a RAG (Retrieval-Augmented Generation) approach
        4. This means the AI retrieves relevant content before generating questions
        """)
        
        # Add debug information in an expander for troubleshooting
        with st.expander("Debug Vector Store Information"):
            st.write("This information is for troubleshooting vector store persistence issues:")
            if hasattr(st.session_state, 'debug_vector_stores') and st.session_state.debug_vector_stores:
                st.json(st.session_state.debug_vector_stores)
            else:
                st.write("No vector stores loaded in RAG manager.")
    
    # Additional resources section
    st.markdown("---")
    st.subheader("Tips for Better Question Generation")
    st.markdown("""
    - Upload clear, well-formatted documents for better results
    - PDFs with searchable text work best (not scanned images)
    - Upload multiple files for the same subject/week to build a comprehensive knowledge base
    - Generate questions from existing knowledge base after uploading several files
    - The system works best with structured content like lecture notes, textbook excerpts, and course materials
    """)