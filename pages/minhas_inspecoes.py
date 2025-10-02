import streamlit as st
import pandas as pd
from utils import load_data, save_data, get_deadline_status
from datetime import date

# Verifica o login.
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.error("Acesso negado. Faça login na página inicial.")
    st.stop()

st.title("📅 Minhas Inspeções e Prazos")

df = load_data()
current_user = st.session_state['username']
role = st.session_state['role']

# --- Filtro de Dados ---
# Inspetores só veem os próprios registros
if role == 'inspetor':
    df_user = df[df['inspetor_id'] == current_user].copy()
else:
    # Coordenadores e Gerência podem ver tudo
    df_user = df.copy()

# Aplica a lógica de status de prazo
df_user['status_prazo'], df_user['cor'] = zip(*df_user.apply(get_deadline_status, axis=1))

st.markdown("---")

# --- Dashboards de Alerta ---
df_pendente = df_user[df_user['status'] == 'Em Andamento']

vencidos = df_pendente[df_pendente['cor'] == 'red']
vencendo = df_pendente[df_pendente['cor'] == 'orange']

col_alerts = st.columns(3)
col_alerts[0].metric(label="Processos Em Andamento", value=len(df_pendente))
col_alerts[1].metric(label="⚠️ Prazos Vencendo (3 dias)", value=len(vencendo), delta="🚨 Ação Imediata", delta_color="normal")
col_alerts[2].metric(label="❌ Prazos VENCIDOS", value=len(vencidos), delta=f"{len(vencidos)} processos críticos", delta_color="inverse")

st.markdown("---")

# --- Lista Detalhada ---
st.subheader("Lista de Pendências e Processos")

situacao_filtro = st.multiselect(
    "Filtrar por Situação",
    options=df_user['status'].unique(),
    default=['Em Andamento']
)

df_filtrado = df_user[df_user['status'].isin(situacao_filtro)].sort_values(by='prazo_retorno_inspetor', ascending=True)

# Função para estilizar a linha (alerta visual)
def style_status(row):
    color = row['cor']
    if color == 'red':
        return ['background-color: #FFDDDD'] * len(row) # Vermelho claro
    elif color == 'orange':
        return ['background-color: #FFF2CC'] * len(row) # Laranja claro
    return [''] * len(row)

st.dataframe(
    df_filtrado.drop(columns=['cor']).style.apply(style_status, axis=1),
    use_container_width=True,
    column_config={
        "ID": st.column_config.Column("ID"),
        "estabelecimento": st.column_config.Column("Estabelecimento"),
        "status_prazo": st.column_config.Column("Status do Prazo"),
        "prazo_retorno_inspetor": st.column_config.DateColumn("Prazo Inspetor", format="DD/MM/YYYY"),
        "prazo_retorno_coord": st.column_config.DateColumn("Prazo Coord.", format="DD/MM/YYYY"),
        "inspetor_id": st.column_config.Column("Inspetor")
    },
    hide_index=True
)

st.markdown("---")

# --- Ação Rápida: Conclusão de Processo ---
st.subheader("Concluir Processo")

df_active = df_user[df_user['status'] == 'Em Andamento']
if not df_active.empty:
    processos_ativos = df_active['ID'].tolist()
    processo_concluir = st.selectbox("Selecione o ID do Processo a Concluir", processos_ativos)
    
    data_conclusao = st.date_input("Data de Conclusão do Processo", date.today())
    confirm_concluir = st.button("Marcar como Concluído", type="primary")

    if confirm_concluir:
        idx = df[df['ID'] == processo_concluir].index[0]
        
        # Check se o usuário é o responsável (apenas inspetor)
        if role == 'inspetor' and df.loc[idx, 'inspetor_id'] != current_user:
            st.error("Você só pode concluir seus próprios processos ativos.")
        else:
            df.loc[idx, 'status'] = 'Concluído'
            df.loc[idx, 'data_conclusao'] = data_conclusao
            df.loc[idx, 'comentarios'] = str(df.loc[idx, 'comentarios']) + f"\n [{current_user} em {date.today().strftime('%d/%m/%Y')}]: Processo finalizado com sucesso."
            save_data(df)
            st.success(f"Processo {processo_concluir} marcado como CONCLUÍDO!")
            st.experimental_rerun()
else:
    st.info("Não há processos ativos para serem concluídos no momento.")
