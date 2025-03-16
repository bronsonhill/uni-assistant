"""
Demo mode UI for tutor module.

This module provides demo content for unauthenticated users to showcase 
the Subject Tutor functionality.
"""
import streamlit as st

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
        
        # Create a fixed-height container for the chat
        chat_container = st.container(height=500, border=True)
        
        # Simulate a chat conversation based on the selected subject
        with chat_container:
            # Display mock conversation
            if selected_subject == "Computer Science":
                _display_cs_demo_conversation()
            elif selected_subject == "Biology":
                _display_biology_demo_conversation()
            else:  # Law
                _display_law_demo_conversation()
        
        # Disabled chat input
        st.chat_input("Ask a question about your course materials...", disabled=True)
    
    # Show login/subscription prompt
    st.info("Sign in and upgrade to premium to chat with an AI tutor that knows your course materials.")

def _display_cs_demo_conversation():
    """Display a sample Computer Science conversation"""
    with st.chat_message("user"):
        st.write("Can you explain how virtual memory works in operating systems?")
    
    with st.chat_message("assistant"):
        st.write("""
        Based on your course materials, virtual memory is a memory management technique that provides an idealized abstraction of the storage resources that are actually available on a given machine.
        
        Here's how it works:
        
        1. **Address Translation**: The operating system maps virtual addresses (used by processes) to physical addresses (actual RAM locations).
        
        2. **Paging**: Virtual memory is divided into fixed-size blocks called pages. Physical memory is divided into page frames of the same size.
        
        3. **Page Tables**: The OS maintains page tables to track mappings between virtual and physical addresses.
        
        4. **Memory Management Unit (MMU)**: Hardware that performs the address translation, reducing overhead.
        
        5. **Demand Paging**: Pages are loaded into physical memory only when needed, not in advance.
        
        6. **Page Faults**: When a program accesses a page not in physical memory, a page fault occurs, and the OS loads the page from disk.
        
        7. **Page Replacement**: When physical memory is full, the OS must choose which pages to remove (using algorithms like LRU, FIFO, or Clock).
        
        Virtual memory allows:
        - Programs to use more memory than physically available
        - Multiple processes to run concurrently
        - Memory protection between processes
        - More efficient use of physical memory
        
        From your course slides, Professor Johnson emphasized that the page replacement policy is particularly important for performance, with LRU (Least Recently Used) offering good theoretical performance but being expensive to implement exactly.
        """)
    
    with st.chat_message("user"):
        st.write("What's the difference between paging and segmentation?")

def _display_biology_demo_conversation():
    """Display a sample Biology conversation"""
    with st.chat_message("user"):
        st.write("Can you explain the process of cellular respiration?")
    
    with st.chat_message("assistant"):
        st.write("""
        Based on your course materials from Dr. Martinez's lectures, cellular respiration is the process cells use to produce ATP by breaking down organic molecules and transferring their energy to ATP.
        
        The complete process involves three main stages:
        
        1. **Glycolysis**:
           - Occurs in the cytoplasm
           - Breaks down glucose (6C) into two pyruvate molecules (3C)
           - Produces 2 ATP and 2 NADH per glucose molecule
           - Does not require oxygen (can occur in aerobic or anaerobic conditions)
           
        2. **Citric Acid Cycle (Krebs Cycle)**:
           - Occurs in the mitochondrial matrix
           - Converts pyruvate to acetyl-CoA (releasing CO₂)
           - Each acetyl-CoA enters the cycle and generates:
             * 3 NADH
             * 1 FADH₂
             * 1 ATP
             * 2 CO₂
           - The cycle turns twice per glucose molecule
           
        3. **Electron Transport Chain**:
           - Located in the inner mitochondrial membrane
           - NADH and FADH₂ donate electrons that flow through protein complexes
           - Energy from electron flow pumps H⁺ ions across the membrane
           - Creates a proton gradient that drives ATP synthesis via ATP synthase
           - Oxygen serves as the final electron acceptor, forming water
           - Produces most of the ATP (about 32-34 per glucose)
           
        In total, one glucose molecule can yield approximately 36-38 ATP molecules through aerobic respiration, which is much more efficient than the 2 ATP produced by fermentation.
        
        As your textbook emphasizes, this process is essential for all eukaryotic cells and is a prime example of how cellular compartmentalization enables metabolic efficiency.
        """)
    
    with st.chat_message("user"):
        st.write("How does this relate to photosynthesis?")

def _display_law_demo_conversation():
    """Display a sample Law conversation"""
    with st.chat_message("user"):
        st.write("Can you explain the concept of consideration in contract law?")
    
    with st.chat_message("assistant"):
        st.write("""
        According to your Contract Law course materials with Professor Williams, consideration is one of the essential elements required for a legally binding contract.
        
        Consideration refers to something of value that is exchanged between the contracting parties. It represents the bargained-for exchange or the price paid for the other's promise.
        
        Key aspects of consideration from your course readings:
        
        1. **Definition**: "Some right, interest, profit, or benefit accruing to one party, or some forbearance, detriment, loss, or responsibility given, suffered, or undertaken by the other" (Currie v. Misa, 1875).
        
        2. **Requirements for valid consideration**:
           - Must have economic value (though need not be adequate)
           - Must be sufficient but need not be adequate (courts don't typically evaluate fairness)
           - Must not be past consideration (must be given in exchange for the promise)
           - Must move from the promisee (the person to whom the promise is made)
        
        3. **Examples of valid consideration**:
           - Money paid for goods or services
           - Promise to do something one has no prior legal duty to do
           - Promise to refrain from doing something one has a right to do (forbearance)
        
        4. **Exceptions and problem areas** (from Professor Williams' Week 3 lecture):
           - Pre-existing duty rule: Promising to do what you're already legally obligated to do is not valid consideration
           - Nominal consideration: Token amounts (e.g., $1) may be scrutinized if clearly not part of a bargain
           - Illusory promises: Promises that don't actually commit to anything
        
        5. **Promissory estoppel**: An equitable doctrine that can sometimes substitute for consideration where reliance on a promise has occurred
        
        The case of *Thomas v. Thomas* (1842) that you studied in Week 2 illustrates that consideration must have some economic value, but courts won't generally inquire into its adequacy.
        """)
    
    with st.chat_message("user"):
        st.write("What are the differences between bilateral and unilateral contracts?") 