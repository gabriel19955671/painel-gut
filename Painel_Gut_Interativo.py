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

aba1, aba2, aba3, aba4, aba5, aba6 = st.tabs([
    "📊 Gráfico Radar",
    "🗂️ Matriz GUT",
    "📝 Plano de Ação",
    "📥 Exportar PDF",
    "🧾 Instruções Finais",
    "✨ Gráficos Especiais"
])

with aba1:
    st.subheader("Gráfico Radar por Departamento, Área e Avaliação")
    st.plotly_chart(fig_radar, use_container_width=True)
    st.dataframe(df_plot[['Departamento', 'Área', 'Avaliação']], use_container_width=True)

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

with aba4:
    st.subheader("Exportar Diagnóstico 360º")
    st.markdown("Selecione o conteúdo que deseja exportar:")
    opcoes_exportacao = st.selectbox("Escolha", ["PDF Completo", "Gráfico Radar", "Matriz GUT", "Plano de Ação", "Instruções Finais", "Gráficos Especiais"])

    if st.button("📥 Gerar PDF"):
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
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

        if opcoes_exportacao in ["PDF Completo", "Gráfico Radar"]:
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, "Gráfico Radar de Avaliações", ln=True, align="C")
            buf_radar = BytesIO()
            fig_radar.write_image(buf_radar, format='png')
            with open("radar_temp.png", "wb") as f:
                f.write(buf_radar.getbuffer())
            pdf.image("radar_temp.png", x=10, w=180)

        if opcoes_exportacao in ["PDF Completo", "Matriz GUT"]:
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, "Matriz GUT - Priorização das Dores", ln=True, align="C")
            pdf.set_font("Arial", '', 10)
            colunas = df_gut.columns.tolist()
            largura = 190 / len(colunas)
            for coluna in colunas:
                pdf.cell(largura, 10, coluna[:15], border=1, align="C")
            pdf.ln()
            for _, row in df_gut.iterrows():
                for coluna in colunas:
                    pdf.cell(largura, 10, str(row[coluna])[:15], border=1, align="C")
                pdf.ln()

        if opcoes_exportacao in ["PDF Completo", "Plano de Ação"]:
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, "Plano de Ação - Estratégias de Melhoria", ln=True, align="C")
            pdf.set_font("Arial", '', 10)
            colunas = df_plano.columns.tolist()
            largura = 190 / len(colunas)
            for coluna in colunas:
                pdf.cell(largura, 10, coluna[:15], border=1, align="C")
            pdf.ln()
            for _, row in df_plano.iterrows():
                for coluna in colunas:
                    pdf.cell(largura, 10, str(row[coluna])[:15], border=1, align="C")
                pdf.ln()

        if opcoes_exportacao in ["PDF Completo", "Instruções Finais"]:
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, "Instruções Pós-Diagnóstico", ln=True, align="C")
            pdf.set_font("Arial", '', 12)
            if instrucoes_finais:
                for linha in instrucoes_finais.split('\n'):
                    pdf.multi_cell(0, 10, linha)
            else:
                pdf.multi_cell(0, 10, "Nenhuma instrução preenchida.")
            if os.path.exists("instrucao_img_temp.png"):
                pdf.ln(10)
                pdf.image("instrucao_img_temp.png", x=30, w=150)

        if opcoes_exportacao in ["PDF Completo", "Gráficos Especiais"]:
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, "Top 10 Problemas por Score GUT", ln=True, align="C")
            top10 = df_gut.sort_values(by='Score', ascending=False).head(10)
            for idx, row in top10.iterrows():
                pdf.set_font("Arial", '', 12)
                pdf.multi_cell(0, 10, f"{row['Problema']} - Score: {row['Score']}")

        pdf.output("Diagnostico_360_Exportado.pdf")
        with open("Diagnostico_360_Exportado.pdf", "rb") as f:
            st.download_button("📥 Baixar PDF", f, file_name="Diagnostico_360_Exportado.pdf", mime="application/pdf")

with aba5:
    st.subheader("🧾 Instruções Pós-Diagnóstico")
    instrucoes = st.text_area("Digite aqui as instruções finais para o cliente:", height=300)
    imagem_instrucao = st.file_uploader("Opcional: Anexar imagem para as instruções", type=["png", "jpg", "jpeg"])
    if imagem_instrucao:
        with open("instrucao_img_temp.png", "wb") as f:
            f.write(imagem_instrucao.read())
        st.image("instrucao_img_temp.png", width=400)
    st.session_state['instrucoes_digitadas'] = instrucoes

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
