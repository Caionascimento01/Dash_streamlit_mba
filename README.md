# Dashboard de Análise de Reclamações - Carrefour
Este projeto consiste em um dashboard interativo desenvolvido com Streamlit para a análise de dados de reclamações de clientes da empresa Carrefour, extraídos do site Reclame Aqui. A ferramenta permite a visualização dinâmica de diversas métricas e tendências, facilitando a compreensão dos principais problemas enfrentados pelos consumidores.

## 📋 Objetivo
O objetivo principal deste dashboard é fornecer uma visão clara e detalhada sobre o panorama das reclamações registradas contra o Carrefour. Através de filtros interativos e visualizações de dados, a aplicação permite que usuários, como analistas de dados ou gestores de atendimento, possam:

- Identificar os principais motivos de insatisfação dos clientes.
- Analisar a distribuição geográfica das reclamações.
- Acompanhar a evolução das queixas ao longo do tempo.
- Avaliar a eficiência da equipe de atendimento na resolução dos problemas.

## 🚀 Tecnologias Utilizadas
- **Python:** Linguagem principal do projeto.
- **Streamlit:** Framework para a criação do dashboard web interativo.
- **Pandas:** Para manipulação e análise dos dados.
- **Plotly Express:** Para a criação de gráficos interativos (linha, barras, dispersão, histograma).
- **GeoPandas & Shapely:** Para processamento e manipulação de dados geoespaciais.
- **Folium:** Para a criação de mapas coropléticos interativos.
- **WordCloud:** Para a geração da nuvem de palavras.
- **NLTK:** Para processamento de linguagem natural, especificamente para a remoção de stopwords em português.

## 📊 Gráficos e Visualizações
O dashboard é composto por várias seções, cada uma com um propósito analítico específico:

### 1. Métricas Gerais por Situação
- **O que faz:** Apresenta cartões com o número total de reclamações para cada status: Resolvido, Respondida, Em réplica, Não respondida, Não resolvido e o Total.
- **Objetivo:** Oferecer uma visão geral e rápida do volume de reclamações e da performance do atendimento.

### 2. Reclamações por Situação - Análise Temporal
- Gráfico: Gráfico de Linhas.
- O que faz: Mostra a quantidade de reclamações ao longo do tempo, com linhas separadas por cor para cada status.
- Objetivo: Permitir a identificação de picos de reclamações, sazonalidades e a evolução da capacidade de resposta da empresa ao longo do período selecionado.

### 3. Frequência de Reclamações por Localidade
- Gráfico: Gráfico de Barras.
- O que faz: Exibe a quantidade de reclamações por estado. Se um estado específico for selecionado no filtro, o gráfico mostra a distribuição por município.
- Objetivo: Identificar as regiões com maior concentração de reclamações, ajudando a direcionar ações de melhoria.

### 4. Distribuição do Tamanho dos Textos das Reclamações
- Gráfico: Histograma.
- O que faz: Mostra a frequência de reclamações com base no número de caracteres na descrição. Inclui métricas de tamanho mínimo, médio e máximo.
- Objetivo: Entender o nível de detalhamento que os clientes fornecem em suas queixas. Textos muito longos podem indicar problemas complexos.

### 5. Dispersão: Tamanho do Texto vs. Tempo
- Gráfico: Gráfico de Dispersão.
- O que faz: Plota cada reclamação como um ponto no gráfico, relacionando a data em que foi feita com o tamanho do texto da descrição. Os pontos são coloridos de acordo com o status da reclamação.
- Objetivo: Analisar se há correlações entre o tempo, o detalhe da reclamação e o seu desfecho (status).

### 6. WordCloud - Palavras Mais Frequentes
- Gráfico: Nuvem de Palavras.
- O que faz: Exibe os termos mais comuns encontrados nos textos das reclamações, com tamanho proporcional à sua frequência. Palavras comuns e pouco informativas (stopwords) são removidas.
- Objetivo: Identificar rapidamente os principais temas e produtos mencionados nas reclamações, como "entrega", "pedido", "pagamento", "cancelamento", etc.

### 7. Mapa de Calor de Reclamações por Localidade
- Gráfico: Mapa Coroplético (usando Folium).
- O que faz: Gera um mapa interativo do Brasil que exibe a concentração de reclamações por estado, com cores que indicam a intensidade. Ao selecionar um estado específico no filtro, o mapa se aproxima e mostra a distribuição das queixas por município. Um filtro de ano também permite analisar a distribuição em períodos específicos.
- Objetivo: Fornecer uma perspectiva geográfica clara sobre os focos de reclamações, permitindo a identificação de estados ou municípios que demandam mais atenção e a análise de padrões regionais.

### ⚙️ Como Utilizar
- Clone o repositório:

```git clone <url-do-repositorio>```

- Instale as dependências:

```pip install -r requirements.txt```

- Execute a aplicação Streamlit:

```streamlit run app.py```

- Interaja com os filtros na barra lateral para segmentar os dados por período, estado e situação da reclamação. Os gráficos serão atualizados dinamicamente.
- Navegue entre as páginas "Home" e "Mapa" para acessar as diferentes visualizações.
