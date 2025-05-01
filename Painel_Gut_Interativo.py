import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO
from fpdf import FPDF
import os
from PIL import Image

st.set_page_config(page_title="Diagnóstico 360º - Potencialize Resultados", layout="wide")

# CAPTURA DOS DADOS PARA USO NO TOPO

# TOPO COM LOGOMARCA FIXA
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    if os.path.exists("logo_PR_FIXA.png"):
        logo_img = Image.open("logo_PR_FIXA.png")
        st.image(logo_img, width=300)
with col2:
    if 'nome_cliente' in st.session_state and st.session_state['nome_cliente']:
        nome_cliente = st.session_state['nome_cliente']
    else:
        nome_cliente = ""

    st.markdown(f"""
        <div style='text-align: center; padding-top: 15px; padding-bottom: 5px;'>
            <h1 style='font-size: 32px; margin-bottom: 5px;'>Diagnóstico Potencialize 360º</h1>
            <h3 style='margin-top: 0; font-size: 20px; color: #333;'>{nome_cliente}</h3>
<h4 style='margin-top: 0; font-size: 16px; color: #666;'>{st.session_state['data_diagnostico'].strftime('%d/%m/%Y')}</h4>
        </div>
    """, unsafe_allow_html=True)
with col3:
    if os.path.exists("logo_cliente_temp.png"):
        logo_cliente = Image.open("logo_cliente_temp.png")
        st.image(logo_cliente, width=220)

# SIDEBAR
data_diagnostico = st.sidebar.date_input("Data de Apresentação do Diagnóstico")
st.session_state['data_diagnostico'] = data_diagnostico
nome_cliente = st.sidebar.text_input("Nome do Cliente")
st.session_state['nome_cliente'] = nome_cliente
uploaded_logo = st.sidebar.file_uploader("Anexar Logomarca do Cliente", type=["png", "jpg", "jpeg"])

if uploaded_logo:
    with open("logo_cliente_temp.png", "wb") as f:
        f.write(uploaded_logo.read())

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

aba1, aba2, aba3, aba4, aba5, aba6 = st.tabs([
    "📊 Gráfico Radar",
    "💂️ Matriz GUT",
    "📝 Plano de Ação",
    "📅 Exportar PDF",
    "🧾 Instruções Finais",
    "✨ Gráficos Especiais"
])

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

    # Calcula df_plot globalmente para uso no PDF
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

with aba2:
    st.subheader("Matriz GUT - Priorização das Dores")
    score_min, score_max = st.slider("Filtro por Score GUT", 0, int(df_gut['Score'].max()), (0, int(df_gut['Score'].max())))
    df_gut_filtrado = df_gut[(df_gut['Score'] >= score_min) & (df_gut['Score'] <= score_max)]
    st.dataframe(df_gut_filtrado, use_container_width=True)

    fig_gut = go.Figure(data=[go.Scatter(
        x=df_gut_filtrado['Urgência'],
        y=df_gut_filtrado['Gravidade'],
        mode='markers+text',
        text=df_gut_filtrado['Problema'],
        textposition="top center",
        marker=dict(size=df_gut_filtrado['Tendência']*5, color=df_gut_filtrado['Score'], colorscale='Reds', showscale=True)
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
    col1, col2 = st.columns(2)
    with col1:
        prazos = df_plano['Prazo'].unique()
        filtro_prazo = st.multiselect("Filtrar por Prazo", options=prazos, default=prazos)
    with col2:
        if 'Responsável' in df_plano.columns:
            responsaveis = df_plano['Responsável'].dropna().unique()
            filtro_resp = st.multiselect("Filtrar por Responsável", options=responsaveis, default=responsaveis)
            df_filtrado = df_plano[
                (df_plano['Prazo'].isin(filtro_prazo)) &
                (df_plano['Responsável'].isin(filtro_resp))
            ]
    st.dataframe(df_filtrado, use_container_width=True)

with aba5:
    st.subheader("🧾 Instruções Pós-Diagnóstico")
    instrucoes = st.text_area("Digite aqui as instruções finais para o cliente:", height=300)
    imagem_instrucao = st.file_uploader("Opcional: Anexar imagem para as instruções", type=["png", "jpg", "jpeg"])
    if imagem_instrucao:
        with open("img_instrucao_temp.png", "wb") as f:
            f.write(imagem_instrucao.read())
    st.session_state['instrucoes_digitadas'] = instrucoes

with aba6:
    st.subheader("✨ Gráficos Especiais")
    st.markdown("#### 🔝 Top 10 Problemas por Score GUT")
    top10 = df_gut.sort_values(by='Score', ascending=False).head(10)
    fig_top10 = go.Figure(go.Bar(x=top10['Score'], y=top10['Problema'], orientation='h', marker_color='crimson'))
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

with aba4:
    st.subheader("Exportar Diagnóstico 360º em PDF")
    opcoes_exportacao = st.selectbox("Escolha o conteúdo para exportar:", [
        "PDF Completo", "Gráfico Radar", "Matriz GUT", "Plano de Ação", "Instruções Finais", "Gráficos Especiais"])
    if st.button("Gerar PDF"):
        fig_radar.write_image("radar_temp.png")
        fig_gut.write_image("gut_temp.png")
        fig_top10.write_image("top10_temp.png")
        fig_linha.write_image("linha_temp.png")
        pdf = FPDF()
        secoes = [("Diagnóstico 360º", "Capa")]
        if opcoes_exportacao == "PDF Completo":
            secoes += [
                ("Gráfico Radar", "radar_temp.png"),
                ("Matriz GUT", "gut_temp.png"),
                ("Plano de Ação", None),
                ("Instruções Finais", None),
                ("Top 10 Problemas", "top10_temp.png"),
                ("Evolução por Área", "linha_temp.png")
            ]
        else:
            secoes = [(opcoes_exportacao, None)]

        for titulo, imagem in secoes:
            pdf.add_page()
            if imagem == "Capa":
                if os.path.exists("logo_PR_FIXA.png"):
                    pdf.image("logo_PR_FIXA.png", x=10, y=8, w=70)
                if os.path.exists("logo_cliente_temp.png"):
                    pdf.image("logo_cliente_temp.png", x=150, y=8, w=50)
                pdf.ln(40)
                pdf.set_font("Arial", "B", 20)
                pdf.cell(0, 20, "Diagnóstico 360º", ln=True, align="C")
                pdf.ln(10)
                pdf.set_font("Arial", "", 14)
                pdf.cell(0, 10, f"Cliente: {nome_cliente}", ln=True, align="C")
                pdf.cell(0, 10, f"Data do Diagnóstico: {data_diagnostico.strftime('%d/%m/%Y')}", ln=True, align="C")
                continue

            if os.path.exists("logo_PR_FIXA.png"):
                pdf.image("logo_PR_FIXA.png", x=10, y=8, w=50)
            pdf.set_font("Arial", "B", 16)
            pdf.set_y(10)
            pdf.cell(0, 10, "Diagnóstico 360º - Potencialize Resultados", ln=True, align="C")
            pdf.set_font("Arial", "", 10)
            pdf.cell(0, 10, f"Cliente: {nome_cliente} | Data: {data_diagnostico.strftime('%d/%m/%Y')}", ln=True, align="C")
            pdf.ln(10)
            pdf.set_font("Arial", "", 12)

            if imagem and os.path.exists(imagem):
                pdf.image(imagem, x=10, y=30, w=190)
            elif titulo == "Plano de Ação":
                for _, row in df_plano.iterrows():
                    pdf.multi_cell(0, 10, f"- {row['Ação']} | Resp: {row['Responsável']} | Prazo: {row['Prazo']}")
                pdf.ln(5)
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 10, "Tabela Completa:", ln=True)
                pdf.set_font("Arial", "", 10)
                for col in df_plano.columns:
                    pdf.cell(40, 10, col, border=1)
                pdf.ln()
                for _, row in df_plano.iterrows():
                    for col in df_plano.columns:
                        valor = str(row[col])[:35]
                        pdf.cell(40, 10, valor, border=1)
                    pdf.ln()
            elif titulo == "Gráfico Radar":
                pdf.ln(5)
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 10, "Tabela de Pontuações Filtradas:", ln=True)
                pdf.set_font("Arial", "", 10)
                for col in df_plot[['Departamento', 'Área', 'Avaliação']].columns:
                    pdf.cell(50, 10, col, border=1)
                pdf.ln()
                for _, row in df_plot[['Departamento', 'Área', 'Avaliação']].iterrows():
                    for col in df_plot[['Departamento', 'Área', 'Avaliação']].columns:
                        valor = str(row[col])[:30]
                        pdf.cell(50, 10, valor, border=1)
                    pdf.ln()
            elif titulo == "Matriz GUT":
                pdf.ln(5)
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 10, "Tabela GUT:", ln=True)
                pdf.set_font("Arial", "", 10)
                for col in df_gut_filtrado.columns:
                    pdf.cell(40, 10, str(col)[:15], border=1)
                pdf.ln()
                for _, row in df_gut_filtrado.iterrows():
                    for col in df_gut_filtrado.columns:
                        valor = str(row[col])[:35]
                        pdf.cell(40, 10, valor, border=1)
                    pdf.ln()
            elif titulo == "Top 10 Problemas":
                pdf.ln(5)
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 10, "Top 10 Problemas - Tabela:", ln=True)
                pdf.set_font("Arial", "", 10)
                for col in top10.columns:
                    pdf.cell(40, 10, str(col)[:15], border=1)
                pdf.ln()
                for _, row in top10.iterrows():
                    for col in top10.columns:
                        valor = str(row[col])[:35]
                        pdf.cell(40, 10, valor, border=1)
                    pdf.ln()
            elif titulo == "Evolução por Área":
                pdf.ln(5)
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 10, "Evolução por Área - Tabela:", ln=True)
                pdf.set_font("Arial", "", 10)
                for col in media_por_area.columns:
                    pdf.cell(40, 10, str(col)[:15], border=1)
                pdf.ln()
                for _, row in media_por_area.iterrows():
                    for col in media_por_area.columns:
                        valor = str(row[col])[:35]
                        pdf.cell(40, 10, valor, border=1)
                    pdf.ln()
            elif titulo == "Instruções Finais":
                pdf.multi_cell(0, 10, instrucoes_finais)

        pdf.output("diagnostico_360_exportado.pdf")
        with open("diagnostico_360_exportado.pdf", "rb") as f:
            st.download_button("📅 Baixar PDF", f, file_name="diagnostico_360_exportado.pdf", mime="application/pdf")
