import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO
from fpdf import FPDF
import os
from PIL import Image

st.set_page_config(page_title="Diagnóstico 360º - Potencialize Resultados", layout="wide")

# TOPO COM LOGOMARCA FIXA
col_logo_esquerdo, col_restante = st.columns([1, 6])
with col_logo_esquerdo:
    if os.path.exists("logo_PR_FIXA.png"):
        logo_img = Image.open("logo_PR_FIXA.png")
        st.image(logo_img, width=240)  # AUMENTADO PARA MAIOR DESTAQUE
    else:
        st.warning("Logomarca não encontrada.")

# SIDEBAR
data_diagnostico = st.sidebar.date_input("Data de Apresentação do Diagnóstico")
st.session_state['data_diagnostico'] = data_diagnostico
nome_cliente = st.sidebar.text_input("Nome do Cliente")
st.session_state['nome_cliente'] = nome_cliente
uploaded_logo = st.sidebar.file_uploader("Anexar Logomarca do Cliente", type=["png", "jpg", "jpeg"])

if uploaded_logo:
    with open("logo_cliente_temp.png", "wb") as f:
        f.write(uploaded_logo.read())

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

aba1, aba2, aba3, aba4, aba5, aba6 = st.tabs([
    "📊 Gráfico Radar",
    "🗂️ Matriz GUT",
    "📝 Plano de Ação",
    "📥 Exportar PDF",
    "🧾 Instruções Finais",
    "✨ Gráficos Especiais"
])

# ... (restante do código permanece igual até o bloco de exportação de PDF)

        for titulo, imagem in secoes:
            pdf.add_page()
            if imagem == "Capa":
                if os.path.exists("logo_PR_FIXA.png"):
                    pdf.image("logo_PR_FIXA.png", x=10, y=8, w=70)  # LOGO MAIOR NA CAPA
                pdf.ln(40)
                pdf.set_font("Arial", "B", 20)
                pdf.cell(0, 20, "Diagnóstico 360º", ln=True, align="C")
                pdf.ln(10)
                pdf.set_font("Arial", "", 14)
                pdf.cell(0, 10, f"Cliente: {nome_cliente}", ln=True, align="C")
                pdf.cell(0, 10, f"Data do Diagnóstico: {data_diagnostico.strftime('%d/%m/%Y')}", ln=True, align="C")
                continue

            # Cabeçalho para todas as outras páginas
            if os.path.exists("logo_PR_FIXA.png"):
                pdf.image("logo_PR_FIXA.png", x=10, y=8, w=50)
            pdf.set_font("Arial", "B", 14)
            pdf.set_y(15)
            pdf.cell(0, 10, "Diagnóstico 360º - Potencialize Resultados", ln=True, align="C")
            pdf.ln(10)
            pdf.set_font("Arial", "", 12)

            if imagem and os.path.exists(imagem):
                pdf.image(imagem, x=10, y=30, w=190)
            elif titulo == "Plano de Ação":
                for _, row in df_plano.iterrows():
                    pdf.multi_cell(0, 10, f"- {row['Ação']} | Resp: {row['Responsável']} | Prazo: {row['Prazo']}")
            elif titulo == "Instruções Finais":
                pdf.multi_cell(0, 10, instrucoes_finais)

        pdf.output("diagnostico_360_exportado.pdf")
        with open("diagnostico_360_exportado.pdf", "rb") as f:
            st.download_button("📥 Baixar PDF", f, file_name="diagnostico_360_exportado.pdf", mime="application/pdf")
