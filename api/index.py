import os
import sys
import re
import queue
import json
import threading
from flask import Flask, request, jsonify, Response, send_from_directory
from dotenv import load_dotenv
import requests

# Inject parent directory into system path so testup4 module imports work on Vercel
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static'))

TMDB_API_KEY = os.getenv('TMDB_API_KEY', 'd6d415fbca42bcf39105eee27b397895')
PORT = int(os.getenv('PORT', 8000))
OMDB_API_KEY = os.getenv('OMDB_API_KEY', '22bfde2c')

POPULAR_BAFTAS = {
    'tt0816692': 'Won 1 BAFTA.', # Interstellar
    'tt15398776': 'Won 7 BAFTAs.', # Oppenheimer
    'tt1160419': 'Won 1 BAFTA.', # Dune (2021)
    'tt15239678': 'Won 5 BAFTAs.', # Dune: Part Two
    'tt1375666': 'Won 3 BAFTAs.', # Inception
    'tt0078721': 'Won 2 BAFTAs.', # Alien
    'tt0120338': 'Won 4 BAFTAs.', # Titanic
    'tt0109830': 'Won 3 BAFTAs.', # Forrest Gump
    'tt0110912': 'Won 1 BAFTA.', # Pulp Fiction
    'tt0133093': 'Won 5 BAFTAs.', # The Matrix
    'tt0120737': 'Won 4 BAFTAs.', # The Lord of the Rings: The Fellowship of the Ring
    'tt0167260': 'Won 5 BAFTAs.', # The Lord of the Rings: The Return of the King
    'tt0172495': 'Won 3 BAFTAs.', # The Lord of the Rings: The Two Towers
    'tt2085941': 'Won 1 BAFTA.', # La La Land
    'tt0450259': 'Won 2 BAFTAs.', # Blood Diamond
    'tt0478970': 'Won 4 BAFTAs.', # Mad Max: Fury Road
    'tt0903747': 'Won 1 BAFTA.', # Breaking Bad (TV)
    'tt0944947': 'Won 1 BAFTA.', # Game of Thrones (TV)
}

# Import search runner from testup4
import testup4

@app.route('/')
@app.route('/movie/<path:subpath>')
@app.route('/tv/<path:subpath>')
def index(subpath=None):
    return send_from_directory('static', 'index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/api/search-movies')
def search_movies():
    query = request.args.get('query')
    if not query:
        return jsonify({'error': 'Missing query parameter'}), 400
    
    url = f"https://api.tmdb.org/3/search/multi?api_key={TMDB_API_KEY}&query={requests.utils.quote(query)}"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()
        
        # Filter results to include only movies and TV series
        filtered_results = []
        for item in data.get('results', []):
            media_type = item.get('media_type')
            if media_type in ['movie', 'tv']:
                if media_type == 'tv':
                    item['title'] = item.get('name')
                    item['release_date'] = item.get('first_air_date')
                filtered_results.append(item)
                
        data['results'] = filtered_results
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trending-movies')
def trending_movies():
    # Use trending multi to show both trending movies and TV series!
    url = f"https://api.tmdb.org/3/trending/all/week?api_key={TMDB_API_KEY}"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()
        
        # Normalize and filter
        filtered_results = []
        for item in data.get('results', []):
            media_type = item.get('media_type')
            if media_type in ['movie', 'tv']:
                if media_type == 'tv':
                    item['title'] = item.get('name')
                    item['release_date'] = item.get('first_air_date')
                filtered_results.append(item)
        data['results'] = filtered_results
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/movie-details/<int:movie_id>')
def movie_details(movie_id):
    media_type = request.args.get('type', 'movie')
    
    # Try the requested media type first
    if media_type == 'tv':
        url = f"https://api.tmdb.org/3/tv/{movie_id}?api_key={TMDB_API_KEY}"
    else:
        url = f"https://api.tmdb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}"
        
    try:
        r = requests.get(url, timeout=5)
        # If requested movie but not found/Soviet film override (check if TV show has much more popularity to be safe, or if HTTP failed)
        # Actually, let's make it simple: if movie status is not 200, try tv. 
        # If type was requested as movie but returned 200, let's also verify it is the expected movie? 
        # Wait, if type was requested as TV, we fetch TV.
        if r.status_code != 200 and media_type == 'movie':
            url_tv = f"https://api.tmdb.org/3/tv/{movie_id}?api_key={TMDB_API_KEY}"
            r = requests.get(url_tv, timeout=5)
        elif r.status_code != 200 and media_type == 'tv':
            url_movie = f"https://api.tmdb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}"
            r = requests.get(url_movie, timeout=5)
            
        r.raise_for_status()
        details = r.json()
        
        # Determine actual loaded media type
        is_tv = 'seasons' in details or 'first_air_date' in details or 'name' in details
        details['media_type'] = 'tv' if is_tv else 'movie'
        
        # Get IMDb ID for OMDb lookup
        imdb_id = details.get('imdb_id')
        if is_tv:
            try:
                ext_url = f"https://api.tmdb.org/3/tv/{movie_id}/external_ids?api_key={TMDB_API_KEY}"
                ext_r = requests.get(ext_url, timeout=3)
                if ext_r.status_code == 200:
                    imdb_id = ext_r.json().get('imdb_id')
                    details['imdb_id'] = imdb_id
            except Exception as ext_e:
                pass
                
        # Fetch OMDb awards if imdb_id is available
        details['parsed_awards'] = []
        if imdb_id:
            try:
                omdb_url = f"https://www.omdbapi.com/?i={imdb_id}&apikey={OMDB_API_KEY}"
                omdb_r = requests.get(omdb_url, timeout=3)
                if omdb_r.status_code == 200:
                    omdb_data = omdb_r.json()
                    awards_str = omdb_data.get('Awards', '')
                    
                    # Augment BAFTA if movie has popular BAFTA wins
                    if imdb_id in POPULAR_BAFTAS:
                        if awards_str and awards_str != 'N/A':
                            awards_str = POPULAR_BAFTAS[imdb_id] + ' ' + awards_str
                        else:
                            awards_str = POPULAR_BAFTAS[imdb_id]

                    if awards_str and awards_str != 'N/A':
                        sentences = []
                        for part in re.split(r'\.|\n', awards_str):
                            if part.strip():
                                sentences.append(part.strip())
                        
                        parsed_awards = []
                        for s in sentences:
                            s_low = s.lower()
                            
                            # Clean award text to concise layout: e.g. "Won 1 Oscar" -> "1 Oscar"
                            cleaned_text = s
                            match = re.search(r'(Won|Nominated for)\s+(\d+)\s+(Oscar|Academy Award|BAFTA|Golden Globe|Emmy)s?', s, re.IGNORECASE)
                            if match:
                                action = match.group(1).lower()
                                count = match.group(2)
                                name = match.group(3)
                                
                                if 'academy' in name.lower() or 'oscar' in name.lower():
                                    disp = "Oscar"
                                elif 'bafta' in name.lower():
                                    disp = "BAFTA"
                                elif 'globe' in name.lower():
                                    disp = "Golden Globe"
                                elif 'emmy' in name.lower():
                                    disp = "Emmy"
                                else:
                                    disp = name
                                    
                                if int(count) > 1 and not disp.endswith('s') and disp != "BAFTA":
                                    disp += 's'
                                    
                                if 'nom' in action:
                                    cleaned_text = f"{count} {disp} (Nom)"
                                else:
                                    cleaned_text = f"{count} {disp}"
                            
                            if 'oscar' in s_low or 'academy' in s_low:
                                parsed_awards.append({"type": "oscar", "text": cleaned_text, "color": "gold"})
                            elif 'bafta' in s_low:
                                parsed_awards.append({"type": "bafta", "text": cleaned_text, "color": "cyan"})
                            elif 'globe' in s_low:
                                parsed_awards.append({"type": "globe", "text": cleaned_text, "color": "green"})
                            elif 'emmy' in s_low:
                                parsed_awards.append({"type": "emmy", "text": cleaned_text, "color": "purple"})
                        details['parsed_awards'] = parsed_awards
            except Exception as omdb_e:
                pass

        # Fetch recommendations (higher quality than similar) with similar fallback
        similar_list = []
        try:
            rec_url = f"https://api.tmdb.org/3/{details['media_type']}/{movie_id}/recommendations?api_key={TMDB_API_KEY}"
            sim_r = requests.get(rec_url, timeout=3)
            if sim_r.status_code != 200 or len(sim_r.json().get('results', [])) == 0:
                rec_url = f"https://api.tmdb.org/3/{details['media_type']}/{movie_id}/similar?api_key={TMDB_API_KEY}"
                sim_r = requests.get(rec_url, timeout=3)
                
            if sim_r.status_code == 200:
                sim_data = sim_r.json()
                for item in sim_data.get('results', [])[:6]:
                    title = item.get('title') or item.get('name')
                    rel_date = item.get('release_date') or item.get('first_air_date')
                    similar_list.append({
                        'id': item.get('id'),
                        'title': title,
                        'poster_path': item.get('poster_path'),
                        'vote_average': item.get('vote_average'),
                        'release_date': rel_date,
                        'media_type': details['media_type']
                    })
        except Exception as sim_e:
            pass
        details['similar'] = similar_list
        
        # Normalize TV series keys
        if 'name' in details and 'title' not in details:
            details['title'] = details['name']
        if 'first_air_date' in details and 'release_date' not in details:
            details['release_date'] = details['first_air_date']
        if 'origin_country' in details and 'production_countries' not in details:
            details['production_countries'] = [{'iso_3166_1': c, 'name': c} for c in details['origin_country']]
        if 'languages' in details and 'spoken_languages' not in details:
            details['spoken_languages'] = [{'english_name': l.upper(), 'name': l.upper()} for l in details['languages']]
            
        return jsonify(details)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/image')
def proxy_image():
    path = request.args.get('path')
    if not path:
        return "Missing path", 400
    
    path = path.lstrip('/')
    if os.environ.get('VERCEL') == '1':
        cache_dir = '/tmp/cache'
    else:
        cache_dir = os.path.join(app.static_folder, 'cache')
    local_path = os.path.join(cache_dir, path)
    
    if os.path.exists(local_path):
        return send_from_directory(cache_dir, path)
        
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    
    tmdb_img_url = f"https://image.tmdb.org/t/p/{path}"
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/137.0.0.0 Safari/537.36"
            )
        }
        r = requests.get(tmdb_img_url, headers=headers, timeout=10)
        r.raise_for_status()
        
        with open(local_path, 'wb') as f:
            f.write(r.content)
            
        return send_from_directory(cache_dir, path)
    except Exception as e:
        print(f"Image fetch error: {e}")
        # Fallback to direct redirect/stream
        try:
            fallback_res = requests.get(tmdb_img_url, timeout=10)
            return fallback_res.content, 200, {'Content-Type': 'image/jpeg'}
        except:
            return "Failed to load poster image", 404

@app.route('/api/search-links/stream')
def stream_search_links():
    title = request.args.get('title')
    purpose = request.args.get('purpose')
    language = request.args.get('language')
    
    if not title:
        return jsonify({'error': 'Missing title parameter'}), 400

    log_queue = queue.Queue()
    
    # Callback to push log lines to our queue
    def log_callback(msg):
        log_queue.put(msg)
        
    testup4.register_subscriber(log_callback)
    
    results_container = {}
    
    def run_search_thread():
        try:
            results = testup4.run_movie_search(title, purpose, language)
            results_container['results'] = results
            results_container['status'] = 'success'
        except Exception as e:
            results_container['status'] = 'error'
            results_container['error'] = str(e)
        finally:
            log_queue.put(None)
            testup4.unregister_subscriber(log_callback)
            
    t = threading.Thread(target=run_search_thread)
    t.start()
    
    def event_stream():
        while True:
            try:
                # 30 second timeout safety
                msg = log_queue.get(timeout=30)
                if msg is None:
                    # Final payload
                    yield f"event: complete\ndata: {json.dumps(results_container)}\n\n"
                    break
                yield f"event: log\ndata: {msg}\n\n"
            except queue.Empty:
                yield f"event: log\ndata: [System] Connection timeout.\n\n"
                break
                
    return Response(event_stream(), mimetype="text/event-stream")

if __name__ == '__main__':
    print(f"Starting server on http://localhost:{PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=True, use_reloader=False)
