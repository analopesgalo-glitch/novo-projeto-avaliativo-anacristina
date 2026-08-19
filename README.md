# Pipeline ETL - Viagens a Servico (Portal da Transparencia)

Projeto avaliativo do curso de Analise de Dados com Python - Modulo 1.

Autora: Ana Cristina ([@analopesgalo-glitch](https://github.com/analopesgalo-glitch))

## Problema

O Portal da Transparencia do Governo Federal disponibiliza dados publicos sobre
viagens a servico de servidores e agentes publicos, mas em sua forma bruta -- sem
tipagem, com inconsistencias e sem estrutura pronta para analise. Este projeto
constroi um pipeline de dados de ponta a ponta (ELT) que extrai, carrega e transforma
esses dados brutos em informacao confiavel para tomada de decisao, seguindo a
Arquitetura Medallion (camadas Raw, Silver e Gold).

O recorte de dados utilizado cobre 6 meses de viagens realizadas em 2025, distribuidas
em 4 arquivos CSV: Viagem, Passagem, Pagamento e Trecho.

## Tecnologias utilizadas

- **Python 3.14** -- linguagem principal do pipeline
- **PostgreSQL 18** -- banco de dados relacional
- **pandas** -- leitura e transformacao dos dados
- **SQLAlchemy** + **psycopg2** -- conexao e execucao de SQL no PostgreSQL
- **python-dotenv** -- gerenciamento seguro de credenciais via `.env`
- **Jupyter Notebook** -- camada de analise e visualizacao
- **matplotlib** e **seaborn** -- geracao dos graficos
- **Git e GitHub** -- versionamento e entrega

## Arquitetura do pipeline (Medallion)

CSVs locais (dados/)
&nbsp;&nbsp;&nbsp;&nbsp;|
&nbsp;&nbsp;&nbsp;&nbsp;v
[1_extrair.py] --> camada RAW (dados brutos, tipagem VARCHAR, fiel ao CSV original)
&nbsp;&nbsp;&nbsp;&nbsp;|
&nbsp;&nbsp;&nbsp;&nbsp;v
[2_transformar.py] --> camada SILVER (tipada, com PK/FK/constraints, colunas calculadas)
&nbsp;&nbsp;&nbsp;&nbsp;|
&nbsp;&nbsp;&nbsp;&nbsp;v
[3_analise.ipynb] --> camada GOLD (agregada via JOIN + GROUP BY, tabela + view) + 4 perguntas de negocio (analise, tabela e grafico)

## Estrutura do repositorio

- `dados/` -- CSVs originais (nao versionados, ver .gitignore)
- `sql/0_criar_banco.sql` -- Fase 0: cria schemas raw/silver e as 8 tabelas
- `1_extrair.py` -- Fase 1: extrai os CSVs e carrega na camada Raw
- `2_transformar.py` -- Fase 2: transforma Raw -> Silver
- `3_analise.ipynb` -- Fase 3: cria a camada Gold e responde as 4 perguntas
- `banco.py` -- conexao com o PostgreSQL (SQLAlchemy)
- `config.py` -- configuracoes e caminhos dos arquivos
- `requirements.txt` -- dependencias do projeto
- `.env.example` -- modelo de variaveis de ambiente
- `.env` -- credenciais reais (nao versionado)
- `.gitignore`

## Como executar o projeto

### Pre-requisitos

- Python 3.10 ou superior instalado
- PostgreSQL instalado e rodando localmente (com o pgAdmin, se preferir interface grafica)
- Os 4 arquivos CSV (2025_Viagem.csv, 2025_Passagem.csv, 2025_Pagamento.csv,
  2025_Trecho.csv) salvos dentro de uma pasta `dados/` na raiz do projeto

### Passo 1 - Clonar o repositorio

    git clone https://github.com/analopesgalo-glitch/novo-projeto-avaliativo-anacristina.git
    cd novo-projeto-avaliativo-anacristina

### Passo 2 - Criar e ativar o ambiente virtual

    python -m venv venv

No Windows (PowerShell):

    .\venv\Scripts\Activate.ps1

No Linux/Mac:

    source venv/bin/activate

### Passo 3 - Instalar as dependencias

    pip install -r requirements.txt

### Passo 4 - Configurar as variaveis de ambiente

Copie o arquivo de exemplo e preencha com suas credenciais reais do PostgreSQL:

    cp .env.example .env

Edite o `.env` com o host, porta, nome do banco, usuario e senha do seu PostgreSQL local.

### Passo 5 - Criar o banco e as tabelas

Abra o pgAdmin (ou outro cliente PostgreSQL), conecte-se ao banco `viagens_gov`
(crie-o antes, se ainda nao existir), e execute o conteudo do arquivo `sql/0_criar_banco.sql`.

Isso cria os schemas `raw` e `silver` e as 8 tabelas do projeto.

### Passo 6 - Rodar a extracao (camada Raw)

    python 1_extrair.py

### Passo 7 - Rodar a transformacao (camada Silver)

    python 2_transformar.py

### Passo 8 - Rodar a analise (camada Gold)

Abra o arquivo `3_analise.ipynb` no VS Code (ou Jupyter), selecione o kernel do
ambiente virtual (venv) e execute todas as celulas em ordem. Esse notebook cria a
camada Gold (tabela e view `gold_resumo_pagamentos_mensais`) e responde as 4 perguntas
de negocio do projeto.

## Perguntas de negocio respondidas

**Camada Silver:**
1. Viagens classificadas como urgentes custam mais por dia do que as nao urgentes?
2. Como o custo medio diario varia conforme a faixa de duracao da viagem?

**Camada Gold:**
3. Como o valor total pago evoluiu mes a mes e qual tipo de pagamento sustenta essa evolucao?
4. Qual e o perfil de gasto dos orgaos pagadores (muitos pagamentos de valor baixo ou poucos pagamentos de valor alto)?

## Principais insights

- Viagens urgentes custam, em media, 35% mais por dia do que as planejadas com
  antecedencia (R$ 597,08 vs R$ 441,95).
- O custo medio diario nao cai de forma linear com a duracao: viagens de 2-3 dias sao
  as mais caras por dia (R$ 577,66), e so viagens de 16+ dias apresentam queda
  expressiva (R$ 341,50).
- O tipo de pagamento "DIARIAS" sustenta a maior parte do valor total pago
  mensalmente, com um pico notavel em janeiro de 2025.
- Orgaos pagadores tem perfis de gasto distintos: alguns fazem poucos pagamentos de
  valor alto (ex: Ministerio das Relacoes Exteriores), enquanto outros concentram
  grande volume de pagamentos de valor mais moderado (ex: Fundo Nacional de Saude).

O detalhamento completo de cada analise, com tabelas e graficos, esta disponivel no
notebook `3_analise.ipynb`.

## Melhorias futuras

- Ampliar o recorte temporal para o ano completo ou anos anteriores, permitindo
  identificar sazonalidade real;
- Investigar o pico de pagamentos de janeiro cruzando com a data de emissao das
  passagens;
- Cruzar a camada Gold com a tabela `silver_trecho` para relacionar custo com
  destinos nacionais vs internacionais;
- Explorar a coluna "Missao?" da tabela Trecho, ainda nao utilizada nas analises;
- Transformar a analise em um dashboard interativo (Streamlit ou Power BI).

## Boas praticas adotadas

- Credenciais armazenadas apenas no `.env`, fora do controle de versao;
- `.gitignore` protegendo `.env`, `venv/` e os CSVs brutos (`dados/`);
- Scripts idempotentes (TRUNCATE antes de cada carga) e resilientes (try/except);
- Codigo modularizado (config.py, banco.py separados dos scripts de execucao);
- Commits sucintos, um por funcionalidade concluida.