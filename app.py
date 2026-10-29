import pandas as pd
import streamlit as st




# Configuração da página
st.set_page_config(
    page_title="Loja Aurora | Dashboard",
    layout="wide"
)

st.title("Dashboard de vendas — Loja Aurora")
st.write("Análise do faturamento do primeiro semestre de 2025.")

# Carregar e tratar os dados
@st.cache_data
def carregar_vendas():
    # Nota: puxando da pasta dados/
    vendas = pd.read_csv("dados/vendas.csv", sep=";")

    vendas["vendedor"] = vendas["vendedor"].astype(str).str.strip().str.title()

    vendas["preco_unitario"] = (
        vendas["preco_unitario"].astype(str)
        .str.replace("R$", "", regex=False)
        .str.strip()
        .str.replace(",", ".", regex=False)
    )
    vendas["preco_unitario"] = pd.to_numeric(vendas["preco_unitario"], errors="raise")

    vendas["quantidade"] = pd.to_numeric(
        vendas["quantidade"].astype(str).str.strip(), errors="coerce"
    )

    vendas["data"] = pd.to_datetime(vendas["data"], format="%d/%m/%Y", errors="raise")

    # Descartar registros sem quantidade válida ANTES de calcular o valor
    vendas = vendas.dropna(subset=["quantidade"]).copy()
    vendas["quantidade"] = vendas["quantidade"].astype(int)
    
    # Criar coluna valor
    vendas["valor"] = vendas["quantidade"] * vendas["preco_unitario"]

    return vendas

@st.cache_data
def carregar_metas():
    metas = pd.read_csv("dados/metas.csv", sep=";")
    metas["vendedor"] = metas["vendedor"].astype(str).str.strip().str.title()
    return metas

# Funções de regra de negócio (Etapa 3)
def comissao(valor):
    if valor < 3000:
        return valor * 0.02
    elif valor < 6000:
        return valor * 0.05
    else:
        return valor * 0.08

def situacao(atingimento):
    return "Meta batida" if atingimento >= 100 else "Abaixo da meta"

# Carregar os dataframes
df = carregar_vendas()
metas = carregar_metas()

# --- FILTROS NA BARRA LATERAL ---
st.sidebar.header("Filtros")

# Filtro 1: Região
regioes = ["Todas"] + sorted(df["regiao"].dropna().unique().tolist())
regiao_selecionada = st.sidebar.selectbox("Selecione a região", regioes)

# Filtro 2: Vendedor (Bônus para ficar mais completo)
vendedores = ["Todos"] + sorted(df["vendedor"].unique().tolist())
vendedor_selecionado = st.sidebar.selectbox("Selecione o vendedor", vendedores)

# Aplicar filtros
df_filtrado = df.copy()
if regiao_selecionada != "Todas":
    df_filtrado = df_filtrado[df_filtrado["regiao"] == regiao_selecionada]
if vendedor_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["vendedor"] == vendedor_selecionado]

# --- INDICADORES (st.metric) ---
faturamento_total = df_filtrado["valor"].sum()
quantidade_vendas = len(df_filtrado)
quantidade_vendedores = df_filtrado["vendedor"].nunique()

col1, col2, col3 = st.columns(3)
col1.metric("Faturamento total", f"R$ {faturamento_total:,.2f}")
col2.metric("Vendas registradas", f"{quantidade_vendas}")
col3.metric("Vendedores", f"{quantidade_vendedores}")

# --- GRÁFICO 1: Faturamento Mensal ---
st.subheader("Faturamento por mês")
meses = {1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho"}
faturamento_mensal = df_filtrado.groupby(df_filtrado["data"].dt.month)["valor"].sum()
faturamento_mensal.index = [meses[mes] for mes in faturamento_mensal.index]
st.line_chart(faturamento_mensal)

# --- GRÁFICO 2: Faturamento por Produto ---
st.subheader("Produtos com maior faturamento")
faturamento_produto = (
    df_filtrado.groupby("produto")["valor"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
)
st.bar_chart(faturamento_produto)

# --- NOVA SEÇÃO: Metas e Comissão ---
st.subheader("Atingimento de Metas e Comissão")
resumo_metas = df_filtrado.groupby("vendedor")["valor"].sum().reset_index()
resumo_metas = resumo_metas.rename(columns={"valor": "total_vendido"})
resumo_metas = resumo_metas.merge(metas, on="vendedor", how="left")

# Calcula atingimento e comissão
resumo_metas["atingimento_%"] = (resumo_metas["total_vendido"] / resumo_metas["meta_semestre"] * 100).round(1)
resumo_metas["situacao"] = resumo_metas["atingimento_%"].apply(situacao)
resumo_metas["comissao"] = resumo_metas["total_vendido"].apply(comissao)

st.dataframe(resumo_metas, use_container_width=True, hide_index=True)

# --- TABELA DE DETALHAMENTO ---
st.subheader("Detalhamento das vendas")
colunas_exibidas = ["data", "id_venda", "vendedor", "regiao", "produto", "quantidade", "preco_unitario", "valor"]
st.dataframe(
    df_filtrado[colunas_exibidas].sort_values("data"),
    use_container_width=True,
    hide_index=True
)