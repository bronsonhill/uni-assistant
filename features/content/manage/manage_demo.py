"""
Demo mode UI for manage module.

This module provides demo content for unauthenticated users to showcase
the Manage Questions functionality.
"""
import streamlit as st
import datetime

# Import from Home
from Home import calculate_weighted_score

# Import from core module
from features.content.manage.manage_core import get_score_emoji

def show_premium_benefits():
    """Show premium benefits section for authenticated but non-premium users"""
    st.markdown("---")
    st.subheader("Premium Features Preview")
    st.markdown("""
    With a premium subscription, you'll get access to additional features:
    
    - Advanced analytics on your learning progress
    - AI-powered study recommendations
    - Enhanced question organization and tagging
    - Study schedule optimization
    """)
    
    # Add upgrade button
    st.button("Upgrade to Premium", type="primary", disabled=True)

def show_demo_content():
    """Display demo content for users in preview mode"""
    # Create dropdown for subject, defaulting to Computer Science
    subject_to_view = st.selectbox(
        "Select Subject",
        ["Computer Science", "Biology", "Law"], 
        index=1,  # Default to Biology
        key="demo_view_subject", 
        disabled=False
    )
    
    # Create dropdown for week, defaulting to Week 1
    week_to_view = st.selectbox(
        "Select Week",
        ["1", "2", "3"],
        index=0, 
        key="demo_view_week",
        disabled=False
    )
    
    # Show a mock metrics section
    st.subheader(f"Questions for {subject_to_view} - Week {week_to_view}")
    
    # Display mock metrics
    metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
    
    with metrics_col1:
        st.metric("Average Score", "🟠 3.5/5")
    
    with metrics_col2:
        st.metric("Knowledge Level", "🟢 2 | 🟠 1 | 🔴 0")
        
    with metrics_col3:
        st.metric("Mastery Level", "67%")
    
    # Show mock histogram
    with st.expander("Score Distribution", expanded=True):
        # Sample data for the histogram
        scores = [3.2, 3.5, 4.0]
        score_df = pd.DataFrame({'score': scores})
        
        # Create the histogram
        histogram = alt.Chart(score_df).mark_bar().encode(
            alt.X('score:Q', bin=alt.Bin(maxbins=10), title='Score'),
            alt.Y('count()', title='Number of Questions'),
            alt.Color('score:Q', scale=alt.Scale(scheme='redyellowgreen'), title='Score'),
            tooltip=['count()', alt.Tooltip('score:Q', title='Score Range')]
        ).properties(
            title='Score Distribution',
            width='container',
            height=200
        )
        
        st.altair_chart(histogram, use_container_width=True)
    
    # Select questions based on the subject
    if subject_to_view == "Computer Science":
        # Computer Science questions
        _display_demo_question(
            0,
            {
                "question": "Explain the difference between stack and heap memory allocation.",
                "answer": "Stack memory allocation is used for static memory allocation where variables are allocated and deallocated in a last-in-first-out order, typically for local variables and function calls. It's faster but limited in size. Heap memory allocation is used for dynamic memory allocation at runtime, managed by the programmer or garbage collector. It's slower but allows for larger and variable-sized data structures with lifetimes not tied to specific scopes.",
                "scores": [
                    {"score": 4.0, "timestamp": "2023-11-15T14:30:00", "user_answer": "Stack memory is for static allocation (function calls, local variables) and follows LIFO order, while heap is for dynamic allocation with manual management and longer lifetimes."}
                ]
            },
            "cs_q1"
        )
        
        _display_demo_question(
            1,
            {
                "question": "What is object-oriented programming and what are its key principles?",
                "answer": "Object-oriented programming (OOP) is a programming paradigm based on the concept of objects that contain data and code. It organizes software design around data, or objects, rather than functions and logic. Key principles include encapsulation (hiding internal states), inheritance (parent-child class relationships), polymorphism (different implementations of the same interface), and abstraction (simplifying complex systems).",
                "scores": [
                    {"score": 3.5, "timestamp": "2023-11-15T14:30:00", "user_answer": "OOP is programming with objects that have data and methods. The main principles are encapsulation, inheritance, polymorphism, and abstraction."}
                ]
            },
            "cs_q2"
        )
        
        _display_demo_question(
            2,
            {
                "question": "Describe the time complexity of common sorting algorithms and their trade-offs.",
                "answer": "Bubble Sort: O(n²) average and worst case, simple but inefficient. Selection Sort: O(n²) in all cases, minimal memory usage. Insertion Sort: O(n²) average and worst, but O(n) for nearly sorted data. Merge Sort: O(n log n) in all cases, stable but requires O(n) extra space. Quick Sort: O(n log n) average, O(n²) worst case, in-place but unstable. Heap Sort: O(n log n) in all cases, in-place but slower than quicksort in practice.",
                "scores": [
                    {"score": 3.0, "timestamp": "2023-11-15T14:30:00", "user_answer": "Bubble, selection, insertion sorts are O(n²). Merge and quick sorts are O(n log n) but merge sort needs extra space while quicksort can degrade to O(n²)."}
                ]
            },
            "cs_q3"
        )
    elif subject_to_view == "Biology":
        # Biology questions
        _display_demo_question(
            0,
            {
                "question": "Explain the difference between mitosis and meiosis in cell division.",
                "answer": "Mitosis is cell division that results in two identical daughter cells with the same chromosome count as the parent cell, used for growth and repair. Meiosis produces four genetically diverse cells with half the chromosomes, used for sexual reproduction.",
                "scores": [
                    {"score": 4.0, "timestamp": "2023-11-15T14:30:00", "user_answer": "Mitosis creates two identical cells with same chromosome count, while meiosis creates four cells with half the chromosomes and genetic diversity."}
                ]
            },
            "bio_q1"
        )
        
        _display_demo_question(
            1,
            {
                "question": "Describe the structure and function of chloroplasts in plant cells.",
                "answer": "Chloroplasts are organelles in plant cells with a double membrane, stroma, and thylakoids arranged in grana. They contain chlorophyll and perform photosynthesis, converting light energy to chemical energy (ATP and NADPH) and fixing carbon into glucose.",
                "scores": [
                    {"score": 3.5, "timestamp": "2023-11-15T14:30:00", "user_answer": "Chloroplasts are plant organelles with double membranes that contain chlorophyll and carry out photosynthesis to convert light energy into chemical energy."}
                ]
            },
            "bio_q2"
        )
        
        _display_demo_question(
            2,
            {
                "question": "What are the main components of the cell membrane and how does its structure relate to its function?",
                "answer": "The cell membrane consists of a phospholipid bilayer with embedded proteins, cholesterol, and glycoproteins/glycolipids. This structure creates selective permeability, allowing the membrane to control what enters and exits the cell while maintaining fluidity and enabling functions like cell signaling.",
                "scores": [
                    {"score": 3.0, "timestamp": "2023-11-15T14:30:00", "user_answer": "Cell membranes are made of phospholipid bilayers with proteins. The structure allows selective permeability and helps control what moves in and out of the cell."}
                ]
            },
            "bio_q3"
        )
    else:  # Law
        # Law questions
        _display_demo_question(
            0,
            {
                "question": "Explain the difference between common law and civil law legal systems.",
                "answer": "Common law systems are based on precedent and judge-made law, where prior court decisions bind future cases, prominent in the UK and former colonies. Civil law systems are codified, relying primarily on comprehensive written codes and statutes, dominant in continental Europe, Latin America, and parts of Asia and Africa. Common law is more flexible and judge-centered, while civil law is more structured and legislation-centered.",
                "scores": [
                    {"score": 4.0, "timestamp": "2023-11-15T14:30:00", "user_answer": "Common law is based on precedent (judge-made law) while civil law is based on comprehensive written codes and statutes."}
                ]
            },
            "law_q1"
        )
        
        _display_demo_question(
            1,
            {
                "question": "What is the doctrine of precedent (stare decisis) and why is it important in common law systems?",
                "answer": "The doctrine of precedent (stare decisis) is the principle that courts should follow prior decisions when ruling on similar cases. It's vital in common law systems because it ensures consistency and predictability in the law, promotes equality by treating similar cases alike, provides efficiency in legal reasoning, creates stability in the legal system, and allows for gradual, organic development of law through distinguishing cases and occasional overruling.",
                "scores": [
                    {"score": 3.5, "timestamp": "2023-11-15T14:30:00", "user_answer": "Stare decisis means courts follow previous decisions. It's important because it creates consistency, predictability, and equality in how cases are decided."}
                ]
            },
            "law_q2"
        )
        
        _display_demo_question(
            2,
            {
                "question": "Describe the key elements necessary to form a legally binding contract.",
                "answer": "A legally binding contract requires offer (a clear proposal), acceptance (unequivocal agreement to the offer), consideration (something of value exchanged), intention to create legal relations (parties intend to be legally bound), capacity (parties must be legally able to enter contracts), and legality (the purpose must be legal). Some contracts also require specific formalities like writing or witnessing.",
                "scores": [
                    {"score": 3.0, "timestamp": "2023-11-15T14:30:00", "user_answer": "Contract formation needs an offer, acceptance, consideration, intention to create legal relations, legal capacity, and a lawful purpose."}
                ]
            },
            "law_q3"
        )

def _display_demo_question(index, question, key_prefix):
    """Display a demo question with its details and actions"""
    with st.container(border=True):
        # Get score info
        scores = question.get("scores", [])
        # Demo data doesn't have last_practiced, so we pass None explicitly
        # If scores exist, calculate; otherwise, use the demo default 3.5
        weighted_score = calculate_weighted_score(scores, last_practiced=None) if scores else 3.5
        score_display = f"{get_score_emoji(weighted_score)} {weighted_score:.1f}/5" if weighted_score is not None else "⚪ 0/5"
        
        col1, col2, col3, col4 = st.columns([5, 1, 1, 1])
        
        with col1:
            st.markdown(f"**Q{index+1}: {question['question']}**")
        
        with col2:
            st.markdown(f"Score: **{score_display}**")
        
        with col3:
            st.button("Edit", key=f"demo_edit_{key_prefix}", use_container_width=True, disabled=True)
        
        with col4:
            st.button("Delete", key=f"demo_delete_{key_prefix}", use_container_width=True, disabled=True)
        
        # Add details expander below all columns
        with st.expander(f"View details for Q{index+1}"):
            # Question content
            st.write("**Question:**")
            st.write(question["question"])
            
            # Expected answer
            st.write("**Expected Answer:**")
            st.write(question["answer"] if question["answer"] else "No answer provided")
            
            # Score history
            st.write("**Score History:**")
            emoji = get_score_emoji(weighted_score)
            st.metric("Current Score", f"{emoji} {weighted_score:.1f}/5")
            
            # Show past answers if available
            if scores:
                st.write("**Past Answers:**")
                for idx, score_entry in enumerate(reversed(scores)):
                    # Display a past answer with its score and timestamp
                    user_answer = score_entry["user_answer"]
                    score = score_entry["score"]
                    timestamp = score_entry.get("timestamp", "2023-11-15T14:30:00")
                    
                    # Parse and format the timestamp
                    try:
                        dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        formatted_date = dt.strftime("%b %d, %Y at %I:%M %p")
                    except (ValueError, AttributeError):
                        formatted_date = "Unknown date"
                    
                    # Display the answer
                    with st.container(border=True):
                        st.markdown(f"**Attempt {idx+1}** - {formatted_date}")
                        st.markdown(f"Score: **{get_score_emoji(score)} {score}/5**")
                        st.markdown(f"Your answer: {user_answer}") 