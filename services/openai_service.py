from openai import OpenAI
from typing import List, Dict, Optional, Any, Union
import json
import logging
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Question:
    """Data class for representing a study question"""
    question: str
    answer: str
    explanation: Optional[str] = None
    difficulty: Optional[str] = None
    topic: Optional[str] = None

class OpenAIServiceError(Exception):
    """Custom exception for OpenAI service errors"""
    pass

class OpenAIService:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the OpenAI service with API key"""
        try:
            self.client = OpenAI(api_key=api_key)
            logger.info("OpenAI service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI service: {e}")
            raise OpenAIServiceError(f"Failed to initialize OpenAI service: {e}")

    def generate_questions(self, 
                         vector_store_id: str,
                         subject: str,
                         week: str,
                         num_questions: int,
                         custom_prompt: Optional[str] = None,
                         difficulty: Optional[str] = None,
                         topics: Optional[List[str]] = None) -> List[Question]:
        """
        Generate study questions using the responses API
        
        Args:
            vector_store_id: ID of the vector store to search
            subject: Subject name
            week: Week number
            num_questions: Number of questions to generate
            custom_prompt: Optional custom prompt to guide question generation
            difficulty: Optional difficulty level (e.g., "easy", "medium", "hard")
            topics: Optional list of specific topics to focus on
            
        Returns:
            List of Question objects
            
        Raises:
            OpenAIServiceError: If question generation fails
        """
        try:
            # Configure tools for file search
            tools = [{
                "type": "file_search",
                "vector_store_ids": [vector_store_id],
                "max_num_results": 20,
                "ranking_options": {
                    "ranker": "auto",
                    "score_threshold": 0.0
                }
            }]
            
            # Construct the input text
            input_text = self._construct_input_text(
                subject=subject,
                week=week,
                num_questions=num_questions,
                custom_prompt=custom_prompt,
                difficulty=difficulty,
                topics=topics
            )
            
            # Make the API call
            logger.info(f"Generating questions for {subject} Week {week}")
            response = self.client.responses.create(
                model="gpt-4o",
                tools=tools,
                input=input_text,
                tool_choice="auto",
                temperature=0.7,
                top_p=1.0,
                max_output_tokens=2000
            )
            
            # Parse and validate the response
            questions = self._parse_questions_from_response(response)
            
            # Validate the number of questions
            if len(questions) < num_questions:
                logger.warning(f"Generated fewer questions than requested: {len(questions)} vs {num_questions}")
            
            return questions[:num_questions]
            
        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            raise OpenAIServiceError(f"Failed to generate questions: {e}")

    def _construct_input_text(self,
                            subject: str,
                            week: str,
                            num_questions: int,
                            custom_prompt: Optional[str] = None,
                            difficulty: Optional[str] = None,
                            topics: Optional[List[str]] = None) -> str:
        """Construct the input text for question generation"""
        input_text = f"""Generate {num_questions} study questions for {subject}, Week {week}.
Each question should test understanding of key concepts from the content.
Include a mix of factual recall, understanding, and application questions.

For each question, provide:
1. The question text
2. A comprehensive answer
3. An explanation of why the answer is correct
4. The difficulty level (easy, medium, or hard)
5. The main topic being tested

Format the response as a JSON array of objects with the following structure:
[
  {{
    "question": "What is...",
    "answer": "The answer is...",
    "explanation": "This is correct because...",
    "difficulty": "medium",
    "topic": "Topic Name"
  }}
]"""

        if custom_prompt:
            input_text += f"\n\nAdditional context: {custom_prompt}"
            
        if difficulty:
            input_text += f"\n\nFocus on {difficulty} difficulty questions."
            
        if topics:
            topics_str = ", ".join(topics)
            input_text += f"\n\nFocus on these specific topics: {topics_str}"
            
        return input_text

    def _parse_questions_from_response(self, response) -> List[Question]:
        """Parse questions from the response object"""
        try:
            questions = []
            
            # Check if the response is valid
            if not response or not response.output:
                logger.error("Empty response from OpenAI API")
                return []
                
            # Process each output item
            for output in response.output:
                if output.type == "message" and output.role == "assistant":
                    for content in output.content:
                        if content.type == "output_text":
                            # Try to parse the text as JSON
                            try:
                                # Find JSON array in the text
                                json_start = content.text.find('[')
                                json_end = content.text.rfind(']') + 1
                                
                                if json_start >= 0 and json_end > json_start:
                                    json_text = content.text[json_start:json_end]
                                    question_data = json.loads(json_text)
                                    
                                    # Convert each question dict to a Question object
                                    for q in question_data:
                                        question = Question(
                                            question=q.get("question", ""),
                                            answer=q.get("answer", ""),
                                            explanation=q.get("explanation"),
                                            difficulty=q.get("difficulty"),
                                            topic=q.get("topic")
                                        )
                                        questions.append(question)
                            except json.JSONDecodeError as e:
                                logger.error(f"Failed to parse JSON from response: {e}")
                                # Try to extract questions from plain text
                                questions.extend(self._extract_questions_from_text(content.text))
                            
            return questions
            
        except Exception as e:
            logger.error(f"Error parsing questions from response: {e}")
            return []

    def _extract_questions_from_text(self, text: str) -> List[Question]:
        """Extract questions from plain text when JSON parsing fails"""
        questions = []
        try:
            # Split text into lines
            lines = text.split('\n')
            current_question = None
            current_answer = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Look for question markers
                if line.startswith(('Q:', 'Question:', '1.', '2.', '3.')):
                    # Save previous question if exists
                    if current_question and current_answer:
                        questions.append(Question(
                            question=current_question,
                            answer=current_answer
                        ))
                    current_question = line.split(':', 1)[1].strip() if ':' in line else line
                    current_answer = None
                # Look for answer markers
                elif line.startswith(('A:', 'Answer:', 'Answer:')):
                    current_answer = line.split(':', 1)[1].strip() if ':' in line else line
            
            # Add the last question if exists
            if current_question and current_answer:
                questions.append(Question(
                    question=current_question,
                    answer=current_answer
                ))
                
        except Exception as e:
            logger.error(f"Error extracting questions from text: {e}")
            
        return questions

    def validate_questions(self, questions: List[Question]) -> List[Question]:
        """Validate and clean up generated questions"""
        valid_questions = []
        for q in questions:
            # Skip empty questions or answers
            if not q.question.strip() or not q.answer.strip():
                continue
                
            # Clean up the question and answer
            q.question = q.question.strip()
            q.answer = q.answer.strip()
            
            # Add default values if missing
            if not q.difficulty:
                q.difficulty = "medium"
            if not q.topic:
                q.topic = "General"
                
            valid_questions.append(q)
            
        return valid_questions 