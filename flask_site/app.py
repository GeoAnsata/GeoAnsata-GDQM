from flask import Flask, render_template,send_file, request
import pandas as pd
import tempfile
import os
from utils.info_tables import criar_tabela_continuo
UPLOAD_FOLDER = 'temp'

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download_sheet', methods=['GET'])
def download_sheet():
    file_name = request.args.get('file_name')
    selected_sheet = request.args.get('sheet')
    file_path = os.path.join(UPLOAD_FOLDER, file_name)
    df = pd.read_excel(file_path, sheet_name=selected_sheet)
    temp_file_path = os.path.join(tempfile.gettempdir(), f"{file_name}_{selected_sheet}.csv")
    df.to_csv(temp_file_path, index=False)

    return send_file(temp_file_path, as_attachment=True,download_name=f"{file_name}_{selected_sheet}.csv", mimetype='text/csv')


@app.route('/download_csv', methods=['GET'])
def download_csv():
    file_name = request.args.get('file_name')
    file_path = os.path.join(UPLOAD_FOLDER, file_name)

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
            table = df.to_html(classes='table table-striped')
            return render_template('index.html', table=table, file_name=file.filename)
        else:
            return render_template('index.html', error='Formato de arquivo inválido. Apenas arquivos do Excel (xlsx) e CSV são suportados.')



@app.route('/criar_tabela_continuo', methods=['POST'])
def criar_tabela_continuo_route():
    file_name = request.args.get('file_name')
    colunas_selecionadas = request.form.getlist('colunas[]')
    selected_sheet = request.args.get('sheet')
    file_path = os.path.join(UPLOAD_FOLDER, file_name)
    df_selecionado = pd.read_excel(file_path, sheet_name=selected_sheet)
    tabela_continua = criar_tabela_continuo(df_selecionado)
    # Agora você pode renderizar a tabela_continua como desejar, por exemplo:
    return render_template('tabela_continua.html', tabela_continua=tabela_continua.to_html())



@app.route('/show_sheet', methods=['GET'])
def show_sheet():
    selected_sheet = request.args.get('sheet_name')
    file_name = request.args.get('file')

    if file_name:
        file_path = os.path.join(UPLOAD_FOLDER, file_name)
        if file_name.endswith('.xlsx'):
            df = pd.read_excel(file_path, sheet_name=None)
            sheet_names = list(df.keys())
            if selected_sheet not in sheet_names:
                selected_sheet = sheet_names[0] if sheet_names else None
            df_selected = pd.read_excel(file_path, sheet_name=selected_sheet)
        elif file_name.endswith('.csv'):
            df_selected = pd.read_csv(file_path)
            sheet_names = None
        column_names = df_selected.columns.tolist()  # Lista de colunas
        table = df_selected.to_html(classes='table table-striped')
    else:
        table = None
        sheet_names = None
        column_names = None

    return render_template('index.html', table=table, sheet_names=sheet_names, file_name=file_name, sheet=selected_sheet, column_names=column_names)




if __name__ == '__main__':
    app.run(debug=True)