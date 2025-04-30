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

# CABEÇALHO
col_logo, col_titulo, col_logo_cliente = st.columns([1, 5, 1])
with col_logo:
    if os.path.exists("logo PR (3) (2).png"):
        st.image('logo PR (3) (2).png', width=250)
with col_titulo:
    st.markdown("<h1 style='text-align: center;'>Diagnóstico 360º - Potencialize Resultados</h1>", unsafe_allow_html=True)
    if nome_cliente:
        st.markdown(f"<h3 style='text-align: center; color: #555555;'>{nome_cliente}</h3>", unsafe_allow_html=True)
with col_logo_cliente:
    if os.path.exists("cliente_logo_temp.png"):
        st.image('cliente_logo_temp.png', width=150)

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

# GERAÇÃO ANTECIPADA DO GRÁFICO RADAR PARA USO NO PDF
fig_radar = go.Figure()
df_plot = df_radar.copy()
df_agrupado = df_plot.groupby('Área')['Avaliação'].mean().reset_index()
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
