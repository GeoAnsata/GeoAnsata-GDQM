import pandas as pd



def get_table(df, request, start, lines_by_page, reset_index=True):
    sort_column = request.args.get('sort_column', default=None, type=str)
    sort_order = request.args.get('sort_order', default='asc', type=str)
    
    if sort_column and sort_column in df.columns:
        df.sort_values(by=sort_column, ascending=(sort_order == 'asc'), inplace=True)
    
    if(reset_index):
        df = df.reset_index(drop=True)
    
    # Slice the dataframe
    df = df.iloc[start:start + lines_by_page]
    df = df.copy()
    for col in df.select_dtypes(include=['float']).columns:
        df[col] = df[col].map('{:.6f}'.format)
    
    # Convert to HTML
    table_html = df.to_html(classes='table table-striped', index=False)


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

def gerar_resumo_tabela(tabela):
    colunas = []
    tipos_dados = []
    valores_unicos = []
    listas_escolhas = []
    distribuicoes = []
    
    for coluna in tabela.columns:
        # Nome da coluna
        colunas.append(coluna)
        
        # Tipo de dado
        tipos_dados.append(tabela[coluna].dtype)
        
        # Valores únicos e contagem
        valores_unicos.append(tabela[coluna].nunique())
        lista_escolhas = ", ".join(map(str, tabela[coluna].unique()[:10])) if tabela[coluna].nunique() <= 10 else "–"
        listas_escolhas.append(lista_escolhas)
        
        # Distribuição (incluindo NaN)
        distribuicao = tabela[coluna].value_counts(dropna=False, normalize=True) * 100
        qtd_distribuicao = tabela[coluna].value_counts(dropna=False)
        
        distrib_resumo = ", ".join([
            f"{valor if pd.notna(valor) else 'NaN'}: {qtd} ({pct:.1f}%)"
            for valor, qtd, pct in zip(distribuicao.index, qtd_distribuicao, distribuicao)
        ]) if tabela[coluna].nunique() <= 10 else "–"

        distribuicoes.append(distrib_resumo)
    
    # Criar DataFrame com o resumo
    resumo_df = pd.DataFrame({
        "Coluna": colunas,
        "Tipo do dado": tipos_dados,
        "Valores únicos": valores_unicos,
        "Lista de escolhas": listas_escolhas,
        "Distribuição (Qtd., %)": distribuicoes
    })
    
    return resumo_df

def gerar_estatisticas_tabela(tabela):
    resumo = {
        "Variável": [],
        "n": [],
        "min": [],
        "25%": [],
        "50%": [],
        "média": [],
        "75%": [],
        "máx": [],
        "std": []
    }
    
    for coluna in tabela.columns:
        if pd.api.types.is_numeric_dtype(tabela[coluna]):
            resumo["Variável"].append(coluna)
            resumo["n"].append(tabela[coluna].count())
            resumo["min"].append(custom_round(tabela[coluna].min()))
            resumo["25%"].append(custom_round(tabela[coluna].quantile(0.25)))
            resumo["50%"].append(custom_round(tabela[coluna].median()))
            resumo["média"].append(custom_round(tabela[coluna].mean()))
            resumo["75%"].append(custom_round(tabela[coluna].quantile(0.75)))
            resumo["máx"].append(custom_round(tabela[coluna].max()))
            resumo["std"].append(custom_round(tabela[coluna].std()))
        else:
            # Preencher com valores nulos se a coluna não for numérica
            resumo["Variável"].append(coluna)
            resumo["n"].append(tabela[coluna].count())
            resumo["min"].append("–")
            resumo["25%"].append("–")
            resumo["50%"].append("–")
            resumo["média"].append("–")
            resumo["75%"].append("–")
            resumo["máx"].append("–")
            resumo["std"].append("–")
    
    # Criar DataFrame com o resumo
    resumo_df = pd.DataFrame(resumo)
    
    return resumo_df
