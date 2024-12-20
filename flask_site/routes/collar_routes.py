import os
import pandas as pd
import uuid
from flask import Blueprint,session,send_file,jsonify,request, render_template, send_from_directory
from io import BytesIO
from datetime import datetime
from utils.auth_utils import login_required
from utils.project_utils import get_project_folder
from utils.load_df import load_df
import matplotlib.pyplot as plt
from matplotlib.colors import to_hex
import matplotlib
matplotlib.use('Agg')


collar_routes = Blueprint('collar_routes', __name__)

def assign_colors_to_years(years):
    unique_years = sorted(set(years))  # Obter os anos únicos ordenados
    color_map = plt.get_cmap('tab10')  # Usar a paleta tab10
    year_colors = {year: to_hex(color_map(i % 10)) for i, year in enumerate(unique_years)}
    return year_colors

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


import geopandas as gpd, fiona
from shapely.geometry import Point

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
    kml_file = request.files.get('kml_file')

    if not all([year_column, depth_column, x_column, y_column]):
        return jsonify({"error": "Selecione todas as colunas necessárias."}), 400


    # Verificar e converter a coluna de anos se necessário
    if df[year_column].dtype == 'object':
        try:
            df[year_column] = pd.to_datetime(df[year_column], format='%d/%m/%Y', errors='coerce')
            df[year_column] = df[year_column].dt.year
        except Exception as e:
            return jsonify({"error": f"Erro ao processar a coluna de anos: {str(e)}"}), 400
    df[year_column] = df[year_column].fillna('Sem Ano').astype(str).str.split('.').str[0]

    # Carregar o KML se fornecido
    mapa_base = None
    if kml_file:
        kml_path = os.path.join(temp_folder, f"uploaded_{uuid.uuid4().hex}.kml")
        kml_file.save(kml_path)
        fiona.drvsupport.supported_drivers['libkml'] = 'rw' # enable KML support which is disabled by default
        fiona.drvsupport.supported_drivers['LIBKML'] = 'rw' # enable KML support which is disabled 
        mapa_base = gpd.read_file(kml_path)

        # Reprojetar o mapa base para UTM Zona 23S se necessário
        if mapa_base.crs != "EPSG:32723":
            mapa_base = mapa_base.to_crs(epsg=32723)

    # Processar os dados
    df[year_column] = pd.to_datetime(df[year_column], errors='coerce').dt.year.fillna('Sem Ano').astype(str)
    year_colors = assign_colors_to_years(df[year_column])
    plot_files = {}

    # Gráfico 1: Número de Furos por Ano com valores nas barras
    plt.figure(figsize=(10, 6))
    holes_per_year = df[year_column].value_counts().sort_index()
    colors = [year_colors[year] for year in holes_per_year.index]
    bars = holes_per_year.plot(kind='bar', color=colors)

    # Adicionar valores sobre as barras
    for bar in bars.patches:
        plt.text(
            bar.get_x() + bar.get_width() / 2,  # Posição X
            bar.get_height() + 0.5,             # Posição Y
            f'{int(bar.get_height())}',         # Valor a ser exibido
            ha='center', va='bottom', fontsize=10
        )

    plt.title("Número de Furos por Ano")
    plt.xlabel("Ano")
    plt.ylabel("Número de Furos")
    plt.grid(False)
    plt.tight_layout()
    unique_id = uuid.uuid4().hex
    holes_per_year_file = f"holes_per_year_{unique_id}.png"
    plt.savefig(os.path.join(temp_folder, holes_per_year_file))
    plt.close()
    plot_files['holes_per_year'] = holes_per_year_file

    # Gráfico 2: Número de Metros por Ano com valores nas barras
    plt.figure(figsize=(10, 6))
    grouped_depth = df.groupby(year_column)[depth_column].sum().sort_index()
    colors = [year_colors[year] for year in grouped_depth.index]
    bars = grouped_depth.plot(kind='bar', color=colors)

    # Adicionar valores sobre as barras
    for bar in bars.patches:
        plt.text(
            bar.get_x() + bar.get_width() / 2,  # Posição X
            bar.get_height() + 0.5,             # Posição Y
            f'{int(bar.get_height())}',         # Valor a ser exibido
            ha='center', va='bottom', fontsize=10
        )

    plt.title("Número de Metros por Ano")
    plt.xlabel("Ano")
    plt.ylabel("Metros")
    plt.tight_layout()
    plt.grid(False)
    unique_id = uuid.uuid4().hex
    meters_per_year_file = f"meters_per_year_{unique_id}.png"
    plt.savefig(os.path.join(temp_folder, meters_per_year_file))
    plt.close()
    plot_files['meters_per_year'] = meters_per_year_file

    # Criar GeoDataFrame para os pontos
    gdf_pontos = gpd.GeoDataFrame(
        df,
        geometry=[Point(x, y) for x, y in zip(df[x_column], df[y_column])],
        crs="EPSG:32723"
    )

    # Gráfico de Mapa XY com KML (se fornecido)
    plt.figure(figsize=(10, 6))
    if mapa_base is not None:
        mapa_base.plot(ax=plt.gca(), color='lightgray', edgecolor='black', alpha=0.5)

    for year, group in gdf_pontos.groupby(year_column):
        plt.scatter(group.geometry.x, group.geometry.y, label=year, color=year_colors[year], alpha=0.7)

    plt.title("Mapa XY das Localizações dos Furos")
    plt.xlabel("X (Leste)")
    plt.ylabel("Y (Norte)")
    plt.legend(title="Ano")
    plt.tight_layout()
    plt.grid(False)

    map_xy_file = f"map_xy_{uuid.uuid4().hex}.png"
    plt.savefig(os.path.join(temp_folder, map_xy_file))
    plt.close()
    plot_files['map_xy'] = map_xy_file

# Atualizar a sessão do usuário com os caminhos gerados
    if 'generated_images' not in session:
        session['generated_images'] = []
    session['generated_images'].extend(plot_files.values())
    session.modified = True

    # Número de furos por ano
    holes_per_year = df[year_column].value_counts().sort_index()

    # Número de metros furados por ano
    meters_per_year = df.groupby(year_column)[depth_column].sum().sort_index()

    # Printar os resultados no terminal para teste
    print("Número de furos por ano:")
    print(holes_per_year)
    print("\nNúmero de metros furados por ano:")
    print(meters_per_year)

    return render_template('collar.html', uploaded_files=session['sheet_names'], column_names=df.columns.tolist(), plot_files=plot_files, selected_file=session["selected_file"], selected_sheet=session["selected_sheet"])

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
