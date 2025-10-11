from flask import Flask
import os

def create_app():
    app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'), static_folder=os.path.join(os.path.dirname(__file__), '..', 'static'))
    
    # Initialize database
    from app.db import init_db
    init_db(app)
    
    # Load syllabus
    from app.syllabus import init_syllabus
    init_syllabus()
    
    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.questions import questions_bp
    from app.routes.tests import tests_bp
    from app.routes.editor import editor_bp
    from app.routes.upload import upload_bp
    from app.routes.images import images_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(questions_bp)
    app.register_blueprint(tests_bp)
    app.register_blueprint(editor_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(images_bp)
    
    return app