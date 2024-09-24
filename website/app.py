from flask import Flask, render_template, request, redirect, url_for
from flask_cors import CORS
import os
from backend import get_dict_from_image, get_dict_from_text, make_spotify_playlist, get_dict_with_params
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'
app.config['UPLOAD_FOLDER'] = './website/upload_folder'

CORS(app) #adds 'Access-Control-Allow-Origin: *' header to all responses, allowing requests from any origin

@app.route('/')
def body():
    return render_template('index.html', results='Please Upload Lineup')

@app.route('/backend/<method>/<content>', methods=['GET'])
def backend(method, content):
    if method == 'image':
        dict = get_dict_from_image(f'./website/upload_folder/{content}')
    if method == 'search':
        dict = get_dict_from_text(content)
        print(dict)
    with open ('./website/json/lineup.json', 'w') as outfile:
       json.dump(dict, outfile)

    return redirect(url_for('render_results', num_tracks=3, filters='none'))

@app.route('/results/<num_tracks>/<filters>')
def render_results(num_tracks, filters):

    lineup_dict = get_dict_with_params(num_tracks, filters)
    return render_template('results.html', results = lineup_dict)

@app.route('/refresh_params')
def refresh_params():
    num_tracks = request.args['num_tracks']
    filters = request.args['filters']
    if filters == '':
        filters = 'none'
    if num_tracks=='':
        num_tracks=3
    return redirect(url_for('render_results', num_tracks=num_tracks, filters=filters))

@app.route('/upload', methods=['POST'])
def upload_image():
    file = request.files['image']
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)
    return redirect(url_for('backend', method='image', content=file.filename))

@app.route('/search')
def search():
    input_text = request.args['input_text']
    return redirect(url_for('backend', method='search', content=input_text))

@app.route('/make_playlist')
def make_playlist():
    code = request.args.get('code')
    success = make_spotify_playlist('./website/json/lineup_updated.json', code, 'Lineup Playlist')
    if success:
        return '<h1>Success!</h1>'
    else:
        return '<h1>Failed</h1>'



if __name__ == "__main__":
    app.run(debug=True)

