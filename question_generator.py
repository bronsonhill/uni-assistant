import os
import json
import time
import base64
from typing import List, Dict, Any
from openai import OpenAI

def generate_questions_from_file(
    file_bytes: bytes, 
    file_type: str, 
    subject: str, 
    week: str, 
    num_questions: int,
    existing_questions: List[Dict[str, Any]] = None
) -> List[Dict[str, str]]:
    """
    Process uploaded file and generate questions using OpenAI's responses API.
    
    Parameters:
    - file_bytes: The bytes of the uploaded file
    - file_type: The type of file (pdf or txt)
    - subject: The course subject
    - week: The week number
    - num_questions: How many questions to generate
    - existing_questions: List of existing questions to avoid duplication
    
    Returns:
    - List of generated question-answer pairs
    """
    # Make sure OpenAI API key is available
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OpenAI API key not found. Please set the OPENAI_API_KEY environment variable."
        )
    
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    # Format existing questions to avoid duplication
    existing_q_texts = []
    if existing_questions:
        existing_q_texts = [q["question"] for q in existing_questions]
    existing_qs_str = "\n".join([f"- {q}" for q in existing_q_texts])
    
    # Convert file bytes to base64
    base64_string = base64.b64encode(file_bytes).decode("utf-8")
    
    # Construct system prompt
    system_prompt = """You are an expert teacher creating study questions for university students. 
Generate thought-provoking questions based on the uploaded document. 
Each question should test understanding, not just memorization.
For each question, also provide a comprehensive answer that would be useful for studying."""
    
    # Construct user prompt
    user_prompt = f"""Please generate {num_questions} questions based on the contents of the uploaded file.
Each question should have a detailed answer suitable for studying.

Make sure the questions cover key concepts from the document and are varied in difficulty.
"""
    
    # Add existing questions to avoid duplication if there are any
    if existing_q_texts:
        user_prompt += f"""
IMPORTANT: Avoid duplicating these existing questions:
{existing_qs_str}
"""
    
    # Define the function for generating questions
    tools = [
        {
            "type": "function",
            "name": "generate_study_questions",
            "description": "Generate study questions and answers based on document content",
            "parameters": {
                "type": "object",
                "properties": {
                    "questions": {
                        "type": "array",
                        "description": "List of generated questions with answers",
                        "items": {
                            "type": "object",
                            "properties": {
                                "question": {
                                    "type": "string",
                                    "description": "A thought-provoking study question"
                                },
                                "answer": {
                                    "type": "string",
                                    "description": "A comprehensive answer to the question"
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
    
    try:
        # Send request to OpenAI API using responses endpoint
        response = client.responses.create(
            model="gpt-4o",
            instructions=system_prompt,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_file",
                            "filename": f"document.{file_type}",
                            "file_data": f"data:application/{file_type};base64,{base64_string}"
                        },
                        {
                            "type": "input_text",
                            "text": user_prompt
                        }
                    ]
                }
            ],
            tools=tools,
            tool_choice="required",
        )
        
        # Extract the function call arguments from the response
        function_call = None
        for output in response.output:
            if output.type == "function_call":
                function_call = output
                break
                
        if not function_call:
            raise ValueError("No function call found in the response")
            
        function_args = json.loads(function_call.arguments)
        questions = function_args.get("questions", [])
        
        # Validate and format the questions
        validated_questions = []
        for q in questions:
            if "question" in q and "answer" in q:
                validated_questions.append({
                    "question": q["question"],
                    "answer": q["answer"]
                })
        
        # Limit to requested number
        return validated_questions[:num_questions]
        
    except Exception as e:
        # If there's an error, log it and re-raise
        print(f"Error generating questions: {str(e)}")
        raise