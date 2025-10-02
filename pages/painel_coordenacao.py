import streamlit as st
import pandas as pd
from utils import load_data, save_data, get_deadline_status
from datetime import date

# Verifica a permissão de acesso
if 'logged_in' not in st.session_state or st.session_state['role'] not in ['coordenador', 'gerencia']:
    st.error("Acesso negado. Esta área é restrita a Coordenadores e Gerência.")
    st.stop()

st.title("👁️ Painel de Acompanhamento da Coordenação")

df = load_data()

# Aplica a lógica de status de prazo
df['status_prazo'], df['cor'] = zip(*df.apply(get_deadline_status, axis=1))

# --- Dashboard de Alertas da Equipe ---
df_pendente = df[df['status'] == 'Em Andamento']

vencidos = df_pendente[df_pendente['cor'] == 'red']
vencendo = df_pendente[df_pendente['cor'] == 'orange']

col_alerts = st.columns(3)
col_alerts[0].metric(label="Processos Em Andamento", value=len(df_pendente))
col_alerts[1].metric(label="⚠️ Prazos Vencendo (Equipe)", value=len(vencendo), delta_color="normal")
col_alerts[2].metric(label="❌ Prazos VENCIDOS (Equipe)", value=len(vencidos), delta=f"{len(vencidos)} processos críticos", delta_color="inverse")

st.markdown("---")

# --- Tabela de Gestão (Todos os Processos) ---
st.subheader("Tabela de Processos Ativos")

# Filtros
col_f1, col_f2 = st.columns(2)
inspetor_filtro = col_f1.selectbox("Filtrar por Inspetor", options=['Todos'] + list(df['inspetor_id'].unique()))
status_filtro = col_f2.multiselect("Filtrar por Status", options=df['status'].unique(), default=['Em Andamento'])

df_filtrado = df[df['status'].isin(status_filtro)]

if inspetor_filtro != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['inspetor_id'] == inspetor_filtro]

# Função de estilo para destaque
def style_status(row):
    color = row['cor']
    if color == 'red':
        return ['background-color: #FFDDDD'] * len(row) 
    elif color == 'orange':
        return ['background-color: #FFF2CC'] * len(row)
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
    },
    hide_index=True
)

st.markdown("---")

# --- Gestão de Prazos e Comentários (Coordenação) ---
st.subheader("Ações de Coordenação: Editar Prazo ou Comentar")

col_edit_1, col_edit_2 = st.columns([1, 2])

# Usa selectbox para garantir que só IDs ativos sejam selecionáveis
active_ids = df_pendente['ID'].tolist()
processo_edit = col_edit_1.selectbox("ID do Processo para Edição", active_ids)

if processo_edit and processo_edit in df['ID'].values:
    idx_edit = df[df['ID'] == processo_edit].index[0]
    
    # Busca o prazo atual ou usa o de hoje como default
    prazo_atual_coord = df.loc[idx_edit, 'prazo_retorno_coord']
    if pd.isna(prazo_atual_coord):
        # Se não houver prazo de coordenação, usa o prazo do inspetor ou hoje
        prazo_insp = df.loc[idx_edit, 'prazo_retorno_inspetor']
        prazo_ref = prazo_insp if not pd.isna(prazo_insp) else date.today()
    else:
        prazo_ref = prazo_atual_coord

    novo_prazo_coord = col_edit_1.date_input(
        "Novo Prazo Obrigatório da Coordenação", 
        prazo_ref, 
        min_value=date.today()
    )

    novo_comentario = col_edit_2.text_area("Adicionar Comentário Interno", placeholder="Ex: Solicitar mais detalhes sobre o CNPJ.", height=150)

    salvar_edicao = st.button("Salvar Edição de Prazo/Comentário", type="primary")

    if salvar_edicao:
        # 1. Atualiza Prazo de Coordenação
        df.loc[idx_edit, 'prazo_retorno_coord'] = novo_prazo_coord
        
        # 2. Adiciona Comentário ao Histórico
        if novo_comentario:
            comentario_novo = f"\n [{st.session_state['username']} em {date.today().strftime('%d/%m/%Y')} (COORD)]: {novo_comentario}"
            current_comments = str(df.loc[idx_edit, 'comentarios'])
            df.loc[idx_edit, 'comentarios'] = current_comments + comentario_novo
        
        save_data(df)
        st.success(f"Processo {processo_edit} atualizado com novo prazo ({novo_prazo_coord.strftime('%d/%m/%Y')}) e comentários!")
        st.experimental_rerun()
        
    st.subheader(f"Histórico de Comentários (Processo {processo_edit})")
    st.text(df.loc[idx_edit, 'comentarios'])
else:
    st.warning("Não há processos ativos para serem editados.")
