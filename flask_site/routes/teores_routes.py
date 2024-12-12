import os

from flask import Blueprint,session,send_file,jsonify,request, render_template, send_from_directory
from io import BytesIO
from datetime import datetime
from utils.auth_utils import login_required
from utils.project_utils import get_project_folder
from utils.load_df import load_df
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')


teores_routes = Blueprint('teores_routes', __name__)


from xhtml2pdf import pisa
@teores_routes.route('/export_teores_pdf', methods=['GET'])
@login_required
def export_teores_pdf():
    temp_folder = get_project_folder('temp')
    teores_file = os.path.join(temp_folder, 'teores.html')
    pdf_path = os.path.join(temp_folder, 'teores.pdf')
    
    with open(teores_file, "r") as file:
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

@teores_routes.route('/generate_boxplots', methods=['POST'])
@login_required
def generate_boxplots():
    temp_folder = get_project_folder('temp')  # Usar a pasta temporária
    os.makedirs(temp_folder, exist_ok=True)

    df = load_df(temp_folder)

    # Colunas selecionadas pelo usuário
    selected_columns = request.form.getlist('selected_columns')

    if not selected_columns:
        return jsonify({"error": "Selecione ao menos uma coluna para gerar o gráfico."}), 400

    # Gerar o gráfico de boxplot
    plt.figure(figsize=(10, 6))
    df[selected_columns].boxplot()
    plt.title("Boxplots das Colunas Selecionadas")
    plt.ylabel("Valores")
    plt.grid(True)
    
    # Salvar o gráfico
    boxplot_file = os.path.join(temp_folder, 'boxplots_selected_columns.png')
    plt.savefig(boxplot_file)
    plt.close()

    return render_template(
        'teores.html',
        column_names=df.columns.tolist(),
        plot_files={'boxplot': 'boxplots_selected_columns.png'}
    )


@teores_routes.route('/download_plot/<filename>', methods=['GET'])
@login_required
def download_plot(filename):
    temp_folder = get_project_folder('temp')  # Ajustar para a pasta temporária
    return send_from_directory(temp_folder, filename, as_attachment=True)

@teores_routes.route('/add_plot_to_teores/<image_name>', methods=['GET'])
@login_required
def add_plot_to_teores(image_name):
    temp_folder = get_project_folder('temp')  # Ajustar para a pasta temporária
    teores_file = os.path.join(temp_folder, 'teores.html')
    image_path = os.path.join(temp_folder, image_name)

    if os.path.exists(image_path):
        with open(teores_file, "a") as file:
            formatted_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            file.write(f'<p>{formatted_time} - Gráfico adicionado:</p>')
            file.write(f'<img src="{image_path}" alt="{image_name}" style="width:100%; max-width:600px;"/>')
        return jsonify({"status": "success", "message": f"Imagem {image_name} adicionada ao arquivo teores.html"}), 200

    return jsonify({"status": "error", "message": f"Imagem {image_name} não encontrada"}), 400
