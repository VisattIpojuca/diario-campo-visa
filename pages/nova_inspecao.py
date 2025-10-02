import streamlit as st
import pandas as pd
from datetime import date
from utils import load_data, save_data

# Verifica o login.
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.error("Acesso negado. Faça login na página inicial.")
    st.stop()

st.title("📝 Registro de Nova Inspeção")

df = load_data()

# --- Formulário de Cadastro ---
with st.form("nova_inspecao_form"):
    st.header("Dados do Estabelecimento")
    col1, col2, col3 = st.columns(3)
    
    estabelecimento = col1.text_input("Nome do Estabelecimento", required=True)
    cnpj = col2.text_input("CNPJ", required=True, max_chars=18, placeholder="00.000.000/0000-00")
    atividade = col3.selectbox("Atividade Principal", ["Alimentos", "Saúde", "Saneantes", "Cosméticos", "Outro"], required=True)
    
    col4, col5 = st.columns(2)
    risco = col4.selectbox("Classificação de Risco", ["Alto", "Médio", "Baixo"], required=True)
    data_visita = col5.date_input("Data da Inspeção", date.today(), required=True)

    st.header("Diário de Campo e Prazos")
    obs = st.text_area("Observações e Não Conformidades Encontradas")
    
    prazo_retorno_inspetor = st.date_input("Prazo de Retorno (Estabelecido por Você)", 
                                           date.today() + pd.Timedelta(days=15), 
                                           min_value=date.today())

    st.caption("A Coordenação poderá definir um prazo obrigatório posteriormente. O prazo padrão é 15 dias.")
    
    uploaded_files = st.file_uploader("Upload de Fotos ou Documentos (Apenas para demonstração)", accept_multiple_files=True)

    submit_button = st.form_submit_button("Salvar Inspeção e Gerar Processo", type="primary")

    if submit_button:
        if not estabelecimento or not cnpj:
            st.error("Por favor, preencha o Nome do Estabelecimento e o CNPJ.")
        else:
            new_id = df['ID'].max() + 1 if not df.empty else 1
            
            new_record = {
                "ID": new_id,
                "inspetor_id": st.session_state['username'],
                "estabelecimento": estabelecimento,
                "cnpj": cnpj,
                "atividade": atividade,
                "risco": risco,
                "data_inspecao": data_visita,
                "obs_inspetor": obs,
                "prazo_retorno_inspetor": prazo_retorno_inspetor,
                "prazo_retorno_coord": None,
                "status": "Em Andamento",
                "comentarios": "Processo iniciado pelo inspetor.",
                "data_conclusao": None
            }
            
            df.loc[len(df)] = new_record
            save_data(df)
            
            st.success(f"Processo **{new_id}** (Estabelecimento: {estabelecimento}) criado com sucesso!")
            st.info(f"Prazo de Retorno definido para: **{prazo_retorno_inspetor.strftime('%d/%m/%Y')}**.")
            st.balloons()
