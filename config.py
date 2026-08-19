import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

# --- Configurações do Banco de Dados ---
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# --- Caminho dos dados locais (CSVs já baixados) ---
BASE_DIR = Path(__file__).resolve().parent
PASTA_DADOS = BASE_DIR / "dados"

ARQUIVOS_CSV = {
    "viagem": PASTA_DADOS / "2025_Viagem.csv",
    "passagem": PASTA_DADOS / "2025_Passagem.csv",
    "pagamento": PASTA_DADOS / "2025_Pagamento.csv",
    "trecho": PASTA_DADOS / "2025_Trecho.csv",
}