import os
from io import BytesIO
from flask import Blueprint,jsonify,request, send_file, send_from_directory
from datetime import datetime
from utils.auth_utils import login_required
from utils.project_utils import get_project_folder
import matplotlib

matplotlib.use('Agg')


survey_routes = Blueprint('survey_routes', __name__)


from xhtml2pdf import pisa
@survey_routes.route('/export_survey_pdf', methods=['GET'])
@login_required
def export_survey_pdf():
    temp_folder = get_project_folder('temp')
    survey_file = os.path.join(temp_folder, 'survey.html')
    pdf_path = os.path.join(temp_folder, 'survey.pdf')
    
    with open(survey_file, "r") as file:
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


@survey_routes.route('/add_plot_to_survey/<image_name>', methods=['GET'])
@login_required
def add_plot_to_survey(image_name):
    temp_folder = get_project_folder('temp')
    survey_file = os.path.join(temp_folder, 'survey.html')
    image_path = os.path.join(temp_folder, image_name)

    # Check if the image exists
    if os.path.exists(image_path):
        with open(survey_file, "a") as file:  # Append to the existing survey.html file
            # Log the addition of the plot
            formatted_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            file.write(f'<p>{formatted_time} - Gráfico adicionado:</p>')
            # Add the image to the file
            file.write(f'<img src="{image_path}" alt="{image_name}" style="width:100%; max-width:600px;"/>')

        # Return success response
        return jsonify({"status": "success", "message": f"Imagem {image_name} adicionada ao arquivo survey.html"}), 200

    return jsonify({"status": "error", "message": f"Imagem {image_name} não encontrada"}), 400

    
@survey_routes.route('/add_analysis_to_survey', methods=['POST'])
@login_required
def add_analysis_to_survey():
    temp_folder = get_project_folder('temp')
    survey_file = os.path.join(temp_folder, 'survey.html')

    try:
        analysis_text = request.json.get('analysis_text', None)

        if not analysis_text:
            return jsonify({"status": "error", "message": "Texto da análise está vazio."}), 400

        with open(survey_file, "a") as file:
            formatted_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            # Escape any HTML in the analysis text to prevent XSS vulnerabilities
            from markupsafe import escape
            safe_text = escape(analysis_text).replace("\n", "<br>")
            file.write(f'<p>{formatted_time} - Análise adicionada:</p>\n')
            file.write(f'<div>{safe_text}</div>\n')

        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Erro ao adicionar análise: {str(e)}"}), 500


@survey_routes.route('/download_plot/<filename>', methods=['GET'])
@login_required
def download_plot(filename):
    static_temp_folder = os.path.join('static', 'temp')
    return send_from_directory(static_temp_folder, filename, as_attachment=True)