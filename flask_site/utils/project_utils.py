import os
from flask import session, current_app as app

def get_project_folder(folder_type):
    """Retorna o caminho da pasta baseada no usuário, projeto e tipo de pasta ('uploads' ou 'temp')."""
    username = session.get('username')
    if not username:
        return None
    project_name = session.get('current_project')
    if not project_name:
        return None
    base_folder = os.path.join(app.config['USERS_DIR'], username, project_name, folder_type)
    os.makedirs(base_folder, exist_ok=True)
    return base_folder

def get_existing_projects():
    dict_project_names = {}
    
    # Get the list of users' project directories
    users_dir = app.config['USERS_DIR']
    
    # Ensure the users directory exists
    if not os.path.exists(users_dir):
        return dict_project_names  # Return empty if no users directory exists
    
    # Loop through each user directory
    for username in os.listdir(users_dir):
        user_folder = os.path.join(users_dir, username)
        
        if os.path.isdir(user_folder):
            user_projects = []
            
            # Loop through the project directories within the user folder
            for project_folder in os.listdir(user_folder):
                project_path = os.path.join(user_folder, project_folder)
                
                if os.path.isdir(project_path):
                    user_projects.append(project_folder)
            
            # Only add to dict if there are projects
            if user_projects:
                dict_project_names[username] = user_projects
    
    # Save the project dictionary to the session
    session['projects'] = dict_project_names