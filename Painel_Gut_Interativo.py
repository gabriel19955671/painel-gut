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
st.markdown("""
    <div style='margin-top: 120px;'></div>
    <hr style='margin-bottom: 10px;'>
""", unsafe_allow_html=True)
col_logo, col_titulo, col_logo_cliente = st.columns([1, 5, 1])
with col_logo:
    if os.path.exists("logo PR (3) (2).png"):
        st.image("logo PR (3) (2).png", width=250)
    else:
        st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)

with col_titulo:
    st.markdown("<h1 style='text-align: center;'>Diagnóstico 360º - Potencialize Resultados</h1>", unsafe_allow_html=True)
    if nome_cliente:
        st.markdown(f"<h3 style='text-align: center; color: #555555;'>Cliente: {nome_cliente}</h3>", unsafe_allow_html=True)

with col_logo_cliente:
    if os.path.exists("cliente_logo_temp.png"):
        st.image("cliente_logo_temp.png", width=150)
    else:
        st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)

# INSTRUÇÕES
st.subheader("🧾 Instruções Pós-Diagnóstico")
instrucoes = st.text_area("Digite aqui as instruções finais para o cliente:", height=300)
imagem_instrucao = st.file_uploader("Opcional: Anexar imagem para as instruções", type=["png", "jpg", "jpeg"])
if imagem_instrucao:
    with open("instrucao_img_temp.png", "wb") as f:
        f.write(imagem_instrucao.read())
    st.image("instrucao_img_temp.png", width=400)
st.session_state['instrucoes_digitadas'] = instrucoes
