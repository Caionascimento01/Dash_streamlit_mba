import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import folium
from streamlit_folium import st_folium  # CORREÇÃO: Usar st_folium
import nltk
from nltk.corpus import stopwords
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import gdown

# --- Configurações da página ---
st.set_page_config(
    page_title="Dash - Reclamações Carrefour",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Funções de Carregamento de Dados (Otimizadas) ---

@st.cache_data
def load_data_from_url(url, file_name, is_geo=False):
    """
    Baixa um arquivo de uma URL do Google Drive e o carrega.
    Se is_geo=True, carrega como um GeoDataFrame.
    """
    output_path = f"./{file_name}"
    
    try:
        # Baixa o arquivo
        gdown.download(url, output_path, quiet=False)
        
        # Carrega o arquivo
        if is_geo:
            df = pd.read_csv(output_path, sep=',')
            gdf = gpd.GeoDataFrame(
                df,
                geometry=gpd.GeoSeries.from_wkt(df['POLYGON']),
                crs="EPSG:4326"
            )
            return gdf
        else:
            df = pd.read_csv(output_path, sep=',', index_col=0, parse_dates=True, dayfirst=True)
            return df
            
    except Exception as e:
        st.error(f"Falha ao baixar ou carregar o arquivo '{file_name}': {e}")
        return gpd.GeoDataFrame() if is_geo else pd.DataFrame()
    
# --- Função para carregar séries temporais ---
@st.cache_data
def load_series_temporais(df):
    try:
        # Otimização: especifique o formato para pd.to_datetime
        df["TEMPO"] = pd.to_datetime(df['TEMPO'], format='%d-%m-%Y', errors='coerce')
        return df
    except FileNotFoundError:
        st.error(f"Erro: O arquivo de reclamações não foi encontrado em {df}.")
        return pd.DataFrame() # Retorna um DataFrame vazio para evitar erros posteriores
    except Exception as e:
        st.error(f"Erro ao carregar ou processar o arquivo de reclamações: {e}")
        return pd.DataFrame() # Retorna um DataFrame vazio


# --- URLs dos seus arquivos de dados ---
# AVISO: Substitua 'SEU_ID_AQUI' pelo ID correto de compartilhamento do Google Drive para cada arquivo.
GEODATA_ESTADOS_URL = 'https://drive.google.com/uc?id=13z62QLEDqVSE7mXqlhpPaRRtQhszhPDR'
GEODATA_MUNICIPIOS_URL = 'https://drive.google.com/uc?id=1a7lmiRSSzkiqgWV4lHnfXkivIK4iMUys'
RECLAMACOES_URL = 'https://drive.google.com/uc?id=1W771udGNKSk4HTTuSyw77rWn3Mw3H5An'

# --- Carregamento dos dados ---
gdf_estados = load_data_from_url(GEODATA_ESTADOS_URL, "gdf_estados.csv", is_geo=True)
gdf_municipios = load_data_from_url(GEODATA_MUNICIPIOS_URL, "gdf_municipios.csv", is_geo=True)
df_reclamacoes = load_data_from_url(RECLAMACOES_URL, "reclamacoes.csv")
df_reclamacoes = load_series_temporais(df_reclamacoes)

# --- Título do Dashboard ----
st.title("✅ Dashboard de Análise de Reclamações")
st.markdown("---")


# --- Evita que o app quebre se os dados não forem carregados ---
if df_reclamacoes.empty or gdf_municipios.empty:
    st.error("Dados essenciais não puderam ser carregados. O dashboard não pode ser exibido.")
else:
    # --- Sidebar com seletores ---
    st.sidebar.title("Filtros 🔍")
    st.sidebar.header("Selecione o período")
    data_inicio = st.sidebar.date_input("Data de Início", value=df_reclamacoes.index.min(), min_value=df_reclamacoes.index.min(), max_value=df_reclamacoes.index.max())
    data_fim = st.sidebar.date_input("Data de Fim", value=df_reclamacoes.index.max(), min_value=df_reclamacoes.index.min(), max_value=df_reclamacoes.index.max())

    df_filtrado = df_reclamacoes.loc[data_inicio:data_fim]

    st.sidebar.header("Selecione a localidade")
    opcoes_estados = ['Todos'] + sorted(gdf_municipios['NM_UF'].unique())
    estado = st.sidebar.selectbox("Estado", options=opcoes_estados)

    if estado != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['NOME_UF'] == estado]

    st.sidebar.header("Selecione a situação")
    situacoes_disponiveis = sorted(df_filtrado['STATUS'].unique())
    situacao_selecionada = st.sidebar.multiselect("Situação", options=situacoes_disponiveis)

    if situacao_selecionada:
        df_filtrado = df_filtrado[df_filtrado['STATUS'].isin(situacao_selecionada)]

# --- Gráficos temporais por reclamações ---
st.subheader(f"🔢 Reclamações por situação")
col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    container = st.container(border=True)
    container.badge("Resolvido", icon="✅", color="green")
    resolvido = df_filtrado['STATUS'].value_counts().get('Resolvido', 0)
    container.metric("", int(resolvido))

with col2:
    container = st.container(border=True)
    container.badge("Respondida", icon="📑", color="blue")
    respondida = df_filtrado['STATUS'].value_counts().get('Respondida', 0)
    container.metric("", int(respondida))

with col3:
    container = st.container(border=True)
    container.badge("Em réplica", icon="🗯️", color="violet")
    em_replica = df_filtrado['STATUS'].value_counts().get('Em réplica', 0)
    container.metric("", int(em_replica))

with col4:
    container = st.container(border=True)
    container.badge("Não Respondida", icon="‼️", color="orange")
    nao_respondida = df_filtrado['STATUS'].value_counts().get('Não respondida', 0)
    container.metric("", int(nao_respondida))

with col5:
    container = st.container(border=True)
    container.badge("Não Resolvido", icon="❌", color="red")
    nao_resolvido = df_filtrado['STATUS'].value_counts().get('Não resolvido', 0)
    container.metric("", int(nao_resolvido))

with col6:
    container = st.container(border=True)
    total_reclamacoes = df_filtrado['STATUS'].count()
    container.badge("Total", icon="📊", color="gray")
    if pd.isna(total_reclamacoes) or total_reclamacoes is None:
        total_reclamacoes = 0 # Define como 0 se for NaN ou None
    container.metric("", int(total_reclamacoes)) # Linha 153

# --- Gráfico de Linha Interativo ---
# Agrupar por DATA e STATUS, contando quantas reclamações existem
df_grouped = df_filtrado.groupby([df_filtrado['TEMPO'].dt.date, 'STATUS']).size().reset_index(name='quantidade')

df_grouped.columns = ['DATA', 'STATUS', 'quantidade']
# Converter a coluna DATA para datetime
df_grouped['DATA'] = pd.to_datetime(df_grouped['DATA'])

# Pivotar o DataFrame: linhas = datas, colunas = status, valores = quantidade
df_pivot = df_grouped.pivot(index='DATA', columns='STATUS', values='quantidade').fillna(0)

# Configurando o gráfico de linha
fig = px.line(
    df_pivot,
    title='📈 Reclamações por situação - Temporal',
    labels={
        "DATA": "Data Reclamação",      # Renomeia o eixo X
        "value": "Nº de Reclamações",      # Renomeia o eixo Y
        "STATUS": "Situação"               # Renomeia o título da legenda e das séries no hover
    }
)

# Ajustando legenda do gráfico
fig.update_layout(
    legend=dict(
        title="Situação",
        orientation="h", # 'h' para horizontal
        yanchor="top",
        y=1.1, # Coloca um pouco abaixo do gráfico
        xanchor="right",
        x=0.5
    )
)

# Configurando o eixo X para exibir datas
fig.update_xaxes(
    tickformat='%d/%m',  
    tickangle=-45        # Opcional: rotaciona os rótulos para não sobrepor
)

# Exibir o gráfico de linha interativo
st.plotly_chart(fig, use_container_width=True)


# **Frequência de reclamações por estado / município.**
st.subheader("📊 Frequência de reclamações por estado / município")

if estado != 'Todos':
    # Filtrar o DataFrame com base no estado selecionado
    df_estado = df_filtrado[df_filtrado['NOME_UF'] == estado]
    df_agrupado = df_estado.groupby(['MUNICIPIO']).size().reset_index(name='Qtd_Reclamacoes')
    df_ordenado = df_agrupado.sort_values(by='Qtd_Reclamacoes', ascending=True)
    st.write(f"Total de reclamações em {estado}: {df_ordenado['Qtd_Reclamacoes'].sum()}")
    st.bar_chart(df_ordenado, 
                 horizontal=True,
                 x_label='Município', 
                 x='MUNICIPIO', 
                 y_label='Quantidade de Reclamações', 
                 y='Qtd_Reclamacoes', 
                 use_container_width=True)

else:  
    # Agrupar por NOME_UF e contar as reclamações
    df_estado = df_filtrado.groupby(['NOME_UF']).size().reset_index(name='Qtd_Reclamacoes')
    df_ordenado = df_estado.sort_values(by='Qtd_Reclamacoes', ascending=True)
    st.bar_chart(df_ordenado, 
                 x_label='Estado', 
                 x='NOME_UF', 
                 y_label='Quantidade de Reclamações', 
                 y='Qtd_Reclamacoes', 
                 use_container_width=True)


# **Distribuição do tamanho dos textos** das reclamações (coluna `DESCRIÇÃO`).
st.subheader("📏 Distribuição do Tamanho dos Textos das Reclamações")

# Calcular o tamanho dos textos
df_filtrado['Tamanho_Texto'] = df_filtrado['DESCRICAO'].apply(lambda x: len(str(x)) if pd.notnull(x) else 0)

# Agrupar por tamanho do texto e contar as reclamações
df_tamanho_texto = df_filtrado.groupby('Tamanho_Texto').size().reset_index(name='Qtd_Reclamacoes')

# Metricas gerais
st.markdown("##### Métricas Gerais")
col1, col2, col3 = st.columns(3)
tamanho_medio = int(df_filtrado['Tamanho_Texto'].mean())
tamanho_max = int(df_filtrado['Tamanho_Texto'].max())
tamanho_min = int(df_filtrado['Tamanho_Texto'].min())

col1.metric("Tamanho Mínimo", f"{tamanho_min} caracteres")
col2.metric("Tamanho Médio", f"{tamanho_medio} caracteres")
col3.metric("Tamanho Máximo", f"{tamanho_max} caracteres")

tamanho = st.select_slider(
    "Filtre pelo intervalo de tamanho do texto:",
    options=sorted(df_filtrado['Tamanho_Texto'].unique()),
    value=(tamanho_min, tamanho_max) # Valor inicial pega o mínimo e máximo
)

# Filtrar o DataFrame principal com base na seleção do slider
df_para_plotar = df_filtrado[
    (df_filtrado['Tamanho_Texto'] >= tamanho[0]) &
    (df_filtrado['Tamanho_Texto'] <= tamanho[1])
]


if not df_para_plotar.empty:
    # O histograma é o gráfico ideal para ver a distribuição de uma variável numérica.
    fig = px.histogram(
        df_para_plotar,
        x='Tamanho_Texto',
        nbins=30, # Define o número de "barras" ou "faixas" do histograma
        title='Frequência de Reclamações por Faixa de Tamanho de Texto',
        labels={'Tamanho_Texto': 'Tamanho do Texto (em caracteres)', 'count': 'Nº de Reclamações'}
    )

    fig.update_layout(
        bargap=0.1, # Espaço entre as barras
        yaxis_title="Nº de Reclamações" # Título do eixo Y
    )

    # Configurando o eixo X para exibir datas
    fig.update_xaxes(
        tickformat='%d/%m',  
        tickangle=-45        # Opcional: rotaciona os rótulos para não sobrepor
    )
    
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Nenhuma reclamação encontrada no intervalo de tamanho selecionado.")

st.subheader("📈 Dispersão: Tamanho do Texto vs. Tempo")

if not df_filtrado.empty:
    # --- Criação do Gráfico de Dispersão com Plotly ---
    fig = px.scatter(
        df_filtrado,
        x='TEMPO',
        y='Tamanho_Texto',
        color='STATUS',  # Usa a coluna 'STATUS' para colorir os pontos
        title='Cada ponto representa uma reclamação individual. Use o filtro para analisar por status',
        labels={'Tamanho_Texto': 'Tamanho do Texto (caracteres)', 'TEMPO': 'Data da Reclamação'},
        # over_data=['DESCRICAO'], # Mostra a descrição no hover
    )

    # Customizações visuais
    fig.update_traces(
        marker=dict(size=5, opacity=0.7), # Deixa os pontos menores e um pouco transparentes
        selector=dict(mode='markers')
    )

    # Configurando o eixo X para exibir datas
    fig.update_xaxes(
        tickformat='%d/%m/%Y',  
        tickangle=-45        # Opcional: rotaciona os rótulos para não sobrepor
    )
    
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Nenhum dado para exibir com os filtros selecionados.")

# **WordCloud** com as palavras mais frequentes nos textos das descrições.
st.subheader("📝 WordCloud - Palavras mais Frequentes nas Descrições")

nltk.download('stopwords')

# Obter a lista de stopwords em português
stopwords_portugues = stopwords.words('portuguese')

novas_stopwords = ["empresa", "comprei", "loja", "não", "pra", "tive", "minha", "nao", "apenas"
                   , "ter", "bem", "bom", "muito", "pouco", "mais", "menos", "ainda", "já", "agora", "hoje"
                   , "ontem", "amanhã", "sempre", "nunca", "todo", "toda", "todos", "todas", "algum", "alguma"
                   , "alguns", "algumas", "cada", "qualquer", "quaisquer", "quem", "onde", "quando", "como", "porque"
                   , "dia", "dias", "reclame", "aqui", "problema", "já", "pois", "outro", "outra", "Carrefour"
                   , "lá", "dentro", "toda", "fiz", "R", "vez", "vou", "tudo", "porém", "então", "assim", "havia", "disse"
                   , "compra", "produto", "produtos", "serviço", "serviços", "cliente", "clientes", "deu", "falou", "sobre"
                   , "aí", "q", "após", "aí", "ir", "mesma", "passar", "forma", "levar", "comprar", "pedi", "nenhum", "volta"
                   , "voltar", "fazer", "Além", "fazendo", "favor", "deram", "chegou", "chegar", "ir", "vir", "iria", "quero"
                   , "queria", "querer", "ser", "caso", "casa", "informar", "informou", "informe", "ano", "reais", "pagar"
                   , "sendo", "nota", "falta", "faltar", "data", "novamente", "poder", "poderia", "pessoa", "absurdo"
                   , "momento", "Editado", "Editar", "hora", "falar", "pq", "mal", "colocar", "coloquei", "mal", "mau", "bem"
                   , "bom", "ficou", "fiquei", "total", "recebi", "recebeu"]

for palavra in novas_stopwords:
    stopwords_portugues.append(palavra)
# Concatenar todas as descrições em uma única string
textos = ' '.join(df_filtrado['DESCRICAO'].dropna().astype(str).tolist())

texto = " ".join(df_filtrado['DESCRICAO'].astype(str).tolist())
print(len(texto)) 
print(texto[:100])

if texto and not texto.isspace():
    
    try:
       # Gerar a nuvem de palavras
        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color='white',
            stopwords=stopwords_portugues,
            colormap='viridis', 
            max_words=50
        ).generate(texto)

        # Plotar a WordCloud
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')  # Remove os eixos
        st.pyplot(fig)
        
    except Exception as e:
        st.error(f"Ocorreu um erro ao gerar a nuvem de palavras: {e}")

else:
    st.info("Não há dados de texto suficientes para gerar a nuvem de palavras com os filtros selecionados.")


# **Mapa do Brasil com heatmap** mostrando a quantidade de reclamações por **ano**, com granularidade por **estado ou município**.
#  > O mapa **deve conter um seletor para o ano** que será visualizado.
st.subheader("🗺️ Mapa de calor - Reclamações por Estado / Município")
st.markdown("Para apresentar as informações por municípios, selecione um estado nos filtros laterais")

map_col1, map_col2 = st.columns([1, 4])
with map_col1:
    anos_disponiveis = ['Todos'] + sorted(df_filtrado.index.year.unique())
    ano_mapa = st.selectbox("Ano do Mapa", options=anos_disponiveis)

df_mapa = df_filtrado[df_filtrado.index.year == ano_mapa] if ano_mapa != 'Todos' else df_filtrado.copy()

# Define o objeto do mapa
mapa = folium.Map(location=[-15.78, -47.92], zoom_start=4)

if estado != 'Todos':
    # --- Lógica para Municípios ---
    reclamacoes_por_municipio = df_mapa.groupby('MUNICIPIO').size().reset_index(name='Qtd_Reclamacoes')
    gdf_municipios_estado = gdf_municipios[gdf_municipios['NM_UF'] == estado]
    
    gdf_final = gdf_municipios_estado.merge(reclamacoes_por_municipio, left_on='NM_MUN', right_on='MUNICIPIO', how='left')
    gdf_final['Qtd_Reclamacoes'] = gdf_final['Qtd_Reclamacoes'].fillna(0)
    
    # CORREÇÃO: Garante que o centroide seja calculado em um GeoDataFrame
    if not gdf_final.empty:
        mapa.location = [gdf_final.geometry.centroid.y.mean(), gdf_final.geometry.centroid.x.mean()]
        mapa.zoom_start = 6
    
    key_on = 'feature.properties.NM_MUN'
    columns = ['NM_MUN', 'Qtd_Reclamacoes']

else:
    # --- Lógica para Estados ---
    reclamacoes_por_estado = df_mapa.groupby('NOME_UF').size().reset_index(name='Qtd_Reclamacoes')
    gdf_final = gdf_estados.merge(reclamacoes_por_estado, on='NOME_UF', how='left')
    gdf_final['Qtd_Reclamacoes'] = gdf_final['Qtd_Reclamacoes'].fillna(0)
    key_on = 'feature.properties.NM_UF'
    columns = ['NOME_UF', 'Qtd_Reclamacoes']

# Adiciona a camada Choropleth ao mapa
if not gdf_final.empty:
    folium.Choropleth(
        geo_data=gdf_final.to_json(),
        data=gdf_final,
        columns=columns,
        key_on=key_on,
        fill_color='YlOrRd',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Quantidade de Reclamações'
    ).add_to(mapa)

# CORREÇÃO: Usa st_folium para renderizar o mapa
st_folium(mapa, use_container_width=True, height=600)

### Fim do código