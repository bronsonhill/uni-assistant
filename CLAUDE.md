# Study Legend Assistant Guidelines

## Setup & Commands
- **Run App**: `streamlit run Home.py`
- **Run Admin**: `streamlit run admin.py`
- **Install Dependencies**: `pip install -r requirements.txt`
- **Environment Setup**: Create `.env` file with OPENAI_API_KEY, ADMIN_USERNAME, ADMIN_PASSWORD

## Code Style Guidelines
- **Formatting**: Use consistent indentation (4 spaces) and follow PEP 8
- **Imports**: Group imports (stdlib, third-party, local), use absolute imports
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Documentation**: Docstrings for functions/classes, concise comments for complex logic
- **Error Handling**: Use try/except with specific error types, provide clear error messages
- **Types**: Use type hints when declaring function parameters and return values
- **Session State**: Use st.session_state for maintaining state between reruns
- **Functions**: Create single-purpose functions, follow SOLID principles
- **UI Components**: Follow streamlit container/column pattern for consistent layouts
- **Caching**: Use @st.cache_data for expensive operations (especially file I/O)

## Architecture
- **Pages**: Each feature in `features/` folder has a corresponding `run()` function
- **Data**: MonggDB (migrated from early development json files)
- **Auth**: Uses st_paywall for authentication, subscription status stored locally
- **Navigation**: Defined in common_nav.py with routes to different features