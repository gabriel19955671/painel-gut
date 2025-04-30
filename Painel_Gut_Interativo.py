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

# FILTROS GERAIS
st.sidebar.markdown("---")
st.sidebar.subheader("Filtros Globais")
data_col = st.sidebar.date_input("Filtrar por Período", [])
colaboradores = st.sidebar.multiselect("Filtrar por Colaborador", options=sorted(df_radar['Departamento'].unique()))

if data_col and 'Data' in df_radar.columns:
    df_radar = df_radar[df_radar['Data'].between(pd.to_datetime(data_col[0]), pd.to_datetime(data_col[1]))]

if colaboradores:
    df_radar = df_radar[df_radar['Departamento'].isin(colaboradores)]
    if 'Responsável' in df_plano.columns:
        df_plano = df_plano[df_plano['Responsável'].isin(colaboradores)]

# CRIAÇÃO DAS ABAS
aba1, aba2, aba3, aba4, aba5, aba6 = st.tabs([
    "📊 Gráfico Radar", 
    "🗂️ Matriz GUT", 
    "📝 Plano de Ação", 
    "📥 Exportar PDF", 
    "🧾 Instruções",
    "✨ Gráficos Especiais"])

# ABA 1 - Gráfico Radar
with aba1:
    st.subheader("Radar de Avaliação por Área e Departamento")
    fig_radar = go.Figure()
    df_agrupado = df_radar.groupby('Área')['Avaliação'].mean().reset_index()
    fig_radar.add_trace(go.Scatterpolar(
        r=df_agrupado['Avaliação'],
        theta=df_agrupado['Área'],
        fill='toself',
        name='Avaliação Média'
    ))
    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 10])), showlegend=False)
    st.plotly_chart(fig_radar, use_container_width=True)

    st.markdown("#### 📋 Tabela de Avaliações por Área")
    st.dataframe(df_agrupado, use_container_width=True)

# ABA 2 - Matriz GUT
with aba2:
    st.subheader("Matriz GUT")
    fig_gut = go.Figure(data=[go.Scatter(
        x=df_gut['Urgência'],
        y=df_gut['Gravidade'],
        mode='markers+text',
        text=df_gut['Problema'],
        textposition="top center",
        marker=dict(size=df_gut['Tendência'] * 5, color=df_gut['Score'], colorscale='Reds', showscale=True)
    )])
    fig_gut.update_layout(title="Visualização Matriz GUT", xaxis_title="Urgência", yaxis_title="Gravidade")
    st.plotly_chart(fig_gut, use_container_width=True)

    st.markdown("#### 📋 Tabela da Matriz GUT")
    st.dataframe(df_gut, use_container_width=True)

# ABA 3 - Plano de Ação
with aba3:
    st.subheader("Plano de Ação")
    st.dataframe(df_plano, use_container_width=True)

# ABA 4 - Exportar PDF
with aba4:
    st.subheader("Exportar Diagnóstico em PDF")
    if st.button("📄 Gerar PDF Completo"):
        fig_radar.write_image("radar_temp.png")
        fig_gut.write_image("gut_temp.png")

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)

        # CAPA
        pdf.add_page()
        if os.path.exists("cliente_logo_temp.png"):
            pdf.image("cliente_logo_temp.png", x=150, y=8, w=50)
        pdf.set_font("Arial", 'B', 20)
        pdf.ln(60)
        pdf.cell(0, 15, "Diagnóstico 360º - Potencialize Resultados", ln=True, align="C")
        if nome_cliente:
            pdf.set_font("Arial", '', 14)
            pdf.ln(10)
            pdf.cell(0, 10, f"Cliente: {nome_cliente}", ln=True, align="C")
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 10, f"Data: {data_diagnostico}", ln=True, align="C")

        # Radar
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Radar de Avaliação", ln=True, align="C")
        pdf.image("radar_temp.png", x=10, w=180)

        # GUT
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Matriz GUT", ln=True, align="C")
        pdf.image("gut_temp.png", x=10, w=180)

        # Instruções
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Instruções Pós-Diagnóstico", ln=True, align="C")
        pdf.set_font("Arial", '', 12)
        if st.session_state.get('instrucoes_digitadas'):
            for linha in st.session_state['instrucoes_digitadas'].split('
'):
                pdf.multi_cell(0, 10, linha)
        else:
            pdf.multi_cell(0, 10, "Nenhuma instrução preenchida.")

        # Rodapé
        pdf.set_y(-15)
        pdf.set_font("Arial", 'I', 10)
        rodape = "Potencialize Resultados - Diagnóstico 360º"
        if nome_cliente:
            rodape += f" | Cliente: {nome_cliente}"
        pdf.cell(0, 10, rodape, 0, 0, 'C')

        pdf.output("diagnostico_360.pdf")
        with open("diagnostico_360.pdf", "rb") as f:
            st.download_button("📥 Baixar PDF", f, file_name="diagnostico_360.pdf", mime="application/pdf")

# ABA 5 - Instruções
with aba5:
    st.subheader("Instruções Pós-Diagnóstico")
    instrucoes = st.text_area("Digite as instruções finais para o cliente:", height=300)
    st.session_state['instrucoes_digitadas'] = instrucoes

# ABA 6 - Gráficos Especiais
with aba6:
    st.subheader("Gráficos Especiais")

    st.markdown("#### 🔝 Top 10 Problemas por Score GUT")
    top10 = df_gut.sort_values(by='Score', ascending=False).head(10)
    fig_top10 = go.Figure(go.Bar(
        x=top10['Score'],
        y=top10['Problema'],
        orientation='h',
        marker_color='crimson'
    ))
    st.plotly_chart(fig_top10, use_container_width=True)

    st.markdown("#### 📊 Avaliação Média por Área e Departamento")
    media_area_dep = df_radar.groupby(['Departamento', 'Área'])['Avaliação'].mean().reset_index()
    fig_bar = go.Figure()
    for dep in media_area_dep['Departamento'].unique():
        df_dep = media_area_dep[media_area_dep['Departamento'] == dep]
        fig_bar.add_trace(go.Bar(x=df_dep['Área'], y=df_dep['Avaliação'], name=dep))
    fig_bar.update_layout(barmode='group', xaxis_title='Área', yaxis_title='Avaliação Média')
    st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("#### 📈 Distribuição de Avaliações por Faixa")
    bins = [0, 2, 4, 6, 8, 10]
    labels = ['0-2', '2-4', '4-6', '6-8', '8-10']
    df_radar['Faixa'] = pd.cut(df_radar['Avaliação'], bins=bins, labels=labels, include_lowest=True)
    faixa_counts = df_radar['Faixa'].value_counts().sort_index()
    fig_faixa = go.Figure([go.Bar(x=faixa_counts.index.astype(str), y=faixa_counts.values)])
    st.plotly_chart(fig_faixa, use_container_width=True)

    st.markdown("#### 🧑‍💼 Ações por Responsável")
    if 'Responsável' in df_plano.columns:
        responsaveis = df_plano['Responsável'].value_counts().reset_index()
        responsaveis.columns = ['Responsável', 'Quantidade']
        fig_resp = go.Figure([go.Bar(x=responsaveis['Responsável'], y=responsaveis['Quantidade'])])
        st.plotly_chart(fig_resp, use_container_width=True)

    st.markdown("#### 🔺 Dispersão por Área")
    fig_dispersao = go.Figure()
    for area in df_radar['Área'].unique():
        df_area = df_radar[df_radar['Área'] == area]
        fig_dispersao.add_trace(go.Box(y=df_area['Avaliação'], name=area))
    st.plotly_chart(fig_dispersao, use_container_width=True)
