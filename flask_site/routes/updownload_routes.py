import os
import shutil
import tempfile
import pandas as pd
from flask import Blueprint,session, redirect, request,url_for, render_template,send_file
from utils.auth_utils import login_required
from utils.project_utils import get_project_folder



updownload_routes = Blueprint('updownload_routes', __name__)



@updownload_routes.route('/upload_file', methods=['POST'])
@login_required
def upload_file():
    if 'files' not in request.files:
        return render_template('upload.html', error='Nenhum arquivo enviado!')
    files = request.files.getlist('files')
    dict_sheet_names=session['sheet_names']
    upload_folder = get_project_folder('upload')
    temp_folder = get_project_folder('temp')
    for file in files:
        if file.filename == '':
            return render_template('upload.html', error='Nenhum arquivo selecionado!')
        file_root, _ = os.path.splitext(file.filename)
        if file and file.filename.endswith('.xlsx'):
            upload_path = os.path.join(upload_folder, file.filename)
            file.save(upload_path)
            
            temp_path = os.path.join(temp_folder, file.filename)
            shutil.copy(upload_path, temp_path)


            df = pd.read_excel(file, sheet_name=None, engine="openpyxl")
            sheet_names=list(df.keys())
            if(len(sheet_names)>1):
                dict_sheet_names[file.filename]=sheet_names
                for sheet_name in sheet_names:
                    df=pd.read_excel(file,sheet_name=sheet_name, engine="openpyxl")
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
    return redirect(url_for('pages_routes.upload', _external=True))

@updownload_routes.route('/download_sheet/<file_name>/<sheet_name>', methods=['GET'])
@login_required
def download_sheet(file_name,sheet_name):
    upload_folder = get_project_folder('upload')
    file_path = os.path.join(upload_folder, file_name)
    df = pd.read_excel(file_path, sheet_name=sheet_name, engine="openpyxl")
    temp_file_path = os.path.join(tempfile.gettempdir(), f"{file_name}_{sheet_name}.csv")
    df.to_csv(temp_file_path, index=False)

    return send_file(temp_file_path, as_attachment=True, download_name=f"{file_name}_{sheet_name}.csv", mimetype='text/csv')

@updownload_routes.route('/download_file/<file_name>', methods=['GET'])
@login_required
def download_file(file_name):
    upload_folder = get_project_folder('upload')
    temp_folder = get_project_folder('temp')
    file_path = os.path.join(upload_folder, file_name)
    
    if file_path.endswith('.xlsx'):
        return send_file(file_path, as_attachment=True, download_name=file_name, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    elif file_path.endswith('.csv'):
        return send_file(file_path, as_attachment=True, download_name=file_name, mimetype='text/csv')
