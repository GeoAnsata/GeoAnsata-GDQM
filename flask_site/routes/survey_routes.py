import os
import pandas as pd
from io import BytesIO
from flask import Blueprint,jsonify,request, render_template, send_file, send_from_directory
from datetime import datetime
from utils.auth_utils import login_required
from utils.project_utils import get_project_folder
from utils.load_df import load_df
import matplotlib.pyplot as plt
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

@survey_routes.route('/survey', methods=['GET','POST'])
@login_required
def survey():
    temp_folder = get_project_folder('temp')
    survey_file = os.path.join(temp_folder, 'survey.html')
    if not os.path.exists(survey_file):
        with open(survey_file, 'w') as f:
            f.write("<h1>Análise Survey</h1>\n")
    static_temp_folder = os.path.join('static', 'temp')  # Path for temporary files
    os.makedirs(static_temp_folder, exist_ok=True)
    
    df = load_df(get_project_folder('temp'))  # Load data for analysis
    column_names = df.columns.tolist() if df is not None else []

    if request.method == 'POST':
        # Retrieve user-defined columns
        dip_column = request.form.get('dip_column')
        max_depth_column = request.form.get('max_depth_column')
        initial_depth_column = request.form.get('initial_depth_column')
        hole_id_column = request.form.get('hole_id_column')

        # Validate column selection
        if not all([dip_column, max_depth_column, initial_depth_column, hole_id_column]):
            return jsonify({"error": "Selecione todas as colunas necessárias para a análise."}), 400

        # Ensure columns are numeric where needed
        df[max_depth_column] = pd.to_numeric(df[max_depth_column], errors='coerce')
        df[initial_depth_column] = pd.to_numeric(df[initial_depth_column], errors='coerce')
        df[dip_column] = pd.to_numeric(df[dip_column], errors='coerce')

        # Calculate Segment Length
        df['Segment Length'] = df[max_depth_column] - df[initial_depth_column]

        # Bar Chart: 90 Degrees vs. Others
        is_90_deg = df[df[dip_column] == -90].shape[0]
        not_90_deg = df[df[dip_column] != -90].shape[0]

        plt.figure(figsize=(10, 6))
        plt.bar(['-90 Degrees', 'Other'], [is_90_deg, not_90_deg], color=['green', 'blue'])
        plt.title("Furos com -90 Graus vs. Outros Ângulos de Perfuração")
        plt.ylabel("Número de furos")
        bar_chart_path = os.path.join(static_temp_folder, 'dip_comparison.png')
        plt.savefig(bar_chart_path)
        plt.close()

        # Analysis of Holes > 100m
        deep_holes = df[df[max_depth_column] > 100]
        total_deep_holes = deep_holes.shape[0]
        avg_depth = deep_holes[max_depth_column].mean()
        avg_segment_length = deep_holes['Segment Length'].mean()
        std_segment_length = deep_holes['Segment Length'].std()
        dip_distribution = deep_holes[dip_column].value_counts().to_dict()

        # Scatter Plot: Hole ID vs. Segment Length
        plt.figure(figsize=(10, 6))
        plt.scatter(df[hole_id_column], df['Segment Length'], alpha=0.7, c='orange')
        plt.title("Comprimento de Segmento dos Furos")
        plt.xlabel("ID do Furo")
        plt.ylabel("Comprimento do Segmento (metros)")
        scatter_chart_path = os.path.join(static_temp_folder, 'segment_length_scatter.png')
        plt.savefig(scatter_chart_path)
        plt.close()

        # Render survey page with results
        return render_template(
            'survey.html',
            column_names=column_names,
            bar_chart_path='temp/dip_comparison.png',
            scatter_chart_path='temp/segment_length_scatter.png',
            deep_hole_analysis={
                'total_deep_holes': total_deep_holes,
                'avg_depth': avg_depth,
                'avg_segment_length': avg_segment_length,
                'std_segment_length': std_segment_length,
                'dip_distribution': dip_distribution
            },
            selected_columns={
                'dip_column': dip_column,
                'max_depth_column': max_depth_column,
                'initial_depth_column': initial_depth_column,
                'hole_id_column': hole_id_column
            }
        )

    # Render initial page without results
    return render_template('survey.html', column_names=column_names, bar_chart_path=None, scatter_chart_path=None, deep_hole_analysis=None)

@survey_routes.route('/add_plot_to_survey/<image_name>', methods=['GET'])
@login_required
def add_plot_to_survey(image_name):
    temp_folder = get_project_folder('temp')
    survey_file = os.path.join(temp_folder, 'survey.html')
    static_temp_folder = os.path.join('static', 'temp')
    image_path = os.path.join(static_temp_folder, image_name)

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