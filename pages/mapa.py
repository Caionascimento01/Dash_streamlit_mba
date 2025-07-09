import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
from shapely import wkt
from shapely.geometry import Polygon, MultiPolygon
import folium
from streamlit_folium import st_folium
from pathlib import Path
from folium.plugins import StripePattern

col1, col2 = st.columns([1,1])
if col1.button("🏠 Home"):
    st.switch_page("app.py")
if col2.button("🗺️ Mapa"):
    st.switch_page("pages/mapa.py")


st.set_page_config(page_title="Mapa de Reclamações", layout="wide")
st.title("🗺️ Mapa de calor - Reclamações por Estado / Município")

df_filtrado = st.session_state['df_filtrado']
gdf_estados = st.session_state.get('gdf_estados')

# --- Função para carregar o GeoDataFrame das localidades ---
@st.cache_data(ttl=3600)
def load_localidade_geodf(path):
    df = pd.read_csv(path, sep=',')  # ajuste o separador se necessário

    if 'POLYGON' not in df.columns:
        st.error(f"Coluna 'POLYGON' não encontrada. Colunas disponíveis: {df.columns.tolist()}")
        return gpd.GeoDataFrame()

    # Converte string WKT -> objetos shapely (Polygon ou MultiPolygon)
    def to_geom(s):
        try:
            return wkt.loads(s)
        except Exception as e:
            st.error(f"Erro convertendo '{s[:50]}...': {e}")
            return None

    df['geometry'] = df['POLYGON'].apply(to_geom)

    gdf = gpd.GeoDataFrame(df, geometry='geometry', crs="EPSG:4326")
    return gdf


# Seletor de localidade
st.sidebar.header("Selecione a localidade")
opcoes_estados = sorted(gdf_estados['NM_UF'].unique())
opcoes_completas = ['Todos'] + opcoes_estados
estado = st.sidebar.selectbox("Estado", options=opcoes_completas)

st.sidebar.header("Selecione o ano")
opcoes_anos = sorted(df_filtrado['ANO'].unique())
todas_opcoes = ['Todos'] + opcoes_anos
ano = st.sidebar.selectbox("Ano", options=todas_opcoes)

if ano != 'Todos':
    df_mapa = df_filtrado[df_filtrado['ANO'] == ano]
else:
    df_mapa = df_filtrado.copy()

# **Mapa do Brasil com heatmap** mostrando a quantidade de reclamações por **ano**, com granularidade por **estado ou município**.
#  > O mapa **deve conter um seletor para o ano** que será visualizado.
st.markdown("Para apresentar as informações por municípios, selecione um estado nos filtros laterais")

# Verifica se o DataFrame df_mapa está vazio
if df_mapa.empty:
    st.warning("Nenhuma reclamação encontrada para o ano selecionado. Por favor, ajuste os filtros.")
    st.stop()  # Interrompe a execução do restante do código

# Identificar a região do Brasil a ser exibida no mapa pelo estado selecionado
if estado == 'Todos':
    gdf_mapa = gdf_estados.copy()
else:
    if estado in ["Acre", "Amazonas", "Roraima", "Rondônia", "Tocantins", "Amapá", "Pará"]:
        gdf_municipios_norte = load_localidade_geodf("./datasets/gdf_municipios_norte.csv")
        gdf_mapa = gdf_municipios_norte.copy()
    elif estado in ["Alagoas", "Bahia", "Ceará", "Maranhão", "Paraíba", "Pernambuco", "Piauí", "Rio Grande do Norte", "Sergipe"]:
        gdf_municipios_nordeste = load_localidade_geodf("./datasets/gdf_municipios_nordeste.csv")
        gdf_mapa = gdf_municipios_nordeste.copy()
    elif estado in ["Distrito Federal", "Goiás", "Mato Grosso", "Mato Grosso do Sul"]:
        gdf_municipios_centro_oeste = load_localidade_geodf("./datasets/gdf_municipios_centro_oeste.csv")
        gdf_mapa = gdf_municipios_centro_oeste.copy()
    elif estado in ["Espírito Santo", "Minas Gerais", "Rio de Janeiro", "São Paulo"]:
        gdf_municipios_sudeste = load_localidade_geodf("./datasets/gdf_municipios_sudeste.csv")
        gdf_mapa = gdf_municipios_sudeste.copy()
    elif estado in ["Paraná", "Rio Grande do Sul", "Santa Catarina"]:
        gdf_municipios_sul = load_localidade_geodf("./datasets/gdf_municipios_sul.csv")
        gdf_mapa = gdf_municipios_sul.copy()
    else:
        st.error("Estado selecionado não pertence a nenhuma região reconhecida.")
        st.stop()

# Verifica se o DataFrame df_mapa está vazio
if gdf_mapa.empty:
    st.warning("Nenhuma reclamação encontrada no estado selecionado. Por favor, ajuste os filtros.")
    st.stop()  # Interrompe a execução do restante do código

if estado != 'Todos':
    df_mapa = df_mapa[df_mapa['NOME_UF'] == estado]
    gdf_municipios = gdf_mapa[gdf_mapa["NM_UF"] == estado]

    # Centralizar o mapa na área de interesse
    mapa = folium.Map(location=[gdf_municipios.geometry.centroid.y.mean(), gdf_municipios.geometry.centroid.x.mean()], zoom_start=6.3)

    # Agrupando informações dos estados
    df_mapa = df_mapa.groupby(['MUNICIPIO']).size().reset_index(name='Qtd_Reclamacoes')

    # Substituindo valores nulos
    df_mapa['Qtd_Reclamacoes'] = df_mapa['Qtd_Reclamacoes'].fillna(0).astype(int)

    # Unificando com os dados de localização de cada estado
    gdf_final = gdf_municipios.merge(df_mapa, left_on='NM_MUN', right_on='MUNICIPIO', how='left')

    cols = ['MUNICIPIO', 'NM_MUN', 'AREA_KM2', 'Qtd_Reclamacoes', 'geometry']

    gdf_final = gdf_final[cols]

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
        nan_fill_color='grey',
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

    # Substituindo valores nulos
    df_mapa['Qtd_Reclamacoes'] = df_mapa['Qtd_Reclamacoes'].fillna(0).astype(int)

    # Unificando com os dados de localização de cada estado
    gdf_final = gdf_estados.merge(df_mapa, left_on='NM_UF', right_on='NOME_UF', how='left')

    cols = ['NOME_UF', 'NM_UF', 'AREA_KM2', 'Qtd_Reclamacoes', 'geometry']

    gdf_final = gdf_final[cols]

    # Centralizar o mapa na área de interesse
    mapa = folium.Map(location=[gdf_final.geometry.centroid.y.mean(), gdf_final.geometry.centroid.x.mean()], zoom_start=4.3)

    # Simplificando a geometria para melhorar o desempenho do mapa
    gdf_final['geometry'] = gdf_final['geometry'].simplify(0.01, preserve_topology=True)

    # Adicionando as informações no mapa
    choropleth = folium.Choropleth(
        geo_data=gdf_final,
        name='choropleth',
        data=gdf_final,
        columns=['NOME_UF', 'Qtd_Reclamacoes'],
        key_on='feature.properties.NM_UF', # Chave no GeoJSON para conectar os dados
        fill_color='YlOrRd', # Nome do colormap (escala de cores)
        nan_fill_color='grey',
        nan_fill_opacity=0.4,
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Quantidade de Reclamações',
        bins=[1, 20, 40, 80, 160, 320, 660],
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

    
st_folium(mapa, width=1100, height=800, returned_objects=[])