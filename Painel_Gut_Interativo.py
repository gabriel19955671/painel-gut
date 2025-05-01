
import streamlit as st
import pandas as pd
from fpdf import FPDF
import os
import plotly.graph_objects as go

st.set_page_config(page_title="Diagnóstico 360º", layout="wide")

# Variáveis simuladas
data_diagnostico = st.sidebar.date_input("Data da apresentação")
nome_cliente = st.sidebar.text_input("Nome do cliente", value="Empresa Exemplo")
instrucoes_finais = "Seguir plano de ação conforme prioridades GUT."

# Cabeçalho com logo fixa e data
col1, col2, col3 = st.columns([1, 5, 1])
with col1:
    st.markdown(f"<p style='font-size:16px;'>📅 {data_diagnostico.strftime('%d/%m/%Y')}</p>", unsafe_allow_html=True)
with col2:
    st.markdown("<h1 style='text-align: center;'>Diagnóstico 360º</h1>", unsafe_allow_html=True)
with col3:
    st.image("logo_PR_FIXA.png", width=160)

# Simular figuras (normalmente geradas por plotly)
fig_radar = go.Figure()
fig_radar.add_trace(go.Bar(x=["Área A", "Área B"], y=[3, 5]))
fig_gut = go.Figure()
fig_gut.add_trace(go.Scatter(x=[1, 2], y=[3, 4], mode='lines'))
fig_top10 = go.Figure()
fig_top10.add_trace(go.Bar(x=["Problema 1", "Problema 2"], y=[8, 6]))
fig_linha = go.Figure()
fig_linha.add_trace(go.Scatter(x=["Jan", "Fev"], y=[3, 4]))

# Simular plano de ação
df_plano = pd.DataFrame({
    "Ação": ["Revisar processos", "Treinar equipe"],
    "Responsável": ["Ana", "Carlos"],
    "Prazo": ["15 dias", "30 dias"]
})

# Exportar PDF
if st.button("Exportar Diagnóstico"):
    fig_radar.write_image("radar_temp.png")
    fig_gut.write_image("gut_temp.png")
    fig_top10.write_image("top10_temp.png")
    fig_linha.write_image("linha_temp.png")

    pdf = FPDF()
    sections = [
        ("Diagnóstico 360º", "Capa", None),
        ("Gráfico Radar", "radar_temp.png"),
        ("Matriz GUT", "gut_temp.png"),
        ("Plano de Ação", None),
        ("Instruções Finais", None),
        ("Top 10 Problemas", "top10_temp.png"),
        ("Evolução por Área", "linha_temp.png")
    ]

    for i, (title, content) in enumerate(sections):
        pdf.add_page()
        if os.path.exists("logo_PR_FIXA.png"):
            pdf.image("logo_PR_FIXA.png", x=140, y=8, w=60)

        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, title, ln=True)
        pdf.set_font("Arial", '', 12)

        if content == "Capa":
            pdf.cell(0, 10, f"Cliente: {nome_cliente}", ln=True)
            pdf.cell(0, 10, f"Data do Diagnóstico: {data_diagnostico.strftime('%d/%m/%Y')}", ln=True)
        elif content and os.path.exists(content):
            pdf.image(content, x=10, y=30, w=190)
        elif title == "Plano de Ação":
            for _, row in df_plano.iterrows():
                pdf.multi_cell(0, 10, f"- {row['Ação']} | Resp: {row['Responsável']} | Prazo: {row['Prazo']}")
        elif title == "Instruções Finais":
            pdf.multi_cell(0, 10, instrucoes_finais)

    pdf.output("diagnostico_completo.pdf")
    with open("diagnostico_completo.pdf", "rb") as f:
        st.download_button("📥 Baixar PDF", f, file_name="diagnostico_completo.pdf", mime="application/pdf")
