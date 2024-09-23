import easyocr
import requests
import json
import math

client_id='335365bdd98b409a8070f5e604bd375a'
client_secret='6e8d86f2cdba40d2bc7bbd8c1e92f7b1'
redirect_uri = 'http://127.0.0.1:5000/make_playlist' #Change this eventually

def get_dict(file_path):
    reader = easyocr.Reader(['en', 'es'])
    result = reader.readtext(file_path)

    response = requests.post('https://accounts.spotify.com/api/token', data={'grant_type': 'client_credentials',
                                                                            'client_id': client_id, 'client_secret': client_secret})
    access_token = response.json().get('access_token')
    headers = {'Authorization': 'Bearer '+access_token}

    detected_name = []
    search_result = []
    genres = []
    top_tracks = []
    top_track_uris = []
    def update_lists(name, genre, id):
        search_result.append(name)
        genres.append(genre)
        
        req = requests.get('https://api.spotify.com/v1/artists/'+id+'/top-tracks', headers=headers)
        top_tracks.append([])
        top_track_uris.append([])
        for i in range(10):
            try:
                top_tracks[-1].append(req.json()['tracks'][i]['name'])
                top_track_uris[-1].append(req.json()['tracks'][i]['uri'])
            except:
                break


    for detection in result:
        q = detection[1].replace(" ", "%20").replace('&', 'and').lower()
        req = requests.get('https://api.spotify.com/v1/search?q='+q+'&type=artist&limit=5',  
                        headers = headers)
        
        if 'artists' in req.json() and req.json()['artists']['items'] != [] and detection[1].isupper():
            detected_name.append(detection[1])
            added=False
            for item in req.json()['artists']['items']:
                if item['name'].lower() == detection[1].lower():
                    update_lists(item['name'], item['genres'], item['id'])
                    added=True
                    break
            if not added:
                update_lists(req.json()['artists']['items'][0]['name'], req.json()['artists']['items'][0]['genres'], req.json()['artists']['items'][0]['id'])
    #Turn lists to dictionaries with index as key
    detected_name_dict = {}
    search_result_dict = {}
    genres_dict = {}
    top_tracks_dict = {}
    top_track_uris_dict = {}
    dicts = [detected_name_dict, search_result_dict, genres_dict, top_tracks_dict, top_track_uris_dict]
    lists = [detected_name, search_result, genres, top_tracks, top_track_uris]
    for dict, lst in zip(dicts, lists):
        for i, val in enumerate(lst):
            dict[i] = val
    
    #Combine dictionaries to one big result_dict
    result_dict = {'Detected Name': detected_name_dict, 'Spotify Name': search_result_dict, 'Genres': 
                   genres_dict, 'Top Tracks': top_tracks_dict, 'URIs': top_track_uris_dict}
    return result_dict

def make_spotify_playlist(path_to_json, code, playlist_name):
    auth_access_token = get_access_token(code)
    print(auth_access_token)
    if auth_access_token is None:
        return False
    user_id = get_user_id(auth_access_token)
    url = f'https://api.spotify.com/v1/users/{user_id}/playlists'
    auth_headers = {
        'Authorization': f'Bearer {auth_access_token}',
        'Content-Type': 'application/json'
    }
    data = {
        'name': playlist_name,
        'description': 'Playlist created using Jack\'s Lineup Reader Website!',
        'public': True
    }
    response = requests.post(url, headers=auth_headers, json=data)

    playlist_id = response.json()['uri'].split(':')[-1]

    with open (path_to_json) as json_file:
        lineup_json = json.load(json_file)
    track_uris = []
    for artist in lineup_json['URIs']:
        for uri in lineup_json['URIs'].get(artist):
            track_uris.append(uri)
    if len(track_uris) > 50:
        for i in range(math.floor(len(track_uris)/50)):
            tracks_response = add_tracks(auth_access_token, playlist_id, track_uris[i*50:(i+1)*50])
    else:
        i=-1
    tracks_response = add_tracks(auth_access_token, playlist_id, track_uris[(i+1)*50:(i+1)*50 + len(track_uris)%50])

    return tracks_response

def get_access_token(code):
    token_url = 'https://accounts.spotify.com/api/token'
    auth_headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri,
        'client_id': client_id,
        'client_secret': client_secret
    }
    response = requests.post(token_url, headers=auth_headers, data=data)
    return response.json().get('access_token')

def get_user_id(auth_access_token):
    url = 'https://api.spotify.com/v1/me'
    headers = {
        'Authorization': f'Bearer {auth_access_token}'
    }
    
    response = requests.get(url, headers=headers)
    print(response)
    return response.json()['uri'].split(':')[-1]

def add_tracks(auth_access_token, playlist_id, track_uris):
    url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
    auth_headers = {
        'Authorization': f'Bearer {auth_access_token}',
        'Content-Type': 'application/json'
    }
    data = {
        'uris': track_uris  # List of track URIs to add to the playlist
    }
    response = requests.post(url, headers=auth_headers, json=data)
    return response.json()

def get_dict_with_params(num_tracks, filters):
    
    with open('./website/json/lineup.json') as lineup_json:
        lineup_dict = json.load(lineup_json)

    try:
        num_tracks=int(num_tracks)
    except ValueError: #If 'static' is passed, dont do anything.
        return lineup_dict
    #Reduce num tracks and URIs
    change_num_tracks(lineup_dict, num_tracks)
    #Filter dictionary by given genre filters
    if filters != 'none':
        filters = filters.split(',')
        filter_dict(lineup_dict, filters)

    #Post updated dict to json folder
    with open ('./website/json/lineup_updated.json', 'w') as outfile:
       json.dump(lineup_dict, outfile)
    return lineup_dict

def change_num_tracks(lineup_dict, num_tracks):
    tracks_and_uris = ['Top Tracks', 'URIs']
    for col in tracks_and_uris:
        trimmed_dict = {}
        for key, val in lineup_dict.get(col).items():
            trimmed_dict[key] = val[0:num_tracks]
        lineup_dict[col] = trimmed_dict
    return lineup_dict

def filter_dict(lineup_dict, filters):
    indices_to_keep = []
    for key, val in lineup_dict.get('Genres').items():
        for filter in filters:
            for genre in val:
                if filter in genre:
                    indices_to_keep.append(key)
    
    for col, dict in lineup_dict.items():
        for key in list(dict.keys()):
            if key not in indices_to_keep:
                lineup_dict[col].pop(key)
    return lineup_dict