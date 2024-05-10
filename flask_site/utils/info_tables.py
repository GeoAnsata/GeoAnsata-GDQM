import pandas as pd
def criar_tabela_continuo(dataset):
    estatisticas = {
        'Nomes das Colunas': [],
        'Média': [],
        'Mediana': [],
        'Mínimo': [],
        'Máximo': [],
        'Desvio Padrão': [],
    }
    for coluna in dataset.columns:
        if pd.api.types.is_numeric_dtype(dataset[coluna]):
            estatisticas['Nomes das Colunas'].append(coluna)
            estatisticas['Média'].append(dataset[coluna].mean())
            estatisticas['Mediana'].append(dataset[coluna].median())
            estatisticas['Mínimo'].append(dataset[coluna].min())
            estatisticas['Máximo'].append(dataset[coluna].max())
            estatisticas['Desvio Padrão'].append(dataset[coluna].std())

    tabela = pd.DataFrame(estatisticas)
    return tabela
