from flask import Blueprint, jsonify, send_from_directory, request
import requests
from daily_pair import daily_pair
from datetime import datetime

def register_routes(app):
    api = Blueprint('api', __name__)

    TMDB_API_KEY = 'Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI1YTc0ZjUwMDJmOGQzNjRmMDIwN2ZiNzY4NWU0YjJiYiIsIm5iZiI6MTcxMzkxNTYxNS41Nzc5OTk4LCJzdWIiOiI2NjI4NDZkZjE3NmE5NDAxN2Y4MjQwN2MiLCJzY29wZXMiOlsiYXBpX3JlYWQiXSwidmVyc2lvbiI6MX0.jaZnUlZDZ-ymiHDFIBbgVJg4plv027Q1084Ut0XKkno'
    headers = {
        'accept': 'application/json',
        'Authorization': TMDB_API_KEY
    }

    @api.route('/test-pair', methods=['GET'])
    def get_daily_pair():
        if not daily_pair.get('starting_person') or not daily_pair.get('ending_person'):
            return jsonify({'error': 'Daily pair not set'}), 503
        return jsonify(daily_pair)

    @app.route('/person', methods=['GET'])
    def get_people():
        try:
            query = request.args.get('search', '').lower()
            results = []

            for page in range(1, 3):
                url = 'https://api.themoviedb.org/3/search/person'
                params = {
                    'query': query,
                    'include-adult': 'false',
                    'language': 'en-US',
                    'page': page
                }
                
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
                
                page_results = response.json().get('results', [])
                filtered = [
                    person for person in page_results
                    if person.get('known_for_department') in ['Acting', 'Directing'] and
                    person.get('popularity', 0) > 0 and
                    person.get('profile_path') is not None
                ]
                results.extend(filtered)

            results.sort(key=lambda x: x.get('popularity', 0), reverse=True)

            return jsonify(results)
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        
    @app.route('/movie', methods=['GET'])
    def get_movies():
        try:
            query = request.args.get('search', '').lower()
            results = []

            for page in range(1, 2):
                url = 'https://api.themoviedb.org/3/search/movie'
                params = {
                    'query': query,
                    'include-adult': 'false',
                    'language': 'en-US',
                    'page': page
                }
                
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
                
                page_results = response.json().get('results', [])
                filtered = [
                    movie for movie in page_results if
                    movie.get('popularity', 0) > 0 and
                    movie.get('poster_path') is not None and
                    movie.get('release_date') != '' and 
                    movie.get('release_date') < datetime.today().strftime('%Y-%m-%d')
                ]
                results.extend(filtered)

            results.sort(key=lambda x: x.get('popularity', 0), reverse=True)

            return jsonify(results)
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500

        
    @app.route('/person-credits', methods=['GET'])
    def get_person_credits():
        try:
            person_id = request.args.get('person_id', '')
            url = f'https://api.themoviedb.org/3/person/{person_id}/movie_credits?language=en-US'
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            cast_in = response.json().get('cast', [])
            cast_in_sorted = sorted(cast_in, key=lambda movie: movie.get('popularity', 0), reverse=True)
            crew_for = response.json().get('crew', [])

            movieIDs = [movie.get('id') for movie in cast_in_sorted]
            movieIDs.extend([movie.get('id') for movie in crew_for if movie.get('job') == 'Director'])

            poster_paths = [movie.get('poster_path') for movie in crew_for if movie.get('job') == 'Director']
            poster_paths.extend([movie.get('poster_path') for movie in cast_in_sorted if movie.get('poster_path') is not None and movie.get('popularity', 0) > 0])
            
            return jsonify({'IDs': movieIDs, 'images': poster_paths})
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        

    @app.route('/movie-credits', methods=['GET'])
    def get_movie_credits():
        try:
            movie_id = request.args.get('movie_id', '')
            url = f'https://api.themoviedb.org/3/movie/{movie_id}/credits?language=en-US'
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            cast = response.json().get('cast', [])
            crew = response.json().get('crew', [])

            personIDs = [person.get('id') for person in cast]
            personIDs.extend([person.get('id') for person in crew if person.get('job') == 'Director'])

            profile_paths = [person.get('profile_path') for person in crew if person.get('job') == 'Director'] # get the director
            profile_paths.extend([person.get('profile_path') for person in cast if person.get('profile_path') is not None]) # get everyone else

            return jsonify({'IDs': personIDs, 'images': profile_paths})
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500


    """@app.route('test-pair', methods=['GET'])
    def get_daily_pair_test():
        try:
            url1 = 'https://api.themoviedb.org/3/search/person?query=colin%20farrells&include_adult=false&language=en-US&page=1'
            url2 = 'https://api.themoviedb.org/3/search/person?query=cillian%20murphy&include_adult=false&language=en-US&page=1'
            
            response1 = requests.get(url1, headers=headers)
            response1.raise_for_status()
            response2 = requests.get(url2, headers=headers)
            response2.raise_for_status()

            starting_person = response1.json().get('results', [])[0]
            ending_person = response2.json().get('results', [])[0] 
            
            print(starting_person.get('name', 'Unknown'), f"(ID: {starting_person.get('id')})")

            return jsonify({
                'starting_person': starting_person,
                'ending_person': ending_person
            })

        except Exception as e:
            return jsonify({'error': str(e)}), 500"""
        
        
    app.register_blueprint(api, url_prefix='/api')

    @app.route('/')
    def home():
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/api/health')
    def health():
        return 'ok', 200
