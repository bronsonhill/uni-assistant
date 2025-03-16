# Content Features

This directory contains the various content features of the application, organized into feature-specific folders.

## Folder Structure

- `add_ai/`: AI Question Generator feature
  - `add_ai_content.py`: Main integration file
  - `add_ai_core.py`: Core functionality
  - `add_ai_ui.py`: UI components
  - `add_ai_demo.py`: Demo content

- `add_manual/`: Add Questions Manually feature
  - `add_manual_content.py`: Main file

- `manage/`: Manage Questions feature
  - `manage_content.py`: Main integration file
  - `manage_core.py`: Core functionality
  - `manage_ui.py`: UI components
  - `manage_demo.py`: Demo content

- `practice/`: Practice feature
  - `practice_content.py`: Main integration file
  - `practice_core.py`: Core functionality
  - `practice_ui.py`: UI components
  - `practice_demo.py`: Demo content

- `tutor/`: Subject Tutor feature
  - `tutor_content.py`: Main integration file
  - `tutor_core.py`: Core functionality
  - `tutor_ui.py`: UI components
  - `tutor_demo.py`: Demo content

- `base_content.py`: Shared functionality used across features

## Architecture

Each feature follows a modular architecture with the following components:

1. **Content**: The main integration file that orchestrates the feature
2. **Core**: Core functionality and business logic
3. **UI**: User interface components and display functions
4. **Demo**: Demo content for unauthenticated users

This modular approach improves:
- **Readability**: Each file has a clear, specific purpose
- **Maintainability**: Smaller files are easier to work with
- **Reusability**: Components can be reused across features
- **Testability**: Isolated components are easier to test 