from functools import wraps
from flask import session, redirect, url_for
# Login required decorator to restrict access to pages
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('auth_routes.login', _external=True))
        return f(*args, **kwargs)
    return decorated_function