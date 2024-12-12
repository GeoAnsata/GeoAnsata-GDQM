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


@collar_routes.route('/add_plot_to_collar/<image_name>', methods=['GET'])
@login_required
def add_plot_to_collar(image_name):
    temp_folder = get_project_folder('temp')
    collar_file = os.path.join(temp_folder, 'collar.html')
    static_temp_folder = os.path.join('static', 'temp')
    image_path = os.path.join(static_temp_folder, image_name)

    # Check if the image exists
    if os.path.exists(image_path):
        with open(collar_file, "a") as file:  # Append to the existing collar.html file
            # Log the addition of the plot
            formatted_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            file.write(f'<p>{formatted_time} - Gráfico adicionado:</p>')
            # Add the image to the file
            file.write(f'<img src="{image_path}" alt="{image_name}" style="width:100%; max-width:600px;"/>')

        # Return success response
        return jsonify({"status": "success", "message": f"Imagem {image_name} adicionada ao arquivo collar.html"}), 200

    return jsonify({"status": "error", "message": f"Imagem {image_name} não encontrada"}), 400



@collar_routes.route('/generate_custom_charts', methods=['POST'])
@login_required
def generate_custom_charts():
    static_temp_folder = os.path.join('static', 'temp')  # Correct path for static files
    os.makedirs(static_temp_folder, exist_ok=True)

    df = load_df(get_project_folder('temp'))

    # Columns selected by the user
    year_column = request.form.get('year_column')
    depth_column = request.form.get('depth_column')
    x_column = request.form.get('x_column')
    y_column = request.form.get('y_column')

    # Validate columns
    if not all([year_column, depth_column, x_column, y_column]):
        return jsonify({"error": "Selecione todas as colunas necessárias."}), 400

    # Dictionary to store file paths for the plots
    plot_files = {}

    # Plot 1: Number of holes per year
    plt.figure(figsize=(10, 6))
    df[year_column].value_counts().sort_index().plot(kind='bar')
    plt.title("Número de Furos por Ano")
    plt.xlabel("Ano")
    plt.ylabel("Número de Furos")
    plt.grid(True)
    holes_per_year_file = os.path.join(static_temp_folder, 'holes_per_year.png')
    plt.savefig(holes_per_year_file)
    plt.close()
    plot_files['holes_per_year'] = 'temp/holes_per_year.png'

    # Plot 2: Number of meters per year
    plt.figure(figsize=(10, 6))
    df.groupby(year_column)[depth_column].sum().sort_index().plot(kind='bar')
    plt.title("Número de Metros por Ano")
    plt.xlabel("Ano")
    plt.ylabel("Metros")
    plt.grid(True)
    meters_per_year_file = os.path.join(static_temp_folder, 'meters_per_year.png')
    plt.savefig(meters_per_year_file)
    plt.close()
    plot_files['meters_per_year'] = 'temp/meters_per_year.png'

    # Plot 3: XY map divided by year
    plt.figure(figsize=(10, 6))
    for year, group in df.groupby(year_column):
        plt.scatter(group[x_column], group[y_column], label=str(year), alpha=0.7)
    plt.title("Mapa XY das Localizações dos Furos")
    plt.xlabel("X (Leste)")
    plt.ylabel("Y (Norte)")
    plt.legend(title="Ano")
    plt.grid(True)
    map_xy_file = os.path.join(static_temp_folder, 'map_xy.png')
    plt.savefig(map_xy_file)
    plt.close()
    plot_files['map_xy'] = 'temp/map_xy.png'

    return render_template(
        'collar.html',
        column_names=df.columns.tolist(),
        plot_files=plot_files
    )

@collar_routes.route('/download_plot/<filename>', methods=['GET'])
@login_required
def download_plot(filename):
    static_temp_folder = os.path.join('static', 'temp')
    return send_from_directory(static_temp_folder, filename, as_attachment=True)