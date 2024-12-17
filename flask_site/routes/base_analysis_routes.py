import os

from flask import Blueprint,session,send_file,jsonify
from io import BytesIO
from datetime import datetime
from utils.auth_utils import login_required
from utils.project_utils import get_project_folder


base_analysis_routes = Blueprint('base_analysis_routes', __name__)


from xhtml2pdf import pisa
@base_analysis_routes.route('/export_base_analysis_pdf', methods=['GET'])
@login_required
def export_base_analysis_pdf():
    temp_folder = get_project_folder('temp')
    base_analysis_file = os.path.join(temp_folder, 'base_analysis.html')
    pdf_path = os.path.join(temp_folder, 'base_analysis.pdf')
    
    with open(base_analysis_file, "r") as file:
        html_content = file.read()
    with open("./templates/includes/history_pdf.html", "r") as file:
        html_style = file.read()

    html_content = f"""
    <div>
        {html_content}  <!-- Include the complete table HTML -->
    </div>
    {html_style}  <!-- Include the updated styles -->
    """
    pdf_output = BytesIO()
    # Generate the PDF
    pisa.CreatePDF(html_content, dest=pdf_output, encoding='utf-8')
    # Open a PDF file for writing in binary mode
    with open(pdf_path, "wb") as pdf_file:
            pdf_file.write(pdf_output.getvalue())
    # Return the generated PDF
    return send_file(pdf_path, as_attachment=True)

@base_analysis_routes.route('/add_table_to_base_analysis', methods=['GET'])
@login_required
def add_table_to_history():
    temp_folder = get_project_folder('temp')
    base_analysis_file = os.path.join(temp_folder, 'base_analysis.html')
    table_html = session['table_html']
    file_name = session['selected_file']
    sheet_name = session['selected_sheet']
    try:
        with open(base_analysis_file, "a") as file:
            # Log the addition of the plot to the history
            formatted_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            if(sheet_name):
                file.write(f'<p>{formatted_time} - Tabela da página {sheet_name} do arquivo {file_name} adicionada a histórico</p>')
            else:
                file.write(f'<p>{formatted_time} - Tabela do arquivo {file_name} adicionada a histórico</p>')
            # Include image in the HTML by adding an <img> tag
            file.write(f'<div class="table-responsive">{table_html}</div>')
        

        # Return success response
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Erro: {str(e)}")  # Log no terminal
        return jsonify({"status": "error", "message": f"Erro ao adicionar tabela: {str(e)}"}), 400


@base_analysis_routes.route('/add_plot_to_base_analysis', methods=['GET'])
@login_required
def add_plot_to_history():
    temp_folder = get_project_folder('temp')
    base_analysis_file = os.path.join(temp_folder, 'base_analysis.html')
    temp_filename = session['image_filename']
    file_name = session['selected_file']
    sheet_name = session['selected_sheet']
    
    if temp_filename and os.path.exists(temp_filename):
        with open(base_analysis_file, "a") as file:
            # Log the addition of the plot to the history
            formatted_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            if(sheet_name):
                file.write(f'<p>{formatted_time} - Gráfico da página {sheet_name} do arquivo {file_name} adicionada a histórico</p>')
            else:
                file.write(f'<p>{formatted_time} - Gráfico do arquivo {file_name} adicionada a histórico</p>')
            # Include image in the HTML by adding an <img> tag
            file.write(f'<img src="{temp_filename}" alt="Gráfico" style="width:100%; max-width:600px;"/>')
            

        # Return success response
        return jsonify({"status": "success"}), 200
    
    return jsonify({"status": "error", "message": "Não há gráfico para adicionar a histórico"}), 400
