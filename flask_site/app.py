from flask import Flask, render_template, request, redirect, url_for, send_file, session
from utils.clear_directory import clear_directory
from utils.info_tables import *
from utils.load_df import *
import tempfile
import os
import re
import pandas as pd
import shutil
from datetime import datetime


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['TEMP_FOLDER'] = 'temp/'
app.config['SECRET_KEY'] = 'your_secret_key'



@app.before_first_request
def init_session_vars():
    clear_directory(app.config['UPLOAD_FOLDER'])
    clear_directory(app.config['TEMP_FOLDER'])

    session['sheet_names'] = {}
    session['selected_file']=''
    session['selected_sheet']=''


@app.route('/upload_file', methods=['POST'])
def upload_file():
    if 'files' not in request.files:
        return render_template('upload.html', error='Nenhum arquivo enviado!')
    files = request.files.getlist('files')
    dict_sheet_names=session['sheet_names']
    for file in files:
        if file.filename == '':
            return render_template('upload.html', error='Nenhum arquivo selecionado!')
        file_root, _ = os.path.splitext(file.filename)
        if file and file.filename.endswith('.xlsx'):
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(upload_path)
            
            temp_path = os.path.join(app.config['TEMP_FOLDER'], file.filename)
            shutil.copy(upload_path, temp_path)


            df = pd.read_excel(file, sheet_name=None)
            sheet_names=list(df.keys())
            if(len(sheet_names)>1):
                dict_sheet_names[file.filename]=sheet_names
                for sheet_name in sheet_names:
                    df=pd.read_excel(file,sheet_name=sheet_name)
                    df.to_csv(os.path.join(app.config['TEMP_FOLDER'], file_root + "_" + sheet_name + ".csv"),index=False)
                    f = open(os.path.join(app.config['TEMP_FOLDER'], file_root + "_" + sheet_name + ".txt"), "w")
                    f.close()                    
                    f = open(os.path.join(app.config['UPLOAD_FOLDER'], file_root + "_" + sheet_name + ".txt"), "w")
                    f.close()
            else:
                dict_sheet_names[file.filename]=[]
                f = open(os.path.join(app.config['TEMP_FOLDER'], file_root + ".txt"), "w")
                f.close()
                f = open(os.path.join(app.config['UPLOAD_FOLDER'], file_root + ".txt"), "w")
                f.close()

        elif file and file.filename.endswith('.csv'):
            dict_sheet_names[file.filename]=[]
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(upload_path)
            
            temp_path = os.path.join(app.config['TEMP_FOLDER'], file.filename)
            shutil.copy(upload_path, temp_path)
            f = open(os.path.join(app.config['TEMP_FOLDER'], file_root + ".txt"), "w")
            f.close()
            f = open(os.path.join(app.config['UPLOAD_FOLDER'], file_root + ".txt"), "w")
            f.close()
    session['sheet_names']=dict_sheet_names
    return redirect(url_for('upload'))


@app.route('/download_sheet/<file_name>/<sheet_name>', methods=['GET'])
def download_sheet(file_name,sheet_name):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    temp_file_path = os.path.join(tempfile.gettempdir(), f"{file_name}_{sheet_name}.csv")
    df.to_csv(temp_file_path, index=False)

    return send_file(temp_file_path, as_attachment=True, download_name=f"{file_name}_{sheet_name}.csv", mimetype='text/csv')


@app.route('/download_file/<file_name>', methods=['GET'])
def download_file(file_name):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
    
    if file_path.endswith('.xlsx'):
        return send_file(file_path, as_attachment=True, download_name=file_name, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    elif file_path.endswith('.csv'):
        return send_file(file_path, as_attachment=True, download_name=file_name, mimetype='text/csv')

 
    
@app.route('/remove_columns', methods=['POST'])
def remove_columns():
    columns_to_remove = request.form.getlist('columns_to_remove')
    comment = request.form.get('comment')
    if(comment):
        comment="Comentário: " + comment 
    file_name = session['selected_file']
    file_root, _ = os.path.splitext(file_name)
    dict_sheet_names = session['sheet_names']
    file_path = os.path.join(app.config['TEMP_FOLDER'], file_name)
    df=load_df(app)
    table_html = get_table(df[columns_to_remove], request, 0, 100)
    num_lines = "Número de linhas = " + str(df.shape[0])
    current_time = datetime.now()
    formatted_time = current_time.strftime('[%d-%m-%Y %H:%M:%S] ')
    id =  re.sub(r'\W+', '_', formatted_time)
    history= load_history(app, temp=True)
    history.write(f'<pre><a href="#{id}" data-toggle="collapse" aria-expanded="false" aria-controls="{id}" style="cursor: pointer;">')
    history.write(formatted_time + "Removed columns:" + str(columns_to_remove) + "\n</a></pre>\n")
    history.write(f'<div id="{id}" class="collapse">')
    history.write(f'<p>{num_lines}</p>')
    if(comment):
        history.write(f'<p>{comment}</p>')
    history.write('<div class="table-responsive">')
    history.write(table_html + " </div>")
    history.write('</div>')
    history.close()

    complete_history=load_history_pdf(app,temp=True)
    complete_history.write("<a>"+formatted_time + "Removed columns: " + str(columns_to_remove) + "\n</a>\n")
    full_table_html = get_table(df[columns_to_remove], request, 0, df.shape[0])
    complete_history.write(f'<p>{num_lines}</p>')
    if(comment):
        complete_history.write(f'<p>{comment}</p>')
    complete_history.write('<div class="table-responsive">')
    complete_history.write(full_table_html )
    complete_history.write('</div>')
    complete_history.close()

    df.drop(columns=columns_to_remove, inplace=True, errors='raise')
    df.sort_index(inplace=True)

    if file_name.endswith('.csv'):
        df.to_csv(file_path,index=False)
    elif file_name.endswith('.xlsx') and (len(dict_sheet_names[file_name])>0):
        selected_sheet=session['selected_sheet']
        file_root, _ = os.path.splitext(file_name)
        df.to_csv(os.path.join(app.config['TEMP_FOLDER'], file_root + "_" + selected_sheet + ".csv"),index=False)

    elif file_name.endswith('.xlsx'):
        df.to_excel(file_path,index=False)


    return redirect(url_for('clean_data'))


@app.route('/remove_rows', methods=['POST'])
def remove_rows():
    start_row = int(request.form.get('start_row'))
    end_row = int(request.form.get('end_row'))
    sort_column = request.form.get('sort_column')
    sort_order = request.form.get('sort_order')
    comment = request.form.get('comment')
    if(comment):
        comment="Comentário: " + comment 

    file_name = session['selected_file']
    dict_sheet_names = session['sheet_names']
    file_path = os.path.join(app.config['TEMP_FOLDER'], file_name)
    df = load_df(app)

    # Apply sorting
    if sort_column and sort_column in df.columns:
        df.sort_values(by=sort_column, ascending=(sort_order == 'asc'), inplace=True)
    
    if end_row >= len(df):
        end_row = len(df) - 1
    if start_row < len(df):
        history = load_history(app, temp=True)
        current_time = datetime.now()
        formatted_time = current_time.strftime('[%d-%m-%Y %H:%M:%S] ')
        id =  re.sub(r'\W+', '_', formatted_time)
        table_html = get_table(df.iloc[start_row:end_row + 1], request, 0, 100, reset_index=False)

        num_lines = "Remoção de "+str(end_row-start_row)+" linhas de "+ str(df.shape[0]) + " mantendo " +str(df.shape[0]-end_row+start_row) + " linhas"
        history.write(f'<pre><a href="#{id}" data-toggle="collapse" aria-expanded="false" aria-controls="{id}" style="cursor: pointer;">')
        history.write(formatted_time + "Removed rows from " + str(start_row) + " to " + str(end_row) + "\n</a></pre>\n")
        
        # Tabela colapsável com identificador único
        history.write(f'<div id="{id}" class="collapse">')
        history.write(f'<p>{num_lines}</p>')
        if(comment):
            history.write(f'<p>{comment}</p>')
        history.write('<div class="table-responsive">')
        history.write(table_html + " </div>")
        history.write('</div>')
        history.close()



        complete_history=load_history_pdf(app,temp=True)
        complete_history.write("<a>"+formatted_time + "Removed rows from " + str(start_row) + " to " + str(end_row) + "\n</a>\n")
        full_table_html = get_table(df, request, start_row, end_row + 1, reset_index=False)
        complete_history.write(f'<p>{num_lines}</p>')
        if(comment):
            complete_history.write(f'<p>{comment}</p>')
        complete_history.write('<div class="table-responsive">')
        complete_history.write(full_table_html )
        complete_history.write('</div>')
        complete_history.close()

        df.drop(df.index[start_row:end_row + 1], inplace=True)
        df.sort_index(inplace=True)

    if file_name.endswith('.csv'):
        df.to_csv(file_path, index=False)
    elif file_name.endswith('.xlsx') and (len(dict_sheet_names[file_name]) > 0):
        selected_sheet = session['selected_sheet']
        file_root, _ = os.path.splitext(file_name)
        df.to_csv(os.path.join(app.config['TEMP_FOLDER'], file_root + "_" + selected_sheet + ".csv"), index=False)
    elif file_name.endswith('.xlsx'):
        df.to_excel(file_path, index=False)

    return redirect(url_for('clean_data'))

@app.route('/remove_nulls', methods=['POST'])
def remove_nulls():
    columns_to_remove = request.form.getlist('columns_to_remove')
    comment = request.form.get('comment')
    if(comment):
        comment="Comentário: " + comment 
    file_name = session['selected_file']
    file_root, _ = os.path.splitext(file_name)
    dict_sheet_names = session['sheet_names']
    file_path = os.path.join(app.config['TEMP_FOLDER'], file_name)
    df=load_df(app)
    removed=df[df[columns_to_remove].isna().any(axis=1)]
    table_html = get_table(removed, request, 0, 100)
    num_lines = "Remoção de "+str(removed.shape[0])+" linhas de "+ str(df.shape[0]) + " mantendo " +str(df.shape[0]-removed.shape[0]) + " linhas"
    current_time = datetime.now()
    formatted_time = current_time.strftime('[%d-%m-%Y %H:%M:%S] ')
    id =  re.sub(r'\W+', '_', formatted_time)
    history= load_history(app, temp=True)
    history.write(f'<pre><a href="#{id}" data-toggle="collapse" aria-expanded="false" aria-controls="{id}" style="cursor: pointer;">')
    history.write(formatted_time + "Removed Null values in columns:" + str(columns_to_remove) + "\n</a></pre>\n")
    
    # Tabela colapsável com identificador único
    history.write(f'<div id="{id}" class="collapse">')
    history.write(f'<p>{num_lines}</p>')
    if(comment):
        history.write(f'<p>{comment}</p>')
    history.write('<div class="table-responsive">')
    history.write(table_html + " </div>")
    history.write('</div>')
    history.close()

    complete_history=load_history_pdf(app,temp=True)
    complete_history.write("<a>"+formatted_time + "Removed Null values in columns:" + str(columns_to_remove) + "\n</a>\n")
    full_table_html = get_table(removed, request, 0, removed.shape[0] + 1, reset_index=False)
    complete_history.write(f'<p>{num_lines}</p>')
    if(comment):
        complete_history.write(f'<p>{comment}</p>')
    complete_history.write('<div class="table-responsive">')
    complete_history.write(full_table_html )
    complete_history.write('</div>')
    complete_history.close()


    df.dropna(subset=columns_to_remove, inplace=True)
    df.sort_index(inplace=True)

    if file_name.endswith('.csv'):
        df.to_csv(file_path,index=False)
    elif file_name.endswith('.xlsx') and (len(dict_sheet_names[file_name])>0):
        selected_sheet=session['selected_sheet']
        file_root, _ = os.path.splitext(file_name)
        df.to_csv(os.path.join(app.config['TEMP_FOLDER'], file_root + "_" + selected_sheet + ".csv"),index=False)

    elif file_name.endswith('.xlsx'):
        df.to_excel(file_path,index=False)


    return redirect(url_for('clean_data'))

#adicionar aviso para querys invalidas
@app.route('/remove_query', methods=['POST'])
def remove_query():
    query_str = request.form.get('query_string')
    comment = request.form.get('comment')
    if(comment):
        comment="Comentário: " + comment 
    file_name = session['selected_file']
    file_root, _ = os.path.splitext(file_name)
    dict_sheet_names = session['sheet_names']
    file_path = os.path.join(app.config['TEMP_FOLDER'], file_name)
    df=load_df(app)
    rows_to_drop=df.query(query_str)
    table_html = get_table(rows_to_drop, request, 0, 100)

    num_lines = "Remoção de "+str(rows_to_drop.shape[0])+" linhas de "+ str(df.shape[0]) + " mantendo " +str(df.shape[0]-rows_to_drop.shape[0]) + " linhas"
    current_time = datetime.now()
    formatted_time = current_time.strftime('[%d-%m-%Y %H:%M:%S] ')
    id =  re.sub(r'\W+', '_', formatted_time)
    history= load_history(app, temp=True)
    history.write(f'<pre><a href="#{id}" data-toggle="collapse" aria-expanded="false" aria-controls="{id}" style="cursor: pointer;">')
    history.write(formatted_time + "Removed by query:" + query_str + "\n</a></pre>\n")
    
    # Tabela colapsável com identificador único
    history.write(f'<div id="{id}" class="collapse">')
    history.write(f'<p>{num_lines}</p>')
    if(comment):
        history.write(f'<p>{comment}</p>')
    history.write('<div class="table-responsive">')
    history.write(table_html + " </div>")
    history.write('</div>')
    history.close()



    
    complete_history=load_history_pdf(app,temp=True)
    complete_history.write("<a>"+formatted_time + "Removed by query:" + query_str+ "\n</a>\n")
    full_table_html = get_table(rows_to_drop, request, 0, rows_to_drop.shape[0] + 1, reset_index=False)
    complete_history.write(f'<p>{num_lines}</p>')
    if(comment):
        complete_history.write(f'<p>{comment}</p>')
    complete_history.write('<div class="table-responsive">')
    complete_history.write(full_table_html )
    complete_history.write('</div>')
    complete_history.close()

    
    df.drop(index=rows_to_drop.index, inplace=True)
    df.sort_index(inplace=True)

    if file_name.endswith('.csv'):
        df.to_csv(file_path,index=False)
    elif file_name.endswith('.xlsx') and (len(dict_sheet_names[file_name])>0):
        selected_sheet=session['selected_sheet']
        file_root, _ = os.path.splitext(file_name)
        df.to_csv(os.path.join(app.config['TEMP_FOLDER'], file_root + "_" + selected_sheet + ".csv"),index=False)

    elif file_name.endswith('.xlsx'):
        df.to_excel(file_path,index=False)


    return redirect(url_for('clean_data'))

from xhtml2pdf import pisa
@app.route('/export_pdf', methods=['GET'])
def export_pdf():
    file_name = session['selected_file']
    dict_sheet_names = session['sheet_names']
    file_root, _ = os.path.splitext(file_name)
    if file_name.endswith('.xlsx') and (len(dict_sheet_names[file_name])>0):
        selected_sheet=session['selected_sheet']
        history_path = os.path.join(app.config['UPLOAD_FOLDER'], file_root + "_" + selected_sheet + "complete.html")
        print(history_path)
    else:
        history_path = os.path.join(app.config['UPLOAD_FOLDER'], file_root + "complete.html")
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], 'history.pdf')
    

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
def criar_tabela_continuo_route():
    colunas_selecionadas = request.args.getlist('colunas')
    df = load_df(app)
    tabela_continua = criar_tabela_continuo(df[colunas_selecionadas])
    column_names=None
    if(df is not None):
        column_names = df.columns.tolist()


    file_root, _ = os.path.splitext(session['selected_file'])
    tabela_continua.to_csv(os.path.join(app.config['TEMP_FOLDER'], file_root + "_exploratory_table.csv"),index=False)

    table_html = tabela_continua.to_html(classes='table table-striped')

    # Manually insert <thead> and <tbody>
    table_html = table_html.replace('<table ', '<table class="table table-striped" ')
    table_html = table_html.replace('<thead>', '<thead class="thead-light">')
    table_html = table_html.replace('<tbody>', '<tbody class="table-body">')

    return render_template('exploratory_analysis.html', uploaded_files=session['sheet_names'], column_names=column_names, table=table_html,image=None, selected_file=session["selected_file"], selected_sheet=session["selected_sheet"])


@app.route('/data_dict', methods=['GET'])
def criar_data_dict_route():
    colunas_selecionadas = request.args.getlist('colunas')
    df = load_df(app)
    data_dict = criar_data_dict(df[colunas_selecionadas])
    column_names=None
    if(df is not None):
        column_names = df.columns.tolist()


    file_root, _ = os.path.splitext(session['selected_file'])
    data_dict.to_csv(os.path.join(app.config['TEMP_FOLDER'], file_root + "_exploratory_table.csv"),index=False)

    table_html = data_dict.to_html(classes='table table-striped')

    # Manually insert <thead> and <tbody>
    table_html = table_html.replace('<table ', '<table class="table table-striped" ')
    table_html = table_html.replace('<thead>', '<thead class="thead-light">')
    table_html = table_html.replace('<tbody>', '<tbody class="table-body">')

    return render_template('exploratory_analysis.html', uploaded_files=session['sheet_names'], column_names=column_names, table=table_html,image=None, selected_file=session["selected_file"], selected_sheet=session["selected_sheet"])

@app.route('/download_csv', methods=['GET'])
def download_csv():
    file_root, _ = os.path.splitext(session['selected_file'])
    temp_filename = os.path.join(app.config['TEMP_FOLDER'], file_root + "_exploratory_table.csv")
    if temp_filename and os.path.exists(temp_filename):
        return send_file( temp_filename, as_attachment=True, download_name=file_root + "_exploratory_table.csv", mimetype='text/csv')
    return "No table to download", 400

import matplotlib.pyplot as plt
from io import BytesIO
import base64

@app.route('/plot_graph', methods=['POST'])
def plot_graph():
    x_column = request.form['x_column']
    y_column = request.form['y_column']

    df = load_df(app)
    column_names=None
    if(df is not None):
        column_names = df.columns.tolist()

    plt.figure(figsize=(10, 6))
    plt.plot(df[x_column], df[y_column], marker='o', linestyle='')
    plt.title(f'Gráfico de {y_column} vs {x_column}')
    plt.xlabel(x_column)
    plt.ylabel(y_column)
    plt.grid(True)
    plt.tight_layout()

    img = BytesIO()
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)
    img_base64 = base64.b64encode(img.getvalue()).decode('utf-8')

    file_root, _ = os.path.splitext(session['selected_file'])
    image_filename = os.path.join(app.config['TEMP_FOLDER'], file_root + "_plot.png")
    with open(image_filename, 'wb') as f:
        f.write(img.getvalue())


    return render_template('exploratory_analysis.html', uploaded_files=session['sheet_names'], column_names=column_names, table=None, image=img_base64, selected_file=session["selected_file"], selected_sheet=session["selected_sheet"])

@app.route('/download_plot', methods=['GET'])
def download_plot():
    file_root, _ = os.path.splitext(session['selected_file'])
    temp_filename = os.path.join(app.config['TEMP_FOLDER'], file_root + "_plot.png")
    if temp_filename and os.path.exists(temp_filename):
        return send_file( temp_filename, as_attachment=True, download_name=file_root + "_plot.png", mimetype='png')
    return "No plot to download", 400


#da erro se tentar aplicar mudanças sem ter
@app.route('/apply_file_changes', methods=['GET'])
def apply_file_changes():
    file_name = session['selected_file']
    dict_sheet_names = session['sheet_names']
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
    df=load_df(app)
    if df is None:
        df = pd.DataFrame()
    temp_history=load_history(app,"r", temp=True)
    content = temp_history.read()
    temp_history.close()
    temp_history=load_history(app,"w", temp=True)
    temp_history.close()

    history=load_history(app,"a", temp=False)
    history.write(content)
    history.close()



        
    temp_history_pdf=load_history_pdf(app,"r", temp=True)
    content_pdf = temp_history_pdf.read()
    temp_history_pdf.close()
    temp_history_pdf=load_history_pdf(app,"w", temp=True)
    temp_history_pdf.close()

    history_pdf=load_history_pdf(app,"a", temp=False)
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
    return redirect(request.referrer or '/')


@app.route('/discard_file_changes', methods=['GET'])
def discard_file_changes():
    file_name = session['selected_file']
    dict_sheet_names = session['sheet_names']
    file_path = os.path.join(app.config['TEMP_FOLDER'], file_name)
    df=load_backup_df(app)
    temp_history=load_history(app,"w", temp=True)
    temp_history.close()

    temp_history_pdf=load_history_pdf(app,"w", temp=True)
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
def upload():
    if 'sheet_names' not in session:
        session['sheet_names'] = {}
        session['selected_file']=''
        session['selected_sheet']=''
    return render_template('upload.html', uploaded_files=session['sheet_names'], selected_file=session["selected_file"], selected_sheet=session["selected_sheet"])

@app.route('/display')
def display():
    try:
        # Carrega o DataFrame
        df = load_df(app)
        
        # Define os nomes das colunas para o dropdown
        column_names = df.columns.tolist()
        
        # Captura os parâmetros de paginação e filtragem da URL
        start = request.args.get('start', default=0, type=int)
        lines_by_page = request.args.get('lines_by_page', default=100, type=int)
        
        # Captura os parâmetros de filtro
        filter_column = request.args.get('filter_column')
        filter_operator = request.args.get('filter_operator')
        filter_value = request.args.get('filter_value')
        
        # Aplica o filtro ao DataFrame, se todos os parâmetros de filtro estiverem presentes
        if filter_column and filter_operator and filter_value:
            try:
                filter_value = float(filter_value) if filter_value.replace('.', '', 1).isdigit() else filter_value
                if filter_operator == "equals":
                    df = df[df[filter_column] == filter_value]
                elif filter_operator == "not_equals":
                    df = df[df[filter_column] != filter_value]
                elif filter_operator == "greater_than":
                    df = df[pd.to_numeric(df[filter_column], errors='coerce') > filter_value]
                elif filter_operator == "less_than":
                    df = df[pd.to_numeric(df[filter_column], errors='coerce') < filter_value]
                elif filter_operator == "greater_equal":
                    df = df[pd.to_numeric(df[filter_column], errors='coerce') >= filter_value]
                elif filter_operator == "less_equal":
                    df = df[pd.to_numeric(df[filter_column], errors='coerce') <= filter_value]
            except ValueError:
                pass  # Ignore filtering if conversion fails for non-numeric comparisons
        
        # Gera a tabela HTML com base nos dados filtrados e na paginação
        table_html = get_table(df, request, start, lines_by_page)
        
        # Renderiza o template com a tabela e os parâmetros
        return render_template(
            'display.html',
            table=table_html,
            uploaded_files=session['sheet_names'],
            selected_file=session["selected_file"],
            selected_sheet=session["selected_sheet"],
            start=start,
            lines_by_page=lines_by_page,
            num_lines=df.shape[0],
            column_names=column_names  # Passa os nomes das colunas para o template
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
            column_names=[]
        )

@app.route('/download_page')
def download_page():
    return render_template('download.html', uploaded_files=session['sheet_names'], selected_file=session["selected_file"], selected_sheet=session["selected_sheet"])

@app.route('/clean_data')
def clean_data():
    try:
        df = load_df(app)

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
                               num_lines=df.shape[0])
    except:
        return render_template('clean_data.html',
                                table=None,
                                uploaded_files=session['sheet_names'], 
                                column_names=[], 
                                selected_file=session["selected_file"], 
                                selected_sheet=session["selected_sheet"], 
                                start=0, 
                                lines_by_page=100,
                                num_lines=0)

@app.route('/exploratory_analysis')
def exploratory_analysis():
    df = load_df(app)
    column_names=None
    if(df is not None):
        column_names = df.columns.tolist()
    return render_template('exploratory_analysis.html', uploaded_files=session['sheet_names'], column_names=column_names, table=None,image=None, selected_file=session["selected_file"], selected_sheet=session["selected_sheet"])


@app.route('/history')
def history():
    try:
        history=load_history(app,"r",temp=False)
        content = history.read()
        history.close()
        return render_template('history.html',file_history=content,uploaded_files=session['sheet_names'], selected_file=session["selected_file"], selected_sheet=session["selected_sheet"])
    except:
        return render_template('history.html',file_history=None,uploaded_files=session['sheet_names'], selected_file=session["selected_file"], selected_sheet=session["selected_sheet"])

@app.route('/select_file/<file_name>')
def select_file(file_name):
    session['selected_file'] = file_name
    return redirect(request.referrer or '/')

@app.route('/select_file/<file_name>/<sheet_name>')
def select_sheet(file_name, sheet_name):
    session['selected_file'] = file_name
    session['selected_sheet'] = sheet_name
    return redirect(request.referrer or '/')

if __name__ == '__main__':
    app.run(debug=True)
