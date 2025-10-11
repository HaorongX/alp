from flask import Blueprint
from app.image_handler import get_image

images_bp = Blueprint('images', __name__)

@images_bp.route('/get_image', methods=['GET'])
def get_image_route():
    return get_image()