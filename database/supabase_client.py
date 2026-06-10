import streamlit as st


def get_supabase():
    from database.db_client import PgClient
    return PgClient()


def init_supabase():
    return get_supabase()
