# Study Legend

Become a study legend with AI!

## Features

- AI-generated practice questions
- Flashcard-based study with spaced repetition
- AI tutoring with subject knowledge
- Assessments tracking
- Question management
- Multi-page navigation with streamlined UI

## User Authentication and Subscription System

This application includes a user authentication and subscription management system with the following components:

### Authentication

- Google OAuth via `st_paywall` is used to authenticate users.
- User emails are stored securely and used to identify users.

### Subscription Management

The application supports a freemium model:
- **Free tier**: Access to basic features (Practice, Manage Questions, Add Manually)
- **Premium tier**: Access to all features including AI-driven features (Add Cards with AI, Subject Tutor, Assessments)

### Subscription Storage and Verification

The subscription system stores user data in a local JSON file (`users.json`). Each user record includes:

- Email address (primary identifier)
- Subscription status (active/inactive)
- Subscription end date
- Account creation date
- Last login timestamp
- Login count

### Admin Interface

An admin interface is available at `/admin` which provides:

- User management (view/search users)
- Ability to manually activate or deactivate subscriptions
- Set subscription duration
- View user activity

## Setup and Running

1. Install requirements:
   ```
   pip install -r requirements.txt
   ```

2. Set up your API keys and configuration using Streamlit secrets:
   
   a. Create a `.streamlit/secrets.toml` file:
      ```
      # Copy from example_secrets.toml or create a new file
      cp example_secrets.toml .streamlit/secrets.toml
      # Then edit the file with your actual API keys
      ```
   
   b. Add your API keys and credentials to the secrets file:
      ```toml
      # .streamlit/secrets.toml
      OPENAI_API_KEY = "your_openai_api_key"
      ADMIN_USERNAME = "admin_username"  
      ADMIN_PASSWORD = "secure_password"
      DEBUG_MODE = "false"
      ```

   c. Alternatively, you can still use environment variables in a `.env` file:
      ```
      OPENAI_API_KEY=your_openai_api_key
      ADMIN_USERNAME=admin_username
      ADMIN_PASSWORD=secure_password
      DEBUG_MODE=false
      ```

3. Run the application:
   ```
   streamlit run Home.py
   ```

4. Access the admin interface:
   ```
   streamlit run admin.py
   ```

> **Note:** Streamlit secrets are the recommended way to store API keys and credentials because they:
> - Are automatically excluded from version control
> - Work consistently across development and deployment environments
> - Provide better security than environment variables

## Development and Debug Mode

For development purposes, you can enable debug mode by setting `DEBUG_MODE=true` in your environment variables. This bypasses authentication and uses a test user account.

## Integration with External Payment Systems

The system is designed to work with:

1. **st_paywall**: Handles OAuth authentication and subscription verification
2. Local user database: Tracks subscription status and user information

For production use, you would integrate with a real payment provider like Stripe or Buy Me A Coffee through the st_paywall library, which would then update the user records in users.json.

## File Structure

- `Home.py` - Main application entry point
- `admin.py` - Admin interface for user management
- `paywall.py` - Subscription and authentication logic
- `users.py` - User management functions
- `users.json` - User database
- `common_nav.py` - Navigation system
- `features/` - Feature modules
  - `content/` - Content modules for each feature
    - Premium features: add_ai_content.py, tutor_content.py, assessments_content.py
    - Free features: practice_content.py, manage_content.py, add_manual_content.py

## Original Features

- Create and manage study questions with subjects and weeks
- Add optional expected answers for self-checking
- Practice mode with sequential or random question order
- Time-weighted scoring system that tracks your progress
- Smart practice mode that prioritizes questions needing review
- Filter questions by subject and/or week during practice
- Multi-page navigation for improved user experience
- AI-powered feedback on your answers using OpenAI API
- Simple JSON-based storage system
