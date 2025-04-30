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

# CARREGAMENTO DE DADOS COM TRATAMENTO DE ERROS
@st.cache_data
def carregar_unificado():
    try:
        arquivo = pd.ExcelFile('dados_unificado.xlsx', engine='openpyxl')
        df_radar = pd.read_excel(arquivo, sheet_name='Radar')
        df_gut = pd.read_excel(arquivo, sheet_name='Matriz GUT')
        df_plano = pd.read_excel(arquivo, sheet_name='Plano de Ação')

        if 'Score' not in df_gut.columns:
            df_gut['Score'] = df_gut['Gravidade'] * df_gut['Urgência'] * df_gut['Tendência']

        return df_gut, df_radar, df_plano
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        st.stop()

# CARREGAR DADOS
df_gut, df_radar, df_plano = carregar_unificado()

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

# PDF GERAL
if st.button("📄 Gerar PDF Completo com Gráfico Extra"):
    fig_radar = go.Figure()
    df_agrupado = df_radar.groupby('Área')['Avaliação'].mean().reset_index()
    df_full = pd.DataFrame({'Área': df_radar['Área'].unique()})
    df_full = df_full.merge(df_agrupado, on='Área', how='left').fillna(0)
    fig_radar.add_trace(go.Scatterpolar(
        r=df_full['Avaliação'],
        theta=df_full['Área'],
        mode='lines+markers+text',
        fill='toself',
        marker=dict(size=8, color='green'),
        line=dict(color='green', width=3),
        text=df_agrupado['Avaliação'].round(1).astype(str),
        textposition="top center",
        textfont=dict(size=16, color='black')
    ))
    fig_radar.update_layout(
        polar=dict(bgcolor="lavender", radialaxis=dict(visible=True, range=[0,10])),
        title=dict(text="Radar de Avaliação", font=dict(size=20)),
        height=600
    )
    fig_radar.write_image("radar_temp.png", format="png")

    fig_gut = go.Figure(data=[go.Scatter(
        x=df_gut['Urgência'],
        y=df_gut['Gravidade'],
        mode='markers+text',
        text=df_gut['Problema'],
        textposition="top center",
        marker=dict(size=df_gut['Tendência'] * 5, color=df_gut['Score'], colorscale='Reds', showscale=True)
    )])
    fig_gut.update_layout(
        title="Visualização Matriz GUT",
        xaxis_title="Urgência",
        yaxis_title="Gravidade",
        height=500
    )
    fig_gut.write_image("gut_temp.png", format="png")

    pdf = FPDF()
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

    pdf.output("Diagnostico_Completo.pdf")
    with open("Diagnostico_Completo.pdf", "rb") as f:
        st.download_button('📥 Baixar PDF Completo', f, file_name="Diagnostico_Completo.pdf", mime="application/pdf")
