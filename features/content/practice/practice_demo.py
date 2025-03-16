"""
Demo mode UI for practice module.

This module provides demo content for unauthenticated users to showcase practice functionality.
"""
import streamlit as st

def show_demo_content():
    """Show demo content for users in preview mode"""
    # Add subject selector
    selected_subject = st.selectbox(
        "Select Subject for Demo",
        ["Computer Science", "Biology", "Law"],
        index=0,  # Default to Computer Science
        key="practice_demo_subject"
    )
    
    # Display a sample practice question based on selected subject
    with st.container(border=True):
        if selected_subject == "Computer Science":
            st.markdown("**Subject:** Computer Science - Week 3")
            st.markdown("### Q: Explain the difference between stack and heap memory allocation.")
            
            # Sample answer input
            st.text_area(
                "Your answer:",
                value="Stack memory is used for static memory allocation and is managed automatically by the compiler. It stores local variables and function call data. Heap memory is used for dynamic memory allocation controlled by the programmer, storing objects with longer lifetimes.",
                height=150,
                key="demo_cs_answer_input",
                disabled=True
            )
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # Demo check answer button
                st.button("Check Answer", key="cs_check", use_container_width=True, disabled=True)
            
            with col2:
                # Demo show answer button
                st.button("Show Answer", key="cs_show", use_container_width=True, disabled=True)
            
            # Sample answer and feedback
            st.markdown("---")
            st.markdown("### Answer:")
            st.markdown("""
            Stack memory allocation is used for static memory allocation where variables are allocated and 
            deallocated in a last-in-first-out order, typically for local variables and function calls. 
            It's faster but limited in size.
            
            Heap memory allocation is used for dynamic memory allocation at runtime, managed by the programmer 
            (in languages like C/C++) or garbage collector. It's slower but allows for larger and variable-sized 
            data structures with lifetimes not tied to specific scopes.
            """)
            
            # Sample feedback preview
            st.markdown("---")
            st.markdown("### AI Feedback:")
            st.markdown("**Score:** <span style='color:green;font-size:18px;'>4/5</span>", unsafe_allow_html=True)
            st.markdown("""
            **Feedback:** Good answer! You've correctly identified the key differences between stack and heap memory:
            
            ✅ You mentioned stack is for static allocation and heap for dynamic allocation
            ✅ You explained that stack is managed automatically while heap is controlled by the programmer
            ✅ You noted that stack typically stores local variables
            
            To improve your answer, you could add:
            - The LIFO (Last-In-First-Out) structure of stack memory
            - Speed differences (stack is generally faster)
            - Size limitations (stack is more limited)
            - Memory fragmentation concerns with heap memory
            """)
    
            # Sample chat example
            st.markdown("---")
            st.markdown("### Chat with AI about this question")
            
            # Sample conversation
            with st.chat_message("user"):
                st.write("Can you explain what causes stack overflow errors?")
                
            with st.chat_message("assistant"):
                st.write("""
                Stack overflow errors occur when a program attempts to use more memory space in the stack than has been allocated. Here's why they happen:
    
                1. **Limited Stack Size**: The stack has a fixed, predetermined size set by the operating system or compiler.
    
                2. **Common Causes**:
                   - Infinite recursion (a function that keeps calling itself without a proper base case)
                   - Very deep recursion (even with a base case, if the depth is too great)
                   - Allocating large data structures on the stack
                   - Extensive function call chains that exceed stack capacity
    
                3. **Example**:
                ```python
                def infinite_recursion():
                    # No base case to stop recursion
                    print("Recursive call")
                    infinite_recursion()
                    
                infinite_recursion()  # Will eventually cause stack overflow
                ```
    
                4. **Prevention**:
                   - Use iteration instead of recursion when possible
                   - Implement proper base cases for recursive functions
                   - Allocate large objects on the heap instead of the stack
                   - Increase stack size if needed (platform-specific)
                   - Use tail recursion optimization when available
    
                Stack overflows are particularly common in languages without automatic garbage collection like C and C++.
                """)
                
            with st.chat_message("user"):
                st.write("What about memory leaks with heap allocation?")
            
        elif selected_subject == "Biology":
            st.markdown("**Subject:** Biology - Week 2")
            st.markdown("### Q: Explain the process of photosynthesis and its importance for life on Earth.")
            
            # Sample answer input
            st.text_area(
                "Your answer:",
                value="Photosynthesis is the process by which plants, algae, and some bacteria convert light energy into chemical energy. They use sunlight, water, and carbon dioxide to produce glucose and oxygen. This process is vital for life as it produces oxygen for animals to breathe and creates the energy source for most food chains.",
                height=150,
                key="demo_bio_answer_input",
                disabled=True
            )
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # Demo check answer button
                st.button("Check Answer", key="bio_check", use_container_width=True, disabled=True)
            
            with col2:
                # Demo show answer button
                st.button("Show Answer", key="bio_show", use_container_width=True, disabled=True)
            
            # Sample answer and feedback
            st.markdown("---")
            st.markdown("### Answer:")
            st.markdown("""
            Photosynthesis is the biochemical process by which photoautotrophs (plants, algae, and some bacteria) convert light energy from the sun into chemical energy stored in glucose molecules. The process uses carbon dioxide and water, releasing oxygen as a byproduct.
            
            The overall equation is: 6CO₂ + 6H₂O + light energy → C₆H₁₂O₆ + 6O₂
            
            The process occurs in two main stages:
            1. Light-dependent reactions (in the thylakoid membrane): Capture light energy, split water molecules, and produce ATP and NADPH.
            2. Calvin cycle (light-independent reactions): Uses ATP and NADPH to fix carbon dioxide into glucose.
            
            Photosynthesis is crucial for life on Earth because:
            - It produces oxygen required for aerobic respiration in most organisms
            - It forms the base of most food chains, converting solar energy into chemical energy
            - It removes carbon dioxide from the atmosphere, affecting climate regulation
            - It has shaped Earth's atmosphere, enabling the evolution of complex life forms
            """)
            
            # Sample feedback preview
            st.markdown("---")
            st.markdown("### AI Feedback:")
            st.markdown("**Score:** <span style='color:orange;font-size:18px;'>3/5</span>", unsafe_allow_html=True)
            st.markdown("""
            **Feedback:** Good start! You've captured the basic concept of photosynthesis:
            
            ✅ You correctly identified it as a process that converts light energy to chemical energy
            ✅ You mentioned the inputs (sunlight, water, CO₂) and outputs (glucose, oxygen)
            ✅ You noted its importance for producing oxygen and supporting food chains
            
            To improve your answer, consider adding:
            - The specific equation for photosynthesis (6CO₂ + 6H₂O + light → C₆H₁₂O₆ + 6O₂)
            - The two stages of photosynthesis (light-dependent reactions and Calvin cycle)
            - Where photosynthesis occurs in plants (chloroplasts, specifically thylakoids)
            - The role of chlorophyll in capturing light energy
            - More detailed ecological importance (carbon fixation, climate regulation)
            """)
    
            # Sample chat example
            st.markdown("---")
            st.markdown("### Chat with AI about this question")
            
            # Sample conversation
            with st.chat_message("user"):
                st.write("What's the difference between C3, C4, and CAM photosynthesis?")
                
            with st.chat_message("assistant"):
                st.write("""
                C3, C4, and CAM photosynthesis are different adaptations that plants have evolved to fix carbon efficiently in various environments:
    
                **C3 Photosynthesis:**
                - The most common type (~85% of plants)
                - Named because the first product of carbon fixation is a 3-carbon molecule (3-phosphoglycerate)
                - Carbon fixation occurs directly via the Calvin cycle using the enzyme RuBisCO
                - Works best in moderate temperatures and humid conditions
                - Examples: rice, wheat, soybeans, trees
                - Less efficient in hot/dry conditions due to photorespiration
    
                **C4 Photosynthesis:**
                - Evolved as an adaptation to hot, dry environments
                - Named because the first product is a 4-carbon molecule (oxaloacetate)
                - Uses spatial separation: carbon fixation occurs in mesophyll cells, then the 4-carbon molecules are transported to bundle sheath cells for the Calvin cycle
                - Minimizes photorespiration by concentrating CO₂ around RuBisCO
                - More efficient in hot/sunny conditions but requires more energy
                - Examples: corn, sugarcane, sorghum
    
                **CAM Photosynthesis (Crassulacean Acid Metabolism):**
                - Adaptation to extremely arid conditions
                - Uses temporal separation: stomata open at night to collect CO₂, which is stored as malate; during the day, stomata close to conserve water while malate releases CO₂ for the Calvin cycle
                - Highly water-efficient but less energy-efficient overall
                - Examples: cacti, pineapples, agaves, many succulents
    
                These different photosynthetic pathways represent evolutionary adaptations to different environmental conditions, primarily balancing water conservation against photosynthetic efficiency.
                """)
                
            with st.chat_message("user"):
                st.write("Why does photorespiration happen in C3 plants?")
            
        else:  # Law
            st.markdown("**Subject:** Law - Week 4")
            st.markdown("### Q: Explain the concept of precedent in common law legal systems and its importance.")
            
            # Sample answer input
            st.text_area(
                "Your answer:",
                value="Precedent in common law refers to the principle that courts should follow previous decisions from similar cases. It provides consistency, predictability, and stability in the legal system. Precedent is binding when it comes from a higher court but can sometimes be overturned if deemed necessary.",
                height=150,
                key="demo_law_answer_input",
                disabled=True
            )
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # Demo check answer button
                st.button("Check Answer", key="law_check", use_container_width=True, disabled=True)
            
            with col2:
                # Demo show answer button
                st.button("Show Answer", key="law_show", use_container_width=True, disabled=True)
            
            # Sample answer and feedback
            st.markdown("---")
            st.markdown("### Answer:")
            st.markdown("""
            Precedent (stare decisis) is a fundamental principle in common law systems whereby judges are bound to follow previous decisions of courts of the same or higher level when ruling on cases with similar facts and legal issues.
            
            Key aspects of precedent include:
            
            1. Binding vs. Persuasive Precedent
               - Binding precedent must be followed by lower courts
               - Persuasive precedent from other jurisdictions may inform but not bind decisions
            
            2. Ratio Decidendi vs. Obiter Dicta
               - Ratio decidendi: The binding legal principle essential to the decision
               - Obiter dicta: Supplementary remarks that aren't binding
            
            3. Distinguishing and Overruling
               - Courts may distinguish cases based on different facts
               - Higher courts may overrule previous decisions in limited circumstances
            
            Precedent is crucial because it:
            - Ensures consistency and predictability in legal outcomes
            - Promotes equality by treating similar cases alike
            - Provides efficiency in judicial decision-making
            - Creates stability while allowing for incremental legal development
            - Balances rigidity with flexibility through distinguishing and occasional overruling
            
            This doctrine is a defining characteristic of common law systems (UK, US, Canada, Australia) compared to civil law systems that rely primarily on codified statutes.
            """)
            
            # Sample feedback preview
            st.markdown("---")
            st.markdown("### AI Feedback:")
            st.markdown("**Score:** <span style='color:orange;font-size:18px;'>3/5</span>", unsafe_allow_html=True)
            st.markdown("""
            **Feedback:** Your answer provides a basic understanding of precedent:
            
            ✅ You correctly identified precedent as following previous decisions
            ✅ You mentioned its importance for consistency and predictability
            ✅ You noted the binding nature from higher courts and possibility of overturning
            
            To improve your answer, consider adding:
            - The Latin term "stare decisis" ("to stand by decisions")
            - The distinction between ratio decidendi (binding part) and obiter dicta (non-binding)
            - More on how courts can "distinguish" cases without overturning precedent
            - The hierarchy of courts and how it affects binding precedent
            - The balance between legal stability and evolution of law
            - Comparison with civil law systems that rely less on precedent
            """)
    
            # Sample chat example
            st.markdown("---")
            st.markdown("### Chat with AI about this question")
            
            # Sample conversation
            with st.chat_message("user"):
                st.write("What are the circumstances when precedent can be overturned?")
                
            with st.chat_message("assistant"):
                st.write("""
                Precedent can be overturned in several specific circumstances, though courts generally approach this with caution:
    
                **1. By Higher Courts:**
                - Superior courts can overturn precedents set by lower courts
                - For example, the Supreme Court can overturn decisions from Courts of Appeal
    
                **2. By the Same Court:**
                Some courts (especially supreme courts) can overturn their own precedents when:
                - The precedent is clearly wrong or deeply flawed in reasoning
                - The precedent has become unworkable in practice
                - Social, technological, or legal developments have made it obsolete
                - The precedent conflicts with fundamental principles of justice
                - There's been significant change in public policy considerations
    
                **3. Notable Examples:**
                - *Brown v. Board of Education* (1954) overturned *Plessy v. Ferguson* (1896), rejecting "separate but equal" doctrine
                - *Lawrence v. Texas* (2003) overturned *Bowers v. Hardwick* (1986) regarding same-sex relationships
    
                **4. Considerations When Overturning:**
                Courts typically consider:
                - Reliance: Whether people have structured their affairs based on the precedent
                - Stability: The importance of predictability in the legal system
                - Legitimacy: How overturning might affect public perception of the judiciary
                - Evolution: The need for law to adapt to changing societal conditions
    
                **5. Distinguishing vs. Overturning:**
                - Courts often prefer to "distinguish" cases (finding relevant differences) rather than overturn precedent outright
                - This allows more incremental development of law while maintaining respect for precedent
    
                The power to overturn precedent is exercised sparingly and typically accompanied by thorough justification to maintain the integrity of the legal system.
                """)
                
            with st.chat_message("user"):
                st.write("How does the concept of precedent differ between the UK and US legal systems?")
        
        # Disabled chat input to show it's a demo
        st.chat_input("Ask a question about this topic...", disabled=True)
        
        # Show login/subscription prompt
        st.markdown("---")
        st.info("Sign in or upgrade to premium to practice with your own flashcards and get AI feedback on your answers.")

def show_premium_benefits():
    """Show premium benefits section for authenticated but non-premium users"""
    # Show premium benefits
    st.markdown("### 🌟 Upgrade to Premium for these benefits:")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("✅ **Advanced AI feedback on your answers**")
        st.markdown("✅ **Chat with AI about any question**")
        st.markdown("✅ **Detailed progress analytics**")
    
    with col2:
        st.markdown("✅ **Personalized learning recommendations**")
        st.markdown("✅ **Unlimited practice sessions**")
        st.markdown("✅ **Priority support**")

    # Show premium feature notice
    st.warning("Get AI feedback and chat features with a premium subscription.")
    
    # Add upgrade button
    st.button("Upgrade to Premium", type="primary", disabled=True) 