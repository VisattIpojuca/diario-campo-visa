import streamlit as st
import pandas as pd
import plotly.express as px
from utils import load_data

# Verifica a permissão de acesso
if 'logged_in' not in st.session_state or st.session_state['role'] not in ['coordenador', 'gerencia']:
    st.error("Acesso negado. Esta área é restrita a Coordenadores e Gerência.")
    st.stop()

st.title("📈 Dashboard e Indicadores de Gestão")

df = load_data()

if df.empty:
    st.warning("Não há dados registrados para gerar indicadores.")
    st.stop()

# --- 1. Indicadores Chave de Desempenho (KPIs) ---
st.header("Indicadores de Produção")

total_inspecoes = len(df)
concluidos = len(df[df['status'] == 'Concluído'])
em_andamento = len(df[df['status'] == 'Em Andamento'])
perc_concluidos = f"{(concluidos / total_inspecoes * 100):.1f}%" if total_inspecoes > 0 else "0%"

col_kpi = st.columns(3)
col_kpi[0].metric("Total de Inspeções Registradas", total_inspecoes)
col_kpi[1].metric("Processos Concluídos", concluidos)
col_kpi[2].metric("Taxa de Conclusão", perc_concluidos)

st.markdown("---")

# --- 2. Gráfico de Status por Risco ---
st.header("Status dos Processos por Classificação de Risco")
df_risco = df.groupby(['risco', 'status']).size().reset_index(name='Contagem')

fig_risco = px.bar(
    df_risco, 
    x='risco', 
    y='Contagem', 
    color='status',
    title='Contagem de Processos por Risco e Status Atual',
    labels={'risco': 'Risco do Estabelecimento', 'Contagem': 'Número de Processos'},
    category_orders={"risco": ["Alto", "Médio", "Baixo"]},
    color_discrete_map={'Em Andamento': 'blue', 'Concluído': 'green', 'Indeferido': 'red'}
)
st.plotly_chart(fig_risco, use_container_width=True)

st.markdown("---")

# --- 3. Produtividade por Inspetor ---
st.header("Produtividade da Equipe")

df_prod = df.groupby('inspetor_id').size().reset_index(name='Total de Inspeções')
df_prod_status = df[df['status'] == 'Concluído'].groupby('inspetor_id').size().reset_index(name='Concluídas')

df_prod = pd.merge(df_prod, df_prod_status, on='inspetor_id', how='left').fillna(0)
df_prod['Concluídas'] = df_prod['Concluídas'].astype(int)
df_prod['Em Andamento'] = df_prod['Total de Inspeções'] - df_prod['Concluídas']

fig_prod = px.bar(
    df_prod.melt(id_vars='inspetor_id', value_vars=['Concluídas', 'Em Andamento'], var_name='Situação', value_name='Contagem'),
    x='inspetor_id',
    y='Contagem',
    color='Situação',
    title='Inspeções por Inspetor (Concluídas vs. Em Andamento)',
    color_discrete_map={'Concluídas': 'darkgreen', 'Em Andamento': 'gold'}
)
st.plotly_chart(fig_prod, use_container_width=True)

st.markdown("---")

# --- 4. Exportação de Dados ---
st.header("Exportar Dados")

@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')

csv_data = convert_df(df)

st.download_button(
    label="Download de Todos os Dados (CSV)",
    data=csv_data,
    file_name='diario_campo_visa_dados.csv',
    mime='text/csv',
    type="secondary"
)
