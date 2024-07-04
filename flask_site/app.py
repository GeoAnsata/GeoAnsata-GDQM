from flask import Flask, render_template, request, redirect, url_for, send_file, session
from utils.clear_directory import clear_directory
import tempfile
import os
import pandas as pd
import shutil

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
        file_name = session['selected_file']
        dict_sheet_names = session['sheet_names']
        file_path = os.path.join(app.config['TEMP_FOLDER'], file_name)
        if file_name.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_name.endswith('.xlsx') and (len(dict_sheet_names[file_name])>0):
            selected_sheet=session['selected_sheet']
            df = pd.read_excel(file_path, sheet_name=selected_sheet)
        elif file_name.endswith('.xlsx'):
            df = pd.read_excel(file_path, sheet_name=0)

        df.sort_index(inplace=True)
        df=df.head(100)
        return render_template('display.html', table=df.to_html(classes='table table-striped'), uploaded_files=session['sheet_names'])
    except:
        return render_template('display.html', table=None, uploaded_files=session['sheet_names'])
    
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
    return render_template('clean_data.html', uploaded_files=session['sheet_names'])

@app.route('/exploratory_analysis')
def exploratory_analysis():
    return render_template('exploratory_analysis.html', uploaded_files=session['sheet_names'])

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
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
