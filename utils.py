import pandas as pd
from datetime import date, timedelta
import streamlit as st
import os

# --- 1. CONFIGURAÇÃO DE USUÁRIOS (Para autenticação local) ---
# Estrutura: {usuario: (senha, perfil)}
# Perfis: 'inspetor', 'coordenador', 'gerencia'
USERS = {
    "joao.insp": ("insp123", "inspetor"),
    "maria.coord": ("coord456", "coordenador"),
    "chefe.geren": ("geren789", "gerencia")
}

DATA_FILE = "data/banco.csv"

# --- 2. FUNÇÕES DE AUTENTICAÇÃO ---

def authenticate(username, password):
    """Verifica credenciais e retorna o perfil."""
    if username in USERS and USERS[username][0] == password:
        return True, USERS[username][1]
    return False, None

# --- 3. FUNÇÕES DE DADOS (CSV como BD) ---

@st.cache_data
def initialize_data():
    """Cria o DataFrame e o arquivo CSV inicial se não existirem."""
    if not os.path.exists('data'):
        os.makedirs('data')
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)

    # Colunas obrigatórias
    cols = [
        "ID", "inspetor_id", "estabelecimento", "cnpj", "atividade", "risco", 
        "data_inspecao", "obs_inspetor", "prazo_retorno_inspetor", 
        "prazo_retorno_coord", "status", "comentarios", "data_conclusao"
    ]
    
    # Cria um DataFrame vazio com as colunas definidas
    df = pd.DataFrame(columns=cols)
    df.to_csv(DATA_FILE, index=False)
    return df

def load_data():
    """Carrega os dados do CSV."""
    df = initialize_data()
    # Converte colunas de data para o tipo datetime, tratando erros
    date_cols = ["data_inspecao", "prazo_retorno_inspetor", "prazo_retorno_coord", "data_conclusao"]
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
    return df

def save_data(df):
    """Salva os dados de volta para o CSV."""
    df.to_csv(DATA_FILE, index=False)

# --- 4. FUNÇÃO DE GESTÃO DE PRAZOS ---

def get_deadline_status(row):
    """Calcula e retorna o status do prazo com base nas datas."""
    
    # Se o processo já está concluído, o status é OK
    if row['status'] == 'Concluído':
        return "Concluído", "green"

    # Determina o prazo mais relevante (Coordenador > Inspetor)
    prazo_ref = row['prazo_retorno_coord'] if row['prazo_retorno_coord'] else row['prazo_retorno_inspetor']
    
    if pd.isna(prazo_ref) or prazo_ref is None:
        return "Sem Prazo", "gray"

    hoje = date.today()
    
    # Verifica se prazo_ref é um objeto date (necessário após conversão no load_data)
    if not isinstance(prazo_ref, date):
        return "Erro de Data", "gray"

    dias_restantes = (prazo_ref - hoje).days
    
    if dias_restantes < 0:
        return f"VENCIDO há {-dias_restantes} dias", "red"
    elif dias_restantes <= 3:
        return f"VENCE em {dias_restantes} dias", "orange"
    else:
        return f"OK ({dias_restantes} dias)", "green"
