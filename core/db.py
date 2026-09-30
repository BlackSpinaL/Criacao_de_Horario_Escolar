"""Conexão com o banco de dados (PostgreSQL/Supabase ou SQLite local)."""
import os
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def get_db_url() -> str:
    """Lê a URL do banco do secrets ou de variável de ambiente."""
    try:
        return st.secrets["database"]["url"]
    except (KeyError, FileNotFoundError):
        return os.getenv(
            "DATABASE_URL",
            "sqlite:///data/grade.db",
        )


def get_engine():
    """Cria o engine do SQLAlchemy."""
    url = get_db_url()
    if url.startswith("sqlite"):
        os.makedirs("data", exist_ok=True)
    return create_engine(url, future=True, pool_pre_ping=True)


def get_session():
    """Devolve uma sessão do banco."""
    engine = get_engine()
    Session = sessionmaker(bind=engine, future=True)
    return Session()
