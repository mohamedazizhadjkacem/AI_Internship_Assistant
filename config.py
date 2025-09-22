import streamlit as st
import os

# --- Continuous Scraping Configuration ---
SCRAPING_INTERVAL_MINUTES = 15 # The time in minutes between each scrape

# OpenAI API Key
#OPENAI_API_KEY = "YOUR_OPENAI_API_KEY_HERE"

# --- Supabase Configuration ---
# Try to get from Streamlit secrets first, then fallback to environment variables
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except (FileNotFoundError, KeyError):
    # Fallback to environment variables
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")

