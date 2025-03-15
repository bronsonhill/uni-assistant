"""
Generate feature file stubs for Study Legend application.

This script creates empty feature files that use the centralized feature setup module.
"""
import os
import glob
import argparse

# Template content for all feature files
STUB_TEMPLATE = '''"""
{title} feature page.

This page {description}
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from feature_setup import setup_feature_page

# Set up the page with standard configuration
# {comment}
setup_feature_page(display_subscription={display_subscription}, required={required})
'''

def create_stub(file_path, title, description, display_subscription=True, required=False, comment=""):
    """Create a feature file stub using the template."""
    content = STUB_TEMPLATE.format(
        title=title,
        description=description,
        display_subscription=str(display_subscription),
        required=str(required),
        comment=comment
    )
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Write the stub content to the file
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"Created stub for {file_path}")

def main():
    parser = argparse.ArgumentParser(description="Create feature file stubs")
    parser.add_argument("--all", action="store_true", help="Recreate all feature stubs")
    parser.add_argument("--file", help="Create a specific feature file")
    parser.add_argument("--title", help="Title for the feature")
    parser.add_argument("--description", help="Description for the feature")
    
    args = parser.parse_args()
    
    if args.all:
        # Example feature definitions with consistent parameters
        features = [
            {
                "file": "features/1_🤖_Add_Queue_Cards_with_AI.py",
                "title": "Add Queue Cards with AI",
                "description": "allows users to upload course materials and generate study cards using AI.",
                "display_subscription": True,
                "required": False,
                "comment": "This is a premium feature that displays subscription status"
            },
            {
                "file": "features/2_📝_Manage_Questions.py",
                "title": "Manage Questions",
                "description": "allows users to view, edit, and delete their existing questions.",
                "display_subscription": True,
                "required": False,
                "comment": "This is a free feature that displays subscription status"
            },
            {
                "file": "features/3_🆕_Add_Questions_Manually.py",
                "title": "Add Questions Manually",
                "description": "allows users to create new study questions by manually inputting question and answer pairs.",
                "display_subscription": True,
                "required": False,
                "comment": "This is a free feature that displays subscription status"
            },
            {
                "file": "features/4_🎯_Practice.py",
                "title": "Practice",
                "description": "allows users to test their knowledge with their created questions.",
                "display_subscription": True,
                "required": False,
                "comment": "This is a free feature that displays subscription status"
            },
            {
                "file": "features/5_💬_Subject_Tutor.py",
                "title": "Subject Tutor",
                "description": "provides a chat interface to connect users with an AI study buddy that knows their course materials.",
                "display_subscription": False, 
                "required": False,
                "comment": "This is a premium feature where subscription status is handled in the content file"
            },
            {
                "file": "features/6_📅_Assessments.py",
                "title": "Assessments",
                "description": "helps users track exams, assignments, and quizzes with due dates.",
                "display_subscription": False,
                "required": False,
                "comment": "This is a premium feature where subscription status is handled in the content file"
            },
            {
                "file": "features/7_👤_Account.py",
                "title": "Account",
                "description": "provides account management functionality for users.",
                "display_subscription": True,
                "required": False,
                "comment": "For account page, we display subscription status"
            }
        ]
        
        # Create each feature stub
        for feature in features:
            create_stub(
                file_path=feature["file"],
                title=feature["title"],
                description=feature["description"],
                display_subscription=feature["display_subscription"],
                required=feature["required"],
                comment=feature["comment"]
            )
            
        print("All feature stubs created!")
    
    elif args.file and args.title and args.description:
        # Create a single feature stub
        create_stub(
            file_path=args.file,
            title=args.title,
            description=args.description
        )
    else:
        parser.print_help()

if __name__ == "__main__":
    main()