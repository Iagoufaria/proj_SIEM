"""Modelos e sessao do banco de dados (SQLite via SQLAlchemy)."""
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker

import config

Base = declarative_base()

engine = create_engine(
    config.DATABASE_URL,
    connect_args={"check_same_thread": False},
)
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)


class Alerta(Base):
    __tablename__ = "alertas"

    id = Column(Integer, primary_key=True)
    data_hora = Column(DateTime, default=datetime.now)
    usuario = Column(String, nullable=False)
    ip_origem = Column(String, nullable=False)
    pais = Column(String)
    codigo_pais = Column(String)
    mensagem_bruta = Column(String)


class Usuario(Base):
    """Conta de acesso ao painel administrativo do SIEM."""

    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    criado_em = Column(DateTime, default=datetime.now)


def init_db() -> None:
    """Cria as tabelas caso ainda nao existam."""
    Base.metadata.create_all(engine)
