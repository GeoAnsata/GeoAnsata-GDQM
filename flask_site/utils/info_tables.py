import pandas as pd

def custom_round(value):
    try:
        numeric_value = float(value)
        if numeric_value > 1:
            return round(numeric_value, 2)
        else:
            return round(numeric_value, 4)
    except ValueError:
        # If value cannot be converted to float, return it unchanged
        return value



def criar_data_dict(dataset):
    linhas_tabela = []
    
    # Calculate count of null values for each column
    null_counts = dataset.isnull().sum()
    
    for coluna in dataset.columns:
        valores_unicos = dataset[coluna].dropna().unique()  # Drop null values
        
        # Append count of null values for the column
        linhas_tabela.append([coluna, None, null_counts[coluna]])
        
        for valor in valores_unicos:
            contagem = dataset[coluna].eq(valor).sum()
            linhas_tabela.append([coluna, valor, contagem])
    
    # Create DataFrame from list of rows
    tabela = pd.DataFrame(linhas_tabela, columns=['Nomes das Colunas', 'Valores', 'Contagem'])

    total_linhas = len(dataset)
    tabela['Porcentagem'] = round((tabela['Contagem'] / total_linhas) * 100, 2)

    return tabela


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
            estatisticas['Média'].append(custom_round(dataset[coluna].mean()))
            estatisticas['Mediana'].append(custom_round(dataset[coluna].median()))
            estatisticas['Mínimo'].append(custom_round(dataset[coluna].min()))
            estatisticas['Máximo'].append(custom_round(dataset[coluna].max()))
            estatisticas['Desvio Padrão'].append(custom_round(dataset[coluna].std()))

    tabela = pd.DataFrame(estatisticas)
    return tabela