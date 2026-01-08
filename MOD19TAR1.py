# Imports
import pandas            as pd
import streamlit         as st
import seaborn           as sns
import matplotlib.pyplot as plt
from PIL                 import Image
from io                  import BytesIO

# Configuração de estilo Seaborn
custom_params = {"axes.spines.right": False, "axes.spines.top": False}
sns.set_theme(style="ticks", rc=custom_params)

# --- FUNÇÕES DE APOIO ---

# Função para ler os dados com cache moderno
@st.cache_data(show_spinner=True)
def load_data(file_data):
    try:
        return pd.read_csv(file_data, sep=';')
    except:
        return pd.read_excel(file_data)

# Função para filtrar multiseleção
@st.cache_data
def multiselect_filter(relatorio, col, selecionados):
    if 'all' in selecionados or not selecionados:
        return relatorio
    else:
        return relatorio[relatorio[col].isin(selecionados)].reset_index(drop=True)

# Função para converter para excel corrigida
@st.cache_data
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

# --- APLICAÇÃO PRINCIPAL ---

def main():
    st.set_page_config(
        page_title='Telemarketing Analysis',
        page_icon='../img/telmarketing_icon.png',
        layout="wide",
        initial_sidebar_state='expanded'
    )

    st.write('# Telemarketing Analysis')
    st.markdown("---")
    
    # Carregamento da imagem lateral
    try:
        image = Image.open("../img/Bank-Branding.jpg")
        st.sidebar.image(image)
    except:
        st.sidebar.warning("Imagem lateral não encontrada.")

    st.sidebar.write("## Suba o arquivo")
    data_file_1 = st.sidebar.file_uploader("Bank marketing data", type=['csv','xlsx'])

    if data_file_1 is not None:
        bank_raw = load_data(data_file_1)
        bank = bank_raw.copy()

        st.write('## Antes dos filtros')
        st.write(bank_raw.head())

        with st.sidebar.form(key='my_form'):
            graph_type = st.radio('Tipo de gráfico:', ('Barras', 'Pizza'))
        
            # Filtro de Idade
            max_age = int(bank.age.max())
            min_age = int(bank.age.min())
            idades = st.slider(label='Idade', min_value=min_age, max_value=max_age, value=(min_age, max_age), step=1)

            # Filtros Categóricos
            def create_multiselect(label, column):
                options = bank[column].unique().tolist()
                return st.multiselect(label, options + ['all'], ['all'])

            jobs_selected = create_multiselect("Profissão", 'job')
            marital_selected = create_multiselect("Estado civil", 'marital')
            default_selected = create_multiselect("Default", 'default')
            housing_selected = create_multiselect("Financiamento imob?", 'housing')
            loan_selected = create_multiselect("Empréstimo?", 'loan')
            contact_selected = create_multiselect("Meio de contato", 'contact')
            month_selected = create_multiselect("Mês do contato", 'month')
            day_selected = create_multiselect("Dia da semana", 'day_of_week')

            # Processamento dos filtros
            bank = (bank.query("age >= @idades[0] and age <= @idades[1]")
                        .pipe(multiselect_filter, 'job', jobs_selected)
                        .pipe(multiselect_filter, 'marital', marital_selected)
                        .pipe(multiselect_filter, 'default', default_selected)
                        .pipe(multiselect_filter, 'housing', housing_selected)
                        .pipe(multiselect_filter, 'loan', loan_selected)
                        .pipe(multiselect_filter, 'contact', contact_selected)
                        .pipe(multiselect_filter, 'month', month_selected)
                        .pipe(multiselect_filter, 'day_of_week', day_selected))

            submit_button = st.form_submit_button(label='Aplicar')
        
        st.write('## Após os filtros')
        st.write(bank.head())
        
        # Download da tabela filtrada
        df_xlsx = to_excel(bank)
        st.download_button(label='📥 Download tabela filtrada em EXCEL', data=df_xlsx, file_name='bank_filtered.xlsx')
        st.markdown("---")

        # --- PREPARAÇÃO DOS DADOS PARA GRÁFICOS ---
        # Ajuste crucial para evitar o KeyError: 'y'
        bank_raw_target_perc = bank_raw.y.value_counts(normalize=True).to_frame()
        bank_raw_target_perc.columns = ['proporcao']
        bank_raw_target_perc = bank_raw_target_perc.sort_index()
        
        try:
            bank_target_perc = bank.y.value_counts(normalize=True).to_frame()
            bank_target_perc.columns = ['proporcao']
            bank_target_perc = bank_target_perc.sort_index()
        except:
            st.error('Erro ao gerar proporções com os filtros atuais.')
            bank_target_perc = pd.DataFrame()

        # Download das tabelas de proporção
        col1, col2 = st.columns(2)
        col1.write('### Proporção original')
        col1.write(bank_raw_target_perc)
        col1.download_button(label='📥 Download Original', data=to_excel(bank_raw_target_perc), file_name='bank_raw_y.xlsx')
        
        col2.write('### Proporção filtrada')
        col2.write(bank_target_perc)
        if not bank_target_perc.empty:
            col2.download_button(label='📥 Download Filtrada', data=to_excel(bank_target_perc), file_name='bank_y.xlsx')
        
        st.markdown("---")
        st.write('## Comparação Visual')

        # --- PLOTS ---
        fig, ax = plt.subplots(1, 2, figsize=(10, 5))

        if graph_type == 'Barras':
            sns.barplot(x=bank_raw_target_perc.index, y='proporcao', data=bank_raw_target_perc, ax=ax[0])
            ax[0].bar_label(ax[0].containers[0])
            ax[0].set_title('Dados brutos', fontweight="bold")
            
            if not bank_target_perc.empty:
                sns.barplot(x=bank_target_perc.index, y='proporcao', data=bank_target_perc, ax=ax[1])
                ax[1].bar_label(ax[1].containers[0])
                ax[1].set_title('Dados filtrados', fontweight="bold")
        else:
            bank_raw_target_perc.plot(kind='pie', autopct='%.2f%%', y='proporcao', ax=ax[0], legend=False)
            ax[0].set_title('Dados brutos', fontweight="bold")
            ax[0].set_ylabel('')
            
            if not bank_target_perc.empty:
                bank_target_perc.plot(kind='pie', autopct='%.2f%%', y='proporcao', ax=ax[1], legend=False)
                ax[1].set_title('Dados filtrados', fontweight="bold")
                ax[1].set_ylabel('')

        st.pyplot(fig)

if __name__ == '__main__':
    main()

    
