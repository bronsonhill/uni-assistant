import streamlit as st
import sys
import os
import json
import datetime
import time
from typing import Dict, List, Optional, Any
import uuid

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import from Home and rag_manager
import Home
from rag_manager import RAGManager
from paywall import check_subscription, show_premium_benefits, display_subscription_status

def run():
    """Main assessments page content - this gets run by the navigation system"""
    # Check subscription status - required for this premium feature
    is_subscribed, user_email = check_subscription(required=True)
    
    # Display subscription status in sidebar
    # display_subscription_status()
    
    # If user is not subscribed, the above function will redirect them
    # The code below will only execute for subscribed users
    
    # Constants
    ASSESSMENTS_FILE = "assessments.json"
    
    # Helper functions
    def load_assessments() -> Dict:
        """Load assessment data from JSON file"""
        if os.path.exists(ASSESSMENTS_FILE):
            with open(ASSESSMENTS_FILE, "r") as f:
                return json.load(f)
        return {"assessments": []}
    
    def save_assessments(data: Dict) -> None:
        """Save assessment data to JSON file"""
        with open(ASSESSMENTS_FILE, "w") as f:
            json.dump(data, f, indent=2)
    
    def format_date(date_str: str) -> str:
        """Format date string for display"""
        if not date_str:
            return "No date"
        try:
            date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            return date_obj.strftime("%d %b %Y")
        except:
            return str(date_str)
    
    def extract_assessments_from_openai(text: str) -> List[Dict]:
        """
        Extract assessment information from text using OpenAI function calling
        """
        try:
            # Get OpenAI client from session state
            if "openai_client" not in st.session_state:
                from openai import OpenAI
                st.session_state.openai_client = OpenAI()
            
            # Define the function for OpenAI to extract assessment details
            functions = [
                {
                    "name": "extract_assessment_details",
                    "description": "Extract assessment details from course material text",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "assessments": {
                                "type": "array",
                                "description": "List of assessments extracted from the text",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "title": {
                                            "type": "string",
                                            "description": "Title or name of the assessment"
                                        },
                                        "subject": {
                                            "type": "string",
                                            "description": "Subject or course the assessment belongs to"
                                        },
                                        "type": {
                                            "type": "string",
                                            "description": "Type of assessment (exam, quiz, assignment, project, etc.)"
                                        },
                                        "due_date": {
                                            "type": "string",
                                            "description": "Due date in YYYY-MM-DD format"
                                        },
                                        "release_date": {
                                            "type": "string",
                                            "description": "Release date in YYYY-MM-DD format"
                                        },
                                        "weight_percentage": {
                                            "type": "number",
                                            "description": "Weight of the assessment as a percentage (0-100)"
                                        },
                                        "description": {
                                            "type": "string",
                                            "description": "Description or details about the assessment"
                                        },
                                        "location": {
                                            "type": "string",
                                            "description": "Location where the assessment takes place"
                                        }
                                    },
                                    "required": ["title", "subject"]
                                }
                            }
                        },
                        "required": ["assessments"]
                    }
                }
            ]
            
            # Call OpenAI API
            response = st.session_state.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an assistant specialized in extracting assessment information from course materials. Extract all assessment details like assignments, quizzes, exams, etc. with their due dates, weights, and descriptions. Note that it isthe year " + str(datetime.datetime.now().year) + "."},
                    {"role": "user", "content": text}
                ],
                functions=functions,
                function_call={"name": "extract_assessment_details"}
            )
            
            # Parse the response
            function_args = json.loads(response.choices[0].message.function_call.arguments)
            extracted_assessments = function_args.get("assessments", [])
            
            # Generate IDs for each assessment
            for assessment in extracted_assessments:
                assessment["id"] = str(uuid.uuid4())
            
            return extracted_assessments
            
        except Exception as e:
            st.error(f"Error extracting assessments: {str(e)}")
            return []
    
    # Initialize session state
    if "assessments_data" not in st.session_state:
        st.session_state.assessments_data = load_assessments()
    
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    
    if "show_add_form" not in st.session_state:
        st.session_state.show_add_form = False
    
    if "editing_assessment" not in st.session_state:
        st.session_state.editing_assessment = None
    
    if "filter_subject" not in st.session_state:
        st.session_state.filter_subject = "All"
    
    if "filter_period" not in st.session_state:
        st.session_state.filter_period = "All"
    
    if "extracted_assessments" not in st.session_state:
        st.session_state.extracted_assessments = []
    
    if "assessment_inclusion" not in st.session_state:
        st.session_state.assessment_inclusion = []
    
    if "rag_manager" not in st.session_state:
        st.session_state.rag_manager = Home.init_rag_manager()
    
    # Title and description
    st.title("📅 Assessment Dashboard")
    st.markdown("""
    Stay organized with all your deadlines in one place! Track exams, assignments, and quizzes.
    Upload your syllabus to automatically find and add important dates, or add them manually.
    """)
    
    # Main tabs
    tab1, tab2, tab3 = st.tabs(["Dashboard", "Add/Edit Assessments", "Assessment Chat"])
    
    # Dashboard tab
    with tab1:
        st.subheader("Upcoming Assessments")
        
        # Filters
        col1, col2 = st.columns(2)
        
        with col1:
            # Get unique subjects
            subjects = ["All"]
            subject_set = set()
            for assessment in st.session_state.assessments_data["assessments"]:
                if "subject" in assessment and assessment["subject"]:
                    subject_set.add(assessment["subject"])
            subjects.extend(sorted(list(subject_set)))
            
            st.session_state.filter_subject = st.selectbox(
                "Filter by Subject",
                options=subjects,
                index=subjects.index(st.session_state.filter_subject) if st.session_state.filter_subject in subjects else 0
            )
        
        with col2:
            period_options = ["All", "This Week", "Next Week", "This Month", "Overdue"]
            st.session_state.filter_period = st.selectbox(
                "Filter by Period",
                options=period_options,
                index=period_options.index(st.session_state.filter_period) if st.session_state.filter_period in period_options else 0
            )
        
        # Apply filters
        filtered_assessments = []
        today = datetime.datetime.now().date()
        
        for assessment in st.session_state.assessments_data["assessments"]:
            # Subject filter
            if st.session_state.filter_subject != "All" and assessment.get("subject") != st.session_state.filter_subject:
                continue
            
            # Period filter
            if st.session_state.filter_period != "All":
                due_date_str = assessment.get("due_date")
                if not due_date_str:
                    continue
                    
                try:
                    due_date = datetime.datetime.strptime(due_date_str, "%Y-%m-%d").date()
                    
                    if st.session_state.filter_period == "This Week":
                        # Start of current week (Monday)
                        start_of_week = today - datetime.timedelta(days=today.weekday())
                        end_of_week = start_of_week + datetime.timedelta(days=6)
                        if not (start_of_week <= due_date <= end_of_week):
                            continue
                            
                    elif st.session_state.filter_period == "Next Week":
                        # Start of next week
                        start_of_this_week = today - datetime.timedelta(days=today.weekday())
                        start_of_next_week = start_of_this_week + datetime.timedelta(days=7)
                        end_of_next_week = start_of_next_week + datetime.timedelta(days=6)
                        if not (start_of_next_week <= due_date <= end_of_next_week):
                            continue
                            
                    elif st.session_state.filter_period == "This Month":
                        # Same month and year
                        if due_date.month != today.month or due_date.year != today.year:
                            continue
                            
                    elif st.session_state.filter_period == "Overdue":
                        # Due date before today
                        if due_date >= today:
                            continue
                except:
                    continue
            
            filtered_assessments.append(assessment)
        
        # Sort by due date (handle None values safely)
        def safe_due_date_key(assessment):
            due_date = assessment.get("due_date")
            return due_date if due_date else "9999-12-31"  # Default to far future for items without due date
        
        filtered_assessments.sort(key=safe_due_date_key)
        
        # Display assessments
        if not filtered_assessments:
            st.info("No assessments match the selected filters.")
        else:
            # Toggle between view modes
            view_mode = st.radio("View mode:", ["Card View", "Table View"], horizontal=True)
            
            if view_mode == "Table View":
                # Prepare data for the editable dataframe
                if "edited_data" not in st.session_state:
                    st.session_state.edited_data = {}
                
                # Prepare data for display
                table_data = []
                for assessment in filtered_assessments:
                    due_date = assessment.get("due_date")
                    if due_date:
                        try:
                            due_date_obj = datetime.datetime.strptime(due_date, "%Y-%m-%d").date()
                            days_until = (due_date_obj - today).days
                            if days_until < 0:
                                days_status = f"Overdue by {abs(days_until)} days"
                            elif days_until == 0:
                                days_status = "Due today"
                            else:
                                days_status = f"In {days_until} days"
                        except:
                            days_status = ""
                    else:
                        days_status = ""
                    
                    table_data.append({
                        "ID": assessment.get("id", ""),
                        "Subject": assessment.get("subject", ""),
                        "Title": assessment.get("title", ""),
                        "Type": assessment.get("type", ""),
                        "Due Date": assessment.get("due_date", ""),
                        "Status": days_status,
                        "Weight (%)": assessment.get("weight_percentage", 0),
                        "Release Date": assessment.get("release_date", ""),
                        "Location": assessment.get("location", ""),
                        "Description": assessment.get("description", "")
                    })
                
                # Convert to pandas DataFrame for display
                import pandas as pd
                df = pd.DataFrame(table_data)
                
                # Use Streamlit's data editor
                edited_df = st.data_editor(
                    df,
                    column_config={
                        "ID": st.column_config.TextColumn("ID", disabled=True),
                        "Subject": st.column_config.TextColumn("Subject"),
                        "Title": st.column_config.TextColumn("Title"),
                        "Type": st.column_config.SelectboxColumn(
                            "Type", 
                            options=["Assignment", "Exam", "Quiz", "Project", "Presentation", "Other"]
                        ),
                        "Due Date": st.column_config.TextColumn("Due Date"),
                        "Status": st.column_config.TextColumn("Status", disabled=True),
                        "Weight (%)": st.column_config.NumberColumn("Weight (%)", min_value=0, max_value=100),
                        "Release Date": st.column_config.TextColumn("Release Date"),
                        "Location": st.column_config.TextColumn("Location"),
                        "Description": st.column_config.TextColumn("Description"),
                    },
                    hide_index=True,
                    key="assessment_table",
                    num_rows="dynamic"
                )
                
                # Handle edits and save changes
                if not edited_df.equals(df):
                    # Process changes
                    for _, row in edited_df.iterrows():
                        # Get the assessment ID
                        assessment_id = row["ID"]
                        
                        # Find the corresponding assessment
                        for i, assessment in enumerate(st.session_state.assessments_data["assessments"]):
                            if assessment.get("id") == assessment_id:
                                # Update assessment with edited values
                                st.session_state.assessments_data["assessments"][i].update({
                                    "subject": row["Subject"],
                                    "title": row["Title"],
                                    "type": row["Type"],
                                    "due_date": str(row["Due Date"]) if pd.notna(row["Due Date"]) else "",
                                    "weight_percentage": float(row["Weight (%)"]) if pd.notna(row["Weight (%)"]) else 0,
                                    "release_date": str(row["Release Date"]) if pd.notna(row["Release Date"]) else "",
                                    "location": row["Location"],
                                    "description": row["Description"]
                                })
                                break
                    
                    # Save changes
                    save_assessments(st.session_state.assessments_data)
                    st.success("Changes saved successfully!")
                    
                    # Handle new rows (rows without ID)
                    new_rows = edited_df[edited_df["ID"] == ""]
                    if not new_rows.empty:
                        for _, row in new_rows.iterrows():
                            new_assessment = {
                                "id": str(uuid.uuid4()),
                                "subject": row["Subject"],
                                "title": row["Title"],
                                "type": row["Type"],
                                "due_date": str(row["Due Date"]) if pd.notna(row["Due Date"]) else "",
                                "weight_percentage": float(row["Weight (%)"]) if pd.notna(row["Weight (%)"]) else 0,
                                "release_date": str(row["Release Date"]) if pd.notna(row["Release Date"]) else "",
                                "location": row["Location"],
                                "description": row["Description"]
                            }
                            st.session_state.assessments_data["assessments"].append(new_assessment)
                        
                        # Save changes again for new rows
                        save_assessments(st.session_state.assessments_data)
                
                # Add delete button functionality
                if st.button("Delete Selected Rows"):
                    # This would require row selection, which isnt directly supported
                    # Consider using checkboxes or other methods for selection
                    st.warning("Row deletion not implemented in table view. Use card view to delete assessments.")
            
            else:  # Card View
                # Group by subject
                assessments_by_subject = {}
                for assessment in filtered_assessments:
                    subject = assessment.get("subject", "Other")
                    if subject not in assessments_by_subject:
                        assessments_by_subject[subject] = []
                    assessments_by_subject[subject].append(assessment)
                
                # Display by subject
                for subject, assessments in assessments_by_subject.items():
                    st.subheader(subject)
                    
                    for assessment in assessments:
                        with st.container(border=True):
                            col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 1, 1])
                            
                            with col1:
                                title = assessment.get("title", "Untitled Assessment")
                                assessment_type = assessment.get("type", "")
                                st.markdown(f"**{title}** ({assessment_type})")
                                
                                description = assessment.get("description", "")
                                if description:
                                    with st.expander("Details"):
                                        st.write(description)
                            
                            with col2:
                                due_date = assessment.get("due_date")
                                if due_date:
                                    formatted_due = format_date(due_date)
                                    
                                    # Calculate days until due
                                    try:
                                        due_date_obj = datetime.datetime.strptime(due_date, "%Y-%m-%d").date()
                                        days_until = (due_date_obj - today).days
                                        
                                        if days_until < 0:
                                            st.markdown(f"**Due Date:** {formatted_due} (Overdue by {abs(days_until)} days)")
                                        elif days_until == 0:
                                            st.markdown(f"**Due Date:** {formatted_due} (Due today)")
                                        else:
                                            st.markdown(f"**Due Date:** {formatted_due} (In {days_until} days)")
                                    except:
                                        st.markdown(f"**Due Date:** {formatted_due}")
                                else:
                                    st.markdown("**Due Date:** Not specified")
                            
                            with col3:
                                weight = assessment.get("weight_percentage")
                                if weight is not None:
                                    st.write(f"Weight: {weight}%")
                            
                            with col4:
                                if st.button("Edit", key=f"edit_{assessment.get('id', '')}", use_container_width=True):
                                    st.session_state.editing_assessment = assessment
                                    st.session_state.show_add_form = True
                                    # Switch to the Add/Edit tab
                                    st.rerun()
                            
                            with col5:
                                if st.button("Delete", key=f"delete_{assessment.get('id', '')}", use_container_width=True):
                                    # Remove the assessment
                                    st.session_state.assessments_data["assessments"] = [
                                        a for a in st.session_state.assessments_data["assessments"] 
                                        if a.get("id") != assessment.get("id")
                                    ]
                                    # Save changes
                                    save_assessments(st.session_state.assessments_data)
                                    st.success("Assessment deleted.")
                                    st.rerun()
    
    # Add/Edit Assessments tab
    with tab2:
        st.subheader("Manage Assessments")
        
        # Two columns - one for manual entry, one for extraction
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Manual Entry")
            
            # Button to toggle form visibility
            if not st.session_state.show_add_form and not st.session_state.editing_assessment:
                if st.button("Add New Assessment", type="primary"):
                    st.session_state.show_add_form = True
                    st.rerun()
            
            # Assessment form
            if st.session_state.show_add_form or st.session_state.editing_assessment:
                with st.form("assessment_form"):
                    # Pre-fill form if editing
                    editing = st.session_state.editing_assessment is not None
                    assessment = st.session_state.editing_assessment or {}
                    
                    form_title = st.text_input("Title", value=assessment.get("title", ""))
                    
                    # Get all existing subjects for the dropdown
                    subject_set = set()
                    for a in st.session_state.assessments_data["assessments"]:
                        if "subject" in a and a["subject"]:
                            subject_set.add(a["subject"])
                    
                    # Add the current subject if editing
                    if editing and assessment.get("subject"):
                        subject_set.add(assessment.get("subject"))
                    
                    subjects_list = sorted(list(subject_set))
                    
                    # Subject selection with "New Subject" option
                    use_existing_subject = True
                    if subjects_list:
                        use_existing_subject = st.radio(
                            "Subject", 
                            ["Choose existing subject", "Add new subject"],
                            horizontal=True,
                            index=0 if assessment.get("subject") in subjects_list else 1
                        ) == "Choose existing subject"
                    else:
                        use_existing_subject = False
                        
                    if use_existing_subject and subjects_list:
                        selected_index = 0
                        if editing and assessment.get("subject") in subjects_list:
                            selected_index = subjects_list.index(assessment.get("subject"))
                            
                        form_subject = st.selectbox(
                            "Select Subject", 
                            subjects_list,
                            index=selected_index
                        )
                    else:
                        form_subject = st.text_input("Enter New Subject", value=assessment.get("subject", ""))
                    form_type = st.selectbox(
                        "Type", 
                        options=["Assignment", "Exam", "Quiz", "Project", "Presentation", "Other"],
                        index=["Assignment", "Exam", "Quiz", "Project", "Presentation", "Other"].index(assessment.get("type", "Assignment")) if assessment.get("type") in ["Assignment", "Exam", "Quiz", "Project", "Presentation", "Other"] else 0
                    )
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        form_due_date = st.date_input(
                            "Due Date",
                            value=datetime.datetime.strptime(assessment.get("due_date", ""), "%Y-%m-%d").date() if assessment.get("due_date") else None,
                            format="YYYY-MM-DD"
                        )
                    
                    with col2:
                        form_release_date = st.date_input(
                            "Release Date",
                            value=datetime.datetime.strptime(assessment.get("release_date", ""), "%Y-%m-%d").date() if assessment.get("release_date") else None,
                            format="YYYY-MM-DD"
                        )
                    
                    form_weight = st.slider(
                        "Weight (%)",
                        min_value=0,
                        max_value=100,
                        value=int(assessment.get("weight_percentage", 0)) if assessment.get("weight_percentage") is not None else 0
                    )
                    
                    form_location = st.text_input("Location", value=assessment.get("location", ""))
                    form_description = st.text_area("Description", value=assessment.get("description", ""))
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        submit = st.form_submit_button("Save Assessment", use_container_width=True)
                    
                    with col2:
                        cancel = st.form_submit_button("Cancel", use_container_width=True)
                    
                    if submit:
                        if not form_title or not form_subject:
                            st.error("Title and Subject are required fields.")
                        else:
                            # Create or update assessment
                            new_assessment = {
                                "id": assessment.get("id", str(uuid.uuid4())),
                                "title": form_title,
                                "subject": form_subject,
                                "type": form_type,
                                "due_date": form_due_date.strftime("%Y-%m-%d") if form_due_date else "",
                                "release_date": form_release_date.strftime("%Y-%m-%d") if form_release_date else "",
                                "weight_percentage": form_weight,
                                "location": form_location,
                                "description": form_description
                            }
                            
                            if editing:
                                # Update existing assessment
                                st.session_state.assessments_data["assessments"] = [
                                    new_assessment if a.get("id") == new_assessment["id"] else a
                                    for a in st.session_state.assessments_data["assessments"]
                                ]
                            else:
                                # Add new assessment
                                st.session_state.assessments_data["assessments"].append(new_assessment)
                            
                            # Save changes
                            save_assessments(st.session_state.assessments_data)
                            
                            # Reset form state
                            st.session_state.show_add_form = False
                            st.session_state.editing_assessment = None
                            
                            st.success("Assessment saved successfully!")
                            st.rerun()
                    
                    if cancel:
                        st.session_state.show_add_form = False
                        st.session_state.editing_assessment = None
                        st.rerun()
        
        with col2:
            st.markdown("### Extract from Course Materials")
            st.markdown("""
            Upload course materials (syllabus, assignment sheets, etc.) to automatically extract assessment information.
            """)
            
            # Get all existing subjects for the dropdown
            subject_set = set()
            for a in st.session_state.assessments_data["assessments"]:
                if "subject" in a and a["subject"]:
                    subject_set.add(a["subject"])
            subjects_list = sorted(list(subject_set))
            
            # Subject selection with "New Subject" option
            use_existing_subject = True
            if subjects_list:
                use_existing_subject = st.radio(
                    "Subject for extracted assessments", 
                    ["Choose existing subject", "Add new subject"],
                    horizontal=True
                ) == "Choose existing subject"
            else:
                use_existing_subject = False
                
            if use_existing_subject and subjects_list:
                extraction_subject = st.selectbox("Select Subject", subjects_list)
            else:
                extraction_subject = st.text_input("Enter Subject for Extracted Assessments")
            
            # File upload
            uploaded_file = st.file_uploader(
                "Upload a file",
                type=["pdf", "txt", "csv", "md", "docx"],
                key="assessment_file_upload"
            )
            
            if uploaded_file:
                st.success(f"File uploaded: {uploaded_file.name}")
                
                # Process file button
                if st.button("Extract Assessments", type="primary"):
                    with st.spinner("Analyzing document and extracting assessment information..."):
                        try:
                            # Get file content
                            if uploaded_file.type == "application/pdf":
                                # Use RAG manager to extract text from PDF
                                import tempfile
                                import pdfplumber
                                
                                # Create a temporary file
                                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                                    temp_file.write(uploaded_file.getvalue())
                                    temp_path = temp_file.name
                                
                                # Extract text from PDF
                                extracted_text = ""
                                with pdfplumber.open(temp_path) as pdf:
                                    for page in pdf.pages:
                                        extracted_text += page.extract_text() + "\n\n"
                                
                                # Remove the temporary file
                                os.remove(temp_path)
                                
                            else:  # TXT file
                                extracted_text = uploaded_file.getvalue().decode("utf-8")
                            
                            # Extract assessments
                            extracted_assessments = extract_assessments_from_openai(extracted_text)
                            
                            # Apply selected subject if provided and OpenAI didn't identify a subject
                            if extraction_subject:
                                for assessment in extracted_assessments:
                                    if not assessment.get("subject"):
                                        assessment["subject"] = extraction_subject
                            
                            if extracted_assessments:
                                # Store in session state
                                st.session_state.extracted_assessments = extracted_assessments
                                st.session_state.assessment_inclusion = [True] * len(extracted_assessments)
                                
                                st.success(f"Found {len(extracted_assessments)} assessments!")
                                
                                # Display extracted assessments
                                for i, assessment in enumerate(st.session_state.extracted_assessments):
                                    with st.container(border=True):
                                        st.write(f"**{i+1}. {assessment.get('title', 'Untitled')}**")
                                        cols = st.columns(2)
                                        
                                        with cols[0]:
                                            st.write(f"**Subject:** {assessment.get('subject', 'N/A')}")
                                            st.write(f"**Type:** {assessment.get('type', 'N/A')}")
                                            due_date = assessment.get('due_date')
                                            if due_date:
                                                st.write(f"**Due Date:** {format_date(due_date)}")
                                            else:
                                                st.write("**Due Date:** Not specified")
                                            if assessment.get('weight_percentage') is not None:
                                                st.write(f"**Weight:** {assessment.get('weight_percentage')}%")
                                        
                                        with cols[1]:
                                            if assessment.get('description'):
                                                st.write(f"**Description:** {assessment.get('description')}")
                                        
                                        # Checkbox to include this assessment - store value in session state
                                        st.session_state.assessment_inclusion[i] = st.checkbox(
                                            "Add to my assessments", 
                                            value=st.session_state.assessment_inclusion[i], 
                                            key=f"include_{i}"
                                        )
                            else:
                                st.warning("No assessments found in the uploaded file.")
                            
                        except Exception as e:
                            st.error(f"Error processing file: {str(e)}")
            
            # Add button to save assessments if there are any extracted ones in session state
            if len(st.session_state.extracted_assessments) > 0:
                if st.button("Add Selected Assessments", type="primary", key="add_selected_final"):
                    # Get the selected assessments based on inclusion flags
                    selected_assessments = [
                        assessment for i, assessment in enumerate(st.session_state.extracted_assessments)
                        if st.session_state.assessment_inclusion[i]
                    ]
                    
                    if selected_assessments:
                        # Add to existing assessments
                        st.session_state.assessments_data["assessments"].extend(selected_assessments)
                        
                        # Save changes
                        save_assessments(st.session_state.assessments_data)
                        
                        # Clear the extraction data
                        st.session_state.extracted_assessments = []
                        st.session_state.assessment_inclusion = []
                        
                        st.success(f"Added {len(selected_assessments)} assessments successfully!")
                        st.rerun()
                    else:
                        st.warning("No assessments selected. Please check at least one assessment to add.")
            
            # Sample text to show how extraction works
            with st.expander("See Example"):
                st.markdown("""
                **Example Syllabus Text:**
                
                ```
                CS401 Introduction to Machine Learning
                Spring 2025
                
                Assessments:
                1. Midterm Exam (20%) - March 15, 2025
                   Covers topics from weeks 1-6
                   Location: Main Hall 301
                
                2. Final Project (30%) - Due April 30, 2025
                   Implementation of a machine learning algorithm
                   Released on March 20, 2025
                
                3. Weekly Quizzes (25% total) - Every Friday starting Feb 7
                   Best 8 out of 10 quizzes will count
                
                4. Programming Assignments (25%)
                   Assignment 1 (10%) - Due Feb 20, 2025
                   Assignment 2 (15%) - Due April 10, 2025
                ```
                
                This text would be automatically parsed to extract the assessment information.
                """)
    
    # Assessment Chat tab
    with tab3:
        st.subheader("Chat About Your Assessments")
        st.markdown("""
        Ask questions about your assessments like:
        - What do I have due this week?
        - When is my next exam?
        - Tell me about my Computer Science assignments
        - What assessments are worth more than 20%?
        """)
        
        # Chat interface
        chat_container = st.container(height=400, border=True)
        
        with chat_container:
            # Display chat messages
            for msg in st.session_state.chat_messages:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])
        
        # Function to get assessment response
        def get_assessment_response(query: str) -> str:
            try:
                # Get assessments data
                assessments = st.session_state.assessments_data["assessments"]
                
                # Create context with previous messages
                previous_messages = [{"role": msg["role"], "content": msg["content"]} 
                                  for msg in st.session_state.chat_messages[-5:]]  # Last 5 messages for context
                
                # Get today's date to help with relative date queries
                today = datetime.datetime.now().date()
                
                # Create system message with instructions
                system_message = f"""You are an assistant helping a student understand their assessment schedule.
    Today's date is {today.strftime('%Y-%m-%d')}.
    Answer questions about the student's assessments based on the provided data.
    Be concise but informative, and format your responses clearly.
    If asked about a specific time period like "this week", calculate the date range relative to today's date.
    """
                
                # Call OpenAI API
                response = st.session_state.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_message},
                        *previous_messages,
                        {"role": "user", "content": f"Here are my assessments: {json.dumps(assessments)}\n\nMy question is: {query}"}
                    ],
                    temperature=0.7
                )
                
                return response.choices[0].message.content
                
            except Exception as e:
                return f"Error processing your question: {str(e)}"
        
        # User input
        user_question = st.chat_input("Ask about your assessments...")
        
        if user_question:
            # Add user message to chat history
            st.session_state.chat_messages.append({"role": "user", "content": user_question})
            
            # Display user message
            with chat_container:
                with st.chat_message("user"):
                    st.write(user_question)
            
            # Get response
            with st.spinner("Thinking..."):
                response = get_assessment_response(user_question)
            
            # Add assistant response to chat history
            st.session_state.chat_messages.append({"role": "assistant", "content": response})
            
            # Display assistant response
            with chat_container:
                with st.chat_message("assistant"):
                    st.write(response)
            
            # Force a rerun to update the UI
            st.rerun()