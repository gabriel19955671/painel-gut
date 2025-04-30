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
    except FileNotFoundError:
        st.error("❌ Arquivo 'dados_unificado.xlsx' não encontrado.\n\n📅 Por favor, envie o arquivo manualmente na barra lateral.")
        st.stop()
    except ImportError as e:
        st.error(f"❌ Erro de importação: {e}\n\n🔧 Verifique se 'openpyxl' está no requirements.txt.")
        st.stop()
    except Exception as e:
        st.error(f"⚠️ Erro inesperado ao carregar o Excel: {e}")
        st.stop()

# CHAMADA DO CARREGAMENTO
df_gut, df_radar, df_plano = carregar_unificado()

# INSTRUÇÕES
with st.expander("📌 Instruções de Uso do Diagnóstico"):
    st.markdown("""
    Este painel tem como objetivo apresentar graficamente os resultados do diagnóstico 360º. 

    - Envie o arquivo `dados_unificado.xlsx` com as abas `Radar`, `Matriz GUT` e `Plano de Ação`.
    - Visualize os gráficos interativos abaixo.
    - Clique no botão **📄 Gerar PDF Diagnóstico** para exportar os resultados em PDF.
    - O botão **📥 Baixar PDF** aparecerá após a geração ser concluída.
    """)

# GERA A MATRIZ GUT COM MAPA DE CALOR
fig_gut = go.Figure()
if not df_gut.empty:
    fig_gut.add_trace(go.Scatter(
        x=df_gut['Urgência'],
        y=df_gut['Gravidade'],
        mode='markers+text',
        text=df_gut['Problema'],
        textposition="top center",
        marker=dict(
            size=df_gut['Tendência'] * 5,
            color=df_gut['Score'],
            colorscale='Reds',
            showscale=True,
            colorbar=dict(title='Score')
        )
    ))
fig_gut.update_layout(
    title="Visualização Matriz GUT",
    xaxis_title="Urgência",
    yaxis_title="Gravidade",
    margin=dict(l=40, r=40, t=60, b=40),
    height=500
)
st.plotly_chart(fig_gut, use_container_width=True)
fig_gut.write_image("gut_temp.png", format="png")

# PDF GERADO APÓS CLIQUE
if st.button("📄 Gerar PDF Diagnóstico"):
    fig_radar = go.Figure()
    if not df_radar.empty:
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
        polar=dict(
            bgcolor="lavender",
            radialaxis=dict(visible=True, range=[0,10]),
            angularaxis=dict(tickfont=dict(size=14))
        ),
        title=dict(text="Radar de Avaliação", font=dict(size=20)),
        margin=dict(l=20, r=20, t=40, b=20),
        height=600
    )
    fig_radar.write_image("radar_temp.png", format="png")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Gráfico Radar de Avaliações", ln=True, align="C")
    if os.path.exists("radar_temp.png"):
        pdf.image("radar_temp.png", x=10, w=190)

    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Matriz GUT - Priorização das Dores", ln=True, align="C")
    if os.path.exists("gut_temp.png"):
        pdf.image("gut_temp.png", x=10, w=190)

    pdf.output("Diagnostico_360_Resumo.pdf")
    with open("Diagnostico_360_Resumo.pdf", "rb") as f:
        st.download_button('📥 Baixar PDF', f, file_name="Diagnostico_360_Resumo.pdf", mime="application/pdf")
