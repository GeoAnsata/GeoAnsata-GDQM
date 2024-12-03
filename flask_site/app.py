# -*- coding: utf-8 -*-
from flask import Flask
from datetime import timedelta

from routes.auth_routes import auth_routes
from routes.pages_routes import pages_routes
from routes.clean_data_routes import clean_data_routes
from routes.exploratory_analysis_routes import exploratory_analysis_routes
from routes.history_routes import history_routes
from routes.sidebar_routes import sidebar_routes
from routes.projects_routes import projects_routes
from routes.updownload_routes import updownload_routes

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['USERS_DIR']='user_data'
app.permanent_session_lifetime = timedelta(minutes=120)

app.register_blueprint(auth_routes)
app.register_blueprint(pages_routes)
app.register_blueprint(clean_data_routes)
app.register_blueprint(exploratory_analysis_routes)
app.register_blueprint(history_routes)
app.register_blueprint(sidebar_routes)
app.register_blueprint(projects_routes)
app.register_blueprint(updownload_routes)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
