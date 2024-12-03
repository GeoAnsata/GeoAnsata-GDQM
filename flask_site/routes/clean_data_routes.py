import os
import re
from datetime import datetime
from flask import Blueprint, request, redirect, url_for, session,json

clean_data_routes = Blueprint('clean_data_routes', __name__)
from utils.auth_utils import login_required
from utils.project_utils import get_project_folder
from utils.load_df import load_df,load_history, load_history_pdf
from utils.info_tables import get_table

 
@clean_data_routes.route('/remove_columns', methods=['POST'])
@login_required
def remove_columns():
    temp_folder = get_project_folder('temp')
    columns_to_remove = request.form.getlist('columns_to_remove')
    comment = request.form.get('comment')
    if(comment):
        comment="Comentário: " + comment 
    file_name = session['selected_file']
    file_root, _ = os.path.splitext(file_name)
    dict_sheet_names = session['sheet_names']
    file_path = os.path.join(temp_folder, file_name)
    df=load_df(temp_folder)
    table_html = get_table(df[columns_to_remove], request, 0, 100)
    num_lines = "Número de linhas = " + str(df.shape[0])
    current_time = datetime.now()
    formatted_time = current_time.strftime('[%d-%m-%Y %H:%M:%S] ')
    id =  re.sub(r'\W+', '_', formatted_time)
    history= load_history(temp_folder)
    history.write(f'<pre><a href="#{id}" data-toggle="collapse" aria-expanded="false" aria-controls="{id}" style="cursor: pointer;">')
    history.write(formatted_time + "Colunas removidas:" + str(columns_to_remove) + "\n</a></pre>\n")
    history.write(f'<div id="{id}" class="collapse">')
    history.write(f'<p>{num_lines}</p>')
    if(comment):
        history.write(f'<p>{comment}</p>')
    history.write('<div class="table-responsive">')
    history.write(table_html + " </div>")
    history.write('</div>')
    history.close()
    
    complete_history=load_history_pdf(temp_folder)
    complete_history.write(formatted_time + "Colunas removidas: " + str(columns_to_remove) + "\n")
    complete_history.write(f'<p>{num_lines}</p>')
    if(comment):
        complete_history.write(f'<p>{comment}</p>')
    complete_history.close()
    
    df.drop(columns=columns_to_remove, inplace=True, errors='raise')
    df.sort_index(inplace=True)

    if file_name.endswith('.csv'):
        df.to_csv(file_path,index=False)
    elif file_name.endswith('.xlsx') and (len(dict_sheet_names[file_name])>0):
        selected_sheet=session['selected_sheet']
        file_root, _ = os.path.splitext(file_name)
        df.to_csv(os.path.join(temp_folder, file_root + "_" + selected_sheet + ".csv"),index=False)

    elif file_name.endswith('.xlsx'):
        df.to_excel(file_path,index=False)


    return redirect(url_for('pages_routes.clean_data', _external=True))


@clean_data_routes.route('/remove_rows', methods=['POST'])
@login_required
def remove_rows():
    temp_folder = get_project_folder('temp')
    start_row = int(request.form.get('start_row'))
    end_row = int(request.form.get('end_row'))
    sort_column = request.form.get('sort_column')
    sort_order = request.form.get('sort_order')
    comment = request.form.get('comment')
    if(comment):
        comment="Comentário: " + comment 

    file_name = session['selected_file']
    dict_sheet_names = session['sheet_names']
    file_path = os.path.join(temp_folder, file_name)
    df = load_df(temp_folder)

    # Apply sorting
    if sort_column and sort_column in df.columns:
        df.sort_values(by=sort_column, ascending=(sort_order == 'asc'), inplace=True)
    
    if end_row >= len(df):
        end_row = len(df) - 1
    if start_row < len(df):
        history = load_history(temp_folder)
        current_time = datetime.now()
        formatted_time = current_time.strftime('[%d-%m-%Y %H:%M:%S] ')
        id =  re.sub(r'\W+', '_', formatted_time)
        table_html = get_table(df.iloc[start_row:end_row + 1], request, 0, 100, reset_index=False)

        num_lines = "Remoção de "+str(end_row-start_row)+" linhas de "+ str(df.shape[0]) + " mantendo " +str(df.shape[0]-end_row+start_row) + " linhas"
        history.write(f'<pre><a href="#{id}" data-toggle="collapse" aria-expanded="false" aria-controls="{id}" style="cursor: pointer;">')
        history.write(formatted_time + "Removidas linhas de " + str(start_row) + " até " + str(end_row) + "\n</a></pre>\n")
        
        # Tabela colapsável com identificador único
        history.write(f'<div id="{id}" class="collapse">')
        history.write(f'<p>{num_lines}</p>')
        if(comment):
            history.write(f'<p>{comment}</p>')
        history.write('<div class="table-responsive">')
        history.write(table_html + " </div>")
        history.write('</div>')
        history.close()

        

        complete_history=load_history_pdf(temp_folder)
        complete_history.write(formatted_time + "Removidas linhas de " + str(start_row) + " até " + str(end_row) + "\n")
        complete_history.write(f'<p>{num_lines}</p>')
        if(comment):
            complete_history.write(f'<p>{comment}</p>')
        complete_history.close()
        
        df.drop(df.index[start_row:end_row + 1], inplace=True)
        df.sort_index(inplace=True)

    if file_name.endswith('.csv'):
        df.to_csv(file_path, index=False)
    elif file_name.endswith('.xlsx') and (len(dict_sheet_names[file_name]) > 0):
        selected_sheet = session['selected_sheet']
        file_root, _ = os.path.splitext(file_name)
        df.to_csv(os.path.join(temp_folder, file_root + "_" + selected_sheet + ".csv"), index=False)
    elif file_name.endswith('.xlsx'):
        df.to_excel(file_path, index=False)

    return redirect(url_for('pages_routes.clean_data', _external=True))

@clean_data_routes.route('/remove_nulls', methods=['POST'])
@login_required
def remove_nulls():
    temp_folder = get_project_folder('temp')
    columns_to_remove = request.form.getlist('columns_to_remove')
    comment = request.form.get('comment')
    if(comment):
        comment="Comentário: " + comment 
    file_name = session['selected_file']
    file_root, _ = os.path.splitext(file_name)
    dict_sheet_names = session['sheet_names']
    file_path = os.path.join(temp_folder, file_name)
    df=load_df(temp_folder)
    removed=df[df[columns_to_remove].isna().any(axis=1)]
    table_html = get_table(removed, request, 0, 100)
    num_lines = "Remoção de "+str(removed.shape[0])+" linhas de "+ str(df.shape[0]) + " mantendo " +str(df.shape[0]-removed.shape[0]) + " linhas"
    current_time = datetime.now()
    formatted_time = current_time.strftime('[%d-%m-%Y %H:%M:%S] ')
    id =  re.sub(r'\W+', '_', formatted_time)
    history= load_history(temp_folder)
    history.write(f'<pre><a href="#{id}" data-toggle="collapse" aria-expanded="false" aria-controls="{id}" style="cursor: pointer;">')
    history.write(formatted_time + "Remoção de linhas com valores nulos nas colunas:" + str(columns_to_remove) + "\n</a></pre>\n")
    
    # Tabela colapsável com identificador único
    history.write(f'<div id="{id}" class="collapse">')
    history.write(f'<p>{num_lines}</p>')
    if(comment):
        history.write(f'<p>{comment}</p>')
    history.write('<div class="table-responsive">')
    history.write(table_html + " </div>")
    history.write('</div>')
    history.close()

    complete_history=load_history_pdf(temp_folder)
    complete_history.write(formatted_time + "Remoção de linhas com valores nulos nas colunas:" + str(columns_to_remove) + "\n")
    complete_history.write(f'<p>{num_lines}</p>')
    if(comment):
        complete_history.write(f'<p>{comment}</p>')
    complete_history.close() 


    df.dropna(subset=columns_to_remove, inplace=True)
    df.sort_index(inplace=True)

    if file_name.endswith('.csv'):
        df.to_csv(file_path,index=False)
    elif file_name.endswith('.xlsx') and (len(dict_sheet_names[file_name])>0):
        selected_sheet=session['selected_sheet']
        file_root, _ = os.path.splitext(file_name)
        df.to_csv(os.path.join(temp_folder, file_root + "_" + selected_sheet + ".csv"),index=False)

    elif file_name.endswith('.xlsx'):
        df.to_excel(file_path,index=False)


    return redirect(url_for('pages_routes.clean_data', _external=True))

#adicionar aviso para querys invalidas
@clean_data_routes.route('/remove_query', methods=['POST'])
@login_required
def remove_query():
    temp_folder = get_project_folder('temp')
    query_str = request.form.get('query_string')
    comment = request.form.get('comment')
    if(comment):
        comment="Comentário: " + comment 
    file_name = session['selected_file']
    file_root, _ = os.path.splitext(file_name)
    dict_sheet_names = session['sheet_names']
    file_path = os.path.join(temp_folder, file_name)
    df=load_df(temp_folder)
    rows_to_drop=df.query(query_str)
    table_html = get_table(rows_to_drop, request, 0, 100)

    num_lines = "Remoção de "+str(rows_to_drop.shape[0])+" linhas de "+ str(df.shape[0]) + " mantendo " +str(df.shape[0]-rows_to_drop.shape[0]) + " linhas"
    current_time = datetime.now()
    formatted_time = current_time.strftime('[%d-%m-%Y %H:%M:%S] ')
    id =  re.sub(r'\W+', '_', formatted_time)
    history= load_history(temp_folder)
    history.write(f'<pre><a href="#{id}" data-toggle="collapse" aria-expanded="false" aria-controls="{id}" style="cursor: pointer;">')
    history.write(formatted_time + "Removido pela query:" + query_str + "\n</a></pre>\n")
    
    # Tabela colapsável com identificador único
    history.write(f'<div id="{id}" class="collapse">')
    history.write(f'<p>{num_lines}</p>')
    if(comment):
        history.write(f'<p>{comment}</p>')
    history.write('<div class="table-responsive">')
    history.write(table_html + " </div>")
    history.write('</div>')
    history.close()



        
    complete_history=load_history_pdf(temp_folder)
    complete_history.write(formatted_time + "Removido pela query:" + query_str+ "\n")
    complete_history.write(f'<p>{num_lines}</p>')
    if(comment):
        complete_history.write(f'<p>{comment}</p>')
    complete_history.close()
    
    
    df.drop(index=rows_to_drop.index, inplace=True)
    df.sort_index(inplace=True)

    if file_name.endswith('.csv'):
        df.to_csv(file_path,index=False)
    elif file_name.endswith('.xlsx') and (len(dict_sheet_names[file_name])>0):
        selected_sheet=session['selected_sheet']
        file_root, _ = os.path.splitext(file_name)
        df.to_csv(os.path.join(temp_folder, file_root + "_" + selected_sheet + ".csv"),index=False)

    elif file_name.endswith('.xlsx'):
        df.to_excel(file_path,index=False)


    return redirect(url_for('pages_routes.clean_data', _external=True))

@clean_data_routes.route('/apply_filters', methods=['POST'])
@login_required
def apply_filters():
    temp_folder = get_project_folder('temp')
    # Carrega os filtros recebidos como JSON
    filters = request.form.getlist('filters[]')
    filter_logic = request.form.get('filter_logic', 'and')
    comment = request.form.get('comment')
    if(comment):
        comment="Comentário: " + comment 
    file_name = session['selected_file']
    file_path = os.path.join(temp_folder, file_name)
    dict_sheet_names = session['sheet_names']
    
    applied_filters = []

    # Monta a string de consulta para o filtro
    query_conditions = []
    for filter_data in filters:
        filter_dict = json.loads(filter_data)  # Converte JSON para dicionário
        column = filter_dict.get('column')
        operator = filter_dict.get('operator')
        value = filter_dict.get('value')

        # Formata a condição com base no operador
        try:
            numeric_value = float(value)
            is_numeric = True
        except ValueError:
            is_numeric = False

        # Build condition based on the operator
        if operator == "equals":
            condition = f"({column} == '{value}')" if not is_numeric else f"({column} == {numeric_value})"
        elif operator == "not_equals":
            condition = f"({column} != '{value}')" if not is_numeric else f"({column} != {numeric_value})"
        elif operator == "greater_than":
            condition = f"({column} > '{value}')" if not is_numeric else f"({column} > {numeric_value})"
        elif operator == "less_than":
            condition = f"({column} < '{value}')" if not is_numeric else f"({column} < {numeric_value})"
        elif operator == "greater_than_or_equal":
            condition = f"({column} >= '{value}')" if not is_numeric else f"({column} >= {numeric_value})"
        elif operator == "less_than_or_equal":
            condition = f"({column} <= '{value}')" if not is_numeric else f"({column} <= {numeric_value})"
        
        
        query_conditions.append(condition)
        applied_filters.append({'column': column, 'operator': operator, 'value': value})
    
    # Constrói a string de consulta usando o operador lógico selecionado
    query_string = f" {filter_logic} ".join(query_conditions)


    # Aplique a consulta ao DataFrame usando df.query
    df = load_df(temp_folder)

    action = request.form.get('action')

    if action == 'remove_not_selected':
        # To remove items not selected, you can use the negation of the condition
        query_string= "not ( " + query_string + " )"
    rows_to_drop=df.query(query_string)

    # Renderiza a página com os dados filtrados
    table_html = get_table(rows_to_drop, request, 0, 100)
    num_lines = f"Remoção de {rows_to_drop.shape[0]} linhas de {df.shape[0]}, mantendo {df.shape[0] - rows_to_drop.shape[0]} linhas"
    current_time = datetime.now()
    formatted_time = current_time.strftime('[%d-%m-%Y %H:%M:%S] ')
    id = re.sub(r'\W+', '_', formatted_time)

    # Salva o histórico
    history = load_history(temp_folder)
    history.write(f'<pre><a href="#{id}" data-toggle="collapse" aria-expanded="false" aria-controls="{id}" style="cursor: pointer;">')
    history.write(formatted_time + "Removido pelos filtros:" + query_string + "\n</a></pre>\n")
    history.write(f'<div id="{id}" class="collapse">')
    history.write(f'<p>{num_lines}</p>')
    if(comment):
        history.write(f'<p>{comment}</p>')
    history.write('<div class="table-responsive">')
    history.write(table_html + " </div>")
    history.write('</div>')
    history.close()

    complete_history = load_history_pdf(temp_folder)
    complete_history.write(formatted_time + "Removido pelos filtros:" + str(applied_filters) + "\n")
    complete_history.write(f'<p>{num_lines}</p>')
    if(comment):
        complete_history.write(f'<p>{comment}</p>')
    complete_history.close()

    # Remove as linhas selecionadas do DataFrame original
    df.drop(index=rows_to_drop.index, inplace=True)
    df.sort_index(inplace=True)

    # Salva o DataFrame modificado
    if file_name.endswith('.csv'):
        df.to_csv(file_path, index=False)
    elif file_name.endswith('.xlsx') and (len(dict_sheet_names[file_name]) > 0):
        selected_sheet = session['selected_sheet']
        file_root, _ = os.path.splitext(file_name)
        df.to_csv(os.path.join(temp_folder, f"{file_root}_{selected_sheet}.csv"), index=False)
    elif file_name.endswith('.xlsx'):
        df.to_excel(file_path, index=False)

    return redirect(url_for('pages_routes.clean_data', _external=True))
