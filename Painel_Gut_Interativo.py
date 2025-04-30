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

# INSTRUÇÕES
with st.expander("🧾 Instruções Pós-Diagnóstico", expanded=True):
    instrucoes = st.text_area("Digite as instruções finais para o cliente (expansível):", height=300)
    imagem_instrucao = st.file_uploader("📷 Anexar imagem complementar (opcional):", type=["png", "jpg", "jpeg"])
    if imagem_instrucao:
        with open("instrucao_img_temp.png", "wb") as f:
            f.write(imagem_instrucao.read())
        st.image("instrucao_img_temp.png", width=400)
    st.session_state['instrucoes_digitadas'] = instrucoes

# GRÁFICOS
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
fig_radar.update_layout(polar=dict(bgcolor="lavender", radialaxis=dict(visible=True, range=[0, 10])))
fig_radar.write_image("radar_temp.png")

fig_gut = go.Figure(data=[go.Scatter(
    x=df_gut['Urgência'],
    y=df_gut['Gravidade'],
    mode='markers+text',
    text=df_gut['Problema'],
    marker=dict(size=df_gut['Tendência'] * 5, color=df_gut['Score'], colorscale='Reds', showscale=True)
)])
fig_gut.update_layout(title="Matriz GUT", xaxis_title="Urgência", yaxis_title="Gravidade")
fig_gut.write_image("gut_temp.png")

fig_pizza = go.Figure()
fig_barras = go.Figure()
if 'Prazo' in df_plano.columns:
    prazo_counts = df_plano['Prazo'].value_counts().reset_index()
    prazo_counts.columns = ['Prazo', 'Quantidade']
    fig_pizza = go.Figure(data=[go.Pie(labels=prazo_counts['Prazo'], values=prazo_counts['Quantidade'], hole=0.4)])
    fig_pizza.write_image("pizza_temp.png")
    fig_barras = go.Figure()
    fig_barras.add_trace(go.Bar(x=df_plano['Prazo'], y=[1]*len(df_plano), text=df_plano['Ação'], textposition='outside'))
    fig_barras.write_image("barras_temp.png")

# BOTÃO FINAL PARA GERAR PDF EXPANDIDO
if st.button("📄 Gerar PDF Diagnóstico Completo com Gráficos e Tabelas (Expandido)"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Página 1 - Capa com logomarcas e cliente
    pdf.add_page()
    if os.path.exists("logo PR (3) (2).png"):
        pdf.image("logo PR (3) (2).png", x=10, y=8, w=50)
    if os.path.exists("cliente_logo_temp.png"):
        pdf.image("cliente_logo_temp.png", x=150, y=8, w=50)
    pdf.set_font("Arial", 'B', 20)
    pdf.ln(60)
    pdf.cell(0, 15, "Diagnóstico 360º - Potencialize Resultados", ln=True, align="C")
    pdf.set_font("Arial", '', 14)
    if 'nome_cliente' in st.session_state and st.session_state['nome_cliente']:
        pdf.cell(0, 10, f"Cliente: {st.session_state['nome_cliente']}", ln=True, align="C")
    if 'data_diagnostico' in st.session_state and st.session_state['data_diagnostico']:
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 10, f"Data: {st.session_state['data_diagnostico']}", ln=True, align="C")

    # Página 2 - Radar
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "📊 Radar de Avaliações por Área", ln=True, align="C")
    pdf.image("radar_temp.png", x=10, w=190)

    # Página 3 - Matriz GUT
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "🗂️ Matriz GUT - Priorização de Problemas", ln=True, align="C")
    pdf.image("gut_temp.png", x=10, w=190)

    # Página 4 - Plano de Ação: Pizza
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "🥧 Plano de Ação - Distribuição por Prazo", ln=True, align="C")
    pdf.image("pizza_temp.png", x=10, w=190)

    # Página 5 - Plano de Ação: Barras
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "📊 Quantidade de Ações por Prazo para Conclusão", ln=True, align="C")
    pdf.image("barras_temp.png", x=10, w=190)

    # Página 6 - Plano de Ação: Detalhamento
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "📝 Detalhamento do Plano de Ação", ln=True, align="C")
    pdf.set_font("Arial", '', 9)
    for _, row in df_plano.iterrows():
        linha = f"Ação: {row['Ação']} | Responsável: {row.get('Responsável', '')} | Prazo: {row['Prazo']}"
        pdf.multi_cell(0, 10, linha)

    # Página 7 - Instruções
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "🧾 Instruções Pós-Diagnóstico", ln=True, align="C")
    pdf.set_font("Arial", '', 12)
    for linha in instrucoes.split('\n'):
        pdf.multi_cell(0, 10, linha)
    if os.path.exists("instrucao_img_temp.png"):
        pdf.image("instrucao_img_temp.png", x=30, w=150)

    # Rodapé em todas páginas
    for n in range(1, pdf.page_no() + 1):
        pdf.page = n
        pdf.set_y(-15)
        pdf.set_font("Arial", 'I', 8)
        pdf.cell(0, 10, f"Página {n} | Potencialize Resultados", 0, 0, 'C')

    pdf.output("Diagnostico_360_Completo_Expandido.pdf")
    with open("Diagnostico_360_Completo_Expandido.pdf", "rb") as f:
        st.download_button('📥 Baixar PDF Expandido', f, file_name="Diagnostico_360_Completo_Expandido.pdf", mime="application/pdf")
