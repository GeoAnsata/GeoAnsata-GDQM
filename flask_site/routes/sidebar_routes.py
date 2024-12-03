import os
import pandas as pd
from flask import Blueprint,session, redirect, request,url_for
from utils.load_df import load_history_pdf
from utils.auth_utils import login_required
from utils.project_utils import get_project_folder
from utils.load_df import load_df, load_history, load_backup_df


sidebar_routes = Blueprint('sidebar_routes', __name__)


@sidebar_routes.route('/apply_file_changes', methods=['GET'])
@login_required
def apply_file_changes():
    try:
        temp_folder = get_project_folder('temp')
        upload_folder = get_project_folder('upload')
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
            return redirect(url_for('pages_routes.exploratory_analysis', _external=True))
        return redirect(request.referrer or '/')
    
@sidebar_routes.route('/discard_file_changes', methods=['GET'])
@login_required
def discard_file_changes():
    temp_folder = get_project_folder('temp')
    upload_folder = get_project_folder('upload')
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


@sidebar_routes.route('/select_file/<file_name>')
@login_required
def select_file(file_name):
    session['selected_file'] = file_name
    return redirect(request.referrer or '/')

@sidebar_routes.route('/select_file/<file_name>/<sheet_name>')
@login_required
def select_sheet(file_name, sheet_name):
    session['selected_file'] = file_name
    session['selected_sheet'] = sheet_name
    return redirect(request.referrer or '/')
