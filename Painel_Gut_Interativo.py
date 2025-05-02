import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO
from fpdf import FPDF
import os
from PIL import Image

st.set_page_config(page_title="Diagnóstico 360º - Potencialize Resultados", layout="wide")

# SIDEBAR (deve vir antes do cabeçalho)
st.sidebar.markdown("---")
if st.sidebar.button("🔁 Resetar Filtros e Abas"):
    st.session_state.clear()
    st.session_state['reset_filtros'] = True
    st.success("Todos os filtros, dados e abas foram resetados com sucesso.")
data_diagnostico = st.sidebar.date_input("Data de Apresentação do Diagnóstico")
st.session_state['data_diagnostico'] = data_diagnostico
nome_cliente = st.sidebar.text_input("Nome do Cliente")
st.session_state['nome_cliente'] = nome_cliente
uploaded_logo = st.sidebar.file_uploader("Anexar Logomarca do Cliente", type=["png", "jpg", "jpeg"])

if uploaded_logo:
    try:
        image = Image.open(uploaded_logo)
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        image.save("logo_cliente_temp.jpg", format="JPEG", quality=95)
        st.session_state['logo_cliente_path'] = "logo_cliente_temp.jpg"
    except Exception as e:
        st.error(f"Erro ao processar a imagem: {e}")

# TOPO COM LOGOMARCA FIXA
st.sidebar.markdown("---")
if st.sidebar.button("🔄 Limpar Cabeçalho e Logo"):
    st.session_state['nome_cliente'] = ""
    st.session_state['data_diagnostico'] = None
    if os.path.exists("logo_cliente_temp.jpg"):
        os.remove("logo_cliente_temp.jpg")
    st.session_state['logo_cliente_path'] = ""
topo1, topo2, topo3 = st.columns([1, 2, 1])
with topo1:
    if os.path.exists("logo_PR_FIXA.png"):
        logo_img = Image.open("logo_PR_FIXA.png")
        st.image(logo_img, width=300)

with topo2:
    nome_cliente = st.session_state.get('nome_cliente', '')
    data_diagnostico = st.session_state.get('data_diagnostico', None)
    data_formatada = data_diagnostico.strftime('%d/%m/%Y') if data_diagnostico else ''
    st.markdown(f"""
        <div style='text-align: center; padding-top: 15px; padding-bottom: 5px;'>
            <h1 style='font-size: 32px; margin-bottom: 5px;'>Diagnóstico Potencialize 360º</h1>
            <h3 style='margin-top: 0; font-size: 20px; color: #333;'>{nome_cliente}</h3>
            <h4 style='margin-top: 0; font-size: 16px; color: #666;'>{data_formatada}</h4>
        </div>
    """, unsafe_allow_html=True)

with topo3:
    if os.path.exists("logo_cliente_temp.jpg"):
        logo_cliente = Image.open("logo_cliente_temp.jpg")
        st.image(logo_cliente, width=220)

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
top10 = df_gut.sort_values(by='Score', ascending=False).head(10)
media_por_area = df_radar.groupby(['Área', 'Departamento'])['Avaliação'].mean().reset_index()

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
        if 'reset_filtros' in st.session_state and st.session_state['reset_filtros']:
            st.session_state['depto_selecionado'] = departamentos
        depto_selecionado = st.multiselect("Departamento(s)", departamentos, default=st.session_state.get('depto_selecionado', departamentos), key='depto_selecionado')
    with col2:
        areas = sorted(df_radar['Área'].unique())
        if 'reset_filtros' in st.session_state and st.session_state['reset_filtros']:
            st.session_state['area_selecionada'] = areas
        area_selecionada = st.multiselect("Área(s)", areas, default=st.session_state.get('area_selecionada', areas), key='area_selecionada')
    with col3:
        avaliacao_default = (0.0, 10.0)
        if 'reset_filtros' in st.session_state and st.session_state['reset_filtros']:
            st.session_state['avaliacao_range'] = avaliacao_default
        avaliacao_min, avaliacao_max = st.slider("Intervalo de Avaliação", 0.0, 10.0, st.session_state.get('avaliacao_range', avaliacao_default), step=0.1, key='avaliacao_range')

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

    radar_buf = BytesIO()
    fig_radar.write_image(radar_buf, format="png")
    st.download_button("📥 Baixar Gráfico Radar", data=radar_buf.getvalue(), file_name="grafico_radar.png", mime="image/png")

    if 'reset_filtros' in st.session_state:
        st.session_state['reset_filtros'] = False

with aba2:
    st.subheader("Matriz GUT - Priorizacão das Dores")
    score_max_padrao = int(df_gut['Score'].max())
    if 'reset_filtros' in st.session_state and st.session_state['reset_filtros']:
        st.session_state['score_gut_range'] = (0, score_max_padrao)
    score_min, score_max = st.slider("Filtro por Score GUT", 0, score_max_padrao, st.session_state.get('score_gut_range', (0, score_max_padrao)), key='score_gut_range')
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

    gut_buf = BytesIO()
    fig_gut.write_image(gut_buf, format="png")
    st.download_button("📥 Baixar Matriz GUT", data=gut_buf.getvalue(), file_name="matriz_gut.png", mime="image/png")

with aba3:
    st.subheader("Plano de Ação - Estratégias de Melhoria")
    if 'reset_filtros' in st.session_state and st.session_state['reset_filtros']:
        st.session_state['filtro_prazo'] = list(df_plano['Prazo'].unique())
        if 'Responsável' in df_plano.columns:
            st.session_state['filtro_resp'] = list(df_plano['Responsável'].dropna().unique())
    col1, col2 = st.columns(2)
    with col1:
        prazos = df_plano['Prazo'].unique()
        filtro_prazo = st.multiselect("Filtrar por Prazo", options=prazos, default=st.session_state.get('filtro_prazo', list(prazos)), key='filtro_prazo')
    with col2:
        if 'Responsável' in df_plano.columns:
            responsaveis = df_plano['Responsável'].dropna().unique()
            filtro_resp = st.multiselect("Filtrar por Responsável", options=responsaveis, default=st.session_state.get('filtro_resp', list(responsaveis)), key='filtro_resp')
            df_filtrado = df_plano[
                (df_plano['Prazo'].isin(filtro_prazo)) &
                (df_plano['Responsável'].isin(filtro_resp))
            ]
    st.dataframe(df_filtrado, use_container_width=True)

    plano_csv = df_filtrado.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Baixar Plano de Ação Filtrado", data=plano_csv, file_name="plano_acao_filtrado.csv", mime="text/csv")

with aba5:
    st.subheader("🧾 Instruções Pós-Diagnóstico")
    if 'reset_filtros' in st.session_state and st.session_state['reset_filtros']:
        st.session_state['instrucoes_digitadas'] = ""
    instrucoes = st.text_area("Digite aqui as instruções finais para o cliente:", height=300)
    imagem_instrucao = st.file_uploader("Opcional: Anexar imagem para as instruções", type=["png", "jpg", "jpeg"])
    if imagem_instrucao:
        with open("img_instrucao_temp.png", "wb") as f:
            f.write(imagem_instrucao.read())
    st.session_state['instrucoes_digitadas'] = instrucoes

with aba6:
    st.subheader("✨ Gráficos Especiais")

    fig_linha = go.Figure()

    if 'reset_filtros' in st.session_state and st.session_state['reset_filtros']:
        top10 = df_gut.sort_values(by='Score', ascending=False).head(10)
        media_por_area = df_radar.groupby(['Área', 'Departamento'])['Avaliação'].mean().reset_index()

    st.markdown("#### 🔝 Top 10 Problemas por Score GUT")
    fig_top10 = go.Figure(go.Bar(
        x=top10['Score'],
        y=top10['Problema'],
        orientation='h',
        marker_color='crimson'
    ))
    fig_top10.update_layout(height=500, margin=dict(l=120, r=20, t=40, b=40))
    st.plotly_chart(fig_top10, use_container_width=True)

    top10_buf = BytesIO()
    fig_top10.write_image(top10_buf, format="png")
    st.download_button("📥 Baixar Gráfico Top 10 GUT", data=top10_buf.getvalue(), file_name="top10_gut.png", mime="image/png")

    st.markdown("#### 📈 Evolução Média das Avaliações por Área")
    for dep in media_por_area['Departamento'].unique():
        df_dep = media_por_area[media_por_area['Departamento'] == dep]
        fig_linha.add_trace(go.Scatter(
            x=df_dep['Área'],
            y=df_dep['Avaliação'],
            mode='lines+markers',
            name=dep
        ))
    fig_linha.update_layout(height=500, xaxis_title='Área', yaxis_title='Avaliação Média')
    st.plotly_chart(fig_linha, use_container_width=True)

    linha_buf = BytesIO()
    fig_linha.write_image(linha_buf, format="png")
    st.download_button("📥 Baixar Gráfico Evolução", data=linha_buf.getvalue(), file_name="grafico_evolucao.png", mime="image/png")

with aba4:
    st.subheader("📅 Exportar Diagnóstico 360º em PDF")
    opcoes_exportacao = st.selectbox("Escolha o conteúdo para exportar:", [
        "PDF Completo", "Gráfico Radar", "Matriz GUT", "Plano de Ação", "Instruções Finais", "Gráficos Especiais"])

    # ========== GERAÇÃO DO PDF COM LOGO, GRÁFICOS E TABELAS ==========
    if st.button("Gerar PDF"):
        fig_top10.write_image("top10_temp.png", width=600, height=400)
        fig_linha.write_image("linha_temp.png", width=600, height=400)
        fig_radar.write_image("radar_temp.png", width=600, height=400)
        fig_gut.write_image("gut_temp.png", width=600, height=400)

        class FooterPDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font("Arial", "B", 10)
            self.set_text_color(100, 100, 100)
            self.cell(0, 10, "Diagnóstico 360º - Potencialize Resultados", ln=True, align="C")
            self.ln(5)
    def header(self):
        if self.page_no() > 1:
            self.set_font("Arial", "B", 10)
            self.set_text_color(100, 100, 100)
            self.cell(0, 10, "Diagnóstico 360º - Potencialize Resultados", ln=True, align="C")
            self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(180, 180, 180)
        self.cell(0, 10, f"Página {self.page_no()} / {{nb}}", 0, 0, "C")
        self.set_y(-10)
        self.cell(0, 10, "Potencialize Resultados", 0, 0, "C")

        
                pdf = FooterPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.alias_nb_pages()
        secoes = [("Diagnóstico 360º", "Capa")]

        if opcoes_exportacao == "PDF Completo":
            secoes += [
                ("Gráfico Radar", "radar_temp.png"),
                ("Matriz GUT", "gut_temp.png"),
                ("Plano de Ação", None),
                ("Instruções Finais", None),
                
            ]
        else:
            secoes = [(opcoes_exportacao, None)]

        for titulo, imagem in secoes:
            pdf.add_page()
            if imagem == "Capa":
                if os.path.exists("logo_PR_FIXA.png"):
                    pdf.image("logo_PR_FIXA.png", x=10, y=8, w=70)
                logo_cliente_path = st.session_state.get("logo_cliente_path", "")
                if logo_cliente_path and os.path.exists(logo_cliente_path):
                    try:
                        pdf.image(logo_cliente_path, x=160, y=12, w=35)
                    except Exception as e:
                        print(f"Erro ao inserir logo do cliente: {e}")
                pdf.set_y(110)
                pdf.set_font("Arial", "B", 20)
                pdf.cell(0, 10, "Diagnóstico 360º - Potencialize Resultados", ln=True, align="C")
                pdf.set_font("Arial", "", 12)
                pdf.cell(0, 10, f"Cliente: {nome_cliente}", ln=True, align="C")
                pdf.cell(0, 10, f"Data do Diagnóstico: {data_diagnostico.strftime('%d/%m/%Y')}", ln=True, align="C")
                pdf.ln(10)
                continue

            if os.path.exists("logo_PR_FIXA.png"):
                pdf.image("logo_PR_FIXA.png", x=10, y=8, w=50)
            pdf.set_font("Arial", "B", 16)
            pdf.set_y(30)
            pdf.ln(5)
            pdf.cell(0, 10, "Diagnóstico 360º - Potencialize Resultados", ln=True, align="C")
            pdf.set_font("Arial", "", 10)
            pdf.cell(0, 10, f"Cliente: {nome_cliente} | Data: {data_diagnostico.strftime('%d/%m/%Y')}", ln=True, align="C")
            pdf.ln(10)

            if imagem and os.path.exists(imagem):
                # Adiciona tabela correspondente antes do gráfico, se aplicável
                if titulo == "Gráfico Radar":
                    for _, row in df_plot.iterrows():
                        pdf.multi_cell(0, 8, f"Departamento: {row['Departamento']} | Área: {row['Área']} | Avaliação: {row['Avaliação']}")
                    pdf.ln(2)
                elif titulo == "Matriz GUT":
                    for _, row in df_gut_filtrado.iterrows():
                        pdf.multi_cell(0, 8, f"Problema: {row['Problema']} | Gravidade: {row['Gravidade']} | Urgência: {row['Urgência']} | Tendência: {row['Tendência']} | Score: {row['Score']}")
                    pdf.ln(2)
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 10, f"{titulo}", ln=True, align="C")
                pdf.ln(2)
                pdf.ln(10)
                pdf.image(imagem, x=60, y=pdf.get_y(), w=90)
            elif titulo == "Plano de Ação":
                for _, row in df_filtrado.iterrows():
                    pdf.multi_cell(0, 10, f"- {row['Ação']} | Resp: {row['Responsável']} | Prazo: {row['Prazo']}")
            elif titulo == "Instruções Finais":
                if os.path.exists("img_instrucao_temp.png"):
                    pdf.ln(10)
                    pdf.image("img_instrucao_temp.png", x=60, y=pdf.get_y(), w=70)
                    pdf.ln(5)
                pdf.set_font("Arial", "", 10)
                pdf.multi_cell(0, 8, instrucoes_finais)

        pdf.output("diagnostico_360_exportado.pdf")
        with open("diagnostico_360_exportado.pdf", "rb") as f:
            st.download_button("📥 Baixar PDF", f, file_name="diagnostico_360_exportado.pdf", mime="application/pdf")
