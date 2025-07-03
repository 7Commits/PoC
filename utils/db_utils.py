import configparser
from pathlib import Path
from sqlalchemy import create_engine, text

_engine = None


def get_engine():
    """Restituisce un'istanza di motore SQLAlchemy."""
    global _engine
    if _engine is None:
        config = configparser.ConfigParser()
        config.read(Path(__file__).resolve().parent.parent / 'db.config')
        cfg = config['mysql']
        url = (
            f"mysql+pymysql://{cfg['user']}:{cfg['password']}@{cfg['host']}:{cfg.get('port', 3306)}/{cfg['database']}"            f"{cfg['database']}"
        )
        _engine = create_engine(url)
    return _engine


def init_db():
    """Crea le tabelle necessarie se non esistono."""
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                """CREATE TABLE IF NOT EXISTS questions (
                    id VARCHAR(36) PRIMARY KEY,
                    domanda TEXT,
                    risposta_attesa TEXT,
                    categoria TEXT
                )"""
            )
        )
        conn.execute(
            text(
                """CREATE TABLE IF NOT EXISTS question_sets (
                    id VARCHAR(36) PRIMARY KEY,
                    name TEXT,
                    questions TEXT
                )"""
            )
        )
        conn.execute(
            text(
                """CREATE TABLE IF NOT EXISTS question_set_questions (
                    set_id VARCHAR(36),
                    question_id VARCHAR(36),
                    PRIMARY KEY (set_id, question_id)
                )"""
            )
        )
        conn.execute(
            text(
                """CREATE TABLE IF NOT EXISTS test_results (
                    id VARCHAR(36) PRIMARY KEY,
                    set_id VARCHAR(36),
                    timestamp TEXT,
                    results JSON
                )"""
            )
        )
        conn.execute(
            text(
                """CREATE TABLE IF NOT EXISTS api_presets (
                    id VARCHAR(36) PRIMARY KEY,
                    name TEXT,
                    provider_name TEXT,
                    endpoint TEXT,
                    api_key TEXT,
                    model TEXT,
                    temperature FLOAT,
                    max_tokens INT
                )"""
            )
        )

