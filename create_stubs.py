import os
import glob

# Stub content for all feature files
stub_content = '''import streamlit as st
from common_nav import setup_navigation

# Set the page config (should be the same across all pages)
st.set_page_config(
    page_title="Study Legend AI", 
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Create and run the navigation menu
pg = setup_navigation()
pg.run()
'''

# Get all feature files
feature_files = glob.glob("features/*.py")

# Skip __init__.py files
feature_files = [f for f in feature_files if not f.endswith("__init__.py")]

# Process each file
for file_path in feature_files:
    print(f"Creating stub for {file_path}")
    
    # Write the stub content to the file
    with open(file_path, 'w') as f:
        f.write(stub_content)
    
    print(f"Created stub for {file_path}")

print("All feature stubs created\!")
