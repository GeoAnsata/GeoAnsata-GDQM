import os
import pandas as pd
from flask import session
from utils.project_utils import get_project_folder

def load_existing_files():
    """Load existing files in the user's upload folder and update session['sheet_names'] with their sheet names."""
    upload_folder = get_project_folder('upload')
    dict_sheet_names = {}

    # Iterate through existing files in the upload folder
    for filename in os.listdir(upload_folder):
        file_path = os.path.join(upload_folder, filename)
        _, file_ext = os.path.splitext(filename)

        # Process Excel files
        if file_ext == '.xlsx':
            df = pd.read_excel(file_path, sheet_name=None, engine="openpyxl")
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