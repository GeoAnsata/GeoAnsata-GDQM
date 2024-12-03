import os
import shutil
from flask import Blueprint,session,redirect,url_for,flash,current_app
from utils.auth_utils import login_required
from utils.file_utils import load_existing_files


projects_routes = Blueprint('projects_routes', __name__)



@projects_routes.route('/select_project/<project_name>')
@login_required
def select_project(project_name):
    username = session.get('username')
    
    if project_name in session.get('projects').get(username,[]):
        session['current_project'] = project_name
        load_existing_files()
        session['selected_file'] = ''
        session['selected_sheet'] = ''
        session['filters'] = [] 
        session['filter_logic'] = 'and'
        session['image_filename'] = ''
        session['table_html'] = ''
        
        return redirect(url_for('pages_routes.upload', _external=True))  # Redirect to the upload page
    else:
        flash("Projeto não encontrado!")
        return redirect(url_for('pages_routes.projects', _external=True))
    
@projects_routes.route('/delete_project/<project_name>', methods=['POST'])
@login_required
def delete_project(project_name):
    username = session.get('username')
    user_projects = session.get('projects').get(username, [])
    
    if project_name in user_projects:
        # Remova o projeto da lista de projetos do usuário
        user_projects.remove(project_name)
        session['projects'][username] = user_projects
        
        # Remova os arquivos e diretórios associados ao projeto
        project_folder = os.path.join(current_app.config['USERS_DIR'], username, project_name)
        if os.path.exists(project_folder):
            shutil.rmtree(project_folder)
        if(session.get('current_project')==project_name):
            session['current_project']=''
        
        flash(f"Projeto '{project_name}' foi excluído com sucesso.")
    else:
        flash(f"Projeto '{project_name}' não encontrado.")
    
    return redirect(url_for('pages_routes.projects', _external=True))
