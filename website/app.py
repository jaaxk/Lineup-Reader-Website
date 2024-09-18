from flask import Flask, render_template, request, redirect, url_for
from flask_cors import CORS
import os
from backend import get_dict, make_spotify_playlist
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'
app.config['UPLOAD_FOLDER'] = './website/upload_folder'

CORS(app) #adds 'Access-Control-Allow-Origin: *' header to all responses, allowing requests from any origin

@app.route('/')
def body():
    return render_template('index.html', results='Please Upload Lineup')

@app.route('/backend/<filename>', methods=['GET'])
def backend(filename):
    dict = get_dict(f'./website/upload_folder/{filename}')
    with open ('./website/json/lineup.json', 'w') as outfile:
       json.dump(dict, outfile)

    return render_template('results.html', results = dict)

@app.route('/upload', methods=['POST'])
def upload_image():
    file = request.files['image']
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)
    return redirect(url_for('backend', filename=file.filename))

@app.route('/make_playlist')
def make_playlist():
    code = request.args.get('code')
    make_spotify_playlist('./website/json/lineup.json', code, 'Lineup Playlist')
    return '<h1>Success!</h1>'



if __name__ == "__main__":
    app.run(debug=True)

