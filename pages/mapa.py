import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
from shapely import wkt
from shapely.geometry import Polygon, MultiPolygon
import folium
from streamlit_folium import st_folium
from pathlib import Path

st.set_page_config(page_title="Mapa de Reclamações", layout="wide")
st.title("Mapa de Reclamações por Estado / Município")

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

gdf_estados = load_localidade_geodf("./datasets/gdf_estados.csv")
gdf_municipios_norte = load_localidade_geodf("./datasets/gdf_municipios_norte.csv")
gdf_municipios_nordeste = load_localidade_geodf("./datasets/gdf_municipios_nordeste.csv")
gdf_municipios_centro_oeste = load_localidade_geodf("./datasets/gdf_municipios_centro_oeste.csv")
gdf_municipios_sudeste = load_localidade_geodf("./datasets/gdf_municipios_sudeste.csv")
gdf_municipios_sul = load_localidade_geodf("./datasets/gdf_municipios_sul.csv")

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