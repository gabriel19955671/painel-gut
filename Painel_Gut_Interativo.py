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

instrucoes_finais = st.session_state.get("instrucoes_digitadas", "")

# CRIAÇÃO DAS ABAS
aba1, aba2, aba3, aba4, aba5, aba6 = st.tabs([
    "📊 Gráfico Radar",
    "🗂️ Matriz GUT",
    "📝 Plano de Ação",
    "📥 Exportar PDF",
    "🧾 Instruções Finais",
    "✨ Gráficos Especiais"
])

# ABA 4 - Exportar PDF
with aba4:
    st.subheader("Exportar Diagnóstico 360º em PDF")
    opcoes = [
        "PDF Completo",
        "Radar de Avaliação",
        "Matriz GUT",
        "Plano de Ação",
        "Top 10 GUT",
        "Evolução por Área",
        "Instruções Finais"
    ]
    escolha = st.selectbox("Escolha o conteúdo para exportar:", opcoes)

    if st.button("Exportar PDF"):
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, f"{escolha} - Diagnóstico 360º", ln=True, align="C")

        if escolha == "Radar de Avaliação" or escolha == "PDF Completo":
            pdf.add_page()
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, "Radar de Avaliação", ln=True)
            pdf.set_font("Arial", '', 10)
            for index, row in df_radar.iterrows():
                pdf.multi_cell(0, 10, f"Departamento: {row['Departamento']}, Área: {row['Área']}, Avaliação: {row['Avaliação']}")

        if escolha == "Matriz GUT" or escolha == "PDF Completo":
            pdf.add_page()
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, "Matriz GUT", ln=True)
            pdf.set_font("Arial", '', 10)
            for index, row in df_gut.iterrows():
                pdf.multi_cell(0, 10, f"Problema: {row['Problema']}, Gravidade: {row['Gravidade']}, Urgência: {row['Urgência']}, Tendência: {row['Tendência']}, Score: {row['Score']}")

        if escolha == "Plano de Ação" or escolha == "PDF Completo":
            pdf.add_page()
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, "Plano de Ação", ln=True)
            pdf.set_font("Arial", '', 10)
            colunas = df_plano.columns.tolist()
            largura = 190 / len(colunas)
            for col in colunas:
                pdf.cell(largura, 10, col, 1)
            pdf.ln()
            for _, row in df_plano.iterrows():
                for col in colunas:
                    pdf.cell(largura, 10, str(row[col]), 1)
                pdf.ln()

        if escolha == "Top 10 GUT" or escolha == "PDF Completo":
            top10 = df_gut.sort_values(by='Score', ascending=False).head(10)
            pdf.add_page()
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, "Top 10 Problemas GUT", ln=True)
            for index, row in top10.iterrows():
                pdf.multi_cell(0, 10, f"Problema: {row['Problema']} - Score: {row['Score']}")

        if escolha == "Evolução por Área" or escolha == "PDF Completo":
            media_por_area = df_radar.groupby(['Área', 'Departamento'])['Avaliação'].mean().reset_index()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, "Evolução Média das Avaliações por Área", ln=True)
            for index, row in media_por_area.iterrows():
                pdf.multi_cell(0, 10, f"Departamento: {row['Departamento']} - Área: {row['Área']} - Avaliação: {row['Avaliação']:.2f}")

        if escolha == "Instruções Finais" or escolha == "PDF Completo":
            pdf.add_page()
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, "Instruções Finais", ln=True)
            pdf.set_font("Arial", '', 10)
            if instrucoes_finais:
                for linha in instrucoes_finais.split('\n'):
                    pdf.multi_cell(0, 10, linha)
            else:
                pdf.multi_cell(0, 10, "Nenhuma instrução preenchida.")

        pdf.output("Diagnostico_Exportado.pdf")
        with open("Diagnostico_Exportado.pdf", "rb") as f:
            st.download_button("📥 Baixar PDF Exportado", f, file_name="Diagnostico_Exportado.pdf", mime="application/pdf")
