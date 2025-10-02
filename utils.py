import pandas as pd
from datetime import date
import streamlit as st
import gspread
from gspread_dataframe import set_with_dataframe, get_as_dataframe
import os

# --- 1. CONFIGURAÇÃO DE USUÁRIOS (Inalterada) ---
USERS = {
    "joao.insp": ("insp123", "inspetor"),
    "maria.coord": ("coord456", "coordenador"),
    "chefe.geren": ("geren789", "gerencia")
}

# --- 2. CONFIGURAÇÃO DO GOOGLE SHEETS ---
# A URL e as credenciais são obtidas do Streamlit Secrets
SHEETS_URL = st.secrets.get("gsheets_url")
# Garante que a aplicação pare se as chaves não forem configuradas
if not SHEETS_URL:
    # Esta mensagem só aparece no Streamlit Cloud se a chave estiver faltando
    st.error("ERRO DE CONFIGURAÇÃO: A chave 'gsheets_url' não foi encontrada no Streamlit Secrets. Verifique o arquivo .streamlit/secrets.toml.")
    st.stop()


# --- 3. FUNÇÕES DE AUTENTICAÇÃO ---
def authenticate(username, password):
    """Verifica credenciais e retorna o perfil."""
    if username in USERS and USERS[username][0] == password:
        return True, USERS[username][1]
    return False, None

# --- 4. FUNÇÕES DE DADOS (GOOGLE SHEETS) ---

# O cache de recurso garante que a conexão só seja estabelecida uma vez por sessão
# O ttl=3600 (3600 segundos = 1 hora) evita que o Streamlit tente reconectar a cada 5 minutos
@st.cache_resource(ttl=3600) 
def get_sheets_client():
    """Conecta-se ao Google Sheets usando as credenciais do Streamlit Secrets."""
    # st.secrets["gcp_service_account"] é o dicionário JSON que você colou no secrets
    credentials = st.secrets.get("gcp_service_account")
    if not credentials:
        st.error("ERRO DE CONFIGURAÇÃO: A chave 'gcp_service_account' não foi encontrada no Streamlit Secrets. Verifique o arquivo .streamlit/secrets.toml.")
        st.stop()
        
    try:
        # Cria a conexão a partir do dicionário de credenciais
        gc = gspread.service_account_from_dict(credentials)
        return gc
    except Exception as e:
        st.error(f"Erro ao conectar ao Google Sheets. Verifique o JSON da Service Account no Secrets. Erro: {e}")
        st.stop()

# O cache de dados (ttl=5) garante que a leitura não ocorra a cada interação do usuário,
# mas que os dados sejam atualizados a cada 5 segundos ou após um 'save_data'.
@st.cache_data(ttl=5) 
def initialize_data():
    """Conecta, lê os dados da Planilha e faz o tratamento inicial."""
    gc = get_sheets_client()
    try:
        sh = gc.open_by_url(SHEETS_URL)
        # Assumimos que os dados estão na primeira aba ('Sheet1')
        worksheet = sh.worksheet('Sheet1') 

        # Tenta ler a planilha como DataFrame
        df = get_as_dataframe(worksheet, header=0)
        
        # Remoção de linhas completamente vazias
        df = df.dropna(how='all')
        
        # Garante que as colunas essenciais existam
        COLUMNS = ["ID", "inspetor_id", "estabelecimento", "cnpj", "atividade", "risco", 
                   "data_inspecao", "obs_inspetor", "prazo_retorno_inspetor", 
                   "prazo_retorno_coord", "status", "comentarios", "data_conclusao"]
        
        # Adiciona colunas se estiverem faltando (útil para o primeiro carregamento)
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = None

        # Trata IDs
        if not df.empty and 'ID' in df.columns:
             # Converte ID para int, tratando erros e NaN como 0 temporariamente
             df['ID'] = pd.to_numeric(df['ID'], errors='coerce').fillna(0).astype(int)
        
        return df[COLUMNS] # Retorna apenas as colunas na ordem correta

    except Exception as e:
        st.error(f"Erro ao carregar dados da Planilha Google (Planilha ou Aba não encontrada? Verifique a URL e o nome da aba 'Sheet1'). Erro: {e}")
        st.stop()

def load_data():
    """Carrega os dados e formata as colunas de data como objetos date do Python."""
    df = initialize_data()
    # Tratamento de datas (Crucial para o cálculo de prazo)
    date_cols = ["data_inspecao", "prazo_retorno_inspetor", "prazo_retorno_coord", "data_conclusao"]
    for col in date_cols:
        # Converte a coluna para datetime e depois para date (apenas a parte da data)
        df[col] = pd.to_datetime(df[col], errors='coerce').dt.date

    return df

def save_data(df):
    """Salva os dados de volta para a Planilha Google."""
    gc = get_sheets_client()
    sh = gc.open_by_url(SHEETS_URL)
    worksheet = sh.worksheet('Sheet1') 
    
    # 1. Converte objetos date para string ('YYYY-MM-DD') antes de salvar no Sheets
    date_cols = ["data_inspecao", "prazo_retorno_inspetor", "prazo_retorno_coord", "data_conclusao"]
    # Cria uma cópia para evitar SettingWithCopyWarning no Pandas
    df_save = df.copy() 
    for col in date_cols:
         # Converte para string se for um objeto date válido
         df_save[col] = df_save[col].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) and isinstance(x, date) else None)

    # 2. Invalida o cache para que o próximo 'load' busque a versão atualizada da Planilha
    initialize_data.clear() 
    load_data.clear()

    # 3. Sobrescreve a planilha com o novo DataFrame
    # row=1 e col=1 garantem que começamos na célula A1
    set_with_dataframe(worksheet, df_save, row=1, col=1, include_index=False, resize=True)


# --- 5. FUNÇÃO DE GESTÃO DE PRAZOS ---
def get_deadline_status(row):
    """Calcula e retorna o status do prazo com base nas datas."""
    
    # Se o status for 'Concluído', o prazo é 'Concluído'
    if row['status'] == 'Concluído':
        return "Concluído", "green"

    # Determina o prazo mais relevante (Coordenação tem prioridade)
    prazo_ref = row['prazo_retorno_coord'] if row['prazo_retorno_coord'] else row['prazo_retorno_inspetor']
    
    # Se não houver prazo definido
    if pd.isna(prazo_ref) or prazo_ref is None:
        return "Sem Prazo", "gray"

    hoje = date.today()
    
    # Verifica se prazo_ref é um objeto date (para segurança após o load_data)
    if not isinstance(prazo_ref, date):
        return "Erro de Data", "gray"

    dias_restantes = (prazo_ref - hoje).days
    
    if dias_restantes < 0:
        return f"VENCIDO há {-dias_restantes} dias", "red"
    elif dias_restantes <= 3:
        return f"VENCE em {dias_restantes} dias", "orange"
    else:
        return f"OK ({dias_restantes} dias)", "green"
