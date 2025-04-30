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

# [ABAS 1 a 3 já existentes permanecem inalteradas]

# ABA 4 - Exportar PDF
with aba4:
    st.subheader("Exportar Diagnóstico 360º em PDF")
    opcoes_exportacao = st.selectbox("Escolha o conteúdo para exportar:", [
        "PDF Completo", "Gráfico Radar", "Matriz GUT", "Plano de Ação", "Instruções Finais"])
    buf_radar = BytesIO()
    fig_radar.write_image(buf_radar, format='png')

    if st.button("Gerar PDF"):
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)

        if opcoes_exportacao in ["PDF Completo", "Gráfico Radar"]:
            with open("radar_temp.png", "wb") as f:
                f.write(buf_radar.getbuffer())
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, "Gráfico Radar de Avaliações", ln=True, align="C")
            pdf.image("radar_temp.png", x=10, y=None, w=180)

        if opcoes_exportacao in ["PDF Completo", "Matriz GUT"]:
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, "Matriz GUT - Priorização das Dores", ln=True, align="C")
            pdf.set_font("Arial", '', 10)
            colunas_gut = df_gut.columns.tolist()
            largura_coluna = 190 / len(colunas_gut)
            for coluna in colunas_gut:
                pdf.cell(largura_coluna, 10, coluna, border=1, align="C")
            pdf.ln()
            for _, row in df_gut.iterrows():
                for coluna in colunas_gut:
                    texto = str(row[coluna])
                    pdf.cell(largura_coluna, 10, texto, border=1, align="C")
                pdf.ln()

        if opcoes_exportacao in ["PDF Completo", "Plano de Ação"]:
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, "Plano de Ação - Estratégias de Melhoria", ln=True, align="C")
            pdf.set_font("Arial", '', 10)
            colunas_plano = df_plano.columns.tolist()
            largura_coluna = 190 / len(colunas_plano)
            for coluna in colunas_plano:
                pdf.cell(largura_coluna, 10, coluna, border=1, align="C")
            pdf.ln()
            for _, row in df_plano.iterrows():
                for coluna in colunas_plano:
                    texto = str(row[coluna])
                    pdf.cell(largura_coluna, 10, texto, border=1, align="C")
                pdf.ln()

        if opcoes_exportacao in ["PDF Completo", "Instruções Finais"]:
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, "Instruções Pós-Diagnóstico", ln=True, align="C")
            pdf.set_font("Arial", '', 12)
            if instrucoes_finais:
                for linha in instrucoes_finais.split("\n"):
                    pdf.multi_cell(0, 10, linha)
            else:
                pdf.multi_cell(0, 10, "Nenhuma instrução preenchida.")

        pdf.output("Diagnostico_360_Selecionado.pdf")
        st.success(f"PDF de {opcoes_exportacao} gerado com sucesso!")
        with open("Diagnostico_360_Selecionado.pdf", "rb") as f:
            st.download_button('📥 Baixar PDF', f, file_name="Diagnostico_360_Selecionado.pdf", mime="application/pdf")

# ABA 5 - Instruções Finais
with aba5:
    st.subheader("🧾 Instruções Pós-Diagnóstico")
    instrucoes = st.text_area("Digite aqui as instruções finais para o cliente:", height=300)
    imagem_instrucao = st.file_uploader("Opcional: Anexar imagem para as instruções", type=["png", "jpg", "jpeg"])
    if imagem_instrucao:
        with open("instrucao_img_temp.png", "wb") as f:
            f.write(imagem_instrucao.read())
        st.image("instrucao_img_temp.png", width=400)
    st.session_state['instrucoes_digitadas'] = instrucoes

# ABA 6 - Gráficos Especiais
with aba6:
    st.subheader("✨ Gráficos Especiais")
    st.markdown("#### 🔝 Top 10 Problemas por Score GUT")
    top10 = df_gut.sort_values(by='Score', ascending=False).head(10)
    fig_top10 = go.Figure(go.Bar(
        x=top10['Score'],
        y=top10['Problema'],
        orientation='h',
        marker_color='crimson'
    ))
    fig_top10.update_layout(height=500, margin=dict(l=120, r=20, t=40, b=40))
    st.plotly_chart(fig_top10, use_container_width=True)

    st.markdown("#### 📈 Evolução Média das Avaliações por Área")
    media_por_area = df_radar.groupby(['Área', 'Departamento'])['Avaliação'].mean().reset_index()
    fig_linha = go.Figure()
    for dep in media_por_area['Departamento'].unique():
        df_dep = media_por_area[media_por_area['Departamento'] == dep]
        fig_linha.add_trace(go.Scatter(x=df_dep['Área'], y=df_dep['Avaliação'], mode='lines+markers', name=dep))
    fig_linha.update_layout(height=500, xaxis_title='Área', yaxis_title='Avaliação Média')
    st.plotly_chart(fig_linha, use_container_width=True)
