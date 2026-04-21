# database/supabase_client.py
# DEMO MODE: Returns DemoClient that stores data in session_state
# No database connection required — the app works entirely in-memory.
import streamlit as st


def get_supabase():
    from database.demo_client import DemoClient
    return DemoClient()


def init_supabase():
    return get_supabase()