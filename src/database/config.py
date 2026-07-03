import os
import streamlit as st
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL:
    SUPABASE_URL = st.secrets["supabase_url"]

if not SUPABASE_KEY:
    SUPABASE_KEY = st.secrets["supabase_key"]

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)