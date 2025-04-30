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

# CRIAÇÃO DAS ABAS
aba1, aba2, aba3, aba4, aba5, aba6 = st.tabs([
    "📊 Gráfico Radar", 
    "🗂️ Matriz GUT", 
    "📝 Plano de Ação", 
    "📥 Exportar PDF", 
    "🧾 Instruções",
    "✨ Gráficos Especiais"])

# ABA 1 - Gráfico Radar
with aba1:
    st.subheader("Radar de Avaliação por Área e Departamento")
    fig_radar = go.Figure()
    df_agrupado = df_radar.groupby('Área')['Avaliação'].mean().reset_index()
    fig_radar.add_trace(go.Scatterpolar(
        r=df_agrupado['Avaliação'],
        theta=df_agrupado['Área'],
        fill='toself',
        name='Avaliação Média'
    ))
    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 10])), showlegend=False)
    st.plotly_chart(fig_radar, use_container_width=True)

    st.markdown("#### 📋 Tabela de Avaliações por Área")
    st.dataframe(df_agrupado, use_container_width=True)

# ABA 2 - Matriz GUT
with aba2:
    st.subheader("Matriz GUT")
    fig_gut = go.Figure(data=[go.Scatter(
        x=df_gut['Urgência'],
        y=df_gut['Gravidade'],
        mode='markers+text',
        text=df_gut['Problema'],
        textposition="top center",
        marker=dict(size=df_gut['Tendência'] * 5, color=df_gut['Score'], colorscale='Reds', showscale=True)
    )])
    fig_gut.update_layout(title="Visualização Matriz GUT", xaxis_title="Urgência", yaxis_title="Gravidade")
    st.plotly_chart(fig_gut, use_container_width=True)

    st.markdown("#### 📋 Tabela da Matriz GUT")
    st.dataframe(df_gut, use_container_width=True)

# ABA 3 - Plano de Ação
with aba3:
    st.subheader("Plano de Ação")
    st.dataframe(df_plano, use_container_width=True)

# ABA 4 - Exportar PDF
with aba4:
    st.subheader("Exportar Diagnóstico em PDF")
    if st.button("📄 Gerar PDF Completo"):
        fig_radar.write_image("radar_temp.png")
        fig_gut.write_image("gut_temp.png")

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)

        # CAPA
        pdf.add_page()
        if os.path.exists("cliente_logo_temp.png"):
            pdf.image("cliente_logo_temp.png", x=150, y=8, w=50)
        pdf.set_font("Arial", 'B', 20)
        pdf.ln(60)
        pdf.cell(0, 15, "Diagnóstico 360º - Potencialize Resultados", ln=True, align="C")
        if nome_cliente:
            pdf.set_font("Arial", '', 14)
            pdf.ln(10)
            pdf.cell(0, 10, f"Cliente: {nome_cliente}", ln=True, align="C")
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 10, f"Data: {data_diagnostico}", ln=True, align="C")

        # Radar
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Radar de Avaliação", ln=True, align="C")
        pdf.image("radar_temp.png", x=10, w=180)

        # GUT
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Matriz GUT", ln=True, align="C")
        pdf.image("gut_temp.png", x=10, w=180)

        # Instruções
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Instruções Pós-Diagnóstico", ln=True, align="C")
        pdf.set_font("Arial", '', 12)
        if st.session_state.get('instrucoes_digitadas'):
            for linha in st.session_state['instrucoes_digitadas'].split('
'):
