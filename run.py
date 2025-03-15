import streamlit as st
import os
import sys
from Home import main

if __name__ == "__main__":
    # This script is a simple wrapper that calls the main function from Home.py
    # It's provided for convenience when running the app using `python run.py`
    try:
        print("running main")
        sys.stdout.flush()
        main()

    except Exception as e:
        print(e)
        sys.stdout.flush()