"""Conexão com o banco de dados (PostgreSQL/Supabase ou SQLite local)."""
import os
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool


@st.cache_resource(show_spinner=False)
def _criar_engine(url: str):
    """
    Cria o engine do SQLAlchemy uma única vez por URL.

    - NullPool: abre e fecha conexão a cada uso (evita esgotar o limite do Supabase)
    - pool_pre_ping: verifica se a conexão está viva antes de usar
    - cache_resource: reaproveita o engine entre reruns do Streamlit
    """
    return create_engine(
        url,
        future=True,
        poolclass=NullPool,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 10},
    )


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
    """Devolve um engine único do SQLAlchemy (cacheado)."""
    url = get_db_url()
    if url.startswith("sqlite"):
        os.makedirs("data", exist_ok=True)
    return _criar_engine(url)


def get_session():
    """Devolve uma sessão do banco."""
    engine = get_engine()
    Session = sessionmaker(bind=engine, future=True)
    return Session()
