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
    arquivo = pd.ExcelFile('dados_unificado.xlsx')
    df_radar = pd.read_excel(arquivo, sheet_name='Radar')
    df_gut = pd.read_excel(arquivo, sheet_name='Matriz GUT')
    df_plano = pd.read_excel(arquivo, sheet_name='Plano de Ação')
    return df_gut, df_radar, df_plano

df_gut, df_radar, df_plano = carregar_unificado()

# SIDEBAR
st.sidebar.title("Configurações")
if st.sidebar.button("🔄 Recarregar Dados", key="recarregar_dados"):
    st.session_state.recarregar = True

if st.session_state.get("recarregar", False):
    st.success("✅ Dados atualizados com sucesso!")
    st.cache_data.clear()
    st.session_state.recarregar = False
    st.rerun()
data_diagnostico = st.sidebar.date_input("Data de Apresentação do Diagnóstico")
nome_cliente = st.sidebar.text_input("Nome do Cliente")
uploaded_logo = st.sidebar.file_uploader("Anexar Logomarca do Cliente", type=["png", "jpg", "jpeg"])

if uploaded_logo:
    with open("cliente_logo_temp.png", "wb") as f:
        f.write(uploaded_logo.read())

# CABEÇALHO
col_logo, col_titulo, col_logo_cliente = st.columns([1, 5, 1])
with col_logo:
    st.image('logo PR (3) (2).png', width=250)
with col_titulo:
    st.markdown("<h1 style='text-align: center;'>Diagnóstico 360º - Potencialize Resultados</h1>", unsafe_allow_html=True)
    if nome_cliente:
        st.markdown(f"<h3 style='text-align: center; color: #555555;'>{nome_cliente}</h3>", unsafe_allow_html=True)
with col_logo_cliente:
    if os.path.exists("cliente_logo_temp.png"):
        st.image('cliente_logo_temp.png', width=150)
    else:
        st.empty()

# CRIAÇÃO DAS ABAS
aba1, aba2, aba3, aba4, aba5 = st.tabs(["📊 Gráfico Radar", "🗂️ Matriz GUT", "📝 Plano de Ação", "📥 Exportar PDF", "🧾 Instruções"])

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
            radialaxis=dict(visible=True, range=[0,10]),
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

    if 'Score' not in df_gut.columns:
        df_gut['Score'] = df_gut['Gravidade'] * df_gut['Urgência'] * df_gut['Tendência']

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

# ABA 5 - Instruções
with aba5:
    st.subheader("🧾 Instruções Pós-Diagnóstico")
    instrucoes = st.text_area("Digite aqui as instruções finais para o cliente:", height=300)
    st.session_state['instrucoes_digitadas'] = instrucoes

# ABA 4 - Exportar PDF
with aba4:
    st.subheader("Exportar Diagnóstico 360º em PDF")
    buf_radar = BytesIO()
    fig_radar.write_image(buf_radar, format='png')

    if st.button("Gerar PDF Completo"):
        with open("radar_temp.png", "wb") as f:
            f.write(buf_radar.getbuffer())

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)

        # CAPA
        pdf.add_page()
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

        # Gráfico Radar
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Gráfico Radar de Avaliações", ln=True, align="C")
        pdf.image("radar_temp.png", x=10, y=None, w=180)

        # Matriz GUT
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

        # Plano de Ação
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

        # Instruções
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Instruções Pós-Diagnóstico", ln=True, align="C")
        pdf.set_font("Arial", '', 12)
        if st.session_state.get('instrucoes_digitadas'):
            for linha in st.session_state['instrucoes_digitadas'].split('\n'):
                pdf.multi_cell(0, 10, linha)
        else:
            pdf.multi_cell(0, 10, "Nenhuma instrução preenchida.")

        # Rodapé final
        pdf.set_y(-15)
        pdf.set_font("Arial", 'I', 10)
        rodape = "Potencialize Resultados - Diagnóstico 360º"
        if nome_cliente:
            rodape += f" | Cliente: {nome_cliente}"
        pdf.cell(0, 10, rodape, 0, 0, 'C')

        pdf.output("Diagnostico_360_Completo.pdf")
        st.success("PDF completo gerado com sucesso!")
        with open("Diagnostico_360_Completo.pdf", "rb") as f:
            st.download_button('📥 Baixar PDF Completo', f, file_name="Diagnostico_360_Completo.pdf", mime="application/pdf")

        os.remove("radar_temp.png")
