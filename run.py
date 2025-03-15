import streamlit as st
import os
from Home import main

if __name__ == "__main__":
    # This script is a simple wrapper that calls the main function from Home.py
    # It's provided for convenience when running the app using `python run.py`
    try:
        os.write("running main")
        main()

    except Exception as e:
        os.write("log: " + e)