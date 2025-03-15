import os
import json
from typing import Dict, Optional, List, Any
from openai import OpenAI
import streamlit as st

# Set your OpenAI API key from environment variable
# You'll need to set OPENAI_API_KEY in your environment
# Try to get API key from environment variable first, then fall back to Streamlit secrets
api_key = os.environ.get("OPENAI_API_KEY")
try:
    if not api_key and hasattr(st, "secrets") and "openai" in st.secrets:
        api_key = st.secrets["openai"]["api_key"]
except ImportError:
    # Streamlit is not available, continue with only environment variable
    pass
client = OpenAI(api_key=api_key) if api_key else None

# Cache evaluation results with TTL=1 hour to avoid repeated API calls for identical questions/answers
@st.cache_data(ttl=3600, show_spinner=False)
def cached_evaluate_answer(question: str, user_answer: str, expected_answer: Optional[str] = None) -> Dict:
    """
    Cached version of evaluate_answer that uses the cache_data decorator.
    This reduces API calls for identical inputs within the TTL period.
    
    Args:
        question: The question text
        user_answer: The user's answer to evaluate
        expected_answer: The expected answer (if provided)
    
    Returns:
        Dict containing evaluation results
    """
    # This function wraps the non-streaming version of evaluate_answer
    return _evaluate_answer_impl(question, user_answer, expected_answer)

def evaluate_answer(question: str, user_answer: str, expected_answer: Optional[str] = None, stream_handler = None) -> Dict:
    """
    Evaluate a user's answer to a question using OpenAI API
    
    Args:
        question: The question text
        user_answer: The user's answer to evaluate
        expected_answer: The expected answer (if provided)
        stream_handler: Optional callback function for streaming response status
    
    Returns:
        Dict containing:
        - score: integer from 1-5
        - feedback: string with brief feedback
        - hint: string with a hint (if score < 4)
    """
    # If no stream handler is provided, we can use the cached version
    if stream_handler is None:
        return cached_evaluate_answer(question, user_answer, expected_answer)
    
    # Otherwise, we need to use the non-cached implementation directly
    # since streaming responses can't be cached
    return _evaluate_answer_impl(question, user_answer, expected_answer)

# The actual implementation - not cached directly
def _evaluate_answer_impl(question: str, user_answer: str, expected_answer: Optional[str] = None) -> Dict:
    """
    Implementation of answer evaluation that both cached and non-cached versions use
    """
    if not api_key:
        return {
            "score": 1, 
            "feedback": "OpenAI API key not set. Please set the OPENAI_API_KEY environment variable.",
            "hint": "Set OPENAI_API_KEY in your environment."
        }
    
    if not user_answer.strip():
        return {
            "score": 1,
            "feedback": "No answer provided.",
            "hint": "Please provide an answer to evaluate."
        }
    
    # Prepare the messages for the API call
    messages = [
        {"role": "system", "content": """You are an educational evaluation assistant that assesses answers to questions. 
        Evaluate the user's answer for correctness and provide:
        1. A score from 1-5 where 5 is perfect
        2. Brief but specific feedback (1-2 sentences) on the answer quality
        3. A helpful hint if the score is below 4/5
        4. You should almost never give 5/5. There is always room for improvement whether it be clarity, detail, or accuracy.
        5. Ensure the answer covers all aspects of the Expected Answer and deduct points where it doesn't.
        
        Return only a JSON object with these three fields."""},
        {"role": "user", "content": f"""Question: {question}
        
        User's Answer: {user_answer}
        
        {"Expected Answer: " + expected_answer if expected_answer else "There is no provided expected answer, please evaluate based on general knowledge and reasonableness."}
        
        Evaluate this answer and return a JSON object with:
        1. score (integer 1-5)
        2. feedback (string, 1-2 sentences)
        3. hint (string, only if score < 4, otherwise null)
        """
        }
    ]
    
    # Define the function call for structured output
    functions = [
        {
            "name": "provide_evaluation",
            "description": "Provide evaluation of a student answer",
            "parameters": {
                "type": "object",
                "properties": {
                    "score": {
                        "type": "integer",
                        "description": "Score from 1-5, where 5 is perfect"
                    },
                    "feedback": {
                        "type": "string",
                        "description": "Brief but specific feedback on the answer"
                    },
                    "hint": {
                        "type": "string",
                        "description": "A helpful hint if the score is below 4/5, otherwise null"
                    }
                },
                "required": ["score", "feedback"]
            }
        }
    ]
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            functions=functions,
            function_call={"name": "provide_evaluation"}
        )
        
        # Extract the function call arguments
        function_args = json.loads(response.choices[0].message.function_call.arguments)
        
        # Ensure the score is within bounds
        score = max(1, min(5, function_args.get("score", 1)))
        
        return {
            "score": score,
            "feedback": function_args.get("feedback", "No feedback provided."),
            "hint": function_args.get("hint") if score < 4 else None
        }
    
    except Exception as e:
        return {
            "score": 1,
            "feedback": f"Error evaluating answer: {str(e)}",
            "hint": "Please try again or contact support."
        }

# Cache vector searches to reduce repeated API calls for identical subject/topic queries
@st.cache_data(ttl=1800, show_spinner=False)
def cached_vector_search(vector_store_id: str, query: str):
    """
    Cache vector search results to reduce API calls
    
    Args:
        vector_store_id: The ID of the vector store to search
        query: The search query
        
    Returns:
        List of search results or empty list if error
    """
    try:
        # Import here to avoid circular imports
        from rag_manager import RAGManager
        rag = RAGManager()
        
        # Search the vector store with the query
        results = rag.client.vector_stores.vector_search.create(
            vector_store_id=vector_store_id,
            query=query,
            return_object='file_chunk',
            limit=3  # Limit to top 3 sources
        )
        
        # Get filenames for the sources
        sources = []
        for item in results.data:
            try:
                # Try to get file info
                file_info = rag.get_vector_store_file(vector_store_id, item.file_id)
                if file_info and "filename" in file_info:
                    sources.append(file_info["filename"])
            except Exception:
                # If we can't get the filename, continue to the next item
                pass
                
        # Return unique sources
        return list(set(sources))
        
    except Exception as e:
        print(f"Error searching vector store: {e}")
        return []

# Generate system message for chat context
def _create_system_message(question: str, expected_answer: str, user_answer: str, 
                          feedback: Dict[str, Any], subject: str, week: str) -> str:
    """
    Create a consistent system message for chat conversations
    
    Args:
        question: The question text
        expected_answer: The expected answer
        user_answer: The user's answer
        feedback: The AI feedback dictionary
        subject: The subject of the question
        week: The week of the question
        
    Returns:
        String containing the system message
    """
    return f"""You are an educational AI tutor specialized in {subject}, helping students understand concepts in Week {week}.
You're discussing a specific question the student has recently answered. Here's the relevant information:
Question: {question}
Expected Answer: {expected_answer}
User's Answer: {user_answer}
Feedback Score: {feedback.get('score', 'N/A')}/5
Feedback: {feedback.get('feedback', 'No feedback available')}
Hint: {feedback.get('hint', 'No hint available')}
Your role is to be a Socratic tutor who:
1. Asks thought-provoking questions before giving direct answers
2. Guides students to discover answers themselves through critical thinking
3. Helps clarify concepts by breaking them down into smaller parts
4. Encourages deeper exploration with "why" and "how" questions
5. Is patient, encouraging and supportive
Keep your responses BRIEF (1-3 sentences when possible) and focused on helping the student understand the material better.
Do not share the complete answer immediately, but guide the student toward deeper understanding through questioning.
"""

def chat_about_question(
    question: str, 
    expected_answer: str, 
    user_answer: str, 
    feedback: Dict[str, Any],
    subject: str,
    week: str,
    vector_store_id: Optional[str] = None,
    chat_messages: Optional[List[Dict[str, str]]] = None,
    stream_handler = None
) -> str:
    """
    Generate a response from AI to discuss a question and answer with the user.
    
    Args:
        question: The question text
        expected_answer: The expected answer
        user_answer: The user's answer
        feedback: The AI feedback dictionary containing score, feedback, and hint
        subject: The subject of the question
        week: The week of the question
        vector_store_id: Optional vector store ID for RAG
        chat_messages: Optional list of previous chat messages
        stream_handler: Optional callback function for streaming responses
    
    Returns:
        String containing the AI's response or empty string if streaming
    """
    if not api_key:
        return "OpenAI API key not set. Please set the OPENAI_API_KEY environment variable."
    
    # Default to empty list if chat_messages is None
    if chat_messages is None:
        chat_messages = []
    
    # Prepare the system message with context
    system_message = _create_system_message(
        question, expected_answer, user_answer, feedback, subject, week
    )
    
    # Prepare the messages for the API call
    messages = [{"role": "system", "content": system_message}]
    
    # Add previous chat messages if available
    messages.extend(chat_messages)
    
    # Initialize tools for vector search if vector_store_id is provided
    tools = None
    tool_choice = None
    
    if vector_store_id:
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_vector_store",
                    "description": "Search for information in the vector store to provide context for your response",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query to find relevant information"
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]
        tool_choice = "auto"
    
    try:
        # If we have a stream handler, use streaming mode
        if stream_handler:
            # In streaming mode we return an empty string since the handler will
            # process the response chunks directly
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=tools,
                tool_choice=tool_choice,
                max_tokens=400,
                stream=True  # Enable streaming
            )
            
            full_response = ""
            # Process the streaming response
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    # Call the stream handler with the content chunk
                    stream_handler(content)
            
            # Check for references to course materials and add source citations
            # For streaming mode, we need to check the content for mentions of references
            # and add citations if detected
            references_detected = False
            if any(term in full_response.lower() for term in ["according to", "as mentioned in", "as stated in", "source", "reference", "material", "reading", "text", "document"]):
                references_detected = True
                
            if references_detected and vector_store_id:
                # Extract query from user messages for vector search
                query = ""
                for msg in chat_messages:
                    if msg["role"] == "user":
                        query = msg["content"]
                        break
                
                # If no user message found, use the full response to search for relevant sources
                if not query:
                    query = full_response
                
                # Use cached vector search to get sources
                sources = cached_vector_search(vector_store_id, query) if vector_store_id else []
                
                # Create citation note
                if sources:
                    sources_text = ", ".join(sources[:3])
                    return f"{full_response}\n\n(Sources: {sources_text})"
                else:
                    # Fallback if we detected references but couldn't get sources
                    return f"{full_response}\n\n(Source: Course materials)"
            elif "course materials" in full_response.lower():
                # Generic fallback for course material references
                return f"{full_response}\n\n(Source: Course materials)"
            
            return full_response
        
        # Non-streaming mode (original behavior)
        else:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=tools,
                tool_choice=tool_choice,
                max_tokens=400  # Limit response length to keep it concise
            )
            
            # Extract the message content
            message = response.choices[0].message
            
            # Process tool calls if any
            if hasattr(message, 'tool_calls') and message.tool_calls:
                # Process each tool call
                for tool_call in message.tool_calls:
                    if tool_call.function.name == "search_vector_store":
                        # Extract info from tool call
                        function_args = json.loads(tool_call.function.arguments)
                        query = function_args.get("query", "")
                        
                        # Get sources using cached vector search
                        sources = cached_vector_search(vector_store_id, query) if vector_store_id else []
                        
                        # Create citation note
                        if sources:
                            sources_text = ", ".join(sources[:3])  # Limit to 3 sources to avoid clutter
                            return f"{message.content}\n\n(Sources: {sources_text})"
                        else:
                            # Fallback to generic note
                            return f"{message.content}\n\n(Source: Course materials)"
            
            return message.content
        
    except Exception as e:
        return f"Error generating response: {str(e)}. Please try again."