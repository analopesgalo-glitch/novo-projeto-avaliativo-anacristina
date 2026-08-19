import pandas as pd
from config import ARQUIVOS_CSV

for nome, caminho in ARQUIVOS_CSV.items():
    print(f"\n{'='*60}")
    print(f"TABELA: {nome.upper()}  ({caminho.name})")
    print(f"{'='*60}")
    try:
        df = pd.read_csv(caminho, sep=None, engine="python", encoding="latin-1", nrows=5)
        print(f"Total de colunas: {len(df.columns)}\n")
        for i, col in enumerate(df.columns, start=1):
            print(f"  {i:2d}. {col}")
    except Exception as e:
        print(f"Erro ao ler {caminho.name}: {e}")