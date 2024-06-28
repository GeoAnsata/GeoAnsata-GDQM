from flask import Flask, render_template, send_file, request, session, redirect, url_for, make_response
import pandas as pd
import tempfile
import os
from utils.info_tables import criar_tabela_continuo, criar_data_dict
from io import BytesIO
import matplotlib.pyplot as plt

UPLOAD_FOLDER = 'temp'
SECRET_KEY = 'your_secret_key'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = SECRET_KEY


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/download_sheet', methods=['GET'])
def download_sheet():
    file_name = request.args.get('file_name')
    selected_sheet = request.args.get('sheet')
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
    df = pd.read_excel(file_path, sheet_name=selected_sheet)
    temp_file_path = os.path.join(tempfile.gettempdir(), f"{file_name}_{selected_sheet}.csv")
    df.to_csv(temp_file_path, index=False)

    return send_file(temp_file_path, as_attachment=True, download_name=f"{file_name}_{selected_sheet}.csv", mimetype='text/csv')


@app.route('/download_csv', methods=['GET'])
def download_csv():
    file_name = request.args.get('file_name')
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)

    return send_file(file_path, as_attachment=True, mimetype='text/csv')


@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return render_template('index.html', error='Nenhum arquivo enviado!')
    
    file = request.files['file']
    if file.filename == '':
        return render_template('index.html', error='Nenhum arquivo selecionado!')

    if file:
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)
        if file.filename.endswith('.xlsx'):
            df = pd.read_excel(file_path, sheet_name=None)
            sheet_names = list(df.keys())
            return render_template('index.html', sheet_names=sheet_names, file_name=file.filename)
        elif file.filename.endswith('.csv'):
            df = pd.read_csv(file_path)
            # Armazenar DataFrame original para referência
            session['previous_data'] = df.to_dict(orient='records')

            # Armazenar DataFrame de pré-visualização e garantir ordenação pelo índice
            df_preview = df.copy()
            df_preview.sort_index(inplace=True)
            session['current_data'] = df_preview.to_dict(orient='records')

            column_names = df.columns.tolist()
            table = df_preview.to_html(classes='table table-striped')
            return render_template('index.html', table=table, file_name=file.filename, column_names=column_names)
        else:
            return render_template('index.html', error='Formato de arquivo inválido. Apenas arquivos do Excel (xlsx) e CSV são suportados.')



@app.route('/show_sheet', methods=['GET'])
def show_sheet():
    selected_sheet = request.args.get('sheet')
    file_name = request.args.get('file')

    if file_name:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
        if file_name.endswith('.xlsx'):
            df = pd.read_excel(file_path, sheet_name=selected_sheet)
            sheet_names = list(df.keys())
            column_names = df.columns.tolist()  # Lista de colunas
            table = df.to_html(classes='table table-striped')
        else:
            table = None
            column_names = None

    return render_template('index.html', table=table, sheet_names=sheet_names, file_name=file_name, sheet=selected_sheet, column_names=column_names, df=df)


@app.route('/criar_tabela_continuo', methods=['GET'])
def criar_tabela_continuo_route():
    colunas_selecionadas = request.args.getlist('colunas')

    df_selecionado = pd.DataFrame(session['current_data'])
    tabela_continua = criar_tabela_continuo(df_selecionado[colunas_selecionadas])

    return render_template('tabela_continua.html', tabela_continua=tabela_continua)


@app.route('/data_dict', methods=['GET'])
def criar_data_dict_route():
    file_name = request.args.get('file_name')
    selected_sheet = request.args.get('sheet')
    colunas_selecionadas = request.args.getlist('colunas')

    df_selecionado = pd.DataFrame(session['current_data'])
    data_dict = criar_data_dict(df_selecionado[colunas_selecionadas])

    return render_template('data_dict.html', data_dict=data_dict)


@app.route('/plot_graph', methods=['GET'])
def plot_graph():
    x_column = request.args.get('x_column')
    y_column = request.args.get('y_column')

    df = pd.DataFrame(session['current_data'])

    plt.figure()
    plt.plot(df[x_column], df[y_column])
    plt.xlabel(x_column)
    plt.ylabel(y_column)
    plt.title(f'{y_column} vs {x_column}')

    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)

    response = make_response(img.read())
    response.headers.set('Content-Type', 'image/png')
    response.headers.set('Content-Disposition', 'inline', filename='plot.png')

    return response


@app.route('/remove_columns', methods=['POST'])
def remove_columns():
    columns_to_remove = request.form.getlist('columns_to_remove')
    print(columns_to_remove)
    df_preview = pd.DataFrame(session['current_data'])

    # Remover colunas selecionadas
    df_preview.drop(columns=columns_to_remove, inplace=True, errors='raise')

    # Reordenar pelo índice das linhas após remoção de colunas
    df_preview.sort_index(inplace=True)

    session['current_data'] = df_preview.to_dict(orient='records')

    # Redirecionar para a rota 'show_data' após remoção de colunas
    return redirect(url_for('show_data'))


@app.route('/remove_rows', methods=['POST'])
def remove_rows():
    start_row = int(request.form.get('start_row'))
    end_row = int(request.form.get('end_row'))
    df_preview = pd.DataFrame(session['current_data'])
    if end_row >= len(df_preview):
        end_row = len(df_preview) - 1
    df_preview.drop(df_preview.index[start_row:end_row + 1], inplace=True)
    #ta mudando o index da linha depois de remover, tenho que pensar se quero que seja assim
    df_preview.sort_index(inplace=True)
    session['current_data'] = df_preview.to_dict(orient='records')

    return redirect(url_for('show_data'))


@app.route('/apply_changes', methods=['POST'])
def apply_changes():
    session['previous_data'] = session['current_data']
    return redirect(url_for('show_data'))


@app.route('/discard_changes', methods=['POST'])
def discard_changes():
    session['current_data'] = session['previous_data']
    return redirect(url_for('show_data'))


@app.route('/show_data', methods=['GET'])
def show_data():
    df = pd.DataFrame(session['current_data'])
    df.sort_index(inplace=True)
    column_names = df.columns.tolist()
    table = df.to_html(classes='table table-striped')
    return render_template('index.html', table=table, column_names=column_names, df=df)


if __name__ == '__main__':
    app.run(debug=True)
