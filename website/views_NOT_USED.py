#Define all our URLs here
from flask import Blueprint, render_template, request
import os
from werkzeug.utils import secure_filename
from app import app

views = Blueprint('views', __name__)

@views.route('/')
def body():
    return render_template('index.html')

@views.route('/upload', methods=['POST'])
def upload_image():
    file = request.files['image']
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)
    pass

@views.route('/example', methods=['GET'])
def example():
    return {'TEST_KEY': 'TEST_VALUE'}