import pandas as pd



def get_table(df, request, start, lines_by_page):
    sort_column = request.args.get('sort_column', default=None, type=str)
    sort_order = request.args.get('sort_order', default='asc', type=str)
    
    if sort_column and sort_column in df.columns:
        df.sort_values(by=sort_column, ascending=(sort_order == 'asc'), inplace=True)
    
    df = df.reset_index(drop=True)
    
    # Slice the dataframe
    df = df.iloc[start:start + lines_by_page]
    
    table_html = df.to_html(classes='table table-striped')

    # Manually insert <thead> and <tbody>
    table_html = table_html.replace('<table ', '<table class="table table-striped" ')
    table_html = table_html.replace('<thead>', '<thead class="thead-light">')
    table_html = table_html.replace('<tbody>', '<tbody class="table-body">')

    # Add data-column attribute to headers for easier access
    for col in df.columns:
        sort_arrow = '<i class="fas fa-sort"></i>'
        if col == sort_column:
            sort_arrow = '<i class="fas fa-sort-up"></i>' if sort_order == 'asc' else '<i class="fas fa-sort-down"></i>'
        table_html = table_html.replace(f'<th>{col}</th>', f'<th data-column="{col}" style="cursor: pointer;">{col} {sort_arrow}</th>')
    return table_html



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