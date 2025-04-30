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

# CABEÇALHO
st.markdown("""
    <div style='margin-top: 120px;'></div>
    <hr style='margin-bottom: 10px;'>
""", unsafe_allow_html=True)
col_logo, col_titulo, col_logo_cliente = st.columns([1, 5, 1])
with col_logo:
    if os.path.exists("logo PR (3) (2).png"):
        st.image("logo PR (3) (2).png", width=250)
    else:
        st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)

with col_titulo:
    st.markdown("<h1 style='text-align: center;'>Diagnóstico 360º - Potencialize Resultados</h1>", unsafe_allow_html=True)
    if nome_cliente:
        st.markdown(f"<h3 style='text-align: center; color: #555555;'>Cliente: {nome_cliente}</h3>", unsafe_allow_html=True)

with col_logo_cliente:
    if os.path.exists("cliente_logo_temp.png"):
        st.image("cliente_logo_temp.png", width=150)
    else:
        st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)

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
    st.subheader("Gráfico Radar por Departamento, Área e Avaliação")
    col1, col2, col3 = st.columns([3, 3, 4])
    with col1:
        departamentos = sorted(df_radar['Departamento'].unique())
        depto_selecionado = st.multiselect("Departamento(s)", departamentos, default=departamentos)
    with col2:
        areas = sorted(df_radar['Área'].unique())
        area_selecionada = st.multiselect("Área(s)", areas, default=areas)
    with col3:
        avaliacao_min, avaliacao_max = st.slider("Intervalo de Avaliação", 0.0, 10.0, (0.0, 10.0), step=0.1)

    df_plot = df_radar[
        (df_radar['Departamento'].isin(depto_selecionado)) &
        (df_radar['Área'].isin(area_selecionada)) &
        (df_radar['Avaliação'] >= avaliacao_min) &
        (df_radar['Avaliação'] <= avaliacao_max)
    ]

    fig_radar = go.Figure()
    if not df_plot.empty:
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
            radialaxis=dict(visible=True, range=[0, 10]),
            angularaxis=dict(tickfont=dict(size=14))
        ),
        title=dict(text="Radar de Avaliação", font=dict(size=20)),
        margin=dict(l=20, r=20, t=40, b=20),
        height=600
    )
    st.plotly_chart(fig_radar, use_container_width=True)
    st.subheader("Tabela de Pontuações Filtradas")
    st.dataframe(df_plot[['Departamento', 'Área', 'Avaliação']], use_container_width=True)

# ABA 2 - Matriz GUT
with aba2:
    st.subheader("Matriz GUT - Priorização das Dores")
    st.dataframe(df_gut, use_container_width=True)

    fig_gut = go.Figure(data=[go.Scatter(
        x=df_gut['Urgência'],
        y=df_gut['Gravidade'],
        mode='markers+text',
        text=df_gut['Problema'],
        textposition="top center",
        marker=dict(size=df_gut['Tendência']*5, color=df_gut['Score'], colorscale='Reds', showscale=True)
    )])

    fig_gut.update_layout(
        title="Visualização Matriz GUT",
        xaxis_title="Urgência",
        yaxis_title="Gravidade",
        margin=dict(l=40, r=40, t=60, b=40),
        height=500
    )
    st.plotly_chart(fig_gut, use_container_width=True)

# ABA 3 - Plano de Ação
with aba3:
    st.subheader("Plano de Ação - Estratégias de Melhoria")
    st.dataframe(df_plano, use_container_width=True)

    if 'Prazo' in df_plano.columns:
        prazo_counts = df_plano['Prazo'].value_counts().reset_index()
        prazo_counts.columns = ['Prazo', 'Quantidade']

        st.markdown("### 🥧 Distribuição das Ações por Prazo")
        fig_pizza = go.Figure(data=[go.Pie(labels=prazo_counts['Prazo'], values=prazo_counts['Quantidade'], hole=0.4)])
        st.plotly_chart(fig_pizza, use_container_width=True)

        st.markdown("### 📊 Quantidade de Ações por Prazo para Conclusão")
        fig_barras = go.Figure()
        fig_barras.add_trace(go.Bar(
            x=df_plano['Prazo'],
            y=[1]*len(df_plano),
            text=df_plano['Ação'],
            textposition='outside'
        ))
        st.plotly_chart(fig_barras, use_container_width=True)

# ABA 4 - Exportar PDF
with aba4:
    st.subheader("Exportar Diagnóstico 360º em PDF")
    st.markdown("### Clique abaixo para exportar o relatório completo")

    if st.button("📥 Gerar PDF Completo"):
        buf = BytesIO()
        fig_radar.write_image("radar_temp.png")

        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # CAPA
        if os.path.exists("logo PR (3) (2).png"):
            pdf.image("logo PR (3) (2).png", x=10, y=8, w=50)
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
        pdf.image("radar_temp.png", x=10, y=None, w=180)

        # GUT Table
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Matriz GUT - Priorização das Dores", ln=True, align="C")
        pdf.set_font("Arial", '', 10)
        col_gut = df_gut.columns.tolist()
        for i in col_gut:
            pdf.cell(190/len(col_gut), 10, i, border=1, align="C")
        pdf.ln()
        for _, row in df_gut.iterrows():
            for i in col_gut:
                pdf.cell(190/len(col_gut), 10, str(row[i]), border=1, align="C")
            pdf.ln()

        # Plano de Ação
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Plano de Ação - Estratégias de Melhoria", ln=True, align="C")
        pdf.set_font("Arial", '', 10)
        col_plano = df_plano.columns.tolist()
        for i in col_plano:
            pdf.cell(190/len(col_plano), 10, i, border=1, align="C")
        pdf.ln()
        for _, row in df_plano.iterrows():
            for i in col_plano:
                pdf.cell(190/len(col_plano), 10, str(row[i]), border=1, align="C")
            pdf.ln()

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

        if os.path.exists("instrucao_img_temp.png"):
            pdf.image("instrucao_img_temp.png", x=30, w=150)

        # Gráficos Especiais
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Gráficos Especiais - Top 10 Problemas GUT", ln=True, align="C")
        fig_top10.write_image("fig_top10.png")
        pdf.image("fig_top10.png", x=10, w=190)

        pdf.add_page()
        pdf.cell(0, 10, "Avaliação Média por Área e Departamento", ln=True, align="C")
        fig_bar.write_image("fig_bar.png")
        pdf.image("fig_bar.png", x=10, w=190)

        pdf.add_page()
        pdf.cell(0, 10, "Distribuição de Avaliações por Faixa", ln=True, align="C")
        fig_faixa.write_image("fig_faixa.png")
        pdf.image("fig_faixa.png", x=10, w=190)

        if 'Responsável' in df_plano.columns:
            pdf.add_page()
            pdf.cell(0, 10, "Ações por Responsável", ln=True, align="C")
            fig_resp.write_image("fig_resp.png")
            pdf.image("fig_resp.png", x=10, w=190)

        pdf.add_page()
        pdf.cell(0, 10, "Dispersão de Avaliações por Área", ln=True, align="C")
        fig_dispersao.write_image("fig_dispersao.png")
        pdf.image("fig_dispersao.png", x=10, w=190)

        pdf.output("Diagnostico_360_Completo.pdf")
        st.success("PDF completo gerado com sucesso!")
        with open("Diagnostico_360_Completo.pdf", "rb") as f:
            st.download_button('📥 Baixar PDF Completo', f, file_name="Diagnostico_360_Completo.pdf", mime="application/pdf")


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
        marker_color='crimson',
        text=top10['Score'].round(1),
        textposition='auto'
    ))
    fig_top10.update_layout(height=500, margin=dict(l=100, r=20, t=40, b=40))
    st.plotly_chart(fig_top10, use_container_width=True)

    st.markdown("#### 📊 Avaliação Média por Área e Departamento")
    media_area_dep = df_radar.groupby(['Departamento', 'Área'])['Avaliação'].mean().reset_index()
    fig_bar = go.Figure()
    for dep in media_area_dep['Departamento'].unique():
        df_dep = media_area_dep[media_area_dep['Departamento'] == dep]
        fig_bar.add_trace(go.Bar(x=df_dep['Área'], y=df_dep['Avaliação'], name=dep, text=df_dep['Avaliação'].round(1), textposition='auto'))
    fig_bar.update_layout(barmode='group', xaxis_title='Área', yaxis_title='Avaliação Média', height=500)
    st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("#### 📈 Distribuição de Avaliações por Faixa")
    bins = [0, 2, 4, 6, 8, 10]
    labels = ['0-2', '2-4', '4-6', '6-8', '8-10']
    df_radar['Faixa'] = pd.cut(df_radar['Avaliação'], bins=bins, labels=labels, include_lowest=True)
    faixa_counts = df_radar['Faixa'].value_counts().sort_index()
    fig_faixa = go.Figure([go.Bar(x=faixa_counts.index.astype(str), y=faixa_counts.values, text=faixa_counts.values, textposition='auto')])
    fig_faixa.update_layout(xaxis_title='Faixa de Avaliação', yaxis_title='Quantidade', height=400)
    st.plotly_chart(fig_faixa, use_container_width=True)

    st.markdown("#### 🧑‍💼 Ações por Responsável")
    if 'Responsável' in df_plano.columns:
        responsaveis = df_plano['Responsável'].value_counts().reset_index()
        responsaveis.columns = ['Responsável', 'Quantidade']
        fig_resp = go.Figure([go.Bar(x=responsaveis['Responsável'], y=responsaveis['Quantidade'], text=responsaveis['Quantidade'], textposition='auto')])
        fig_resp.update_layout(xaxis_title='Responsável', yaxis_title='Quantidade de Ações', height=400)
        st.plotly_chart(fig_resp, use_container_width=True)

    st.markdown("#### 🔺 Dispersão por Área")
    fig_dispersao = go.Figure()
    for area in sorted(df_radar['Área'].unique()):
        df_area = df_radar[df_radar['Área'] == area]
        fig_dispersao.add_trace(go.Box(y=df_area['Avaliação'], name=area))
    fig_dispersao.update_layout(yaxis_title='Avaliação', height=500)
    st.plotly_chart(fig_dispersao, use_container_width=True)

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
