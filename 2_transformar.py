import pandas as pd
from sqlalchemy import text
from banco import get_engine

# ==========================================================================
# FASE 2 - TRANSFORMACAO E CAMADA SILVER
# Copia raw -> silver convertendo tipos (texto -> DECIMAL e DATE),
# respeitando a integridade referencial e calculando colunas derivadas.
# ==========================================================================


def converter_valor_monetario(serie):
    """
    Converte texto no formato brasileiro (ex: '1.234,56') para float.
    Strings vazias ou invalidas viram NaN (tratado como NULL no banco).
    """
    serie_limpa = (
        serie.astype(str)
        .str.strip()
        .replace({"": None, "nan": None, "None": None})
    )
    serie_limpa = serie_limpa.str.replace(".", "", regex=False)   # remove separador de milhar
    serie_limpa = serie_limpa.str.replace(",", ".", regex=False)  # troca decimal br -> padrao
    return pd.to_numeric(serie_limpa, errors="coerce")


def converter_data(serie):
    """Converte texto DD/MM/AAAA para data. Valores invalidos viram NaT (NULL)."""
    return pd.to_datetime(serie, format="%d/%m/%Y", errors="coerce")


def truncar_silver(engine):
    """Limpa todas as tabelas silver em uma unica instrucao (respeita as FKs)."""
    with engine.begin() as conexao:
        conexao.execute(text("""
            TRUNCATE TABLE
                silver.silver_passagem,
                silver.silver_pagamento,
                silver.silver_trecho,
                silver.silver_viagem
            RESTART IDENTITY;
        """))
    print("Tabelas silver truncadas.")


def filtrar_orfaos(df, ids_validos, nome_tabela):
    """Remove linhas cujo id_viagem nao existe na silver_viagem. Loga quantas foram descartadas."""
    total_antes = len(df)
    df_filtrado = df[df["id_viagem"].isin(ids_validos)].copy()
    descartadas = total_antes - len(df_filtrado)
    if descartadas > 0:
        print(f"  Aviso: {descartadas} linhas de {nome_tabela} descartadas "
              f"(id_viagem sem correspondencia em silver_viagem).")
    return df_filtrado


def transformar_viagem(engine):
    print("\nProcessando: SILVER_VIAGEM")
    df = pd.read_sql("SELECT * FROM raw.raw_viagem", con=engine)

    df["valor_diarias"] = converter_valor_monetario(df["valor_diarias"])
    df["valor_passagens"] = converter_valor_monetario(df["valor_passagens"])
    df["valor_devolucao"] = converter_valor_monetario(df["valor_devolucao"])
    df["valor_outros_gastos"] = converter_valor_monetario(df["valor_outros_gastos"])

    df["data_inicio"] = converter_data(df["data_inicio"])
    df["data_fim"] = converter_data(df["data_fim"])

    # colunas calculadas
    df["duracao_dias"] = (df["data_fim"] - df["data_inicio"]).dt.days + 1
    df["duracao_dias"] = df["duracao_dias"].fillna(1)
    df.loc[df["duracao_dias"] < 1, "duracao_dias"] = 1  # nunca menor que 1 dia

    df["valor_total"] = (
        df["valor_diarias"].fillna(0)
        + df["valor_passagens"].fillna(0)
        + df["valor_outros_gastos"].fillna(0)
        - df["valor_devolucao"].fillna(0)
    )

    df["custo_medio_diario"] = df["valor_total"] / df["duracao_dias"]

    df_silver = df.rename(columns={"nome": "nome_viajante"})[[
        "id_viagem", "num_proposta", "situacao", "viagem_urgente",
        "cod_orgao_superior", "nome_orgao_superior", "nome_viajante", "cargo",
        "data_inicio", "data_fim", "destinos", "motivo",
        "valor_diarias", "valor_passagens", "valor_devolucao", "valor_outros_gastos",
        "valor_total", "duracao_dias", "custo_medio_diario",
    ]]

    # remove duplicidade de PK, caso exista, mantendo a primeira ocorrencia
    df_silver = df_silver.drop_duplicates(subset="id_viagem", keep="first")

    df_silver.to_sql("silver_viagem", con=engine, schema="silver",
                      if_exists="append", index=False)
    print(f"  {len(df_silver)} linhas carregadas em silver.silver_viagem.")

    return set(df_silver["id_viagem"])


def transformar_passagem(engine, ids_validos):
    print("\nProcessando: SILVER_PASSAGEM")
    df = pd.read_sql("SELECT * FROM raw.raw_passagem", con=engine)

    df["valor_passagem"] = converter_valor_monetario(df["valor_passagem"])
    df["taxa_servico"] = converter_valor_monetario(df["taxa_servico"])
    df["data_emissao"] = converter_data(df["data_emissao"])

    df = filtrar_orfaos(df, ids_validos, "raw_passagem")

    df_silver = df[[
        "id_viagem", "meio_transporte", "pais_origem_ida", "uf_origem_ida",
        "cidade_origem_ida", "pais_destino_ida", "uf_destino_ida",
        "cidade_destino_ida", "valor_passagem", "taxa_servico", "data_emissao",
    ]]

    df_silver.to_sql("silver_passagem", con=engine, schema="silver",
                      if_exists="append", index=False)
    print(f"  {len(df_silver)} linhas carregadas em silver.silver_passagem.")


def transformar_pagamento(engine, ids_validos):
    print("\nProcessando: SILVER_PAGAMENTO")
    df = pd.read_sql("SELECT * FROM raw.raw_pagamento", con=engine)

    df["valor"] = converter_valor_monetario(df["valor"])
    df = filtrar_orfaos(df, ids_validos, "raw_pagamento")

    # tipo_pagamento e NOT NULL na silver: descarta linhas sem essa informacao
    antes = len(df)
    df = df[df["tipo_pagamento"].notna() & (df["tipo_pagamento"].str.strip() != "")]
    descartadas = antes - len(df)
    if descartadas > 0:
        print(f"  Aviso: {descartadas} linhas de raw_pagamento descartadas (tipo_pagamento vazio).")

    df_silver = df[[
        "id_viagem", "num_proposta", "nome_orgao_pagador",
        "nome_ug_pagadora", "tipo_pagamento", "valor",
    ]]

    df_silver.to_sql("silver_pagamento", con=engine, schema="silver",
                      if_exists="append", index=False)
    print(f"  {len(df_silver)} linhas carregadas em silver.silver_pagamento.")


def transformar_trecho(engine, ids_validos):
    print("\nProcessando: SILVER_TRECHO")
    df = pd.read_sql("SELECT * FROM raw.raw_trecho", con=engine)

    df["origem_data"] = converter_data(df["origem_data"])
    df["destino_data"] = converter_data(df["destino_data"])
    df["numero_diarias"] = converter_valor_monetario(df["numero_diarias"])
    df["sequencia_trecho"] = pd.to_numeric(df["sequencia_trecho"], errors="coerce")

    df = filtrar_orfaos(df, ids_validos, "raw_trecho")

    # remove duplicidade de (id_viagem, sequencia_trecho), que e UNIQUE na silver
    antes = len(df)
    df = df.drop_duplicates(subset=["id_viagem", "sequencia_trecho"], keep="first")
    descartadas = antes - len(df)
    if descartadas > 0:
        print(f"  Aviso: {descartadas} linhas de raw_trecho descartadas (sequencia_trecho duplicada).")

    df_silver = df[[
        "id_viagem", "sequencia_trecho", "origem_data", "origem_uf", "origem_cidade",
        "destino_data", "destino_uf", "destino_cidade", "meio_transporte", "numero_diarias",
    ]]

    df_silver.to_sql("silver_trecho", con=engine, schema="silver",
                      if_exists="append", index=False)
    print(f"  {len(df_silver)} linhas carregadas em silver.silver_trecho.")


def main():
    engine = get_engine()

    try:
        truncar_silver(engine)
        ids_validos = transformar_viagem(engine)
        transformar_passagem(engine, ids_validos)
        transformar_pagamento(engine, ids_validos)
        transformar_trecho(engine, ids_validos)
        print("\nTransformacao concluida.")
    except Exception as erro:
        print(f"\nERRO durante a transformacao: {erro}")


if __name__ == "__main__":
    main()