from flask import Flask, render_template, request, redirect, url_for, send_file, session,jsonify, json, flash
from functools import wraps
from utils.info_tables import *
from utils.load_df import *
import seaborn as sns
import tempfile
import os
import re
import pandas as pd
import shutil
from datetime import *
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import numpy as np


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.permanent_session_lifetime = timedelta(minutes=10)

USERS = {
    "user1": "password1",
    "user2": "password2",
}

def get_user_folder(folder_type):
    """Get the folder path for the current user based on folder_type ('upload' or 'temp')."""
    username = session.get('username')
    if not username:
        return None
    user_folder = os.path.join(folder_type, username)
    os.makedirs(user_folder, exist_ok=True)  # Ensure folder exists
    return user_folder

def load_existing_files():
    """Load existing files in the user's upload folder and update session['sheet_names'] with their sheet names."""
    upload_folder = get_user_folder('upload')
    dict_sheet_names = {}

    # Iterate through existing files in the upload folder
    for filename in os.listdir(upload_folder):
        file_path = os.path.join(upload_folder, filename)
        _, file_ext = os.path.splitext(filename)

        # Process Excel files
        if file_ext == '.xlsx':
            df = pd.read_excel(file_path, sheet_name=None)
            sheet_names = list(df.keys())
            if len(sheet_names) > 1:
                dict_sheet_names[filename] = sheet_names
            else:
                dict_sheet_names[filename] = []

        # Process CSV files
        elif file_ext == '.csv':
            dict_sheet_names[filename] = []

    # Update session with the sheet names found in existing files
    session['sheet_names'] = dict_sheet_names

# Login required decorator to restrict access to pages
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if the user exists and password matches
        if USERS.get(username) == password:
            session['username'] = username
            session.permanent = True
            load_existing_files()
            session['selected_file']=''
            session['selected_sheet']=''
            session['filters'] = [] 
            session['filter_logic']='and'
            session['image_filename']=''
            session['table_html']=''
            return redirect(url_for('upload'))  # Redirect to base page
        else:
            flash("Invalid credentials, please try again.")
            return render_template('login.html', error="Invalid username or password.")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/upload_file', methods=['POST'])
@login_required
def upload_file():
    if 'files' not in request.files:
        return render_template('upload.html', error='Nenhum arquivo enviado!')
    files = request.files.getlist('files')
    dict_sheet_names=session['sheet_names']
    upload_folder = get_user_folder('upload')
    temp_folder = get_user_folder('temp')
    for file in files:
        if file.filename == '':
            return render_template('upload.html', error='Nenhum arquivo selecionado!')
        file_root, _ = os.path.splitext(file.filename)
        if file and file.filename.endswith('.xlsx'):
            upload_path = os.path.join(upload_folder, file.filename)
            file.save(upload_path)
            
            temp_path = os.path.join(temp_folder, file.filename)
            shutil.copy(upload_path, temp_path)


            df = pd.read_excel(file, sheet_name=None)
            sheet_names=list(df.keys())
            if(len(sheet_names)>1):
                dict_sheet_names[file.filename]=sheet_names
                for sheet_name in sheet_names:
                    df=pd.read_excel(file,sheet_name=sheet_name)
                    df.to_csv(os.path.join(temp_folder, file_root + "_" + sheet_name + ".csv"),index=False)
                    f = open(os.path.join(temp_folder, file_root + "_" + sheet_name + ".txt"), "w")
                    f.close()                    
                    f = open(os.path.join(upload_folder, file_root + "_" + sheet_name + ".txt"), "w")
                    f.close()
            else:
                dict_sheet_names[file.filename]=[]
                f = open(os.path.join(temp_folder, file_root + ".txt"), "w")
                f.close()
                f = open(os.path.join(upload_folder, file_root + ".txt"), "w")
                f.close()

        elif file and file.filename.endswith('.csv'):
            dict_sheet_names[file.filename]=[]
            upload_path = os.path.join(upload_folder, file.filename)
            file.save(upload_path)
            
            temp_path = os.path.join(temp_folder, file.filename)
            shutil.copy(upload_path, temp_path)
            f = open(os.path.join(temp_folder, file_root + ".txt"), "w")
            f.close()
            f = open(os.path.join(upload_folder, file_root + ".txt"), "w")
            f.close()
    session['sheet_names']=dict_sheet_names
    return redirect(url_for('upload'))


@app.route('/download_sheet/<file_name>/<sheet_name>', methods=['GET'])
@login_required
def download_sheet(file_name,sheet_name):
    upload_folder = get_user_folder('upload')
    file_path = os.path.join(upload_folder, file_name)
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    temp_file_path = os.path.join(tempfile.gettempdir(), f"{file_name}_{sheet_name}.csv")
    df.to_csv(temp_file_path, index=False)

    return send_file(temp_file_path, as_attachment=True, download_name=f"{file_name}_{sheet_name}.csv", mimetype='text/csv')


@app.route('/download_file/<file_name>', methods=['GET'])
@login_required
def download_file(file_name):
    upload_folder = get_user_folder('upload')
    temp_folder = get_user_folder('temp')
    file_path = os.path.join(upload_folder, file_name)
    
    if file_path.endswith('.xlsx'):
        return send_file(file_path, as_attachment=True, download_name=file_name, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    elif file_path.endswith('.csv'):
        return send_file(file_path, as_attachment=True, download_name=file_name, mimetype='text/csv')

 
    
@app.route('/remove_columns', methods=['POST'])
@login_required
def remove_columns():
    temp_folder = get_user_folder('temp')
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


    return redirect(url_for('clean_data'))


@app.route('/remove_rows', methods=['POST'])
@login_required
def remove_rows():
    temp_folder = get_user_folder('temp')
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

    return redirect(url_for('clean_data'))

@app.route('/remove_nulls', methods=['POST'])
@login_required
def remove_nulls():
    temp_folder = get_user_folder('temp')
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


    return redirect(url_for('clean_data'))

#adicionar aviso para querys invalidas
@app.route('/remove_query', methods=['POST'])
@login_required
def remove_query():
    temp_folder = get_user_folder('temp')
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


    return redirect(url_for('clean_data'))

@app.route('/apply_filters', methods=['POST'])
@login_required
def apply_filters():
    temp_folder = get_user_folder('temp')
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

    return redirect(url_for('clean_data'))





from xhtml2pdf import pisa
@app.route('/export_pdf', methods=['GET'])
@login_required
def export_pdf():
    upload_folder = get_user_folder('upload')
    file_name = session['selected_file']
    dict_sheet_names = session['sheet_names']
    file_root, _ = os.path.splitext(file_name)
    if file_name.endswith('.xlsx') and (len(dict_sheet_names[file_name])>0):
        selected_sheet=session['selected_sheet']
        history_path = os.path.join(upload_folder, file_root + "_" + selected_sheet + "complete.html")
        pdf_path = os.path.join(upload_folder, 'history' + selected_sheet + '.pdf')
    else:
        history_path = os.path.join(upload_folder, file_root + "complete.html")
        pdf_path = os.path.join(upload_folder, 'history' + file_root + '.pdf')
    

    with open(history_path, "r") as file:
        html_content = file.read()


    with open("./templates/includes/history_pdf.html", "r") as file:
        html_style = file.read()

    pdf_output = BytesIO()

    pisa.CreatePDF(html_content + html_style, dest=pdf_output, encoding='utf-8')

    # Open a PDF file for writing in binary mode
    with open(pdf_path, "wb") as pdf_file:
    
        # Write the PDF content to the file
        pdf_file.write(pdf_output.getvalue())
    
    return send_file(pdf_path, as_attachment=True)


@app.route('/criar_tabela_continuo', methods=['GET'])
@login_required
def criar_tabela_continuo_route():
    temp_folder = get_user_folder('temp')
    colunas_selecionadas = request.args.getlist('colunas')
    df = load_df(temp_folder)
    tabela_continua = gerar_estatisticas_tabela(df[colunas_selecionadas])
    column_names=None
    if(df is not None):
        column_names = df.columns.tolist()


    file_root, _ = os.path.splitext(session['selected_file'])
    tabela_continua.to_csv(os.path.join(temp_folder, file_root + "_exploratory_table.csv"),index=False)

    table_html = tabela_continua.to_html(classes='table table-striped')

    # Manually insert <thead> and <tbody>
    table_html = table_html.replace('<table ', '<table class="table table-striped" ')
    table_html = table_html.replace('<thead>', '<thead class="thead-light">')
    table_html = table_html.replace('<tbody>', '<tbody class="table-body">')
    session['table_html']=table_html
    return render_template('exploratory_analysis.html', uploaded_files=session['sheet_names'], column_names=column_names, table=table_html,image=None, selected_file=session["selected_file"], selected_sheet=session["selected_sheet"])

@app.route('/data_dict', methods=['GET'])
@login_required
def criar_data_dict_route():
    temp_folder = get_user_folder('temp')
    colunas_selecionadas = request.args.getlist('colunas')
    df = load_df(temp_folder)
    #data_dict = criar_data_dict(df[colunas_selecionadas])
    data_dict = gerar_resumo_tabela(df[colunas_selecionadas])
    column_names=None
    if(df is not None):
        column_names = df.columns.tolist()


    file_root, _ = os.path.splitext(session['selected_file'])
    data_dict.to_csv(os.path.join(temp_folder, file_root + "_exploratory_table.csv"),index=False)

    table_html = data_dict.to_html(classes='table table-striped')

    # Manually insert <thead> and <tbody>
    table_html = table_html.replace('<table ', '<table class="table table-striped" ')
    table_html = table_html.replace('<thead>', '<thead class="thead-light">')
    table_html = table_html.replace('<tbody>', '<tbody class="table-body">')
    session['table_html']=table_html
    return render_template('exploratory_analysis.html', uploaded_files=session['sheet_names'], column_names=column_names, table=table_html,image=None, selected_file=session["selected_file"], selected_sheet=session["selected_sheet"])

@app.route('/download_csv', methods=['GET'])
@login_required
def download_csv():
    temp_folder = get_user_folder('temp')
    file_root, _ = os.path.splitext(session['selected_file'])
    temp_filename = os.path.join(temp_folder, file_root + "_exploratory_table.csv")
    if temp_filename and os.path.exists(temp_filename):
        return send_file( temp_filename, as_attachment=True, download_name=file_root + "_exploratory_table.csv", mimetype='text/csv')
    return "No table to download", 400

@app.route('/completude_graph', methods=['GET'])
@login_required
def completude_graph():
    temp_folder = get_user_folder('temp')
    colunas_selecionadas = request.args.getlist('colunas')
    df = load_df(temp_folder)
    column_names = df.columns.tolist() if df is not None else None
    #data_dict = criar_data_dict(df[colunas_selecionadas])

    plt.figure(figsize=(10, 6))  # Ajuste o tamanho conforme necessário
    sns.heatmap(df[colunas_selecionadas].transpose().isnull(), cbar=False, cmap=["purple", "yellow"], linecolor='white')

    plt.xlabel(f"{df[colunas_selecionadas].shape[0]} linhas")
    plt.ylabel(f"{df[colunas_selecionadas].shape[1]} colunas")

    # Set the y-tick positions at row boundaries (between rows)
    plt.gca().set_yticks(np.arange(0, df[colunas_selecionadas].shape[1]))  # Gridlines between rows

    # Set the y-tick labels to column names and shift their positions to the middle
    plt.gca().set_yticklabels(df[colunas_selecionadas].columns)

    # Add horizontal gridlines at row boundaries (between rows)
    plt.grid(axis='y', color='white', linewidth=1, linestyle='-', zorder=0)

    img = BytesIO()
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)
    img_base64 = base64.b64encode(img.getvalue()).decode('utf-8')
    
    file_root, _ = os.path.splitext(session['selected_file'])
    image_filename = os.path.join(temp_folder, str(datetime.now().strftime("%d%m%Y%H%M%S")) + "_completude_graph.png")
    session['image_filename'] = image_filename
    with open(image_filename, 'wb') as f:
        f.write(img.getvalue())
    return render_template('exploratory_analysis.html', uploaded_files=session['sheet_names'], column_names=column_names, table=None, image=img_base64, selected_file=session["selected_file"], selected_sheet=session["selected_sheet"])

@app.route('/plot_graph', methods=['POST'])
@login_required
def plot_graph():
    temp_folder = get_user_folder('temp')
    x_column = request.form['x_column']
    y_column = request.form['y_column']
    chart_type = request.form['chart_type']
    image_size = request.form['image_size'].split('x')
    width, height = int(image_size[0]), int(image_size[1])
    point_color = request.form['point_color']
    
    # Obter título personalizado, se fornecido
    custom_title = request.form.get('custom_title', '')
    
    # Obter as unidades de medida para X e Y, se fornecidas
    x_unit = request.form.get('x_unit', '')
    y_unit = request.form.get('y_unit', '')

    df = load_df(temp_folder)
    column_names = df.columns.tolist() if df is not None else None
    x_min, x_max = min(df[x_column]), max(df[x_column])
    plt.figure(figsize=(width, height))

    # Definir título com base no valor personalizado ou título padrão
    title = custom_title if custom_title else f'Gráfico de {chart_type.capitalize()} {y_column} vs {x_column}'

    # Verifica o tipo de gráfico e plota
    if chart_type == 'line':
        plt.plot(df[x_column], df[y_column], marker='o', color=point_color, linestyle='-')
        plt.xlim(x_min, x_max)
        plt.title(title)
        plt.xlabel(f"{x_column} ({x_unit})" if x_unit else x_column)
        plt.ylabel(f"{y_column} ({y_unit})" if y_unit else y_column)
    elif chart_type == 'scatter':
        plt.scatter(df[x_column], df[y_column], color=point_color)
        plt.xlim(x_min, x_max)
        plt.title(title)
        plt.xlabel(f"{x_column} ({x_unit})" if x_unit else x_column)
        plt.ylabel(f"{y_column} ({y_unit})" if y_unit else y_column)
    elif chart_type == 'bar':
        plt.bar(df[x_column], df[y_column], color=point_color)
        plt.xlim(x_min, x_max)
        plt.title(title)
        plt.xlabel(f"{x_column} ({x_unit})" if x_unit else x_column)
        plt.ylabel(f"{y_column} ({y_unit})" if y_unit else y_column)
    elif chart_type == 'histogram':
        plt.title(title)
        plt.xlim(x_min, x_max)
        plt.hist(df[x_column], bins=30, color=point_color)
        plt.ylabel(f"{x_column} ({x_unit})" if x_unit else x_column)

    plt.grid(True)
    plt.tight_layout()

    img = BytesIO()
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)
    img_base64 = base64.b64encode(img.getvalue()).decode('utf-8')

    file_root, _ = os.path.splitext(session['selected_file'])
    image_filename = os.path.join(temp_folder, str(datetime.now().strftime("%d%m%Y%H%M%S")) + str(chart_type) + "_plot.png")
    session['image_filename'] = image_filename
    with open(image_filename, 'wb') as f:
        f.write(img.getvalue())

    return render_template('exploratory_analysis.html', uploaded_files=session['sheet_names'], column_names=column_names, table=None, image=img_base64, selected_file=session["selected_file"], selected_sheet=session["selected_sheet"])

@app.route('/download_plot', methods=['GET'])
@login_required
def download_plot():
    file_root, _ = os.path.splitext(session['selected_file'])
    temp_filename = session['image_filename']
    if temp_filename and os.path.exists(temp_filename):
        return send_file( temp_filename, as_attachment=True, download_name=file_root + "_plot.png", mimetype='png')
    return "No plot to download", 400

@app.route('/add_table_to_history', methods=['GET'])
@login_required
def add_table_to_history():
    temp_folder = get_user_folder('temp')
    table_html = session['table_html']
    print(table_html)
    try:
        # Load complete history (for HTML storage)
        complete_history = load_history_pdf(temp_folder)

        # Log the addition of the plot to the history
        formatted_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        complete_history.write(f'<p>{formatted_time} - Tabela adicionada a histórico</p>')

        # Include image in the HTML by adding an <img> tag
        complete_history.write(f'<div class="table-responsive">{table_html}</div>')
        complete_history.close()

        # Return success response
        return jsonify({"status": "success"}), 200
    except:
        return jsonify({"status": "error", "message": "Não há gráfico para adicionar a histórico"}), 400

@app.route('/add_plot_to_history', methods=['GET'])
@login_required
def add_plot_to_history():
    temp_folder = get_user_folder('temp')
    temp_filename = session['image_filename']
    
    if temp_filename and os.path.exists(temp_filename):
        # Load complete history (for HTML storage)
        complete_history = load_history_pdf(temp_folder)

        # Log the addition of the plot to the history
        formatted_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        complete_history.write(f'<p>{formatted_time} - Gráfico adicionado a histórico</p>')

        # Include image in the HTML by adding an <img> tag
        complete_history.write(f'<img src="{temp_filename}" alt="Gráfico" style="width:100%; max-width:600px;"/>')
        complete_history.close()

        # Return success response
        return jsonify({"status": "success"}), 200
    
    return jsonify({"status": "error", "message": "Não há gráfico para adicionar a histórico"}), 400

#da erro se tentar aplicar mudanças sem ter
@app.route('/apply_file_changes', methods=['GET'])
@login_required
def apply_file_changes():
    try:
        temp_folder = get_user_folder('temp')
        upload_folder = get_user_folder('upload')
        file_name = session['selected_file']
        dict_sheet_names = session['sheet_names']
        file_path = os.path.join(upload_folder, file_name)
        df=load_df(temp_folder)
        if df is None:
            df = pd.DataFrame()
        temp_history=load_history(temp_folder,"r")
        content = temp_history.read()
        temp_history.close()
        temp_history=load_history(temp_folder,"w")
        temp_history.close()

        history=load_history(upload_folder,"a")
        history.write(content)
        history.close()



         
        temp_history_pdf=load_history_pdf(temp_folder,"r")
        content_pdf = temp_history_pdf.read()
        temp_history_pdf.close()
        temp_history_pdf=load_history_pdf(temp_folder,"w")
        temp_history_pdf.close()
        history_pdf=load_history_pdf(upload_folder,"a")
        history_pdf.write(content_pdf)
        history_pdf.close() 
        


        if file_name.endswith('.csv'):
            df.to_csv(file_path,index=False)
        elif file_name.endswith('.xlsx') and (len(dict_sheet_names[file_name])>0):
            selected_sheet=session['selected_sheet']
            with pd.ExcelWriter(file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                df.to_excel(writer, sheet_name=selected_sheet, index=False)
        elif file_name.endswith('.xlsx'):
            df.to_excel(file_path,index=False)
    finally:
        if request.referrer and request.referrer.endswith('/plot_graph'):
            return redirect(url_for('exploratory_analysis'))
        return redirect(request.referrer or '/')
    
@app.route('/discard_file_changes', methods=['GET'])
@login_required
def discard_file_changes():
    temp_folder = get_user_folder('temp')
    upload_folder = get_user_folder('upload')
    file_name = session['selected_file']
    dict_sheet_names = session['sheet_names']
    file_path = os.path.join(temp_folder, file_name)
    df=load_backup_df(upload_folder)
    temp_history=load_history(temp_folder,"w")
    temp_history.close()

    temp_history_pdf=load_history_pdf(temp_folder,"w")
    temp_history_pdf.close()
    if file_name.endswith('.csv'):
        df.to_csv(file_path,index=False)
    elif file_name.endswith('.xlsx') and (len(dict_sheet_names[file_name])>0):
        selected_sheet=session['selected_sheet']
        file_root, _ = os.path.splitext(file_path)
        df.to_csv(file_root + "_" + selected_sheet + ".csv",index=False)
    elif file_name.endswith('.xlsx'):
        df.to_excel(file_path,index=False)
    return redirect(request.referrer or '/')

@app.route('/')
@login_required
def upload():
    if 'sheet_names' not in session:
        session['sheet_names'] = {}
        session['selected_file']=''
        session['selected_sheet']=''
    return render_template('upload.html', uploaded_files=session['sheet_names'], selected_file=session["selected_file"], selected_sheet=session["selected_sheet"])

@app.route('/display', methods=['GET', 'POST'])
@login_required
def display():
    try:
        temp_folder = get_user_folder('temp')
        df = load_df(temp_folder)
        column_names = df.columns.tolist()
        
        # Captura os parâmetros de paginação
        start = request.args.get('start', default=0, type=int)
        lines_by_page = request.args.get('lines_by_page', default=100, type=int)
        
        if request.method == 'POST':
            filter_column = request.form.get('filter_column')
            filter_operator = request.form.get('filter_operator')
            filter_value = request.form.get('filter_value')
            
            if filter_column and filter_operator and filter_value:
                # Append the new filter to the existing list of filters
                session['filters'].append({
                    'column': filter_column,
                    'operator': filter_operator,
                    'value': filter_value
                })
                session.modified = True 
        # Remover filtro específico
        if 'remove_filter' in request.args:
            filter_index = int(request.args.get('remove_filter'))
            session['filters'].pop(filter_index)
            session.modified = True

        # Limpar todos os filtros
        if 'clear_filters' in request.args:
            session['filters'] = []
            session.modified = True


        # Definir operador de combinação dos filtros (AND/OR)
        filter_logic = request.args.get('filter_logic', 'and')
        
        # Aplica os filtros ao DataFrame
        for filter_item in session['filters']:
            col = filter_item['column']
            op = filter_item['operator']
            val = filter_item['value']
            
            try:
                val = float(val) if val.replace('.', '', 1).isdigit() else val
                if op == "equals":
                    condition = df[col] == val
                elif op == "not_equals":
                    condition = df[col] != val
                elif op == "greater_than":
                    condition = pd.to_numeric(df[col], errors='coerce') > val
                elif op == "less_than":
                    condition = pd.to_numeric(df[col], errors='coerce') < val
                elif op == "greater_equal":
                    condition = pd.to_numeric(df[col], errors='coerce') >= val
                elif op == "less_equal":
                    condition = pd.to_numeric(df[col], errors='coerce') <= val

                # Aplica o filtro como AND ou OR
                if filter_logic == 'and':
                    df = df[condition]
                else:
                    df = pd.concat([df[condition], df[~condition]]).drop_duplicates()

            except ValueError:
                pass  # Ignorar se houver erro de tipo

        # Gera a tabela HTML com os dados filtrados e paginação
        table_html = get_table(df, request, start, lines_by_page)
        
        # Renderiza o template com a tabela, filtros e opções
        return render_template(
            'display.html',
            table=table_html,
            uploaded_files=session['sheet_names'],
            selected_file=session["selected_file"],
            selected_sheet=session["selected_sheet"],
            start=start,
            lines_by_page=lines_by_page,
            num_lines=df.shape[0],
            column_names=column_names,
            filters=session['filters'],
            filter_logic=filter_logic
        )
    except Exception as e:
        print(f"Erro ao exibir a tabela: {e}")
        return render_template(
            'display.html',
            table=None,
            uploaded_files=session['sheet_names'],
            selected_file=session["selected_file"],
            selected_sheet=session["selected_sheet"],
            start=0,
            lines_by_page=100,
            num_lines=0,
            column_names=[],
            filters=[],
            filter_logic='and'
        )

@app.route('/download_page')
@login_required
def download_page():
    return render_template('download.html', uploaded_files=session['sheet_names'], selected_file=session["selected_file"], selected_sheet=session["selected_sheet"])

@app.route('/clean_data',  methods=['GET', 'POST'])
@login_required
def clean_data():
    try:
        temp_folder = get_user_folder('temp')
        df = load_df(temp_folder)

        start = request.args.get('start', default=0, type=int)
        lines_by_page = request.args.get('lines_by_page', default=100, type=int)

        column_names = df.columns.tolist()
        table_html = get_table(df, request, start, lines_by_page)

        return render_template('clean_data.html', 
                               table=table_html, 
                               uploaded_files=session['sheet_names'], 
                               column_names=column_names, 
                               selected_file=session["selected_file"], 
                               selected_sheet=session["selected_sheet"],
                               start=start,
                               lines_by_page=lines_by_page,
                               num_lines=df.shape[0],
                               filters=session['filters'],
                                filter_logic=session['filter_logic'])
    except:
        return render_template('clean_data.html',
                                table=None,
                                uploaded_files=session['sheet_names'], 
                                column_names=[], 
                                selected_file=session["selected_file"], 
                                selected_sheet=session["selected_sheet"], 
                                start=0, 
                                lines_by_page=100,
                                num_lines=0,
                                filters=[],
                                filter_logic='and')

@app.route('/exploratory_analysis')
@login_required
def exploratory_analysis():
    temp_folder = get_user_folder('temp')
    df = load_df(temp_folder)
    column_names=None
    if(df is not None):
        column_names = df.columns.tolist()
    return render_template('exploratory_analysis.html', uploaded_files=session['sheet_names'], column_names=column_names, table=None,image=None, selected_file=session["selected_file"], selected_sheet=session["selected_sheet"])

@app.route('/recommended_graphs')
@login_required
def recommended_graphs():
    return render_template('recommended_graphs.html',uploaded_files=session['sheet_names'], selected_file=session["selected_file"], selected_sheet=session["selected_sheet"])


@app.route('/history')
@login_required
def history():
    try:

        upload_folder = get_user_folder('upload')
        history=load_history(upload_folder,"r")
        content = history.read()
        history.close()
        return render_template('history.html',file_history=content,uploaded_files=session['sheet_names'], selected_file=session["selected_file"], selected_sheet=session["selected_sheet"])
    except:
        return render_template('history.html',file_history=None,uploaded_files=session['sheet_names'], selected_file=session["selected_file"], selected_sheet=session["selected_sheet"])

@app.route('/select_file/<file_name>')
@login_required
def select_file(file_name):
    session['selected_file'] = file_name
    return redirect(request.referrer or '/')

@app.route('/select_file/<file_name>/<sheet_name>')
@login_required
def select_sheet(file_name, sheet_name):
    session['selected_file'] = file_name
    session['selected_sheet'] = sheet_name
    return redirect(request.referrer or '/')

if __name__ == '__main__':
    app.run(debug=True)
