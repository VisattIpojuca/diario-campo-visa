import streamlit as st
from utils import authenticate, load_data

st.set_page_config(page_title="Diário de Campo VISA", layout="wide", initial_sidebar_state="expanded")

# --- Inicialização do Estado da Sessão ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = None
if 'role' not in st.session_state:
    st.session_state['role'] = None

# --- SIDEBAR (Visível após o login) ---
if st.session_state['logged_in']:
    st.sidebar.title("Menu do Sistema")
    st.sidebar.write(f"Usuário: **{st.session_state['username']}**")
    st.sidebar.write(f"Perfil: **{st.session_state['role'].capitalize()}**")

    # Botão de Logout
    if st.sidebar.button("Sair (Logout)", type="primary"):
        st.session_state['logged_in'] = False
        st.session_state['username'] = None
        st.session_state['role'] = None
        st.success("Sessão encerrada.")
        st.experimental_rerun() 
    
    # Conteúdo Principal (Visão Geral)
    st.title("📒 Visão Geral do Diário de Campo")
    
    df = load_data()
    total_inspecoes = len(df)
    
    # Exibir informações conforme o perfil
    if st.session_state['role'] == 'inspetor':
        df_user = df[df['inspetor_id'] == st.session_state['username']]
        total_inspecoes_user = len(df_user)
        st.info(f"Você tem **{total_inspecoes_user}** inspeções registradas. Acesse **Minhas Inspeções** para ver seus prazos!")
    else:
        st.success(f"Há **{total_inspecoes}** inspeções registradas no total.")
        st.warning("Acesse **Painel Coordenação** ou **Indicadores** para gerenciar a equipe.")

    st.markdown("---")
    st.markdown("""
    Use o menu lateral para navegar entre as funcionalidades.
    Este é o ponto de partida para a gestão da Vigilância Sanitária baseada em dados e prazos.
    """)

# --- TELA DE LOGIN ---
if not st.session_state['logged_in']:
    st.title("🔒 Acesso Restrito - Diário de Campo Digital")
    st.markdown("Insira suas credenciais para acessar a plataforma.")

    col1, col2 = st.columns([1, 2])
    
    with col1:
        with st.form("login_form"):
            username = st.text_input("Usuário", placeholder="joao.insp")
            password = st.text_input("Senha", type="password", placeholder="insp123 / coord456 / geren789")
            submit_button = st.form_submit_button("Entrar")

            if submit_button:
                success, role = authenticate(username, password)
                if success:
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = username
                    st.session_state['role'] = role
                    st.success(f"Login efetuado! Bem-vindo(a), {role.capitalize()}.")
                    st.experimental_rerun() 
                else:
                    st.error("Usuário ou senha inválidos.")
    with col2:
        st.image("https://placehold.co/600x200/4F46E5/FFFFFF?text=VISA+Digital", use_column_width=True)
