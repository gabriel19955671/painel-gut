import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO
from fpdf import FPDF
import os
from PIL import Image

st.set_page_config(page_title="Diagnóstico 360º - Potencialize Resultados", layout="wide")

# SIDEBAR (deve vir antes do cabeçalho)
data_diagnostico = st.sidebar.date_input("Data de Apresentação do Diagnóstico")
st.session_state['data_diagnostico'] = data_diagnostico
nome_cliente = st.sidebar.text_input("Nome do Cliente")
st.session_state['nome_cliente'] = nome_cliente
uploaded_logo = st.sidebar.file_uploader("Anexar Logomarca do Cliente", type=["png", "jpg", "jpeg"])

if uploaded_logo:
    with open("logo_cliente_temp.png", "wb") as f:
        f.write(uploaded_logo.read())

# TOPO COM LOGOMARCA FIXA
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    if os.path.exists("logo_PR_FIXA.png"):
        logo_img = Image.open("logo_PR_FIXA.png")
        st.image(logo_img, width=300)

with col2:
    nome_cliente = st.session_state.get('nome_cliente', '')
    data_diagnostico = st.session_state.get('data_diagnostico', None)
    data_formatada = data_diagnostico.strftime('%d/%m/%Y') if data_diagnostico else ''

    st.markdown(f"""
        <div style='text-align: center; padding-top: 15px; padding-bottom: 5px;'>
            <h1 style='font-size: 32px; margin-bottom: 5px;'>Diagnóstico Potencialize 360º</h1>
            <h3 style='margin-top: 0; font-size: 20px; color: #333;'>{nome_cliente}</h3>
            <h4 style='margin-top: 0; font-size: 16px; color: #666;'>{data_formatada}</h4>
        </div>
    """, unsafe_allow_html=True)

with col3:
    if os.path.exists("logo_cliente_temp.png"):
        logo_cliente = Image.open("logo_cliente_temp.png")
        st.image(logo_cliente, width=220)

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
instrucoes_finais = st.session_state.get("instrucoes_digitadas", "")

# Dados globais para exportação
top10 = df_gut.sort_values(by='Score', ascending=False).head(10)
media_por_area = df_radar.groupby(['Área', 'Departamento'])['Avaliação'].mean().reset_index()

# TABS DO APLICATIVO
aba1, aba2, aba3, aba4, aba5, aba6 = st.tabs([
    "📊 Gráfico Radar",
    "💂️ Matriz GUT",
    "📝 Plano de Ação",
    "📅 Exportar PDF",
    "📟 Instruções Finais",
    "✨ Gráficos Especiais"
])

with aba4:
    st.subheader("📅 Exportar Diagnóstico 360º em PDF")
    from fpdf import FPDF
    import plotly.io as pio

    opcao = st.selectbox("Escolha o conteúdo para exportar:", ["PDF Completo", "Gráfico Radar", "Matriz GUT", "Plano de Ação", "Instruções Finais", "Gráficos Especiais"])

    if st.button("Gerar PDF"):
        # Gerar imagens dos gráficos
        fig_radar = go.Figure()
        fig_radar.write_image("radar_temp.png")

        fig_gut = go.Figure()
        fig_gut.write_image("gut_temp.png")

        fig_top10 = go.Figure()
        fig_top10.write_image("top10_temp.png")

        fig_linha = go.Figure()
        fig_linha.write_image("linha_temp.png")

        # Criar PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Diagnóstico 360º - Potencialize Resultados", ln=True, align="C")
        pdf.cell(200, 10, txt=f"Cliente: {nome_cliente} | Data: {data_formatada}", ln=True, align="C")
        pdf.ln(10)

        if opcao == "PDF Completo" or opcao == "Gráfico Radar":
            pdf.cell(200, 10, txt="Gráfico Radar", ln=True, align="L")
            if os.path.exists("radar_temp.png"):
                pdf.image("radar_temp.png", x=10, y=pdf.get_y(), w=180)
                pdf.ln(65)

        if opcao == "PDF Completo" or opcao == "Matriz GUT":
            pdf.cell(200, 10, txt="Matriz GUT", ln=True, align="L")
            if os.path.exists("gut_temp.png"):
                pdf.image("gut_temp.png", x=10, y=pdf.get_y(), w=180)
                pdf.ln(65)

        if opcao == "PDF Completo" or opcao == "Plano de Ação":
            pdf.cell(200, 10, txt="Plano de Ação", ln=True, align="L")
            for _, row in df_plano.iterrows():
                pdf.multi_cell(0, 10, f"- {row['Ação']} | Resp: {row['Responsável']} | Prazo: {row['Prazo']}")

        if opcao == "PDF Completo" or opcao == "Instruções Finais":
            pdf.cell(200, 10, txt="Instruções Finais", ln=True, align="L")
            pdf.multi_cell(0, 10, instrucoes_finais)

        if opcao == "PDF Completo" or opcao == "Gráficos Especiais":
            pdf.cell(200, 10, txt="Top 10 Problemas por Score GUT", ln=True, align="L")
            if os.path.exists("top10_temp.png"):
                pdf.image("top10_temp.png", x=10, y=pdf.get_y(), w=180)
                pdf.ln(65)

            pdf.cell(200, 10, txt="Evolução Média das Avaliações por Área", ln=True, align="L")
            if os.path.exists("linha_temp.png"):
                pdf.image("linha_temp.png", x=10, y=pdf.get_y(), w=180)

        pdf.output("diagnostico_360_exportado.pdf")
        with open("diagnostico_360_exportado.pdf", "rb") as f:
            st.download_button("📥 Baixar PDF", f, file_name="diagnostico_360_exportado.pdf", mime="application/pdf")
