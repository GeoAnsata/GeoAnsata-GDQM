import os
import uuid
from flask import Blueprint,session,send_file,jsonify,request, render_template, send_from_directory
from io import BytesIO
from datetime import datetime
from utils.auth_utils import login_required
from utils.project_utils import get_project_folder
from utils.load_df import load_df
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')


collar_routes = Blueprint('collar_routes', __name__)


from xhtml2pdf import pisa
@collar_routes.route('/export_collar_pdf', methods=['GET'])
@login_required
def export_collar_pdf():
    temp_folder = get_project_folder('temp')
    collar_file = os.path.join(temp_folder, 'collar.html')
    pdf_path = os.path.join(temp_folder, 'collar.pdf')
    
    with open(collar_file, "r") as file:
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


@collar_routes.route('/generate_custom_charts', methods=['POST'])
@login_required
def generate_custom_charts():
    temp_folder = get_project_folder('temp')
    os.makedirs(temp_folder, exist_ok=True)

    df = load_df(temp_folder)

    # Colunas selecionadas pelo usuário
    year_column = request.form.get('year_column')
    depth_column = request.form.get('depth_column')
    x_column = request.form.get('x_column')
    y_column = request.form.get('y_column')

    if not all([year_column, depth_column, x_column, y_column]):
        return jsonify({"error": "Selecione todas as colunas necessárias."}), 400

    plot_files = {}

    # Gerar Gráfico 1: Número de Furos por Ano
    plt.figure(figsize=(10, 6))
    df[year_column].value_counts().sort_index().plot(kind='bar')
    plt.title("Número de Furos por Ano")
    plt.xlabel("Ano")
    plt.ylabel("Número de Furos")
    plt.grid(True)
    unique_id = uuid.uuid4().hex
    holes_per_year_file = f"holes_per_year_{unique_id}.png"
    plt.savefig(os.path.join(temp_folder, holes_per_year_file))
    plt.close()
    plot_files['holes_per_year'] = holes_per_year_file

    # Gerar Gráfico 2: Número de Metros por Ano
    plt.figure(figsize=(10, 6))
    df.groupby(year_column)[depth_column].sum().sort_index().plot(kind='bar')
    plt.title("Número de Metros por Ano")
    plt.xlabel("Ano")
    plt.ylabel("Metros")
    plt.grid(True)
    unique_id = uuid.uuid4().hex
    meters_per_year_file = f"meters_per_year_{unique_id}.png"
    plt.savefig(os.path.join(temp_folder, meters_per_year_file))
    plt.close()
    plot_files['meters_per_year'] = meters_per_year_file

    # Gerar Gráfico 3: Mapa XY
    plt.figure(figsize=(10, 6))
    for year, group in df.groupby(year_column):
        plt.scatter(group[x_column], group[y_column], label=str(year), alpha=0.7)
    plt.title("Mapa XY das Localizações dos Furos")
    plt.xlabel("X (Leste)")
    plt.ylabel("Y (Norte)")
    plt.legend(title="Ano")
    plt.grid(True)
    unique_id = uuid.uuid4().hex
    map_xy_file = f"map_xy_{unique_id}.png"
    plt.savefig(os.path.join(temp_folder, map_xy_file))
    plt.close()
    plot_files['map_xy'] = map_xy_file

    # Atualizar a sessão do usuário com os caminhos gerados
    if 'generated_images' not in session:
        session['generated_images'] = []
    session['generated_images'].extend(plot_files.values())
    session.modified = True

    return render_template('collar.html', column_names=df.columns.tolist(), plot_files=plot_files)


@collar_routes.route('/download_plot/<filename>', methods=['GET'])
@login_required
def download_plot(filename):
    temp_folder = get_project_folder('temp')  # Ajustar para a pasta temporária
    return send_from_directory(temp_folder, filename, as_attachment=True)

@collar_routes.route('/add_plot_to_collar/<image_name>', methods=['GET'])
@login_required
def add_plot_to_collar(image_name):
    temp_folder = get_project_folder('temp')  # Ajustar para a pasta temporária
    collar_file = os.path.join(temp_folder, 'collar.html')
    image_path = os.path.join(temp_folder, image_name)

    if os.path.exists(image_path):
        with open(collar_file, "a") as file:
            formatted_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            file.write(f'<p>{formatted_time} - Gráfico adicionado:</p>')
            file.write(f'<img src="{image_path}" alt="{image_name}" style="width:100%; max-width:600px;"/>')
        return jsonify({"status": "success", "message": f"Imagem {image_name} adicionada ao arquivo collar.html"}), 200

    return jsonify({"status": "error", "message": f"Imagem {image_name} não encontrada"}), 400
