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

if st.sidebar.button("Remover Logomarca do Cliente"):
    if os.path.exists("cliente_logo_temp.png"):
        os.remove("cliente_logo_temp.png")
        st.sidebar.success("Logomarca removida com sucesso.")

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

# CRIAÇÃO DAS ABAS
aba1, aba2, aba3, aba4, aba5, aba6 = st.tabs(["📊 Gráfico Radar", "🗂️ Matriz GUT", "📝 Plano de Ação", "📥 Exportar PDF", "🧾 Instruções", "✨ Gráficos Especiais"])

# ... [ABAS 1 a 3 e 5 a 6 continuam iguais]

# ABA 4 - Exportar PDF
with aba4:
    st.subheader("Exportar Diagnóstico 360º em PDF")
    if st.button("Gerar PDF do Plano de Ação"):
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Plano de Ação - Estratégias de Melhoria", ln=True, align="C")
        pdf.set_font("Arial", '', 10)
        colunas_plano = df_plano.columns.tolist()
        largura_coluna = 190 / len(colunas_plano)
        for coluna in colunas_plano:
            pdf.cell(largura_coluna, 10, coluna, border=1, align="C")
        pdf.ln()
        for _, row in df_plano.iterrows():
            for coluna in colunas_plano:
                texto = str(row[coluna])
                pdf.cell(largura_coluna, 10, texto, border=1, align="C")
            pdf.ln()
        pdf.output("Plano_de_Acao.pdf")
        with open("Plano_de_Acao.pdf", "rb") as f:
            st.download_button("📥 Baixar PDF do Plano de Ação", f, file_name="Plano_de_Acao.pdf", mime="application/pdf")
