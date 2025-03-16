"""
Demo mode UI for add_ai module.

This module provides demo content for unauthenticated users to showcase
the AI Question Generator functionality.
"""
import streamlit as st
import pandas as pd

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

def _render_bio_question_1():
    """Helper function to render the first biology question"""
    with st.container(border=True):
        # Question header with title and checkbox in columns
        header_col1, header_col2 = st.columns([3, 1])
        with header_col1:
            st.markdown("**Q1: Explain the process of cellular respiration and its main stages.**")
        
        with header_col2:
            st.checkbox("", value=True, disabled=True, key="demo_check1")
        
        # Answer section (expandable)
        with st.expander("View expected answer"):
            st.write("""
            Cellular respiration is the process cells use to convert glucose into energy in the form of ATP. 
            
            The three main stages are:
            1. Glycolysis: Occurs in the cytoplasm, breaks down glucose into pyruvate, produces 2 ATP and 2 NADH.
            2. Krebs Cycle (Citric Acid Cycle): Occurs in the mitochondrial matrix, completes the oxidation of glucose, produces 2 ATP, 6 NADH, and 2 FADH2.
            3. Electron Transport Chain: Located in the inner mitochondrial membrane, electrons from NADH and FADH2 flow through protein complexes, creating a proton gradient that drives ATP synthase to produce ATP.
            
            In total, one glucose molecule can yield approximately 36-38 ATP molecules.
            """)

def _render_bio_question_2():
    """Helper function to render the second biology question"""
    with st.container(border=True):
        # Question header with title and checkbox in columns
        header_col1, header_col2 = st.columns([3, 1])
        with header_col1:
            st.markdown("**Q2: Compare and contrast mitosis and meiosis.**")
        
        with header_col2:
            st.checkbox("", value=True, disabled=True, key="demo_check2")
        
        # Answer section (expandable)
        with st.expander("View expected answer"):
            st.write("""
            Mitosis and meiosis are both processes of cell division but serve different purposes.
            
            **Mitosis:**
            - Produces two identical diploid daughter cells
            - One round of division
            - Used for growth, repair, and asexual reproduction
            - Maintains chromosome number
            - No genetic variation in daughter cells
            
            **Meiosis:**
            - Produces four haploid daughter cells
            - Two rounds of division (meiosis I and II)
            - Used for sexual reproduction
            - Reduces chromosome number by half
            - Generates genetic variation through crossing over and independent assortment
            """)

def _render_bio_question_3():
    """Helper function to render the third biology question"""
    with st.container(border=True):
        # Question header with title and checkbox in columns
        header_col1, header_col2 = st.columns([3, 1])
        with header_col1:
            st.markdown("**Q3: Describe the structure and function of DNA and its role in protein synthesis.**")
        
        with header_col2:
            st.checkbox("", value=False, disabled=True, key="demo_check3")
        
        # Answer section (expandable)
        with st.expander("View expected answer"):
            st.write("""
            DNA (deoxyribonucleic acid) is a double helix structure composed of nucleotides. Each nucleotide contains a phosphate group, deoxyribose sugar, and one of four nitrogenous bases (adenine, thymine, guanine, or cytosine).
            
            The structure of DNA allows for:
            1. Storage of genetic information in the sequence of bases
            2. Replication through complementary base pairing (A-T, G-C)
            3. Transcription of genetic information into RNA
            
            In protein synthesis, DNA serves as the template for RNA production (transcription), which then directs protein assembly (translation). The process follows the central dogma of molecular biology: DNA → RNA → Protein.
            
            This process involves:
            1. Transcription: DNA is transcribed into mRNA in the nucleus
            2. Translation: mRNA travels to ribosomes where the code is translated into a sequence of amino acids
            3. Post-translational modifications: The protein may undergo further modifications
            """)

def show_demo_content():
    """Display demo content for users in preview mode"""
    # Content for the first tab (generate questions)
    st.subheader("Demo: AI Question Generator")
    
    # Mock file upload and subject/week selection
    col1, col2 = st.columns(2)
    with col1:
        # Use a selectbox with Biology and Create New options
        st.selectbox(
            "Subject",
            options=["Biology", "Create New"],
            index=0,
            disabled=True
        )
    with col2:
        st.number_input("Week", value=1, min_value=1, max_value=52, disabled=True)
    
    # Mock file uploader
    st.file_uploader("Upload a file (PDF or TXT)", type=["pdf", "txt"], disabled=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.button("Generate Questions from Upload", disabled=True, use_container_width=True)
    
    # Preview of generated questions
    st.markdown("### Demo Questions")
    st.write("Here are some sample questions that would be generated from a biology textbook:")
    
    # Display sample questions
    _render_bio_question_1()
    _render_bio_question_2()
    _render_bio_question_3()
    
    # Mock add button
    if st.button("Add Selected Questions", type="primary", disabled=True, use_container_width=True):
        pass
    
    # Notice about sign up/upgrade
    st.info("👆 Sign in using the button in the sidebar and upgrade to premium to generate your own questions from your course materials.")

def show_kb_demo_content():
    """Display knowledge base demo content"""
    st.subheader("Demo: Knowledge Base Management")
    
    # Create a sample dataframe of knowledge bases
    kb_data = [
        {"Subject": "Biology", "Week": "1", "ID": "vs_0001abc123"},
        {"Subject": "Biology", "Week": "2", "ID": "vs_0002def456"},
        {"Subject": "Computer Science", "Week": "1", "ID": "vs_0003ghi789"}
    ]
    
    # Display knowledge bases in a dataframe
    st.dataframe(kb_data, use_container_width=True)
    
    # Sample file management interface
    st.markdown("### Manage Knowledge Base Files")
    st.info("Select a subject and week to manage its files (view, add, or delete files)")
    
    col1, col2 = st.columns(2)
    with col1:
        st.selectbox("Subject", options=["Biology", "Computer Science"], disabled=True, key="demo_manage_subject")
    with col2:
        st.selectbox("Week", options=["1", "2"], disabled=True, key="demo_manage_week")
    
    # Mock file management interface
    with st.expander("📚 Manage Course Materials", expanded=True):
        st.write("Managing materials for: **Biology - Week 1**")
        
        # Sample file list
        st.markdown("### Current Files")
        
        # First file
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write("**Lecture Notes Week 1.pdf** (Added: 2023-03-15)")
            with col2:
                st.button("🗑️ Delete", key="demo_delete_1", disabled=True)
                
        # Second file
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write("**Lab Manual.pdf** (Added: 2023-03-14)")
            with col2:
                st.button("🗑️ Delete", key="demo_delete_2", disabled=True)
        
        # Add new files section
        st.markdown("### Add New Files")
        st.file_uploader(
            "Upload PDF, TXT, or other documents",
            type=["pdf", "txt", "docx", "md"],
            accept_multiple_files=True,
            disabled=True,
            key="demo_file_upload"
        )
        st.button("Process Files", use_container_width=True, disabled=True)
    
    # Sample deletion interface
    st.markdown("### Delete Knowledge Base")
    st.warning("⚠️ Deleting a knowledge base will remove the stored course material but not the questions already generated.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.selectbox("Subject", options=["Biology", "Computer Science"], disabled=True, key="demo_delete_subject")
    with col2:
        st.selectbox("Week", options=["1", "2"], disabled=True, key="demo_delete_week")
    
    st.button("Delete Knowledge Base", disabled=True, use_container_width=True, key="demo_delete_kb")
    
    st.info("This interface allows premium users to manage their stored course materials and knowledge bases.") 