from flask import Blueprint, request, redirect, url_for, session, render_template, flash

auth_routes = Blueprint('auth_routes', __name__)  # Definindo o blueprint

USERS = {
    "Adão": "123",
    "Gabriel": "123",
    "Glaucia": "123",
    "Yuri": "123"
}

@auth_routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check if the user exists and password matches
        if USERS.get(username) == password:
            session['username'] = username
            session.permanent = True
            session['current_project']=''
            session['projects']={}
            return redirect(url_for('pages_routes.projects', _external=True))  # Redirect to base page
        else:
            flash("Invalid credentials, please try again.")
            return render_template('login.html', error="Invalid username or password.")

    return render_template('login.html')

@auth_routes.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('current_project',None)
    session.pop('selected_file',None)
    session.pop('selected_sheet',None)
    session.pop('filters',None)
    session.pop('image_filename',None)
    session.pop('table_html',None)
    session.pop('sheet_names',None)
    return redirect(url_for('auth_routes.login', _external=True))