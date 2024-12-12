import os
import pandas as pd
from flask import Blueprint, request, session, render_template, flash,current_app, jsonify
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from utils.auth_utils import login_required
from utils.project_utils import get_project_folder, get_existing_projects
from utils.load_df import load_df,load_history
from utils.info_tables import get_table

pages_routes = Blueprint('pages_routes', __name__)


@pages_routes.route('/')
@login_required
def upload():
    if 'sheet_names' not in session:
        session['sheet_names'] = {}
        session['selected_file']=''
        session['selected_sheet']=''
    return render_template('upload.html', uploaded_files=session['sheet_names'], selected_file=session["selected_file"], selected_sheet=session["selected_sheet"])

@pages_routes.route('/display', methods=['GET', 'POST'])
@login_required
def display():
    try:
        temp_folder = get_project_folder('temp')
        df = load_df(temp_folder)
        column_names = df.columns.tolist()
        
        # Captura os parâmetros de paginação
        start = request.args.get('start', default=0, type=int)
        lines_by_page = request.args.get('lines_by_page', default=100, type=int)
        
        if request.method == 'POST':
            filter_column = request.form.get('filter_column')
            filter_operator = request.form.get('filter_operator')
            filter_value = request.form.get('filter_value')
            
            if filter_column and filter_operator and filter_value:
                # pages_routesend the new filter to the existing list of filters
                session['filters'].pages_routesend({
                    'column': filter_column,
                    'operator': filter_operator,
                    'value': filter_value
                })
                session.modified = True 
        # Remover filtro específico
        if 'remove_filter' in request.args:
            filter_index = int(request.args.get('remove_filter'))
            session['filters'].pop(filter_index)
            session.modified = True

        # Limpar todos os filtros
        if 'clear_filters' in request.args:
            session['filters'] = []
            session.modified = True


        # Definir operador de combinação dos filtros (AND/OR)
        filter_logic = request.args.get('filter_logic', 'and')
        
        # Aplica os filtros ao DataFrame
        for filter_item in session['filters']:
            col = filter_item['column']
            op = filter_item['operator']
            val = filter_item['value']
            
            try:
                val = float(val) if val.replace('.', '', 1).isdigit() else val
                if op == "equals":
                    condition = df[col] == val
                elif op == "not_equals":
                    condition = df[col] != val
                elif op == "greater_than":
                    condition = pd.to_numeric(df[col], errors='coerce') > val
                elif op == "less_than":
                    condition = pd.to_numeric(df[col], errors='coerce') < val
                elif op == "greater_equal":
                    condition = pd.to_numeric(df[col], errors='coerce') >= val
                elif op == "less_equal":
                    condition = pd.to_numeric(df[col], errors='coerce') <= val

                # Aplica o filtro como AND ou OR
                if filter_logic == 'and':
                    df = df[condition]
                else:
                    df = pd.concat([df[condition], df[~condition]]).drop_duplicates()

            except ValueError:
                pass  # Ignorar se houver erro de tipo

        # Gera a tabela HTML com os dados filtrados e paginação
        table_html = get_table(df, request, start, lines_by_page)
        
        # Renderiza o template com a tabela, filtros e opções
        return render_template(
            'display.html',
            table=table_html,
            uploaded_files=session['sheet_names'],
            selected_file=session["selected_file"],
            selected_sheet=session["selected_sheet"],
            start=start,
            lines_by_page=lines_by_page,
            num_lines=df.shape[0],
            column_names=column_names,
            filters=session['filters'],
            filter_logic=filter_logic
        )
    except Exception as e:
        print(f"Erro ao exibir a tabela: {e}")
        return render_template(
            'display.html',
            table=None,
            uploaded_files=session['sheet_names'],
            selected_file=session["selected_file"],
            selected_sheet=session["selected_sheet"],
            start=0,
            lines_by_page=100,
            num_lines=0,
            column_names=[],
            filters=[],
            filter_logic='and'
        )

@pages_routes.route('/download_page')
@login_required
def download_page():
    return render_template('download.html', uploaded_files=session['sheet_names'], selected_file=session["selected_file"], selected_sheet=session["selected_sheet"])

@pages_routes.route('/clean_data',  methods=['GET', 'POST'])
@login_required
def clean_data():
    try:
        temp_folder = get_project_folder('temp')
        df = load_df(temp_folder)

        start = request.args.get('start', default=0, type=int)
        lines_by_page = request.args.get('lines_by_page', default=100, type=int)

        column_names = df.columns.tolist()
        table_html = get_table(df, request, start, lines_by_page)

        return render_template('clean_data.html', 
                               table=table_html, 
                               uploaded_files=session['sheet_names'], 
                               column_names=column_names, 
                               selected_file=session["selected_file"], 
                               selected_sheet=session["selected_sheet"],
                               start=start,
                               lines_by_page=lines_by_page,
                               num_lines=df.shape[0],
                               filters=session['filters'],
                                filter_logic=session['filter_logic'])
    except:
        return render_template('clean_data.html',
                                table=None,
                                uploaded_files=session['sheet_names'], 
                                column_names=[], 
                                selected_file=session["selected_file"], 
                                selected_sheet=session["selected_sheet"], 
                                start=0, 
                                lines_by_page=100,
                                num_lines=0,
                                filters=[],
                                filter_logic='and')
    

@pages_routes.route('/exploratory_analysis')
@login_required
def exploratory_analysis():
    temp_folder = get_project_folder('temp')
    df = load_df(temp_folder)
    column_names=None
    if(df is not None):
        column_names = df.columns.tolist()
    return render_template('exploratory_analysis.html', uploaded_files=session['sheet_names'], column_names=column_names, table=None,image=None, selected_file=session["selected_file"], selected_sheet=session["selected_sheet"])


@pages_routes.route('/recommended_graphs')
@login_required
def recommended_graphs():
    return render_template('recommended_graphs.html',uploaded_files=session['sheet_names'], selected_file=session["selected_file"], selected_sheet=session["selected_sheet"])

@pages_routes.route('/base_analysis')
@login_required
def base_analysis():
    temp_folder = get_project_folder('temp')
    base_analysis_file = os.path.join(temp_folder, 'base_analysis.html')
    if not os.path.exists(base_analysis_file):
        with open(base_analysis_file, 'w') as f:
            f.write("<h1>Análise Preeliminar</h1>\n")

    df = load_df(temp_folder)
    column_names=None
    if(df is not None):
        column_names = df.columns.tolist()
    return render_template('base_analysis.html', uploaded_files=session['sheet_names'], column_names=column_names, table=None,image=None, selected_file=session["selected_file"], selected_sheet=session["selected_sheet"])


@pages_routes.route('/collar')
@login_required
def collar():
    temp_folder = get_project_folder('temp')
    collar_file = os.path.join(temp_folder, 'collar.html')
    if not os.path.exists(collar_file):
        with open(collar_file, 'w') as f:
            f.write("<h1>Análise Collar</h1>\n")

    df = load_df(temp_folder)
    column_names=None
    if(df is not None):
        column_names = df.columns.tolist()
    return render_template('collar.html', uploaded_files=session['sheet_names'], column_names=column_names, image=None, selected_file=session["selected_file"], selected_sheet=session["selected_sheet"])

@pages_routes.route('/survey', methods=['GET','POST'])
@login_required
def survey():
    temp_folder = get_project_folder('temp')  # Usar pasta temporária do projeto
    survey_file = os.path.join(temp_folder, 'survey.html')
    if not os.path.exists(survey_file):
        with open(survey_file, 'w') as f:
            f.write("<h1>Análise Survey</h1>\n")
    
    df = load_df(temp_folder)  # Carregar dados para análise
    column_names = df.columns.tolist() if df is not None else []

    if request.method == 'POST':
        # Recuperar colunas definidas pelo usuário
        dip_column = request.form.get('dip_column')
        max_depth_column = request.form.get('max_depth_column')
        initial_depth_column = request.form.get('initial_depth_column')
        hole_id_column = request.form.get('hole_id_column')

        if not all([dip_column, max_depth_column, initial_depth_column, hole_id_column]):
            return jsonify({"error": "Selecione todas as colunas necessárias para a análise."}), 400

        # Certificar que as colunas são numéricas
        df[max_depth_column] = pd.to_numeric(df[max_depth_column], errors='coerce')
        df[initial_depth_column] = pd.to_numeric(df[initial_depth_column], errors='coerce')
        df[dip_column] = pd.to_numeric(df[dip_column], errors='coerce')

        # Cálculos e gráficos
        df['Segment Length'] = df[max_depth_column] - df[initial_depth_column]

        # Gráfico de Barras
        plt.figure(figsize=(10, 6))
        is_90_deg = df[df[dip_column] == -90].shape[0]
        not_90_deg = df[df[dip_column] != -90].shape[0]
        plt.bar(['-90 Degrees', 'Other'], [is_90_deg, not_90_deg], color=['green', 'blue'])
        plt.title("Furos com -90 Graus vs. Outros Ângulos de Perfuração")
        plt.ylabel("Número de furos")
        bar_chart_path = os.path.join(temp_folder, 'dip_comparison.png')
        plt.savefig(bar_chart_path)
        plt.close()

        # Scatter Plot
        plt.figure(figsize=(10, 6))
        plt.scatter(df[hole_id_column], df['Segment Length'], alpha=0.7, c='orange')
        plt.title("Comprimento de Segmento dos Furos")
        plt.xlabel("ID do Furo")
        plt.ylabel("Comprimento do Segmento (metros)")
        scatter_chart_path = os.path.join(temp_folder, 'segment_length_scatter.png')
        plt.savefig(scatter_chart_path)
        plt.close()

        return render_template(
            'survey.html',
            column_names=column_names,
            bar_chart_path=f'temp/dip_comparison.png',
            scatter_chart_path=f'temp/segment_length_scatter.png',
            deep_hole_analysis={
                'total_deep_holes': len(df[df[max_depth_column] > 100]),
                'avg_depth': df[max_depth_column].mean(),
                'avg_segment_length': df['Segment Length'].mean(),
                'std_segment_length': df['Segment Length'].std(),
                'dip_distribution': df[dip_column].value_counts().to_dict(),
            },
            selected_columns={
                'dip_column': dip_column,
                'max_depth_column': max_depth_column,
                'initial_depth_column': initial_depth_column,
                'hole_id_column': hole_id_column,
            }
        )


    # Render initial page without results
    return render_template('survey.html', column_names=column_names,uploaded_files=session['sheet_names'], selected_file=session["selected_file"], selected_sheet=session["selected_sheet"])


@pages_routes.route('/teores')
@login_required
def teores():
    temp_folder = get_project_folder('temp')
    teores_file = os.path.join(temp_folder, 'teores.html')
    if not os.path.exists(teores_file):
        with open(teores_file, 'w') as f:
            f.write("<h1>Análise Teores</h1>\n")

    df = load_df(temp_folder)
    column_names=None
    if(df is not None):
        column_names = df.columns.tolist()
    return render_template('teores.html', uploaded_files=session['sheet_names'], column_names=column_names, image=None, selected_file=session["selected_file"], selected_sheet=session["selected_sheet"])



@pages_routes.route('/history')
@login_required
def history():
    try:
        upload_folder = get_project_folder('upload')
        history=load_history(upload_folder,"r")
        content = history.read()
        history.close()
        return render_template('history.html',file_history=content,uploaded_files=session['sheet_names'], selected_file=session["selected_file"], selected_sheet=session["selected_sheet"])
    except:
        return render_template('history.html',file_history=None,uploaded_files=session['sheet_names'], selected_file=session["selected_file"], selected_sheet=session["selected_sheet"])

@pages_routes.route('/projects', methods=['GET', 'POST'])
@login_required
def projects():
    # Get the existing projects for all users and update session
    get_existing_projects()
    
    # Get the current user and their projects from session
    username = session.get('username')
    user_projects = session.get('projects').get(username, [])

    if not user_projects:
        flash("Você não tem projetos existentes.")

    # Handle adding a new project
    if request.method == 'POST':
        project_name = request.form.get('project_name').strip()
        
        # Ensure the project name isn't empty and doesn't already exist
        if project_name and project_name not in user_projects:
            # Add the new project to the user's list
            user_projects.append(project_name)
            
            # Save the updated projects list back to the session
            session['projects'][username] = user_projects
            
            # Create the necessary directories for the new project
            user_folder = os.path.join(current_app.config['USERS_DIR'], username)
            project_folder = os.path.join(user_folder, project_name)
            
            # Create the project directory and its subdirectories
            os.makedirs(project_folder, exist_ok=True)
            os.makedirs(os.path.join(project_folder, 'upload'), exist_ok=True)
            os.makedirs(os.path.join(project_folder, 'temp'), exist_ok=True)

            flash(f"Projeto '{project_name}' adicionado com sucesso!")
        else:
            flash("Projeto inválido ou já existe.")
    #adicionar passagem de outros parametros quando nao for o inicio da execução
    return render_template('projects.html', projects=user_projects)