from flask import Flask, render_template, send_file, request, session, redirect, url_for, make_response
import pandas as pd
import tempfile
import os
from utils.info_tables import criar_tabela_continuo, criar_data_dict
from io import BytesIO
import matplotlib.pyplot as plt


# O LITHO E ASSAY SAO MUITO GRANDES AI EU NAO CONSIGO CARREGAR ELES NO SESSION STORAGE
UPLOAD_FOLDER = 'D:/GeoAnsata/AnaliseExploratoria/flask_site/temp'
SECRET_KEY = 'your_secret_key'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = SECRET_KEY


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/download_sheet', methods=['GET'])
def download_sheet():
    file_name = session['file_name']
    selected_sheet = session['selected_sheet']
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
    df = pd.read_excel(file_path, sheet_name=selected_sheet)
    temp_file_path = os.path.join(tempfile.gettempdir(), f"{file_name}_{selected_sheet}.csv")
    df.to_csv(temp_file_path, index=False)

    return send_file(temp_file_path, as_attachment=True, download_name=f"{file_name}_{selected_sheet}.csv", mimetype='text/csv')


#VOU TER QUE MUDAR
@app.route('/download_csv', methods=['GET'])
def download_csv():
    file_name=session['file_name']
    file_path = os.path.join(UPLOAD_FOLDER, file_name)
    
    if file_path.endswith('.xlsx'):
        return send_file(file_path, as_attachment=True, download_name=file_name, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    elif file_path.endswith('.csv'):
        return send_file(file_path, as_attachment=True, download_name=file_name, mimetype='text/csv')





@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return render_template('index.html', error='Nenhum arquivo enviado!')
    
    file = request.files['file']
    if file.filename == '':
        return render_template('index.html', error='Nenhum arquivo selecionado!')
    else:
        session['file_name']=file.filename
        session['sheet_names']=[]
        session['selected_sheet']=''

    if file:
        
        if file.filename.endswith('.xlsx'):
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)

            df = pd.read_excel(file, sheet_name=None)
            session['sheet_names'] = list(df.keys())
            

            return render_template('index.html', sheet_names=session['sheet_names'], file_name=session['file_name'])
        
        elif file.filename.endswith('.csv'):
            df = pd.read_csv(file)
            df.sort_index(inplace=True)
            
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            df.to_csv(file_path,index=False)

            file_path = os.path.join(UPLOAD_FOLDER, 'temp.csv')
            df.to_csv(file_path,index=False)

            column_names = df.columns.tolist()
            table = df.to_html(classes='table table-striped')
            return render_template('index.html', table=table, column_names=column_names)
        else:
            return render_template('index.html', error='Formato de arquivo inválido. Apenas arquivos do Excel (xlsx) e CSV são suportados.')



@app.route('/show_sheet', methods=['GET'])
def show_sheet():
    selected_sheet = request.args.get('sheet')
    print(selected_sheet)
    if(selected_sheet==None):
        selected_sheet=session['selected_sheet']
    print(selected_sheet)
    session['selected_sheet']=selected_sheet
    file_name=session['file_name']

    if file_name:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
        if file_name.endswith('.xlsx'):
            df = pd.read_excel(file_path, sheet_name=selected_sheet)
            df.to_csv(os.path.join(UPLOAD_FOLDER, 'temp.csv'),index=False)
            column_names = df.columns.tolist()  # Lista de colunas
            table = df.to_html(classes='table table-striped')
        else:
            table = None
            column_names = None

    return render_template('index.html', table=table, sheet_names=session['sheet_names'], file_name=session['file_name'], sheet=selected_sheet, column_names=column_names, df=df)




@app.route('/criar_tabela_continuo', methods=['GET'])
def criar_tabela_continuo_route():
    colunas_selecionadas = request.args.getlist('colunas')
    selected_sheet = session['selected_sheet']
    file_path = os.path.join(UPLOAD_FOLDER, 'temp.csv')
    df_selecionado = pd.read_csv(file_path)

    tabela_continua = criar_tabela_continuo(df_selecionado[colunas_selecionadas])


    return render_template('tabela_continua.html', tabela_continua=tabela_continua)


@app.route('/data_dict', methods=['GET'])
def criar_data_dict_route():
    colunas_selecionadas = request.args.getlist('colunas')
    selected_sheet = session['selected_sheet']
    file_path = os.path.join(UPLOAD_FOLDER, 'temp.csv')
    df_selecionado = pd.read_csv(file_path)
    data_dict = criar_data_dict(df_selecionado[colunas_selecionadas])

    return render_template('data_dict.html', data_dict=data_dict)



@app.route('/remove_columns', methods=['POST'])
def remove_columns():
    columns_to_remove = request.form.getlist('columns_to_remove')
    file_path = os.path.join(UPLOAD_FOLDER, 'temp.csv')
    df_preview = pd.read_csv(file_path)
    print(df_preview)

    # Remover colunas selecionadas
    df_preview.drop(columns=columns_to_remove, inplace=True, errors='raise')

    # Reordenar pelo índice das linhas após remoção de colunas
    df_preview.sort_index(inplace=True)

    df_preview.to_csv(file_path, index=False)

    # Redirecionar para a rota 'show_data' após remoção de colunas
    return redirect(url_for('show_data'))


@app.route('/remove_rows', methods=['POST'])
def remove_rows():
    start_row = int(request.form.get('start_row'))
    end_row = int(request.form.get('end_row'))

    file_path =os.path.join(UPLOAD_FOLDER, 'temp.csv')
    df_preview = pd.read_csv(file_path)

    if end_row >= len(df_preview):
        end_row = len(df_preview) - 1
    df_preview.drop(df_preview.index[start_row:end_row + 1], inplace=True)
    #ta mudando o index da linha depois de remover, tenho que pensar se quero que seja assim

    df_preview.sort_index(inplace=True)

    df_preview.to_csv(file_path, index=False)

    return redirect(url_for('show_data'))


@app.route('/apply_changes', methods=['POST'])
def apply_changes():
    selected_sheet = session['selected_sheet']
    preview_file_path = os.path.join(UPLOAD_FOLDER, 'temp.csv')
    file_path=os.path.join(UPLOAD_FOLDER, session['file_name'])
    df_preview = pd.read_csv(preview_file_path)


    if file_path.endswith('.xlsx'):
        excel_df = pd.read_excel(file_path, sheet_name=None)
        excel_df[selected_sheet]=df_preview
        with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
            for sheet_name, df in excel_df.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        return redirect(url_for('show_sheet'))

    elif file_path.endswith('.csv'):
        df_preview.to_csv(file_path,index=False)
        return redirect(url_for('show_data'))



@app.route('/discard_changes', methods=['POST'])
def discard_changes():
    selected_sheet = session['selected_sheet']
    preview_file_path = os.path.join(UPLOAD_FOLDER, 'temp.csv')
    file_path=os.path.join(UPLOAD_FOLDER, session['file_name'])
    if selected_sheet != '':
        excel_df = pd.read_excel(file_path, sheet_name=None)
        excel_df[selected_sheet].to_csv(preview_file_path,index=False)
        return redirect(url_for('show_sheet'))
    else:
        df=pd.read_csv(file_path)
        df.to_csv(preview_file_path,index=False)
        return redirect(url_for('show_data'))


@app.route('/show_data', methods=['GET'])
def show_data():
    preview_file_path = os.path.join(UPLOAD_FOLDER, 'temp.csv')
    df = pd.read_csv(preview_file_path)
    df.sort_index(inplace=True)

    column_names = df.columns.tolist()

    return render_template('index.html', table=df.to_html(classes='table table-striped'), column_names=column_names, df=df)



@app.route('/plot_graph', methods=['GET', 'POST'])
def plot_graph():
    if request.method == 'POST':
        x_column = request.form['x_column']
        y_column = request.form['y_column']

        file_path = os.path.join(UPLOAD_FOLDER, 'temp.csv')
        df = pd.read_csv(file_path)

        plt.figure(figsize=(10, 6))
        plt.plot(df[x_column], df[y_column], marker='o', linestyle='-')
        plt.title(f'Gráfico de {y_column} vs {x_column}')
        plt.xlabel(x_column)
        plt.ylabel(y_column)
        plt.grid(True)
        plt.tight_layout()

        img = BytesIO()
        plt.savefig(img)
        img.seek(0)

        return send_file(img, mimetype='image/png')

    else:
        file_path = os.path.join(UPLOAD_FOLDER, 'temp.csv')
        df = pd.read_csv(file_path)
        column_names = df.columns.tolist()

        return render_template('plot_graph.html', column_names=column_names)




if __name__ == '__main__':
    app.run(debug=True)
