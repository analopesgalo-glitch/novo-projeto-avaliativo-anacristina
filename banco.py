from sqlalchemy import create_engine
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD


def get_engine():
    """
    Cria e retorna a engine de conexão com o PostgreSQL,
    usada pelos scripts de extração e transformação.
    """
    url = (
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    engine = create_engine(url)
    return engine