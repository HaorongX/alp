from flask import g
import sqlite3

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect('db/9618.db')
        g.db.row_factory = sqlite3.Row
    return g.db

def init_db(app):
    @app.teardown_appcontext
    def close_db(error):
        db = g.pop('db', None)
        if db is not None:
            db.close()