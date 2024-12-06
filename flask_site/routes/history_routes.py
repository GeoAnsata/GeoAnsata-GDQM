import os

from flask import Blueprint,session,send_file,jsonify
from io import BytesIO
from datetime import datetime
from utils.load_df import load_history_pdf
from utils.auth_utils import login_required
from utils.project_utils import get_project_folder


history_routes = Blueprint('history_routes', __name__)


from xhtml2pdf import pisa
@history_routes.route('/export_pdf', methods=['GET'])
@login_required
def export_pdf():
    upload_folder = get_project_folder('upload')
    file_name = session['selected_file']
    dict_sheet_names = session['sheet_names']
    file_root, _ = os.path.splitext(file_name)
    if file_name.endswith('.xlsx') and (len(dict_sheet_names[file_name])>0):
        selected_sheet=session['selected_sheet']
        history_path = os.path.join(upload_folder, file_root + "_" + selected_sheet + "complete.html")
        pdf_path = os.path.join(upload_folder, 'history' + selected_sheet + '.pdf')
    else:
        history_path = os.path.join(upload_folder, file_root + "complete.html")
        pdf_path = os.path.join(upload_folder, 'history' + file_root + '.pdf')
    

    with open(history_path, "r") as file:
        html_content = file.read()

    with open("./templates/includes/history_pdf.html", "r") as file:
        html_style = file.read()

    pdf_output = BytesIO()
    # Generate the PDF

    pisa.CreatePDF(html_content + html_style, dest=pdf_output, encoding='utf-8')
    # Open a PDF file for writing in binary mode
    with open(pdf_path, "wb") as pdf_file:
    
        # Write the PDF content to the file
        pdf_file.write(pdf_output.getvalue())
    # Return the generated PDF
    return send_file(pdf_path, as_attachment=True)

@history_routes.route('/add_table_to_history', methods=['GET'])
@login_required
def add_table_to_history():
    temp_folder = get_project_folder('temp')
    table_html = session['table_html']
    print(table_html)
    try:
        # Load complete history (for HTML storage)
        complete_history = load_history_pdf(temp_folder)

        # Log the addition of the plot to the history
        formatted_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        complete_history.write(f'<p>{formatted_time} - Tabela adicionada a histórico</p>')

        # Include image in the HTML by adding an <img> tag
        complete_history.write(f'<div class="table-responsive">{table_html}</div>')
        complete_history.close()

        # Return success response
        return jsonify({"status": "success"}), 200
    except:
        return jsonify({"status": "error", "message": "Não há gráfico para adicionar a histórico"}), 400

@history_routes.route('/add_plot_to_history', methods=['GET'])
@login_required
def add_plot_to_history():
    temp_folder = get_project_folder('temp')
    temp_filename = session['image_filename']
    
    if temp_filename and os.path.exists(temp_filename):
        # Load complete history (for HTML storage)
        complete_history = load_history_pdf(temp_folder)

        # Log the addition of the plot to the history
        formatted_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        complete_history.write(f'<p>{formatted_time} - Gráfico adicionado a histórico</p>')

        # Include image in the HTML by adding an <img> tag
        complete_history.write(f'<img src="{temp_filename}" alt="Gráfico" style="width:100%; max-width:600px;"/>')
        complete_history.close()

        # Return success response
        return jsonify({"status": "success"}), 200
    
    return jsonify({"status": "error", "message": "Não há gráfico para adicionar a histórico"}), 400
