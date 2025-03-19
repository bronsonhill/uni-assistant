import streamlit as st
import sys
import os
import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import from Home and rag_manager
import Home
import mongodb
from rag_manager import RAGManager

# Import st_paywall instead of custom paywall module
try:
    from st_paywall import add_auth
except ImportError:
    # Fallback if there's an issue with st_paywall
    def add_auth(required=False, login_button_text="Login", login_button_color="primary", login_sidebar=False):
        if "email" not in st.session_state:
            st.session_state.email = "test@example.com"  # Fallback to test user
        return True  # Always return subscribed in fallback mode

# Import base content functions
from features.content.base_content import show_preview_mode

def show_premium_benefits():
    """Show the benefits of premium subscription to encourage sign-up"""
    st.markdown("### 🌟 Upgrade to Premium for these benefits:")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("✅ **Chat with a personal study buddy**")
        st.markdown("✅ **Get explanations based on your materials**")
        st.markdown("✅ **Track conversation history**")
    
    with col2:
        st.markdown("✅ **Customized to your course content**")
        st.markdown("✅ **Works with all your study materials**")
        st.markdown("✅ **Save and rename conversations**")
    
    st.markdown("---")

def show_demo_content():
    """Display demo content for users in preview mode"""
    # Display a sample chat interface to show how the feature works
    st.subheader("Preview: Subject Tutor Chat")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Course Material")
        
        # Sample subject selection
        selected_subject = st.selectbox(
            "Select subject",
            options=["Computer Science", "Biology", "Law"],
            index=0,
            key="demo_subject_selection"
        )
        
        # Sample week selection
        st.selectbox(
            "Select week",
            options=["1", "2", "3"],
            index=0,
            key="demo_week_selection",
            disabled=True
        )
        
        # Reset chat button (non-functional in demo)
        st.button("Reset Chat", type="secondary", disabled=True)
        
        with st.expander("About this feature"):
            st.markdown("""
            ### How it works
            
            This chat connects you with an AI study buddy that knows your course materials.
            
            Your study buddy can:
            - Answer questions about your uploaded materials
            - Explain difficult concepts
            - Help you understand challenging topics
            - Provide helpful examples and analogies
            
            For best results:
            - Ask specific questions
            - Upload complete course materials
            - Use this alongside practicing with flashcards
            """)
    
    with col2:
        st.subheader("Chat")
        
        # Create a fixed height chat container with sample messages
        chat_container = st.container(height=400, border=True)
        
        # Show content based on selected subject
        if selected_subject == "Computer Science":
            with chat_container:
                with st.chat_message("user"):
                    st.write("Can you explain the concept of inheritance in object-oriented programming?")
                
                with st.chat_message("assistant"):
                    st.write("""
                    Based on your course materials for Computer Science Week 2, inheritance is a fundamental concept in object-oriented programming.
                    
                    Inheritance allows a class (child class) to inherit properties and methods from another class (parent class). This promotes code reuse and establishes a relationship between the parent and child classes.
                    
                    For example, if you have a `Vehicle` parent class with properties like `speed` and methods like `accelerate()`, you could create child classes like `Car` and `Motorcycle` that inherit these features while adding their own specialized properties and methods.
                    
                    The syntax in Python looks like:
                    ```python
                    class Vehicle:
                        def __init__(self, speed=0):
                            self.speed = speed
                        
                        def accelerate(self, amount):
                            self.speed += amount
                    
                    class Car(Vehicle):  # Car inherits from Vehicle
                        def __init__(self, speed=0, doors=4):
                            super().__init__(speed)  # Call parent constructor
                            self.doors = doors
                    ```
                    
                    Would you like me to explain more about specific aspects of inheritance, like method overriding or multiple inheritance?
                    """)
                
                with st.chat_message("user"):
                    st.write("Yes, please explain method overriding.")
                    
                with st.chat_message("assistant"):
                    st.write("""
                    Method overriding is a key concept in inheritance where a child class provides a specific implementation for a method that's already defined in its parent class.
                    
                    **How it works:**
                    1. The method in the child class must have the same name, parameters, and return type as in the parent class
                    2. When the method is called on an object of the child class, the child's version executes instead of the parent's
                    3. This enables polymorphism - where objects of different classes can be treated as objects of a common parent class
                    
                    **Example in Python:**
                    ```python
                    class Animal:
                        def make_sound(self):
                            return "Generic animal sound"
                            
                    class Dog(Animal):
                        # Override the parent method
                        def make_sound(self):
                            return "Woof!"
                            
                    class Cat(Animal):
                        # Override the parent method
                        def make_sound(self):
                            return "Meow!"
                    
                    # Create objects
                    generic_animal = Animal()
                    dog = Dog()
                    cat = Cat()
                    
                    # Polymorphic behavior
                    print(generic_animal.make_sound())  # "Generic animal sound"
                    print(dog.make_sound())             # "Woof!"
                    print(cat.make_sound())             # "Meow!"
                    ```
                    
                    Would you like me to explain the concept of the `super()` function that's often used with method overriding?
                    """)
        
        elif selected_subject == "Biology":
            with chat_container:
                with st.chat_message("user"):
                    st.write("Can you explain how photosynthesis works?")
                
                with st.chat_message("assistant"):
                    st.write("""
                    Based on your course materials for Biology Week 1, photosynthesis is the process by which plants, algae, and some bacteria convert light energy into chemical energy.
                    
                    **The basic equation:** 6CO₂ + 6H₂O + light energy → C₆H₁₂O₆ (glucose) + 6O₂
                    
                    **The process occurs in two main stages:**
                    
                    1. **Light-dependent reactions** (in the thylakoid membrane):
                       - Chlorophyll and other pigments in photosystems capture light energy
                       - This energy is used to split water molecules (photolysis), releasing oxygen
                       - Energy is temporarily stored as ATP and NADPH
                    
                    2. **Light-independent reactions** (Calvin cycle, in the stroma):
                       - CO₂ is captured and combined with a 5-carbon compound (RuBP)
                       - Using ATP and NADPH from the light reactions, the resulting molecules are reduced to form glucose
                       - RuBP is regenerated to continue the cycle
                    
                    **Key structures involved:**
                    - Chloroplasts: The organelles where photosynthesis occurs
                    - Thylakoids: Membrane structures inside chloroplasts where light reactions happen
                    - Stroma: Fluid inside chloroplasts where the Calvin cycle occurs
                    
                    Would you like me to go into more detail about any specific part of the process?
                    """)
                
                with st.chat_message("user"):
                    st.write("Can you explain more about the role of chlorophyll?")
                    
                with st.chat_message("assistant"):
                    st.write("""
                    Chlorophyll plays a central role in photosynthesis. Here's a detailed explanation:
                    
                    **Structure and Types:**
                    - Chlorophyll is a green pigment molecule with a porphyrin ring structure containing a magnesium ion at the center
                    - The most common types in plants are:
                      - **Chlorophyll a**: The primary photosynthetic pigment (blue-green)
                      - **Chlorophyll b**: An accessory pigment (yellow-green)
                    
                    **Functions:**
                    1. **Light absorption**:
                       - Chlorophyll absorbs primarily blue and red light while reflecting green light (giving plants their color)
                       - Different chlorophyll types expand the range of light wavelengths that can be captured
                    
                    2. **Energy conversion**:
                       - When chlorophyll absorbs photons, electrons in the molecule become excited to a higher energy state
                       - This energy is channeled through a series of electron carriers in the electron transport chain
                    
                    3. **Photosystem organization**:
                       - Chlorophyll molecules are arranged in clusters called photosystems
                       - Photosystem I (PSI) and Photosystem II (PSII) work together in the light reactions
                       - In PSII, chlorophyll's excited electrons are used to split water molecules
                    
                    **Location in the cell:**
                    - Chlorophyll is embedded in the thylakoid membranes within chloroplasts
                    - It's organized into light-harvesting complexes that funnel energy to reaction centers
                    
                    Chlorophyll deficiency results in plants that cannot photosynthesize effectively, appearing yellow or white instead of green (chlorosis).
                    """)
        
        else:  # Law
            with chat_container:
                with st.chat_message("user"):
                    st.write("Can you explain the concept of precedent in common law systems?")
                
                with st.chat_message("assistant"):
                    st.write("""
                    Based on your course materials for Law Week 1, precedent (also known as stare decisis) is a fundamental principle in common law legal systems.
                    
                    **What is Precedent?**
                    Precedent refers to the legal principle where judges are bound to follow previous decisions of courts at the same or higher level when deciding cases with similar facts and legal issues. In Latin, this principle is known as "stare decisis" which means "to stand by decisions."
                    
                    **How Precedent Works:**
                    
                    1. **Binding vs. Persuasive Precedent**:
                       - **Binding precedent**: Decisions from higher courts that lower courts must follow
                       - **Persuasive precedent**: Decisions that courts may consider but aren't obligated to follow (e.g., from courts in other jurisdictions)
                    
                    2. **Ratio Decidendi vs. Obiter Dicta**:
                       - **Ratio decidendi**: The binding part of a judgment - the legal principle upon which the decision is based
                       - **Obiter dicta**: Additional remarks or observations that aren't essential to the decision and don't create binding precedent
                    
                    3. **Hierarchy of Courts**:
                       - In most common law systems, a strict hierarchy determines which precedents bind which courts
                       - For example, in the UK, Supreme Court decisions bind all lower courts
                    
                    **Importance of Precedent:**
                    - Creates predictability and certainty in the law
                    - Ensures similar cases are treated alike (consistency)
                    - Promotes fairness and impartiality
                    - Allows for the gradual, evolutionary development of law
                    
                    Would you like me to explain how precedents can be overturned or distinguished in certain circumstances?
                    """)
                
                with st.chat_message("user"):
                    st.write("Yes, please explain how precedents can be overturned.")
                    
                with st.chat_message("assistant"):
                    st.write("""
                    **Overturning or Avoiding Precedent**
                    
                    Despite the general rule to follow precedent, there are several legitimate ways courts can overturn or avoid previous decisions:
                    
                    **1. Overruling**
                    - Higher courts can directly overturn precedents set by themselves or lower courts
                    - Example: The US Supreme Court overturned *Plessy v. Ferguson* with *Brown v. Board of Education*, rejecting the "separate but equal" doctrine
                    - This typically happens when a court believes the precedent is:
                      - Clearly wrong or poorly reasoned
                      - No longer applicable to modern conditions
                      - Inconsistent with fundamental values or other established legal principles
                    
                    **2. Distinguishing**
                    - Courts can "distinguish" a case from existing precedent by identifying meaningful differences in facts or legal issues
                    - This doesn't overturn the precedent but limits its application
                    - Example: "While the precedent in Smith v. Jones involved a verbal contract for goods, our case involves a written contract for services, making the precedent distinguishable"
                    
                    **3. Transformation Through Interpretation**
                    - Courts can gradually reshape precedent by interpreting it in new ways
                    - This allows for evolution without explicitly overturning cases
                    
                    **4. Legislative Intervention**
                    - Legislatures can pass statutes that effectively overturn judge-made precedent
                    - Example: Parliament passing a law that explicitly changes a rule established by courts
                    
                    **Considerations When Overturning Precedent**
                    Courts typically consider:
                    - The importance of legal certainty and stability
                    - Whether people have relied on the existing precedent
                    - How workable the precedent has proven to be in practice
                    - Whether the original reasoning was flawed
                    
                    In most common law systems, overturning precedent is relatively rare, as stability and predictability are highly valued. This is why distinguishing is often preferred as a more subtle approach.
                    """)
        
        # Disabled chat input
        st.chat_input("Ask a question about your course materials...", disabled=True)

def run():
    """Main tutor page content - this gets run by the navigation system"""
    # Check if user is authenticated and subscribed
    user_email = st.session_state.get("email")
    is_authenticated = user_email is not None
    is_subscribed = st.session_state.get("user_subscribed", False)
    
    # Title and description
    st.title("💬 Chat with Subject Tutor")
    st.markdown("""
    Talk to your personal AI study buddy who knows your course materials!
    Ask questions, get explanations, and deepen your understanding of course topics.
    """)

    # Handle different access scenarios
    if not is_authenticated:
        # Show preview mode for unauthenticated users
        show_preview_mode(
            "Subject Tutor",
            """
            Chat with an AI tutor that understands your course materials.
            Ask questions, get explanations, and improve your understanding
            of complex topics from your lectures and readings.
            
            Your AI study buddy makes learning more interactive and effective.
            """
        )
        
        # Show demo content for unauthenticated users
        show_demo_content()
        return
    
    if not is_subscribed:
        # Show premium feature notice for authenticated but non-subscribed users
        st.warning("This is a premium feature that requires a subscription.")
        show_premium_benefits()
        
        # Show demo content for non-subscribed users
        show_demo_content()
        
        # Add prominent upgrade button
        st.button("Upgrade to Premium", type="primary", disabled=True)
        return
    
    # If we get here, user is authenticated and subscribed - proceed with full functionality
    
    # Initialize session state for chat
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = None
    
    if "assistant_id" not in st.session_state:
        st.session_state.assistant_id = None
    
    if "rag_manager" not in st.session_state:
        # Initialize RAG manager only for the current user if logged in
        st.session_state.rag_manager = Home.init_rag_manager(email=user_email)
    
    # For storing subject/week selections (needed when loading from history)
    if "selected_subject" not in st.session_state:
        st.session_state.selected_subject = None
        
    if "selected_week" not in st.session_state:
        st.session_state.selected_week = None
        
    # For storing chat title
    if "chat_title" not in st.session_state:
        st.session_state.chat_title = None
        
    # For tracking current chat session ID
    if "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = None
    
    # Load data
    if "data" not in st.session_state:
        # Load data only for the current user if logged in
        st.session_state.data = Home.load_data(email=user_email)
    
    # Function to create or get a thread
    def get_or_create_thread():
        """Create a new thread if one doesn't exist"""
        if st.session_state.thread_id is None:
            try:
                thread = st.session_state.rag_manager.client.beta.threads.create()
                st.session_state.thread_id = thread.id
                return thread.id
            except Exception as e:
                st.error(f"Error creating thread: {str(e)}")
                return None
        return st.session_state.thread_id
    
    # Function to create an assistant with access to course materials
    def create_assistant_for_chat(vector_store_id: str):
        """Create or get an assistant that can access the selected course materials"""
        try:
            # Create a new assistant focused on explaining concepts
            assistant = st.session_state.rag_manager.client.beta.assistants.create(
                name="Course Assistant",
                instructions="""You are a helpful teaching assistant for university students.
    Your goal is to help students understand concepts from their course materials.
    Always provide thorough, accurate explanations based on the content you have access to.
    If you're not sure about something, be clear about that rather than making up information.
    Use examples and analogies when helpful to explain complex topics.""",
                model="gpt-4o",
                tools=[{"type": "file_search"}],
                tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}}
            )
            
            st.session_state.assistant_id = assistant.id
            return assistant.id
        except Exception as e:
            st.error(f"Error creating assistant: {str(e)}")
            return None
    
    # Function to send a message and get a response
    def send_message(message: str, vector_store_id: str, subject: str, week: str, stream_handler=None, stream=True):
        """
        Send a message to the assistant and get a response
        
        Args:
            message: Message to send
            vector_store_id: Vector store ID to use
            subject: Subject of the conversation
            week: Week of the conversation
            stream_handler: Optional callback function for streaming responses
            stream: Whether to use streaming (default True)
        
        Returns:
            The assistant's response text
        """
        try:
            # Make sure we have a thread
            thread_id = get_or_create_thread()
            
            if not thread_id:
                return "Error: Could not create or retrieve thread."
            
            # Make sure we have an assistant
            if st.session_state.assistant_id is None:
                assistant_id = create_assistant_for_chat(vector_store_id)
                if not assistant_id:
                    return "Error: Could not create assistant."
            else:
                assistant_id = st.session_state.assistant_id
            
            # Add the user message to the thread
            st.session_state.rag_manager.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=message
            )
            
            # Create a run
            run = st.session_state.rag_manager.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id,
                stream=stream
            )
            
            response_text = ""
            
            # Handle streaming if requested
            if stream and stream_handler:
                # Process the stream
                for chunk in run:
                    if chunk.event == "thread.message.delta" and hasattr(chunk, "data") and hasattr(chunk.data, "delta") and hasattr(chunk.data.delta, "content"):
                        for content in chunk.data.delta.content:
                            if content.type == "text" and hasattr(content.text, "value"):
                                delta_text = content.text.value
                                response_text += delta_text
                                stream_handler(delta_text)
            else:
                # Wait for the run to complete without streaming
                while run.status in ["queued", "in_progress"]:
                    time.sleep(1)
                    run = st.session_state.rag_manager.client.beta.threads.runs.retrieve(
                        thread_id=thread_id,
                        run_id=run.id
                    )
                
                # Get the latest messages (should include the assistant's response)
                messages = st.session_state.rag_manager.client.beta.threads.messages.list(
                    thread_id=thread_id
                )
                
                # Find the assistant's response (the most recent assistant message)
                response_text = "No response from the assistant."
                for message in messages.data:
                    if message.role == "assistant":
                        # Extract and return the text content
                        response_text = ""
                        for content in message.content:
                            if content.type == "text":
                                response_text += content.text.value
                        break
            
            # Save the conversation to MongoDB if we have a user email
            if "email" in st.session_state and st.session_state.email:
                # Get or create chat title
                chat_title = None
                if "chat_title" in st.session_state and st.session_state.chat_title:
                    chat_title = st.session_state.chat_title
                
                # Save conversation to MongoDB
                mongodb.save_chat_session(
                    email=st.session_state.email,
                    subject=subject,
                    week=week,
                    vector_store_id=vector_store_id,
                    messages=st.session_state.chat_messages + [{"role": "assistant", "content": response_text}],
                    thread_id=thread_id,
                    assistant_id=assistant_id,
                    chat_type=mongodb.CHAT_TYPE_TUTOR,
                    title=chat_title
                )
            
            return response_text
        
        except Exception as e:
            return f"Error: {str(e)}"
    
    # Subject and week selection layout
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Add tabs for material selection and chat history
        select_tab, history_tab = st.tabs(["Select Material", "Chat History"])
        
        with select_tab:
            st.subheader("Select Course Material")
            
            # Check if course materials have been loaded
            if not st.session_state.rag_manager.vector_stores:
                # Try to reload course materials directly from the session state data
                st.session_state.rag_manager.load_vector_stores_from_data(st.session_state.data)
                
                # If still no course materials, show debugging info and error
                if not st.session_state.rag_manager.vector_stores:
                    # Check if course materials metadata exists in the data
                    has_metadata = False
                    metadata_info = []
                    
                    for subject in st.session_state.data:
                        if isinstance(st.session_state.data[subject], dict) and "vector_store_metadata" in st.session_state.data[subject]:
                            has_metadata = True
                            metadata_info.append(f"Subject: {subject}, Weeks: {list(st.session_state.data[subject]['vector_store_metadata'].keys())}")
                    
                    if has_metadata:
                        st.error("Your course materials were found but couldn't be loaded properly. This might be due to a connection issue.")
                        with st.expander("Technical Details"):
                            st.write("Course materials found for:")
                            for info in metadata_info:
                                st.write(info)
                    else:
                        st.warning("No course materials found. Please upload your study materials first.")
                    
                    st.markdown("### Upload Materials")
                    st.info("To add your course materials, go to 'Add Queue Cards with AI' and upload your files.")
                    st.link_button("Go to Add Cards with AI", "/render_add_ai")
                    st.stop()
        
        # Get subjects that have course materials
        subjects_with_materials = []
        for subject in st.session_state.data:
            if isinstance(st.session_state.data[subject], dict) and "vector_store_metadata" in st.session_state.data[subject]:
                # Verify that this subject has valid course materials
                has_valid_materials = False
                for week in st.session_state.data[subject]["vector_store_metadata"]:
                    store_key = f"{subject}_{week}"
                    if store_key in st.session_state.rag_manager.vector_stores:
                        has_valid_materials = True
                        break
                
                if has_valid_materials:
                    subjects_with_materials.append(subject)
        
        if not subjects_with_materials:
            st.warning("No course materials found. Please upload materials in the 'Add Queue Cards with AI' page first.")
            st.button("Go to Add Cards with AI", on_click=lambda: st.switch_page("features/1_🤖_Add_Queue_Cards_with_AI.py"))
            st.stop()
            
        # Determine initial subject selection
        default_index = 0
        if st.session_state.selected_subject and st.session_state.selected_subject in subjects_with_materials:
            default_index = subjects_with_materials.index(st.session_state.selected_subject)
        
        # Subject selection
        selected_subject = st.selectbox(
            "Select subject",
            options=subjects_with_materials,
            index=default_index if subjects_with_materials else None
        )
        
        # Store the selected subject in session state
        st.session_state.selected_subject = selected_subject
        
        # Week selection - only show weeks that have valid materials
        weeks_with_materials = []
        if selected_subject and "vector_store_metadata" in st.session_state.data[selected_subject]:
            for week in st.session_state.data[selected_subject]["vector_store_metadata"]:
                store_key = f"{selected_subject}_{week}"
                if store_key in st.session_state.rag_manager.vector_stores:
                    weeks_with_materials.append(week)
            
        if not weeks_with_materials:
            st.warning(f"No course materials found for {selected_subject}. Please upload materials again in the 'Add Cards with AI' page first.")
            st.button("Go to Add Cards with AI", on_click=lambda: st.switch_page("features/1_🤖_Add_Queue_Cards_with_AI.py"))
            st.stop()
            
        # Determine initial week selection
        default_week_index = 0
        if (st.session_state.selected_week and 
            st.session_state.selected_week in weeks_with_materials):
            default_week_index = weeks_with_materials.index(st.session_state.selected_week)
            
        selected_week = st.selectbox(
            "Select week",
            options=weeks_with_materials,
            index=default_week_index if weeks_with_materials else None
        )
        
        # Store the selected week in session state
        st.session_state.selected_week = selected_week
        
        # Get vector store ID
        vector_store_id = None
        if (selected_subject and selected_week and 
            "vector_store_metadata" in st.session_state.data[selected_subject] and
            selected_week in st.session_state.data[selected_subject]["vector_store_metadata"]):
            vector_store_id = st.session_state.data[selected_subject]["vector_store_metadata"][selected_week]["id"]
        
        # Reset chat button
        if st.button("Reset Chat", type="secondary"):
            st.session_state.chat_messages = []
            st.session_state.thread_id = None
            st.session_state.assistant_id = None
            st.rerun()
            
        # Add the chat history tab content
        with history_tab:
            st.subheader("Chat History")
            
            # Check if user is logged in
            if user_email is None:
                st.info("Please log in to view your chat history.")
            else:
                # Get chat history from MongoDB (filter to tutor chats only)
                chat_sessions = mongodb.get_chat_sessions(user_email, chat_type=mongodb.CHAT_TYPE_TUTOR)
                
                if not chat_sessions:
                    st.info("No chat history found. Start a conversation to create history.")
                else:
                    # Display chat sessions
                    for session in chat_sessions:
                        # Use title if available, otherwise create one from subject and week
                        if 'title' in session and session['title']:
                            session_title = f"{session['title']} ({session.get('updated_at_readable', 'Unknown date')})"
                        else:
                            session_title = f"{session.get('subject', 'Unknown')} - Week {session.get('week', 'Unknown')} ({session.get('updated_at_readable', 'Unknown date')})"
                        
                        # Create an expander with preview of last message
                        with st.expander(session_title):
                            # Show session details
                            st.markdown(f"**Last message:** {session.get('last_message', 'No messages')[:100]}...")
                            
                            # Create a row for buttons
                            btn_col1, btn_col2, btn_col3 = st.columns([1, 1.2, 1])
                            
                            # Add option to load this conversation
                            session_id = session.get("_id")
                            with btn_col1:
                                if st.button(f"Load", key=f"load_{session_id}"):
                                    # Load the full session
                                    full_session = mongodb.get_chat_session(session_id)
                                    
                                    if full_session:
                                        # Set the session state variables to match this conversation
                                        st.session_state.chat_messages = full_session.get("messages", [])
                                        st.session_state.thread_id = full_session.get("thread_id")
                                        st.session_state.assistant_id = full_session.get("assistant_id")
                                        st.session_state.current_chat_id = session_id
                                        
                                        # Set the custom title if available
                                        if 'title' in full_session:
                                            st.session_state.chat_title = full_session.get("title")
                                        
                                        # Set the subject and week
                                        subject = full_session.get("subject")
                                        week = full_session.get("week")
                                        
                                        # Check if these are valid and try to set them
                                        if subject in st.session_state.data and "vector_store_metadata" in st.session_state.data[subject]:
                                            # Update the selection if the subject exists
                                            st.session_state.selected_subject = subject
                                            
                                            # Check if the week is valid for this subject
                                            if week in st.session_state.data[subject]["vector_store_metadata"]:
                                                st.session_state.selected_week = week
                                        
                                        # Rerun to update the UI
                                        st.rerun()
                                    else:
                                        st.error(f"Could not load conversation with ID: {session_id}")
                            
                            # Add option to rename this conversation
                            with btn_col2:
                                if st.button(f"Rename", key=f"rename_{session_id}"):
                                    # Store the session ID in session state to show rename form
                                    st.session_state[f"rename_session_{session_id}"] = True
                                    st.rerun()
                            
                            # Add option to delete this conversation
                            with btn_col3:
                                if st.button(f"Delete", key=f"delete_{session_id}", type="secondary"):
                                    success = mongodb.delete_chat_session(session_id, user_email)
                                    if success:
                                        st.success("Conversation deleted successfully.")
                                        # Reset current chat ID if this was the active chat
                                        if st.session_state.current_chat_id == session_id:
                                            st.session_state.current_chat_id = None
                                        # Rerun to update the list
                                        st.rerun()
                                    else:
                                        st.error("Failed to delete conversation. Please try again.")
                            
                            # Show rename form if button was clicked
                            if st.session_state.get(f"rename_session_{session_id}", False):
                                st.write("---")
                                st.write("Rename conversation:")
                                
                                # Get current title or default
                                current_title = session.get('title', f"{session.get('subject', 'Unknown')} - Week {session.get('week', 'Unknown')}")
                                new_title = st.text_input("New title:", value=current_title, key=f"new_title_{session_id}")
                                
                                rename_col1, rename_col2 = st.columns(2)
                                with rename_col1:
                                    if st.button("Save", key=f"save_rename_{session_id}"):
                                        success = mongodb.rename_chat_session(
                                            session_id, 
                                            user_email, 
                                            new_title
                                        )
                                        if success:
                                            st.success("Conversation renamed successfully.")
                                            # Update current chat title if this was the active chat
                                            if st.session_state.current_chat_id == session_id:
                                                st.session_state.chat_title = new_title
                                            # Reset rename state and rerun to update
                                            st.session_state[f"rename_session_{session_id}"] = False
                                            st.rerun()
                                        else:
                                            st.error("Failed to rename conversation. Please try again.")
                                
                                with rename_col2:
                                    if st.button("Cancel", key=f"cancel_rename_{session_id}", type="secondary"):
                                        # Reset rename state and rerun
                                        st.session_state[f"rename_session_{session_id}"] = False
                                        st.rerun()
        
        # Information about the chat
        with st.expander("About this feature"):
            st.markdown("""
            ### How it works
            
            This chat connects you with an AI study buddy that knows your course materials.
            
            Your study buddy can:
            - Answer questions about your uploaded materials
            - Explain difficult concepts
            - Help you understand challenging topics
            - Provide helpful examples and analogies
            
            For best results:
            - Ask specific questions
            - Upload complete course materials
            - Use this alongside practicing with flashcards
            """)
        
        with st.expander("Troubleshooting"):
            st.markdown("""
            ### Common Issues
            
            #### "No materials found" message
            If you're seeing this error even though you've uploaded files:
            
            1. Go to "Add Cards with AI" page
            2. Upload your materials again
            3. Make sure you see "Materials successfully processed" message
            4. Return to this page and try again
            
            #### Connection Issues
            Sometimes the system might experience temporary connection problems:
            
            1. Check your internet connection
            2. Wait a few minutes and try again
            3. Refresh the page
            
            #### Your study buddy doesn't know your materials
            If the AI doesn't seem to know about your uploaded content:
            
            1. Make sure you've selected the correct subject and week
            2. Try uploading your materials again with better quality files
            3. Break large files into smaller chunks when uploading
            """)
    
    with col2:
        st.subheader("Chat")
        
        # Check if course materials are selected
        if not vector_store_id:
            st.info("Please select a subject and week with uploaded course materials to start chatting.")
            st.stop()
        
        # Chat interface
        chat_container = st.container(height=500, border=True)
        
        # Add custom title input for the chat
        if st.session_state.chat_messages:
            # Create a collapsible section for managing the chat
            with st.expander("Chat Settings", expanded=False):
                # Show current title or set a default
                current_title = st.session_state.chat_title or f"{selected_subject} - Week {selected_week}"
                new_chat_title = st.text_input("Chat title:", value=current_title, key="chat_title_input")
                
                # Update chat title if changed
                if new_chat_title != current_title:
                    st.session_state.chat_title = new_chat_title
                    
                    # Update in database if we have a current chat ID
                    if st.session_state.current_chat_id and "email" in st.session_state:
                        mongodb.rename_chat_session(
                            st.session_state.current_chat_id,
                            st.session_state.email,
                            new_chat_title
                        )
        
        with chat_container:
            # Display chat messages
            for msg in st.session_state.chat_messages:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])
        
        # User input with a specific key for tutor chat
        user_message = st.chat_input("Ask a question about your course materials...", key="tutor_chat_input")
        
        if user_message:
            # Add user message to chat history
            st.session_state.chat_messages.append({"role": "user", "content": user_message})
            
            # Display user message
            with chat_container:
                with st.chat_message("user"):
                    st.write(user_message)
            
            # Display assistant message with streaming
            with chat_container:
                with st.chat_message("assistant"):
                    # Create a placeholder for the streaming response
                    message_placeholder = st.empty()
                    full_response = ""
                    
                    # Define the stream handler function
                    def stream_handler(content):
                        nonlocal full_response
                        full_response += content
                        # Update the placeholder with the accumulated response
                        message_placeholder.markdown(full_response + "▌")
                    
                    # Get assistant response with streaming
                    response = send_message(
                        message=user_message, 
                        vector_store_id=vector_store_id,
                        subject=selected_subject,
                        week=selected_week,
                        stream_handler=stream_handler,
                        stream=True
                    )
                    
                    # Update the final response without the cursor
                    message_placeholder.markdown(full_response)
            
            # Add assistant response to chat history
            st.session_state.chat_messages.append({"role": "assistant", "content": response})
            
            # Force a rerun to update the UI
            st.rerun()