import pandas as pd
import os
from flask import session
def load_df(app):
    try:
        file_name = session['selected_file']
        dict_sheet_names = session['sheet_names']
        file_path = os.path.join(app.config['TEMP_FOLDER'], file_name)
        if file_name.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_name.endswith('.xlsx') and (len(dict_sheet_names[file_name])>0):
            selected_sheet=session['selected_sheet']
            file_root, _ = os.path.splitext(file_path)
            df = pd.read_csv(file_root + "_" + selected_sheet + ".csv")
        elif file_name.endswith('.xlsx'):
            df = pd.read_excel(file_path, sheet_name=0)
        return df
    except:
        return None
    

    
def load_history(app,acess_mode="a", temp=True):
    if(temp):
        folder='TEMP_FOLDER'
    else:
        folder='UPLOAD_FOLDER'

    try:
        file_name = session['selected_file']
        dict_sheet_names = session['sheet_names']
        file_root, _ = os.path.splitext(file_name)
        if file_name.endswith('.xlsx') and (len(dict_sheet_names[file_name])>0):
            selected_sheet=session['selected_sheet']
            history = open(os.path.join(app.config[folder], file_root + "_" + selected_sheet + ".txt"), acess_mode)
        else:
            history = open(os.path.join(app.config[folder], file_root + ".txt"), acess_mode)
        return history
    except:
        return None

def load_backup_df(app):
    try:
        file_name = session['selected_file']
        dict_sheet_names = session['sheet_names']
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
        if file_name.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_name.endswith('.xlsx') and (len(dict_sheet_names[file_name])>0):
            selected_sheet=session['selected_sheet']
            df = pd.read_excel(file_path, sheet_name=selected_sheet)
        elif file_name.endswith('.xlsx'):
            df = pd.read_excel(file_path, sheet_name=0)
        return df
    except:
        return None