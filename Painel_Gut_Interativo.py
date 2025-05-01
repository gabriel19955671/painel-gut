
# IMPORTAÇÕES
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO
from fpdf import FPDF
import os
import plotly.io as pio

pio.kaleido.scope.default_format = "png"  # Necessário para salvar gráficos como imagem

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
    if 'Pontuação' in df_gut.columns:
        df_gut['Pontuação'] = pd.to_numeric(df_gut['Pontuação'], errors='coerce')
        df_gut.drop(columns=[col for col in df_gut.columns if col.lower() == 'score'], inplace=True, errors='ignore')
        df_gut.rename(columns={'Pontuação': 'Score'}, inplace=True)
    elif 'Score' not in df_gut.columns:
        df_gut['Score'] = df_gut['Gravidade'] * df_gut['Urgência'] * df_gut['Tendência']
    return df_gut, df_radar, df_plano

df_gut, df_radar, df_plano = carregar_unificado()

instrucoes_finais = st.session_state.get("instrucoes_digitadas", "")

aba1, aba2, aba3, aba4, aba5, aba6 = st.tabs([
    "📊 Gráfico Radar",
    "🗂️ Matriz GUT",
    "📝 Plano de Ação",
    "📥 Exportar PDF",
    "🧾 Instruções Finais",
    "✨ Gráficos Especiais"
])

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


# ABA 4 - Exportar PDF
from matplotlib.backends.backend_agg import RendererAgg
import matplotlib.pyplot as plt
import seaborn as sns
import io
    
with aba4:
    st.subheader("Exportar Diagnóstico 360º em PDF")
    opcoes_exportacao = st.selectbox("Escolha o conteúdo para exportar:", [
        "PDF Completo", "PDF por Área",
        "Gráfico Radar",
        "Matriz GUT", "Plano de Ação", "Instruções Finais", "Gráficos Especiais"
    ])
    
    if st.button("Gerar PDF"):
        with st.spinner("Gerando PDF..."):

            if opcoes_exportacao in ["PDF Completo", "PDF por Área"]:
                pdf.add_page()
                if os.path.exists("logo PR (3) (2).png"):
                    pdf.image("logo PR (3) (2).png", x=10, y=8, w=60)
                if os.path.exists("cliente_logo_temp.png"):
                    pdf.image("cliente_logo_temp.png", x=140, y=8, w=60)
                pdf.set_font("Arial", 'B', 18)
                pdf.ln(60)
                pdf.cell(0, 10, "Diagnóstico 360º - Potencialize Resultados", ln=True, align="C")
                pdf.set_font("Arial", '', 14)
                pdf.cell(0, 10, f"Cliente: {nome_cliente}", ln=True, align="C")
                pdf.cell(0, 10, f"Data do Diagnóstico: {data_diagnostico.strftime('%d/%m/%Y')}", ln=True, align="C")
                pdf.ln(10)

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, f"{opcoes_exportacao} - Diagnóstico 360º", ln=True, align="C")
            pdf.set_font("Arial", '', 12)
            pdf.cell(0, 10, f"Cliente: {nome_cliente}", ln=True)

            
            if opcoes_exportacao == "PDF Completo":
                fig_radar.write_image("radar_temp.png", width=800, height=600)
                fig_gut.write_image("gut_temp.png", width=800, height=600)
                fig_top10.write_image("top10_temp.png", width=800, height=500)
                fig_linha.write_image("linha_temp.png", width=800, height=500)

                pdf.image("radar_temp.png", x=10, y=40, w=190)
                pdf.add_page()
                pdf.image("gut_temp.png", x=10, y=40, w=190)

                pdf.add_page()
                pdf.set_font("Arial", 'B', 14)
                pdf.cell(0, 10, "Tabela Radar - Filtrada", ln=True)
                for index, row in df_plot.iterrows():
                    linha = f"{row.get('Departamento', '')} - {row.get('Área', '')}: {row.get('Avaliação', '')}"
                    pdf.multi_cell(0, 10, linha)

                pdf.add_page()
                pdf.set_font("Arial", 'B', 14)
                pdf.cell(0, 10, "Matriz GUT - Filtrada", ln=True)
                for index, row in df_gut_filtrado.iterrows():
                    linha = f"{row.get('Problema', '')} | Score: {row.get('Score', '')}"
                    pdf.multi_cell(0, 10, linha)

                pdf.add_page()
                pdf.set_font("Arial", '', 12)
                pdf.cell(0, 10, "Plano de Ação:", ln=True)
                for index, row in df_plano.iterrows():
                    linha = f"- {row.get('Ação', '')} | Resp: {row.get('Responsável', '')} | Prazo: {row.get('Prazo', '')}"
                    pdf.multi_cell(0, 10, linha)
                pdf.add_page()
                pdf.cell(0, 10, "Instruções Finais:", ln=True)
                pdf.multi_cell(0, 10, instrucoes_finais if instrucoes_finais else "Nenhuma instrução inserida.")
                if os.path.exists("instrucao_img_temp.png"):
                    pdf.image("instrucao_img_temp.png", x=10, w=150)
                pdf.add_page()
                pdf.image("top10_temp.png", x=10, y=40, w=190)
                pdf.add_page()
                pdf.image("linha_temp.png", x=10, y=40, w=190)

            elif opcoes_exportacao == "PDF por Área":
                for area in df_radar['Área'].unique():
                    pdf.add_page()
                    pdf.set_font("Arial", 'B', 14)
                    pdf.cell(0, 10, f"Área: {area}", ln=True)
                    df_area = df_radar[df_radar['Área'] == area]
                    media_area = df_area.groupby('Departamento')['Avaliação'].mean().reset_index()
                    fig_area = go.Figure()
                    for dep in media_area['Departamento'].unique():
                        df_dep = media_area[media_area['Departamento'] == dep]
                        fig_area.add_trace(go.Scatter(x=[area], y=df_dep['Avaliação'], mode='markers+text', name=dep,
                                                      text=df_dep['Avaliação'].round(1).astype(str)))
                    fig_area.update_layout(title=f"Avaliação por Departamento - {area}", xaxis_title="Área", yaxis_title="Avaliação")
                    file_area = f"grafico_{area}.png".replace(" ", "_")
                    fig_area.write_image(file_area, width=800, height=500)
                    pdf.image(file_area, x=10, y=40, w=190)

            elif opcoes_exportacao == "Gráfico Radar":

                fig_radar.write_image("radar_temp.png", width=800, height=600)
                pdf.image("radar_temp.png", x=10, y=40, w=190)
            elif opcoes_exportacao == "Matriz GUT":
                fig_gut.write_image("gut_temp.png", width=800, height=600)
                pdf.image("gut_temp.png", x=10, y=40, w=190)

                pdf.add_page()
                pdf.set_font("Arial", 'B', 14)
                pdf.cell(0, 10, "Tabela Radar - Filtrada", ln=True)
                for index, row in df_plot.iterrows():
                    linha = f"{row.get('Departamento', '')} - {row.get('Área', '')}: {row.get('Avaliação', '')}"
                    pdf.multi_cell(0, 10, linha)

                pdf.add_page()
                pdf.set_font("Arial", 'B', 14)
                pdf.cell(0, 10, "Matriz GUT - Filtrada", ln=True)
                for index, row in df_gut_filtrado.iterrows():
                    linha = f"{row.get('Problema', '')} | Score: {row.get('Score', '')}"
                    pdf.multi_cell(0, 10, linha)

            elif opcoes_exportacao == "Plano de Ação":
                pdf.ln(10)
                for index, row in df_plano.iterrows():
                    linha = f"- {row.get('Ação', '')} | Resp: {row.get('Responsável', '')} | Prazo: {row.get('Prazo', '')}"
                    pdf.multi_cell(0, 10, linha)
            elif opcoes_exportacao == "Instruções Finais":
                pdf.multi_cell(0, 10, instrucoes_finais if instrucoes_finais else "Nenhuma instrução inserida.")
                if os.path.exists("instrucao_img_temp.png"):
                    pdf.image("instrucao_img_temp.png", x=10, w=150)
            elif opcoes_exportacao == "Gráficos Especiais":
                fig_top10.write_image("top10_temp.png", width=800, height=500)
                fig_linha.write_image("linha_temp.png", width=800, height=500)
                pdf.image("top10_temp.png", x=10, y=40, w=190)
                pdf.add_page()
                pdf.image("linha_temp.png", x=10, y=40, w=190)

            pdf.output("diagnostico_360_exportado.pdf")

        with open("diagnostico_360_exportado.pdf", "rb") as f:
            st.download_button("📥 Baixar PDF", f, file_name="diagnostico_360_exportado.pdf", mime="application/pdf")

        with st.spinner("Gerando PDF..."):

            if opcoes_exportacao in ["PDF Completo", "PDF por Área"]:
                pdf.add_page()
                if os.path.exists("logo PR (3) (2).png"):
                    pdf.image("logo PR (3) (2).png", x=10, y=8, w=60)
                if os.path.exists("cliente_logo_temp.png"):
                    pdf.image("cliente_logo_temp.png", x=140, y=8, w=60)
                pdf.set_font("Arial", 'B', 18)
                pdf.ln(60)
                pdf.cell(0, 10, "Diagnóstico 360º - Potencialize Resultados", ln=True, align="C")
                pdf.set_font("Arial", '', 14)
                pdf.cell(0, 10, f"Cliente: {nome_cliente}", ln=True, align="C")
                pdf.cell(0, 10, f"Data do Diagnóstico: {data_diagnostico.strftime('%d/%m/%Y')}", ln=True, align="C")
                pdf.ln(10)

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, f"{opcoes_exportacao} - Diagnóstico 360º", ln=True, align="C")
            pdf.set_font("Arial", '', 12)
            pdf.cell(0, 10, f"Cliente: {nome_cliente}", ln=True)

            
            if opcoes_exportacao == "PDF Completo":
                fig_radar.write_image("radar_temp.png", width=800, height=600)
                fig_gut.write_image("gut_temp.png", width=800, height=600)
                fig_top10.write_image("top10_temp.png", width=800, height=500)
                fig_linha.write_image("linha_temp.png", width=800, height=500)

                pdf.image("radar_temp.png", x=10, y=40, w=190)
                pdf.add_page()
                pdf.image("gut_temp.png", x=10, y=40, w=190)

                pdf.add_page()
                pdf.set_font("Arial", 'B', 14)
                pdf.cell(0, 10, "Tabela Radar - Filtrada", ln=True)
                for index, row in df_plot.iterrows():
                    linha = f"{row.get('Departamento', '')} - {row.get('Área', '')}: {row.get('Avaliação', '')}"
                    pdf.multi_cell(0, 10, linha)

                pdf.add_page()
                pdf.set_font("Arial", 'B', 14)
                pdf.cell(0, 10, "Matriz GUT - Filtrada", ln=True)
                for index, row in df_gut_filtrado.iterrows():
                    linha = f"{row.get('Problema', '')} | Score: {row.get('Score', '')}"
                    pdf.multi_cell(0, 10, linha)

                pdf.add_page()
                pdf.set_font("Arial", '', 12)
                pdf.cell(0, 10, "Plano de Ação:", ln=True)
                for index, row in df_plano.iterrows():
                    linha = f"- {row.get('Ação', '')} | Resp: {row.get('Responsável', '')} | Prazo: {row.get('Prazo', '')}"
                    pdf.multi_cell(0, 10, linha)
                pdf.add_page()
                pdf.cell(0, 10, "Instruções Finais:", ln=True)
                pdf.multi_cell(0, 10, instrucoes_finais if instrucoes_finais else "Nenhuma instrução inserida.")
                if os.path.exists("instrucao_img_temp.png"):
                    pdf.image("instrucao_img_temp.png", x=10, w=150)
                pdf.add_page()
                pdf.image("top10_temp.png", x=10, y=40, w=190)
                pdf.add_page()
                pdf.image("linha_temp.png", x=10, y=40, w=190)

            elif opcoes_exportacao == "PDF por Área":
                for area in df_radar['Área'].unique():
                    pdf.add_page()
                    pdf.set_font("Arial", 'B', 14)
                    pdf.cell(0, 10, f"Área: {area}", ln=True)
                    df_area = df_radar[df_radar['Área'] == area]
                    media_area = df_area.groupby('Departamento')['Avaliação'].mean().reset_index()
                    fig_area = go.Figure()
                    for dep in media_area['Departamento'].unique():
                        df_dep = media_area[media_area['Departamento'] == dep]
                        fig_area.add_trace(go.Scatter(x=[area], y=df_dep['Avaliação'], mode='markers+text', name=dep,
                                                      text=df_dep['Avaliação'].round(1).astype(str)))
                    fig_area.update_layout(title=f"Avaliação por Departamento - {area}", xaxis_title="Área", yaxis_title="Avaliação")
                    file_area = f"grafico_{area}.png".replace(" ", "_")
                    fig_area.write_image(file_area, width=800, height=500)
                    pdf.image(file_area, x=10, y=40, w=190)

            elif opcoes_exportacao == "Gráfico Radar":

                fig_radar.write_image("radar_temp.png", width=800, height=600)
                pdf.image("radar_temp.png", x=10, y=40, w=190)
            elif opcoes_exportacao in ["Matriz GUT", "Plano de Ação", "Instruções Finais", "Gráficos Especiais"]:
                fig_gut.write_image("gut_temp.png", width=800, height=600)
                pdf.image("gut_temp.png", x=10, y=40, w=190)

                pdf.add_page()
                pdf.set_font("Arial", 'B', 14)
                pdf.cell(0, 10, "Tabela Radar - Filtrada", ln=True)
                for index, row in df_plot.iterrows():
                    linha = f"{row.get('Departamento', '')} - {row.get('Área', '')}: {row.get('Avaliação', '')}"
                    pdf.multi_cell(0, 10, linha)

                pdf.add_page()
                pdf.set_font("Arial", 'B', 14)
                pdf.cell(0, 10, "Matriz GUT - Filtrada", ln=True)
                for index, row in df_gut_filtrado.iterrows():
                    linha = f"{row.get('Problema', '')} | Score: {row.get('Score', '')}"
                    pdf.multi_cell(0, 10, linha)


            pdf.output("diagnostico_360_exportado.pdf")

        with open("diagnostico_360_exportado.pdf", "rb") as f:
            st.download_button("📥 Baixar PDF", f, file_name="diagnostico_360_exportado.pdf", mime="application/pdf")
