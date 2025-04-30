# IMPORTAÇÕES
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO
from fpdf import FPDF
import os

st.set_page_config(page_title="Diagnóstico 360º - Potencialize Resultados", layout="wide")

# SIDEBAR
st.sidebar.title("Configurações")
data_diagnostico = st.sidebar.date_input("Data de Apresentação do Diagnóstico")
st.session_state['data_diagnostico'] = data_diagnostico
nome_cliente = st.sidebar.text_input("Nome do Cliente")
st.session_state['nome_cliente'] = nome_cliente
uploaded_logo = st.sidebar.file_uploader("Anexar Logomarca do Cliente", type=["png", "jpg", "jpeg"])

if uploaded_logo:
    with open("cliente_logo_temp.png", "wb") as f:
        f.write(uploaded_logo.read())

# CARREGAMENTO DE DADOS
@st.cache_data
def carregar_unificado():
    arquivo = pd.ExcelFile('dados_unificado.xlsx', engine='openpyxl')
    df_radar = pd.read_excel(arquivo, sheet_name='Radar')
    df_gut = pd.read_excel(arquivo, sheet_name='Matriz GUT')
    df_plano = pd.read_excel(arquivo, sheet_name='Plano de Ação')
    if 'Score' not in df_gut.columns:
        df_gut['Score'] = df_gut['Gravidade'] * df_gut['Urgência'] * df_gut['Tendência']
    return df_gut, df_radar, df_plano

df_gut, df_radar, df_plano = carregar_unificado()

# FILTROS GERAIS
st.sidebar.markdown("---")
st.sidebar.subheader("Filtros Globais")
data_col = st.sidebar.date_input("Filtrar por Período", [])
colaboradores = st.sidebar.multiselect("Filtrar por Colaborador", options=sorted(df_radar['Departamento'].unique()))

if data_col and 'Data' in df_radar.columns:
    df_radar = df_radar[df_radar['Data'].between(pd.to_datetime(data_col[0]), pd.to_datetime(data_col[1]))]

if colaboradores:
    df_radar = df_radar[df_radar['Departamento'].isin(colaboradores)]
    if 'Responsável' in df_plano.columns:
        df_plano = df_plano[df_plano['Responsável'].isin(colaboradores)]

# CABEÇALHO
col_logo, col_titulo, col_logo_cliente = st.columns([1, 5, 1])
with col_logo:
    if os.path.exists("logo PR (3) (2).png"):
        st.image("logo PR (3) (2).png", width=250)
    else:
        st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)

with col_titulo:
    st.markdown("<h1 style='text-align: center;'>Diagnóstico 360º - Potencialize Resultados</h1>", unsafe_allow_html=True)
    nome_cliente_exibir = st.session_state.get('nome_cliente')
    if nome_cliente_exibir:
        st.markdown(f"<h3 style='text-align: center; color: #555555;'>Cliente: {nome_cliente_exibir}</h3>", unsafe_allow_html=True)

with col_logo_cliente:
    if os.path.exists("cliente_logo_temp.png"):
        st.image("cliente_logo_temp.png", width=150)
    else:
        st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)

# CRIAÇÃO DAS ABAS
aba1, aba2, aba3, aba4, aba5, aba6 = st.tabs([
    "📊 Gráfico Radar", 
    "🗂️ Matriz GUT", 
    "📝 Plano de Ação", 
    "📥 Exportar PDF", 
    "🧾 Instruções",
    "✨ Gráficos Especiais"])

# (as abas de 1 a 5 continuam como estão no código anterior)

# ABA 6 - Gráficos Especiais
with aba6:
    st.subheader("✨ Gráficos Especiais")

    st.markdown("#### 🔝 Top 10 Problemas por Score GUT")
    top10 = df_gut.sort_values(by='Score', ascending=False).head(10)
    fig_top10 = go.Figure(go.Bar(
        x=top10['Score'],
        y=top10['Problema'],
        orientation='h',
        marker_color='crimson'
    ))
    st.plotly_chart(fig_top10, use_container_width=True)

    st.markdown("#### 📊 Avaliação Média por Área e Departamento")
    media_area_dep = df_radar.groupby(['Departamento', 'Área'])['Avaliação'].mean().reset_index()
    fig_bar = go.Figure()
    for dep in media_area_dep['Departamento'].unique():
        df_dep = media_area_dep[media_area_dep['Departamento'] == dep]
        fig_bar.add_trace(go.Bar(x=df_dep['Área'], y=df_dep['Avaliação'], name=dep))
    fig_bar.update_layout(barmode='group', xaxis_title='Área', yaxis_title='Avaliação Média')
    st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("#### 📈 Distribuição de Avaliações por Faixa")
    bins = [0, 2, 4, 6, 8, 10]
    labels = ['0-2', '2-4', '4-6', '6-8', '8-10']
    df_radar['Faixa'] = pd.cut(df_radar['Avaliação'], bins=bins, labels=labels, include_lowest=True)
    faixa_counts = df_radar['Faixa'].value_counts().sort_index()
    fig_faixa = go.Figure([go.Bar(x=faixa_counts.index.astype(str), y=faixa_counts.values)])
    st.plotly_chart(fig_faixa, use_container_width=True)

    st.markdown("#### 🧑‍💼 Ações por Responsável")
    if 'Responsável' in df_plano.columns:
        responsaveis = df_plano['Responsável'].value_counts().reset_index()
        responsaveis.columns = ['Responsável', 'Quantidade']
        fig_resp = go.Figure([go.Bar(x=responsaveis['Responsável'], y=responsaveis['Quantidade'])])
        st.plotly_chart(fig_resp, use_container_width=True)

    st.markdown("#### 🔺 Dispersão por Área")
    fig_dispersao = go.Figure()
    for area in df_radar['Área'].unique():
        df_area = df_radar[df_radar['Área'] == area]
        fig_dispersao.add_trace(go.Box(y=df_area['Avaliação'], name=area))
    st.plotly_chart(fig_dispersao, use_container_width=True)
