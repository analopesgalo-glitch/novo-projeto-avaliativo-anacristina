import pandas as pd
from sqlalchemy import text
from config import ARQUIVOS_CSV
from banco import get_engine

# ==========================================================================
# FASE 1 - EXTRACAO E CAMADA RAW
# Le os 4 CSVs locais e carrega nas tabelas raw, sem alterar o conteudo.
# Processo idempotente (TRUNCATE) e resiliente (try/except).
# ==========================================================================

TAMANHO_BLOCO = 50_000  # linhas por bloco (chunksize)

# Mapeamento: nome da coluna no CSV original -> nome da coluna na tabela raw
# (so muda o NOME da coluna; o conteudo/valor permanece 100% original)

MAPA_VIAGEM = {
    "Identificador do processo de viagem": "id_viagem",
    "Número da Proposta (PCDP)": "num_proposta",
    "Situação": "situacao",
    "Viagem Urgente": "viagem_urgente",
    "Justificativa Urgência Viagem": "justificativa_urgencia_viagem",
    "Código do órgão superior": "cod_orgao_superior",
    "Nome do órgão superior": "nome_orgao_superior",
    "Código órgão solicitante": "cod_orgao_solicitante",
    "Nome órgão solicitante": "nome_orgao_solicitante",
    "CPF viajante": "cpf_viajante",
    "Nome": "nome",
    "Cargo": "cargo",
    "Função": "funcao",
    "Descrição Função": "descricao_funcao",
    "Período - Data de início": "data_inicio",
    "Período - Data de fim": "data_fim",
    "Destinos": "destinos",
    "Motivo": "motivo",
    "Valor diárias": "valor_diarias",
    "Valor passagens": "valor_passagens",
    "Valor devolução": "valor_devolucao",
    "Valor outros gastos": "valor_outros_gastos",
}

MAPA_PASSAGEM = {
    "Identificador do processo de viagem": "id_viagem",
    "Número da Proposta (PCDP)": "num_proposta",
    "Meio de transporte": "meio_transporte",
    "País - Origem ida": "pais_origem_ida",
    "UF - Origem ida": "uf_origem_ida",
    "Cidade - Origem ida": "cidade_origem_ida",
    "País - Destino ida": "pais_destino_ida",
    "UF - Destino ida": "uf_destino_ida",
    "Cidade - Destino ida": "cidade_destino_ida",
    "País - Origem volta": "pais_origem_volta",
    "UF - Origem volta": "uf_origem_volta",
    "Cidade - Origem volta": "cidade_origem_volta",
    "Pais - Destino volta": "pais_destino_volta",
    "UF - Destino volta": "uf_destino_volta",
    "Cidade - Destino volta": "cidade_destino_volta",
    "Valor da passagem": "valor_passagem",
    "Taxa de serviço": "taxa_servico",
    "Data da emissão/compra": "data_emissao",
    "Hora da emissão/compra": "hora_emissao",
}

MAPA_PAGAMENTO = {
    "Identificador do processo de viagem": "id_viagem",
    "Número da Proposta (PCDP)": "num_proposta",
    "Código do órgão superior": "cod_orgao_superior",
    "Nome do órgão superior": "nome_orgao_superior",
    "Codigo do órgão pagador": "cod_orgao_pagador",
    "Nome do órgao pagador": "nome_orgao_pagador",
    "Código da unidade gestora pagadora": "cod_ug_pagadora",
    "Nome da unidade gestora pagadora": "nome_ug_pagadora",
    "Tipo de pagamento": "tipo_pagamento",
    "Valor": "valor",
}

MAPA_TRECHO = {
    "Identificador do processo de viagem": "id_viagem",
    "Número da Proposta (PCDP)": "num_proposta",
    "Sequência Trecho": "sequencia_trecho",
    "Origem - Data": "origem_data",
    "Origem - País": "origem_pais",
    "Origem - UF": "origem_uf",
    "Origem - Cidade": "origem_cidade",
    "Destino - Data": "destino_data",
    "Destino - País": "destino_pais",
    "Destino - UF": "destino_uf",
    "Destino - Cidade": "destino_cidade",
    "Meio de transporte": "meio_transporte",
    "Número Diárias": "numero_diarias",
    "Missao?": "missao",
}

TABELAS = {
    "viagem":   {"tabela_raw": "raw_viagem",   "mapa": MAPA_VIAGEM},
    "passagem": {"tabela_raw": "raw_passagem", "mapa": MAPA_PASSAGEM},
    "pagamento":{"tabela_raw": "raw_pagamento","mapa": MAPA_PAGAMENTO},
    "trecho":   {"tabela_raw": "raw_trecho",   "mapa": MAPA_TRECHO},
}


def truncar_tabela(engine, tabela_raw):
    """Garante idempotencia: limpa a tabela raw antes de recarregar."""
    with engine.begin() as conexao:
        conexao.execute(text(f"TRUNCATE TABLE raw.{tabela_raw};"))
    print(f"  Tabela raw.{tabela_raw} truncada.")


def carregar_csv_em_blocos(caminho_csv, mapa_colunas, engine, tabela_raw):
    """Le o CSV em blocos (chunksize) e insere na tabela raw correspondente."""
    total_linhas = 0
    leitor = pd.read_csv(
        caminho_csv,
        sep=";",
        encoding="latin-1",
        dtype=str,               # mantem tudo como texto, sem alterar o conteudo
        chunksize=TAMANHO_BLOCO,
    )

    for bloco in leitor:
        bloco.columns = bloco.columns.str.strip()          # remove espacos extras do cabecalho
        bloco = bloco.rename(columns=mapa_colunas)
        bloco = bloco[list(mapa_colunas.values())]          # garante so as colunas mapeadas, na ordem certa

        bloco.to_sql(
            tabela_raw,
            con=engine,
            schema="raw",
            if_exists="append",
            index=False,
        )
        total_linhas += len(bloco)

    print(f"  {total_linhas} linhas carregadas em raw.{tabela_raw}.")


def main():
    engine = get_engine()

    for nome, info in TABELAS.items():
        print(f"\nProcessando: {nome.upper()}")
        tabela_raw = info["tabela_raw"]
        mapa = info["mapa"]
        caminho_csv = ARQUIVOS_CSV[nome]

        try:
            truncar_tabela(engine, tabela_raw)
            carregar_csv_em_blocos(caminho_csv, mapa, engine, tabela_raw)
        except Exception as erro:
            print(f"  ERRO ao processar {nome}: {erro}")

    print("\nExtracao concluida.")


if __name__ == "__main__":
    main()