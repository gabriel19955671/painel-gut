import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from io import BytesIO
from fpdf import FPDF

# Estilizar página
st.set_page_config(page_title="Diagnóstico 360º - Potencialize Resultados", layout="wide")
st.markdown("""
    <style>
        body {
            background-color: #ffffff;
        }
        .css-18e3th9 {
            background-color: #ffffff;
        }
        h1 {
            font-family: 'Arial', sans-serif;
            color: #333333;
        }
        footer {
            visibility: hidden;
        }
        .custom-footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: #f97316;
            color: white;
            text-align: center;
            padding: 10px 0;
            font-size: 14px;
            font-family: Arial, sans-serif;
        }
        .stButton>button {
            border-radius: 8px;
            background-color: #3b82f6;
            color: white;
            height: 3em;
            width: 100%;
            font-size: 16px;
        }
    </style>
""", unsafe_allow_html=True)

# Carregar dados
def carregar_gut():
    return pd.read_excel('dados_prioridade.xlsx')

def carregar_radar():
    return pd.read_excel('dados_radar.xlsx')

def carregar_plano_acao():
    return pd.read_excel('dados_plano_acao.xlsx')

df_gut = carregar_gut()
df_radar = carregar_radar()
df_plano = carregar_plano_acao()

# Título e Logomarca
col_logo, col_titulo, _ = st.columns([1, 5, 1])
with col_logo:
    st.image('logo PR (3) (2).png', width=200)
with col_titulo:
    st.markdown("<h1 style='text-align: center;'>Diagnóstico 360º - Painel Interativo</h1>", unsafe_allow_html=True)

# Tabs para organização
aba1, aba2, aba3, aba4 = st.tabs(["📊 Gráfico Radar", "🗂️ Matriz GUT", "📝 Plano de Ação", "📥 Exportar PDF"])

with aba1:
    st.header("Gráfico Radar por Departamento")
    departamentos = ['Todos'] + sorted(df_radar['Departamento'].unique())
    depto_selecionado = st.selectbox("Selecione o Departamento", departamentos)

    if depto_selecionado != 'Todos':
        df_plot = df_radar[df_radar['Departamento'] == depto_selecionado]
    else:
        df_plot = df_radar

    fig_radar = px.line_polar(
        df_plot,
        r='Avaliação',
        theta='Área',
        color='Departamento',
        line_close=True,
        color_discrete_sequence=['#f97316', '#facc15', '#10b981', '#3b82f6', '#8b5cf6']
    )
    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0,10])))

    st.plotly_chart(fig_radar, use_container_width=True)

    buf_radar = BytesIO()
    fig_radar.write_image(buf_radar, format='png')

with aba2:
    st.header("Tabela de Dados com Filtros - Matriz GUT")
    with st.sidebar:
        st.header("Filtros GUT")
        gravidade_selecionada = st.multiselect("Gravidade", options=df_gut["Gravidade"].unique(), default=df_gut["Gravidade"].unique())
        urgencia_selecionada = st.multiselect("Urgência", options=df_gut["Urgência"].unique(), default=df_gut["Urgência"].unique())
        tendencia_selecionada = st.multiselect("Tendência", options=df_gut["Tendência"].unique(), default=df_gut["Tendência"].unique())

    df_gut_filtrado = df_gut[
        (df_gut["Gravidade"].isin(gravidade_selecionada)) &
        (df_gut["Urgência"].isin(urgencia_selecionada)) &
        (df_gut["Tendência"].isin(tendencia_selecionada))
    ]

    st.dataframe(df_gut_filtrado.sort_values(by="Prioridade Final", ascending=True), use_container_width=True)

with aba3:
    st.header("Plano de Ação por Período")
    st.dataframe(df_plano, use_container_width=True)

with aba4:
    st.header("Exportar Diagnóstico em PDF")

    if st.button("📄 Gerar PDF do Diagnóstico"):
        pdf = FPDF()
        pdf.add_page()
        pdf.image('logo PR (3) (2).png', x=80, w=50)
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Diagnóstico 360º", ln=True, align='C')
        pdf.ln(10)

        # Inserir Gráfico Radar
        buf_radar.seek(0)
        with open("radar_temp.png", "wb") as f:
            f.write(buf_radar.getbuffer())
        pdf.image("radar_temp.png", x=30, w=150)
        pdf.ln(10)

        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, "Resumo Matriz GUT", ln=True)
        for prob in df_gut['Problema'].head(5):
            pdf.cell(0, 10, f"- {prob}", ln=True)
        pdf.ln(5)

        pdf.cell(0, 10, "Resumo Plano de Ação", ln=True)
        for dep in df_plano['Departamento'].unique():
            pdf.cell(0, 10, f"- {dep}", ln=True)

        output = BytesIO()
        pdf.output(output)
        st.download_button(
            label="📥 Baixar PDF Completo",
            data=output.getvalue(),
            file_name="diagnostico_360_completo.pdf",
            mime="application/pdf"
        )

# Rodapé personalizado
st.markdown("""
<div class='custom-footer'>
    Desenvolvido por Potencialize Resultados © 2025
</div>
""", unsafe_allow_html=True)
