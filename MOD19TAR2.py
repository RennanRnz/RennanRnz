# Imports
import pandas            as pd
import streamlit         as st
import seaborn           as sns
import matplotlib.pyplot as plt
from PIL                 import Image
from io                  import BytesIO

# --- 1. ESTILIZAÇÃO CUSTOMIZADA (CSS) ---
def local_css():
    st.markdown("""
        <style>
        /* Estilo para o botão de Aplicar */
        div.stButton > button:first-child {
            background-color: #004b8d;
            color: white;
            border-radius: 5px;
            width: 100%;
            border: none;
            padding: 0.5rem;
            font-weight: bold;
            transition: 0.3s;
        }
        div.stButton > button:first-child:hover {
            background-color: #003366;
            border: none;
            color: #ffcc00;
        }
        </style>
    """, unsafe_allow_html=True)

# Configuração de estilo Seaborn para os gráficos
custom_params = {"axes.spines.right": False, "axes.spines.top": False}
sns.set_theme(style="ticks", rc=custom_params)

# --- 2. FUNÇÕES DE APOIO (COM CACHE MODERNO) ---

@st.cache_data(show_spinner=True)
def load_data(file_data):
    try:
        return pd.read_csv(file_data, sep=';')
    except:
        return pd.read_excel(file_data)

@st.cache_data
def multiselect_filter(relatorio, col, selecionados):
    if 'all' in selecionados or not selecionados:
        return relatorio
    else:
        return relatorio[relatorio[col].isin(selecionados)].reset_index(drop=True)

@st.cache_data
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

# --- 3. APLICAÇÃO PRINCIPAL ---

def main():
    # REGRA DE OURO: set_page_config deve ser o PRIMEIRO comando Streamlit
    st.set_page_config(
        page_title='Telemarketing Analysis',
        page_icon='../img/telmarketing_icon.png',
        layout="wide",
        initial_sidebar_state='expanded'
    )
    
    # Agora podemos chamar o CSS e outros elementos
    local_css()

    st.write('# Telemarketing Analysis')
    st.markdown("---")
    
    # Sidebar com imagem e upload
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

        # FORMULÁRIO DE FILTROS NA SIDEBAR
        with st.sidebar.form(key='my_form'):
            graph_type = st.radio('Tipo de gráfico:', ('Barras', 'Pizza'))
        
            max_age = int(bank.age.max())
            min_age = int(bank.age.min())
            idades = st.slider(label='Idade', min_value=min_age, max_value=max_age, value=(min_age, max_age))

            def create_multiselect(label, column):
                options = sorted(bank[column].unique().tolist())
                return st.multiselect(label, options + ['all'], ['all'])

            jobs_selected = create_multiselect("Profissão", 'job')
            marital_selected = create_multiselect("Estado civil", 'marital')
            default_selected = create_multiselect("Default", 'default')
            housing_selected = create_multiselect("Financiamento imob?", 'housing')
            loan_selected = create_multiselect("Empréstimo?", 'loan')
            contact_selected = create_multiselect("Meio de contato", 'contact')
            month_selected = create_multiselect("Mês do contato", 'month')
            day_selected = create_multiselect("Dia da semana", 'day_of_week')

            submit_button = st.form_submit_button(label='Aplicar Filtros')

        # PROCESSAMENTO DOS FILTROS (MÉTODO PIPE)
        bank = (bank.query("age >= @idades[0] and age <= @idades[1]")
                    .pipe(multiselect_filter, 'job', jobs_selected)
                    .pipe(multiselect_filter, 'marital', marital_selected)
                    .pipe(multiselect_filter, 'default', default_selected)
                    .pipe(multiselect_filter, 'housing', housing_selected)
                    .pipe(multiselect_filter, 'loan', loan_selected)
                    .pipe(multiselect_filter, 'contact', contact_selected)
                    .pipe(multiselect_filter, 'month', month_selected)
                    .pipe(multiselect_filter, 'day_of_week', day_selected))

        # --- 4. VERIFICAÇÃO DE DADOS FILTRADOS (PROGRAMAÇÃO DEFENSIVA) ---
        if len(bank) > 0:
            st.write('## Resultados da Análise')
            
            # Exibição de métricas rápidas (Opcional, mas recomendado)
            c1, c2 = st.columns(2)
            c1.metric("Total de Registros", len(bank))
            c2.metric("Taxa de Aceite", f"{(bank.y == 'yes').mean():.2%}")

            st.dataframe(bank.head(), use_container_width=True)
            
            # Botão de download
            df_xlsx = to_excel(bank)
            st.download_button(label='📥 Download tabela filtrada em EXCEL', 
                             data=df_xlsx, 
                             file_name='bank_filtered.xlsx')
            
            st.markdown("---")

            # --- PREPARAÇÃO DOS DADOS PARA GRÁFICOS ---
            bank_raw_target_perc = bank_raw.y.value_counts(normalize=True).to_frame()
            bank_raw_target_perc.columns = ['proporcao']
            bank_raw_target_perc = bank_raw_target_perc.sort_index()
            
            bank_target_perc = bank.y.value_counts(normalize=True).to_frame()
            bank_target_perc.columns = ['proporcao']
            bank_target_perc = bank_target_perc.sort_index()

            col_g1, col_g2 = st.columns(2)
            with col_g1:
                st.write('### Proporção Original')
                st.write(bank_raw_target_perc)
            with col_g2:
                st.write('### Proporção Filtrada')
                st.write(bank_target_perc)
            
            st.markdown("---")
            
            # --- RENDERIZAÇÃO DOS GRÁFICOS ---
            fig, ax = plt.subplots(1, 2, figsize=(10, 5))

            if graph_type == 'Barras':
                sns.barplot(x=bank_raw_target_perc.index, y='proporcao', data=bank_raw_target_perc, ax=ax[0])
                ax[0].set_title('Dados Brutos', fontweight="bold")
                ax[0].bar_label(ax[0].containers[0])
                
                sns.barplot(x=bank_target_perc.index, y='proporcao', data=bank_target_perc, ax=ax[1])
                ax[1].set_title('Dados Filtrados', fontweight="bold")
                ax[1].bar_label(ax[1].containers[0])
            else:
                bank_raw_target_perc.plot(kind='pie', autopct='%.2f%%', y='proporcao', ax=ax[0], legend=False)
                ax[0].set_title('Dados Brutos', fontweight="bold")
                
                bank_target_perc.plot(kind='pie', autopct='%.2f%%', y='proporcao', ax=ax[1], legend=False)
                ax[1].set_title('Dados Filtrados', fontweight="bold")
            
            for a in ax: a.set_ylabel('') # Remove label lateral chata
            st.pyplot(fig)

        else:
            # Caso o filtro não encontre nada
            st.error("### ⚠️ Nenhum dado encontrado!")
            st.warning("Os filtros selecionados resultaram em uma lista vazia. Tente ajustar as opções na barra lateral.")

if __name__ == '__main__':
    main()
    
