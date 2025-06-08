# Study Legend User Guide

## Getting Started

### Installation

1. **Prerequisites**
   - Python 3.8 or higher
   - MongoDB 4.4 or higher
   - Git

2. **Clone the Repository**
   ```bash
   git clone https://github.com/your-org/study-legend.git
   cd study-legend
   ```

3. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

### Running the Application

1. **Start MongoDB**
   ```bash
   mongod --dbpath /path/to/data/directory
   ```

2. **Run the Application**
   ```bash
   streamlit run run.py
   ```

3. **Access the Application**
   - Open your browser
   - Navigate to `http://localhost:8501`

## Basic Usage

### Creating Questions

1. **Navigate to Questions**
   - Click "Questions" in the sidebar
   - Select "Add New Question"

2. **Fill Question Details**
   - Enter subject
   - Select week
   - Write question
   - Provide answer
   - Click "Save"

### Practicing Questions

1. **Start Practice Session**
   - Click "Practice" in the sidebar
   - Select subject and week
   - Click "Start Practice"

2. **Answer Questions**
   - Read each question
   - Type your answer
   - Click "Submit"
   - Review feedback

3. **Track Progress**
   - View score after each question
   - Check overall progress
   - Review weak areas

### Managing Account

1. **Update Profile**
   - Click "Account" in the sidebar
   - Edit profile information
   - Save changes

2. **Change Settings**
   - Navigate to "Settings"
   - Adjust preferences
   - Save changes

## Advanced Features

### Analytics Dashboard

1. **View Statistics**
   - Click "Analytics" in the sidebar
   - View overall progress
   - Check subject-wise performance
   - Monitor weekly progress

2. **Export Data**
   - Click "Export" button
   - Select data range
   - Choose format (CSV/JSON)
   - Download file

### Study Planning

1. **Create Study Plan**
   - Click "Study Plan" in the sidebar
   - Set goals
   - Schedule practice sessions
   - Save plan

2. **Track Progress**
   - View plan completion
   - Adjust goals
   - Update schedule

## Troubleshooting

### Common Issues

1. **Application Won't Start**
   - Check MongoDB connection
   - Verify environment variables
   - Check port availability

2. **Login Issues**
   - Verify email format
   - Check password
   - Clear browser cache

3. **Data Not Saving**
   - Check database connection
   - Verify permissions
   - Check disk space

### Getting Help

1. **Documentation**
   - Check user guide
   - Review API documentation
   - Read FAQs

2. **Support**
   - Email: support@studylegend.com
   - GitHub Issues
   - Community Forum

## Best Practices

### Question Management

1. **Creating Questions**
   - Be specific and clear
   - Include context
   - Use proper formatting

2. **Organizing Questions**
   - Use consistent subjects
   - Follow week structure
   - Add relevant tags

### Study Habits

1. **Regular Practice**
   - Set daily goals
   - Review weak areas
   - Track progress

2. **Effective Learning**
   - Space out practice
   - Review mistakes
   - Use analytics

## Security

### Account Security

1. **Password Management**
   - Use strong passwords
   - Change regularly
   - Enable 2FA

2. **Data Protection**
   - Log out after use
   - Clear browser cache
   - Use secure connection

### Privacy

1. **Data Usage**
   - Review privacy policy
   - Control data sharing
   - Export/delete data

2. **Settings**
   - Adjust visibility
   - Control notifications
   - Manage permissions 