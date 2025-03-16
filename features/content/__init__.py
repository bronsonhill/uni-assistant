# This file makes the features/content directory a proper Python package
# so we can import from it using: from features.content import XXX_content

# Import refactored practice modules for easy access
from features.content.practice.practice_content import run as run_practice
from features.content.practice.practice_core import (
    init_session_state as init_practice_state,
    reset_practice,
    start_practice,
    build_queue
)
from features.content.practice.practice_ui import (
    display_practice_question,
    display_practice_navigation,
    display_knowledge_level_selector,
    display_setup_screen
)
from features.content.practice.practice_demo import (
    show_demo_content,
    show_premium_benefits
)