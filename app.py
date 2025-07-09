import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
from shapely import wkt
from shapely.geometry import Polygon, MultiPolygon
import plotly.express as px
import folium
import ast
from streamlit_folium import st_folium
import nltk
from nltk.corpus import stopwords as nltk_stopwords
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from pathlib import Path

# --- Configurações da página ---
st.set_page_config(
    page_title="Dash - Reclamações Carrefour",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Função para carregar o GeoDataFrame das localidades ---
@st.cache_data(ttl=3600)
def load_localidade_geodf(path):
    df = pd.read_csv(path, sep=';')  # ou ',' se for o caso

    def to_geom(s):
        try:
            geom = wkt.loads(s)
            if isinstance(geom, (Polygon, MultiPolygon)):
                return geom
            else:
                raise ValueError(f"Tipo inválido: {geom.geom_type}")
        except Exception as e:
            st.error(f"Erro convertendo geometria: {e}")
            return None

    df['geometry'] = df['POLYGON'].apply(to_geom)
    return gpd.GeoDataFrame(df, geometry='geometry', crs="EPSG:4326")

# --- Função para carregar séries temporais ---
@st.cache_data(show_spinner=False, ttl=3600)
def load_series_temporais(path):
    try:
        df = pd.read_csv(path, sep=',', index_col=0, parse_dates=['TEMPO'], dayfirst=True)
        # Otimização: especifique o formato para pd.to_datetime
        df["TEMPO"] = pd.to_datetime(df['TEMPO'], format='%d-%m-%Y', errors='coerce')
        return df
    except FileNotFoundError:
        st.error(f"Erro: O arquivo de reclamações não foi encontrado em {path}.")
        return pd.DataFrame() # Retorna um DataFrame vazio para evitar erros posteriores
    except Exception as e:
        st.error(f"Erro ao carregar ou processar o arquivo de reclamações: {e}")
        return pd.DataFrame() # Retorna um DataFrame vazio


# --- Carregamento dos dados ---
# gdf_estados = load_localidade_geodf("..\datasets\gdf_estados.csv")
# gdf_municipios = load_localidade_geodf("..\datasets\gdf_municipios.csv")
# df_reclamacoes = load_series_temporais('..\datasets\RECLAMEAQUI_CARREFUOR_CLS.csv')

# --- Carregamento dos dados ---
df_reclamacoes = load_series_temporais('./datasets/RECLAMEAQUI_CARREFUOR_CLS.csv')
gdf_estados = load_localidade_geodf("./datasets/gdf_estados.csv")
gdf_municipios_norte = load_localidade_geodf("./datasets/gdf_municipios_norte.csv")
gdf_municipios_nordeste = load_localidade_geodf("./datasets/gdf_municipios_nordeste.csv")
gdf_municipios_centro_oeste = load_localidade_geodf("./datasets/gdf_municipios_centro_oeste.csv")
gdf_municipios_sudeste = load_localidade_geodf("./datasets/gdf_municipios_sudeste.csv")
gdf_municipios_sul = load_localidade_geodf("./datasets/gdf_municipios_sul.csv")


# --- Título do Dashboard ----
st.title("✅ Dashboard de Análise de Reclamações")
st.markdown("---")

# --- Sidebar com seletores ---
st.sidebar.title("Filtros 🔍")

# Seletor de periodo
st.sidebar.header("Selecione o período")
data_inicio = st.sidebar.date_input("Data de Início",
                                     value=df_reclamacoes["TEMPO"].min(),
                                     min_value=df_reclamacoes["TEMPO"].min(),
                                     max_value=df_reclamacoes["TEMPO"].max(),
                                     format="DD-MM-YYYY")
data_inicio = pd.to_datetime(data_inicio, format='%d-%m-%Y', errors='coerce')

data_fim = st.sidebar.date_input("Data de Fim", 
                                  value=df_reclamacoes["TEMPO"].max(), 
                                  min_value=df_reclamacoes["TEMPO"].min(), 
                                  max_value=df_reclamacoes["TEMPO"].max(), 
                                  format="DD-MM-YYYY")
data_fim = pd.to_datetime(data_fim, format='%d-%m-%Y', errors='coerce')

# Seletor de localidade
st.sidebar.header("Selecione a localidade")
opcoes_estados = sorted(gdf_estados['NM_UF'].unique())
opcoes_completas = ['Todos'] + opcoes_estados
estado = st.sidebar.selectbox("Estado", options=opcoes_completas)

# Seletor de situação
st.sidebar.header("Selecione a situação")
situacao_selecionada = st.sidebar.multiselect("Situação", options=sorted(df_reclamacoes['STATUS'].unique().tolist()))

# Filtrar o DataFrame com base nas datas selecionadas
mask = (
    (df_reclamacoes["TEMPO"] >= data_inicio) &
    (df_reclamacoes["TEMPO"] <= data_fim)
)

if estado != "Todos":
    mask &= (df_reclamacoes["NOME_UF"] == estado)

if situacao_selecionada:
    mask &= df_reclamacoes["STATUS"].isin(situacao_selecionada)

df_filtrado = df_reclamacoes.loc[mask]

# --- Gráficos temporais por reclamações ---
st.subheader(f"🔢 Reclamações por situação")
col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    container = st.container(border=True)
    container.badge("Resolvido", icon="✅", color="green")
    resolvido = df_filtrado['STATUS'].value_counts().get('Resolvido', 0)
    container.metric("Resolvido", int(resolvido))

with col2:
    container = st.container(border=True)
    container.badge("Respondida", icon="📑", color="blue")
    respondida = df_filtrado['STATUS'].value_counts().get('Respondida', 0)
    container.metric("Respondida", int(respondida))

with col3:
    container = st.container(border=True)
    container.badge("Em réplica", icon="🗯️", color="violet")
    em_replica = df_filtrado['STATUS'].value_counts().get('Em réplica', 0)
    container.metric("Em réplica", int(em_replica))

with col4:
    container = st.container(border=True)
    container.badge("Não Respondida", icon="‼️", color="orange")
    nao_respondida = df_filtrado['STATUS'].value_counts().get('Não respondida', 0)
    container.metric("Não Respondida", int(nao_respondida))

with col5:
    container = st.container(border=True)
    container.badge("Não Resolvido", icon="❌", color="red")
    nao_resolvido = df_filtrado['STATUS'].value_counts().get('Não resolvido', 0)
    container.metric("Não Resolvido", int(nao_resolvido))

with col6:
    container = st.container(border=True)
    total_reclamacoes = df_filtrado['STATUS'].count()
    container.badge("Total", icon="📊", color="gray")
    if pd.isna(total_reclamacoes) or total_reclamacoes is None:
        total_reclamacoes = 0 # Define como 0 se for NaN ou None
    container.metric("Total", int(total_reclamacoes)) # Linha 153

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
# df_filtrado['Tamanho_Texto'] = df_filtrado['DESCRICAO'].apply(lambda x: len(str(x)) if pd.notnull(x) else 0)
df_fil = df_filtrado.copy()
df_fil['Tamanho_Texto'] = df_fil['DESCRICAO'].fillna("").str.len()

# Agrupar por tamanho do texto e contar as reclamações
df_tamanho_texto = df_fil.groupby('Tamanho_Texto').size().reset_index(name='Qtd_Reclamacoes')

# Metricas gerais
st.markdown("##### Métricas Gerais")
col1, col2, col3 = st.columns(3)
tamanho_medio = int(df_fil['Tamanho_Texto'].mean())
tamanho_max = int(df_fil['Tamanho_Texto'].max())
tamanho_min = int(df_fil['Tamanho_Texto'].min())

col1.metric("Tamanho Mínimo", f"{tamanho_min} caracteres")
col2.metric("Tamanho Médio", f"{tamanho_medio} caracteres")
col3.metric("Tamanho Máximo", f"{tamanho_max} caracteres")

tamanho = st.select_slider(
    "Filtre pelo intervalo de tamanho do texto:",
    options=sorted(df_fil['Tamanho_Texto'].unique()),
    value=(tamanho_min, tamanho_max) # Valor inicial pega o mínimo e máximo
)

# Filtrar o DataFrame principal com base na seleção do slider
mask = (
    (df_fil['Tamanho_Texto'] >= tamanho[0]) &
    (df_fil['Tamanho_Texto'] <= tamanho[1])
)
df_para_plotar = df_fil.loc[mask]

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
    #fig.update_xaxes(
    #    tickformat='%d/%m',  
    #    tickangle=-45        # Opcional: rotaciona os rótulos para não sobrepor
    #)
    
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Nenhuma reclamação encontrada no intervalo de tamanho selecionado.")

st.subheader("📈 Dispersão: Tamanho do Texto vs. Tempo")

if not df_fil.empty:
    # --- Criação do Gráfico de Dispersão com Plotly ---
    fig = px.scatter(
        df_fil,
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

# -- Utilizando o NLTK para stopwords em português --
# Aponta para o diretório dentro do repositório
nltk.data.path.append(str(Path(__file__).parent / "nltk_data"))

# 3) agora tente carregar as stopwords
#try:
#    stopwords = set(stopwords.words("portuguese"))
#except LookupError:
#    st.warning("Stopwords do NLTK não encontradas. Usando lista vazia.")
#    stopwords = set()

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
                   , "bom", "ficou", "fiquei", "total", "recebi", "recebeu", "nada", "nenhuma", "nenhum", "nada", "tudo"
                   , "falei", "falaram", "dizer", "dizendo", "dizem", "disseram", "tempo", "coisa", "coisas", "ocorrido"
                   , "ocorreram"]

#for palavra in novas_stopwords:
#    stopwords.append(palavra)

# Agora isso deve funcionar sem precisar baixar
#stopwords = set(stopwords.words("portuguese"))
stop_pt = set(nltk_stopwords.words("portuguese")) | set(novas_stopwords)

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
            stopwords=stop_pt,
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

col1, col2, col3 = st.columns(3)

with col1:
    # Seletor de ano para mapa
    opcoes_anos = sorted(df_filtrado['ANO'].unique())
    todas_opcoes = ['Todos'] + opcoes_anos
    ano = st.selectbox("Selecione o ano:", options=todas_opcoes)

if ano != 'Todos':
    df_mapa = df_filtrado[df_filtrado['ANO'] == ano]
else:
    df_mapa = df_filtrado.copy()

# Verifica se o DataFrame df_mapa está vazio
if df_mapa.empty:
    st.warning("Nenhuma reclamação encontrada para o ano selecionado. Por favor, ajuste os filtros.")
    st.stop()  # Interrompe a execução do restante do código

# Identificar a região do Brasil a ser exibida no mapa pelo estado selecionado
if estado == 'Todos':
    gdf_mapa = gdf_estados.copy()
else:
    if estado in ["ACRE", "AMAZONAS", "RORAIMA", "RONDONIA", "TOCANTINS"]:
        gdf_mapa = gdf_municipios_norte.copy()
    elif estado in ["ALAGOAS", "BAHIA", "CEARA", "MARANHAO", "PARAIBA", "PERNAMBUCO", "PIAUI", "RIO GRANDE DO NORTE", "SERGIPE"]:
        gdf_mapa = gdf_municipios_nordeste.copy()
    elif estado in ["DISTRITO FEDERAL", "GOIAS", "MATO GROSSO", "MATO GROSSO DO SUL"]:
        gdf_mapa = gdf_municipios_centro_oeste.copy()
    elif estado in ["ESPIRITO SANTO", "MINAS GERAIS", "RIO DE JANEIRO", "SAO PAULO"]:
        gdf_mapa = gdf_municipios_sudeste.copy()
    elif estado in ["PARANA", "RIO GRANDE DO SUL", "SANTA CATARINA"]:
        gdf_mapa = gdf_municipios_sul.copy()
    else:
        st.error("Estado selecionado não pertence a nenhuma região reconhecida.")
        st.stop()

# Verifica se o DataFrame df_mapa está vazio
if gdf_mapa.empty:
    st.warning("Nenhuma reclamação encontrada no estado selecionado. Por favor, ajuste os filtros.")
    st.stop()  # Interrompe a execução do restante do código

# Centralizar mapa
mapa = folium.Map(
    location=[-14.2350, -51.9253],
    zoom_start=4.3
)

if estado != 'Todos':
    df_mapa = df_mapa[df_mapa['NOME_UF'] == estado]
    gdf_mapa = gdf_mapa[gdf_mapa["NM_UF"] == estado]

    # Agrupando informações dos estados
    df_mapa = df_mapa.groupby(['MUNICIPIO']).size().reset_index(name='Qtd_Reclamacoes')

    # Unificando com os dados de localização de cada estado
    gdf_final = gdf_mapa.merge(df_mapa, left_on='NM_MUN', right_on='MUNICIPIO', how='left')

    # Substituindo valores nulos
    gdf_final['Qtd_Reclamacoes'] = gdf_final['Qtd_Reclamacoes'].fillna(0).astype(int)

    # Simplificando a geometria para melhorar o desempenho do mapa
    gdf_final['geometry'] = gdf_final['geometry'].simplify(0.01, preserve_topology=True)

    # Adicionando as informações no mapa
    choropleth = folium.Choropleth(
        geo_data=gdf_final,
        name='choropleth',
        data=gdf_final,
        columns=['MUNICIPIO', 'Qtd_Reclamacoes'],
        key_on='feature.properties.NM_MUN', # Chave no GeoJSON para conectar os dados
        fill_color='YlOrRd', # Nome do colormap (escala de cores)
        nan_fill_color='gray',
        nan_fill_opacity=0.4,
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Quantidade de Reclamações',
        highlight=True, # Destaca a área ao passar o mouse
    )

    choropleth.add_to(mapa)

    # --- Adicionar Tooltips Interativos (Informação no Hover) ---
    tooltip = folium.features.GeoJsonTooltip(
        fields=['NM_MUN', 'AREA_KM2', 'Qtd_Reclamacoes'],
        aliases=['Município:', 'Área (Km²):', 'N° de Reclamações:'],
        style="background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;",
        sticky=True
    )

    tooltip.add_to(choropleth.geojson)

else:

    # Agrupando informações dos estados
    df_mapa = df_mapa.groupby(['NOME_UF']).size().reset_index(name='Qtd_Reclamacoes')

    # Unificando com os dados de localização de cada estado
    gdf_final = gdf_mapa.merge(df_mapa, left_on='NM_UF', right_on='NOME_UF', how='left')

    # Substituindo valores nulos
    gdf_final['Qtd_Reclamacoes'] = gdf_final['Qtd_Reclamacoes'].fillna(0).astype(int)

    # Adicionando as informações no mapa
    choropleth = folium.Choropleth(
        geo_data=gdf_final,
        name='choropleth',
        data=gdf_final,
        columns=['NOME_UF', 'Qtd_Reclamacoes'],
        key_on='feature.properties.NM_UF', # Chave no GeoJSON para conectar os dados
        fill_color='YlOrRd', # Nome do colormap (escala de cores)
        nan_fill_color='gray',
        nan_fill_opacity=0.4,
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Quantidade de Reclamações',
        bins=8,
        highlight=True, # Destaca a área ao passar o mouse
    )

    choropleth.add_to(mapa)

    # --- Adicionar Tooltips Interativos (Informação no Hover) ---
    tooltip = folium.features.GeoJsonTooltip(
        fields=['NM_UF', 'AREA_KM2', 'Qtd_Reclamacoes'],
        aliases=['Estado:', 'Área (Km²):', 'N° de Reclamações:'],
        style="background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;",
        sticky=True
    )

    tooltip.add_to(choropleth.geojson)

    
st_folium(mapa, width=1000, height=600)

### Fim do código