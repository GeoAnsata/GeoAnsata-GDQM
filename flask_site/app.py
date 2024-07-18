from flask import Flask, render_template, request, redirect, url_for, send_file, session
from utils.clear_directory import clear_directory
from utils.info_tables import *
from utils.load_df import *
import tempfile
import os
import pandas as pd
import shutil
#TODO fazer com que as tabelas carregadas possam ter o tamanho que o utilizador quiser, atualmente ta 100
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


@app.route('/upload', methods=['POST'])
def upload():
    if 'files' not in request.files:
        return render_template('index.html', error='Nenhum arquivo enviado!')
    files = request.files.getlist('files')
    dict_sheet_names=session['sheet_names']
    for file in files:
        if file.filename == '':
            return render_template('index.html', error='Nenhum arquivo selecionado!')
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
                    file_root, _ = os.path.splitext(file.filename)
                    df.to_csv(os.path.join(app.config['TEMP_FOLDER'], file_root + "_" + sheet_name + ".csv"),index=False)
            else:
                dict_sheet_names[file.filename]=[]

        elif file and file.filename.endswith('.csv'):
            dict_sheet_names[file.filename]=[]
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(upload_path)
            
            # Copy to TEMP_FOLDER
            temp_path = os.path.join(app.config['TEMP_FOLDER'], file.filename)
            shutil.copy(upload_path, temp_path)
    session['sheet_names']=dict_sheet_names
    return redirect(url_for('index'))


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


def show_data():
    try:
        df =load_df(app)
        df.sort_index(inplace=True)
        df=df.head(100)
        table_html = df.to_html(classes='table table-striped')

        # Manually insert <thead> and <tbody>
        table_html = table_html.replace('<table ', '<table class="table table-striped" ')
        table_html = table_html.replace('<thead>', '<thead class="thead-light">')
        table_html = table_html.replace('<tbody>', '<tbody class="table-body">')

        return render_template('display.html', table=table_html, uploaded_files=session['sheet_names'])
    except:
        return render_template('display.html', table=None, uploaded_files=session['sheet_names'])
    
    
#é possivel otimizar isso se eu em vez de salvar o excel salvar cada uma das sheets dele e so na hora de aplicar mudanças eu junto elas em um excel
@app.route('/remove_columns', methods=['POST'])
def remove_columns():
    columns_to_remove = request.form.getlist('columns_to_remove')
    file_name = session['selected_file']
    dict_sheet_names = session['sheet_names']
    file_path = os.path.join(app.config['TEMP_FOLDER'], file_name)
    df=load_df(app)
    df.drop(columns=columns_to_remove, inplace=True, errors='raise')
    df.sort_index(inplace=True)

    if file_name.endswith('.csv'):
        df.to_csv(file_path,index=False)
    elif file_name.endswith('.xlsx') and (len(dict_sheet_names[file_name])>0):
        selected_sheet=session['selected_sheet']
        file_root, _ = os.path.splitext(file_name)
        df.to_csv(os.path.join(app.config['TEMP_FOLDER'], file_root + "_" + selected_sheet + ".csv"),index=False)
        #with pd.ExcelWriter(file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            #df.to_excel(writer, sheet_name=selected_sheet, index=False)
    elif file_name.endswith('.xlsx'):
        df.to_excel(file_path,index=False)


    return redirect(url_for('clean_data'))


@app.route('/remove_rows', methods=['POST'])
def remove_rows():
    start_row = int(request.form.get('start_row'))
    end_row = int(request.form.get('end_row'))
    file_name = session['selected_file']
    dict_sheet_names = session['sheet_names']
    file_path = os.path.join(app.config['TEMP_FOLDER'], file_name)
    df=load_df(app)
    if end_row >= len(df):
        end_row = len(df) - 1
    df.drop(df.index[start_row:end_row + 1], inplace=True)
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



@app.route('/criar_tabela_continuo', methods=['GET'])
def criar_tabela_continuo_route():
    colunas_selecionadas = request.args.getlist('colunas')
    df = load_df(app)
    tabela_continua = criar_tabela_continuo(df[colunas_selecionadas])
    column_names=None
    if(df is not None):
        column_names = df.columns.tolist()

    table_html = tabela_continua.to_html(classes='table table-striped')

    # Manually insert <thead> and <tbody>
    table_html = table_html.replace('<table ', '<table class="table table-striped" ')
    table_html = table_html.replace('<thead>', '<thead class="thead-light">')
    table_html = table_html.replace('<tbody>', '<tbody class="table-body">')

    return render_template('exploratory_analysis.html', uploaded_files=session['sheet_names'], column_names=column_names, table=table_html)


@app.route('/data_dict', methods=['GET'])
def criar_data_dict_route():
    colunas_selecionadas = request.args.getlist('colunas')
    df = load_df(app)
    data_dict = criar_data_dict(df[colunas_selecionadas])
    column_names=None
    if(df is not None):
        column_names = df.columns.tolist()

    table_html = data_dict.to_html(classes='table table-striped')

    # Manually insert <thead> and <tbody>
    table_html = table_html.replace('<table ', '<table class="table table-striped" ')
    table_html = table_html.replace('<thead>', '<thead class="thead-light">')
    table_html = table_html.replace('<tbody>', '<tbody class="table-body">')

    return render_template('exploratory_analysis.html', uploaded_files=session['sheet_names'], column_names=column_names, table=table_html)


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

    return render_template('exploratory_analysis.html', uploaded_files=session['sheet_names'], column_names=column_names, table=None, image=img_base64)
    
@app.route('/apply_file_changes', methods=['GET'])
def apply_file_changes():
    file_name = session['selected_file']
    dict_sheet_names = session['sheet_names']
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
    df=load_df(app)
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
    if file_name.endswith('.csv'):
        df.to_csv(file_path,index=False)
    elif file_name.endswith('.xlsx') and (len(dict_sheet_names[file_name])>0):
        selected_sheet=session['selected_sheet']
        file_root, _ = os.path.splitext(file_path)
        df.to_csv(file_root + "_" + selected_sheet + ".csv",index=False)
    elif file_name.endswith('.xlsx'):
        df.to_excel(file_path,index=False)
    return redirect(request.referrer or '/')


#@app.route('/apply_all_changes', methods=['GET'])
#def apply_all_changes():
#    dict_sheet_names = session['sheet_names']


#@app.route('/discard_all_changes', methods=['GET'])


@app.route('/')
def index():
    return render_template('index.html', uploaded_files=session['sheet_names'])

@app.route('/display')
def display():
    return show_data()

@app.route('/download_page')
def download_page():
    return render_template('download.html', uploaded_files=session['sheet_names'])

@app.route('/clean_data')
def clean_data():
    try:
        df = load_df(app)
        column_names = df.columns.tolist()
        df.sort_index(inplace=True)
        df=df.head(100)
        table_html = df.to_html(classes='table table-striped')

        # Manually insert <thead> and <tbody>
        table_html = table_html.replace('<table ', '<table class="table table-striped" ')
        table_html = table_html.replace('<thead>', '<thead class="thead-light">')
        table_html = table_html.replace('<tbody>', '<tbody class="table-body">')

        return render_template('clean_data.html', table=table_html, uploaded_files=session['sheet_names'], column_names=column_names)
    except:
        return render_template('clean_data.html', table=None, uploaded_files=session['sheet_names'], column_names=[])

@app.route('/exploratory_analysis')
def exploratory_analysis():
    df = load_df(app)
    column_names=None
    if(df is not None):
        column_names = df.columns.tolist()
    return render_template('exploratory_analysis.html', uploaded_files=session['sheet_names'], column_names=column_names, table=None)

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
