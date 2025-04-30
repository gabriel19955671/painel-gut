# IMPORTAÇÕES
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO
from fpdf import FPDF
import os

# LOGIN
def login():
    st.markdown("<h2 style='text-align: center;'>🔒 Acesso ao Diagnóstico 360º</h2>", unsafe_allow_html=True)
    user = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if user.lower() == "diagnostico" and password == "Eleve@123":
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    login()
    st.stop()

# CONFIGURAÇÃO DE PÁGINA
st.set_page_config(page_title="Diagnóstico 360º - Potencialize Resultados", layout="wide")

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

# CAMPO DE INSTRUÇÕES
with st.expander("🧾 Instruções Pós-Diagnóstico", expanded=True):
    instrucoes = st.text_area("Digite as instruções finais para o cliente (expansível):", height=300)
    imagem_instrucao = st.file_uploader("📷 Anexar imagem complementar (opcional):", type=["png", "jpg", "jpeg"])
    if imagem_instrucao:
        with open("instrucao_img_temp.png", "wb") as f:
            f.write(imagem_instrucao.read())
        st.image("instrucao_img_temp.png", width=400)
    st.session_state['instrucoes_digitadas'] = instrucoes

# GRÁFICO ADICIONAL - Top 10 Dores por Score GUT
with st.expander("📊 Top 10 Dores com Maior Score GUT"):
    top_dores = df_gut.sort_values(by='Score', ascending=False).head(10)
    fig_top_dores = go.Figure(data=go.Bar(
        x=top_dores['Score'],
        y=top_dores['Problema'],
        orientation='h',
        marker_color='crimson'
    ))
    fig_top_dores.update_layout(
        title="Top 10 Dores Priorizadas (Score GUT)",
        xaxis_title="Score",
        yaxis_title="Problema",
        height=500,
        margin=dict(l=150, r=40, t=40, b=40)
    )
    st.plotly_chart(fig_top_dores, use_container_width=True)
    fig_top_dores.write_image("top_dores.png", format="png")

# BOTÕES DE EXPORTAÇÃO POR PARTE
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("📄 PDF: Apenas Radar"):
        fig_radar = go.Figure()
        df_agrupado = df_radar.groupby('Área')['Avaliação'].mean().reset_index()
        df_full = pd.DataFrame({'Área': df_radar['Área'].unique()})
        df_full = df_full.merge(df_agrupado, on='Área', how='left').fillna(0)
        fig_radar.add_trace(go.Scatterpolar(
            r=df_full['Avaliação'],
            theta=df_full['Área'],
            mode='lines+markers+text',
            fill='toself'
        ))
        fig_radar.write_image("radar_temp.png")
        pdf = FPDF()
        pdf.add_page()
        pdf.image("radar_temp.png", x=10, w=190)
        pdf.output("Radar_Separado.pdf")
        with open("Radar_Separado.pdf", "rb") as f:
            st.download_button("📥 Baixar Radar", f, file_name="Radar_Separado.pdf")

with col2:
    if st.button("📄 PDF: Apenas GUT"):
        fig_gut = go.Figure(data=[go.Scatter(
            x=df_gut['Urgência'],
            y=df_gut['Gravidade'],
            mode='markers+text',
            text=df_gut['Problema'],
            marker=dict(size=df_gut['Tendência']*5, color=df_gut['Score'], colorscale='Reds')
        )])
        fig_gut.write_image("gut_temp.png")
        pdf = FPDF()
        pdf.add_page()
        pdf.image("gut_temp.png", x=10, w=190)
        pdf.output("GUT_Separado.pdf")
        with open("GUT_Separado.pdf", "rb") as f:
            st.download_button("📥 Baixar GUT", f, file_name="GUT_Separado.pdf")

with col3:
    if st.button("📄 PDF: Apenas Instruções"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", '', 12)
        pdf.multi_cell(0, 10, instrucoes or "Nenhuma instrução preenchida.")
        if os.path.exists("instrucao_img_temp.png"):
            pdf.image("instrucao_img_temp.png", x=30, w=150)
        pdf.output("Instrucoes_Separado.pdf")
        with open("Instrucoes_Separado.pdf", "rb") as f:
            st.download_button("📥 Baixar Instruções", f, file_name="Instrucoes_Separado.pdf")

# BOTÃO PDF COMPLETO
if st.button("📄 Gerar PDF Completo com Tudo"):
    fig_radar = go.Figure()
    df_agrupado = df_radar.groupby('Área')['Avaliação'].mean().reset_index()
    df_full = pd.DataFrame({'Área': df_radar['Área'].unique()})
    df_full = df_full.merge(df_agrupado, on='Área', how='left').fillna(0)
    fig_radar.add_trace(go.Scatterpolar(
        r=df_full['Avaliação'],
        theta=df_full['Área'],
        mode='lines+markers+text',
        fill='toself'
    ))
    fig_radar.write_image("radar_temp.png")

    fig_gut = go.Figure(data=[go.Scatter(
        x=df_gut['Urgência'],
        y=df_gut['Gravidade'],
        mode='markers+text',
        text=df_gut['Problema'],
        marker=dict(size=df_gut['Tendência']*5, color=df_gut['Score'], colorscale='Reds')
    )])
    fig_gut.write_image("gut_temp.png")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Gráfico Radar de Avaliações", ln=True, align="C")
    pdf.image("radar_temp.png", x=10, w=190)

    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Matriz GUT - Priorização das Dores", ln=True, align="C")
    pdf.image("gut_temp.png", x=10, w=190)

    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Top 10 Dores por Score GUT", ln=True, align="C")
    pdf.image("top_dores.png", x=10, w=190)

    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Instruções Pós-Diagnóstico", ln=True, align="C")
    pdf.set_font("Arial", '', 12)
    for linha in instrucoes.split('\n'):
        pdf.multi_cell(0, 10, linha)
    if os.path.exists("instrucao_img_temp.png"):
        pdf.image("instrucao_img_temp.png", x=30, w=150)

    pdf.output("Diagnostico_Completo.pdf")
    with open("Diagnostico_Completo.pdf", "rb") as f:
        st.download_button('📥 Baixar PDF Completo', f, file_name="Diagnostico_Completo.pdf", mime="application/pdf")
