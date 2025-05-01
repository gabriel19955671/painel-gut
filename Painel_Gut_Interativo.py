import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO
from fpdf import FPDF
import os
from PIL import Image

st.set_page_config(page_title="Diagnóstico 360º - Potencialize Resultados", layout="wide")

# SIDEBAR (deve vir antes do cabeçalho)
data_diagnostico = st.sidebar.date_input("Data de Apresentação do Diagnóstico")
st.session_state['data_diagnostico'] = data_diagnostico
nome_cliente = st.sidebar.text_input("Nome do Cliente")
st.session_state['nome_cliente'] = nome_cliente
uploaded_logo = st.sidebar.file_uploader("Anexar Logomarca do Cliente", type=["png", "jpg", "jpeg"])

if uploaded_logo:
    with open("logo_cliente_temp.png", "wb") as f:
        f.write(uploaded_logo.read())

# TOPO COM LOGOMARCA FIXA (agora já pode acessar os valores com segurança)
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    if os.path.exists("logo_PR_FIXA.png"):
        logo_img = Image.open("logo_PR_FIXA.png")
        st.image(logo_img, width=300)

with col2:
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

with col3:
    if os.path.exists("logo_cliente_temp.png"):
        logo_cliente = Image.open("logo_cliente_temp.png")
        st.image(logo_cliente, width=220)

# O restante do código continua daqui (sem alterações nesta parte)...
