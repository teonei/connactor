import requests
from datetime import datetime
import time
import json
import random
import os
from definitions import ROOT_DIR
from .database.db_utils import is_pair_used, add_pair, fetch_actor_data, add_actor, get_pair_by_date
from zoneinfo import ZoneInfo


TMDB_API_KEY = 'Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI1YTc0ZjUwMDJmOGQzNjRmMDIwN2ZiNzY4NWU0YjJiYiIsIm5iZiI6MTcxMzkxNTYxNS41Nzc5OTk4LCJzdWIiOiI2NjI4NDZkZjE3NmE5NDAxN2Y4MjQwN2MiLCJzY29wZXMiOlsiYXBpX3JlYWQiXSwidmVyc2lvbiI6MX0.jaZnUlZDZ-ymiHDFIBbgVJg4plv027Q1084Ut0XKkno'
headers = {
    'accept': 'application/json',
    'Authorization': TMDB_API_KEY
}

def search(type, query):
    try:
        url = f'https://api.themoviedb.org/3/search/{type}'
        results = []

        for page in range(1, 3):
            params = {
                'query': query,
                'include-adult': 'false',
                'language': 'en-US',
                'page': page
            }

            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            page_results = response.json().get('results', [])

            filtered = []
            if (type == 'person'):
                filtered = [
                    person for person in page_results
                    if person.get('known_for_department') in ['Acting', 'Directing'] and
                    person.get('popularity', 0) > 0 and
                    person.get('profile_path') is not None
                ]
            else:
                filtered = [
                    movie for movie in page_results if
                    movie.get('popularity', 0) > 0 and
                    movie.get('poster_path') is not None and
                    movie.get('release_date') != '' and 
                    movie.get('release_date') < get_today()
                ]
            results.extend(filtered)
        
        results.sort(key=lambda x: x.get('popularity', 0), reverse=True)
        return results
    
    except Exception as e:
        return e
    
def get_credits(type, id):
    url = f'https://api.themoviedb.org/3/{type}/{id}/{'movie_' if type == 'person' else ''}credits?language=en-US'
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        cast = response.json().get('cast', [])
        if (type == 'person'): # if getting movie credits for a person, sort the movie by popularity
            cast.sort(key=lambda credit: credit.get('popularity', 0), reverse=True)
        crew = response.json().get('crew', [])

        ids = [credit.get('id') for credit in cast]
        ids.extend([credit.get('id') for credit in crew if credit.get('job') == 'Director'])

        image_path = 'poster_path' if type == 'person' else 'profile_path'
        images = [credit.get(image_path) for credit in crew if credit.get('job') == 'Director' and credit.get(image_path) is not None]
        images.extend([credit.get(image_path) for credit in cast if credit.get(image_path) is not None and credit.get('order', 11) <= 10 and credit.get(image_path) not in images])

        return {'IDs': ids, 'images': images}

    except Exception as e:
        return e

def get_today():
    return datetime.now(ZoneInfo("America/Los_Angeles")).strftime('%Y-%m-%d')

def get_starting_pair():
    today = get_today()

    print('trying to get pair for ', today)
    pair_ids = get_pair_by_date(today)
    
    while (pair_ids is None):
        print('waiting for new pair... @ ', today)
        time.sleep(1)
        pair_ids = get_pair_by_date(today)
        
    print('got pair for ', today)
    actor1 = fetch_actor_data(int(pair_ids[0]))
    actor2 = fetch_actor_data(int(pair_ids[1]))
    return [dict(actor1), dict(actor2)]


def get_random_person():
    url = 'https://api.themoviedb.org/3/person/popular'
    params = {
        'language': 'en-US',
        'page': 1
    }
    
    popularity_threshold = 4 # Minimum popularity for a person to be considered

    popularity = 0
    known_for_movies = False
    known_for_department = ''
    adult_content = True
    poster_path = ''
    chosen_person = {}
    language_is_en = False
    while (popularity < popularity_threshold or not known_for_movies
            or known_for_department != 'Acting' or adult_content or not poster_path or not language_is_en):
        params['page'] = random.randint(1, 100)
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        chosen_person = random.choice(response.json().get('results', []))

        popularity = chosen_person.get('popularity', 0)
    
        known_for_list = chosen_person.get('known_for', [])
        popular_media = sum(
            1 for media in known_for_list
            if media.get('media_type') == 'movie' and media.get('popularity', 0) > popularity_threshold
        )

        language_is_en = all(movie.get('original_language') == 'en' for movie in known_for_list)
        known_for_movies = True if popular_media >= (len(known_for_list) // 2 + 1) else False
        known_for_department = chosen_person.get('known_for_department', '')
        adult_content = chosen_person.get('adult', True)
        poster_path = chosen_person.get('profile_path', '')

    return chosen_person

def get_valid_pair():
    starting_person = get_random_person()
    ending_person = get_random_person()
    while (ending_person.get('id') == starting_person.get('id')):
        ending_person = get_random_person()

    return [starting_person, ending_person]


def update_starting_pair():
    today = get_today()
    print('updating.... @ ', today)

    new_pair = get_valid_pair()
    while is_pair_used([new_pair[0]['id'], new_pair[1]['id']]):
        new_pair = get_valid_pair()

    for actor in new_pair:
        fetched_data = fetch_actor_data(actor['id'])

        if fetched_data is None:
            add_actor(actor)
            print(f'inserted {actor["name"]} ({actor["id"]})')
        else:
            print('fetched data: ', dict(fetched_data))
            print(f' {actor["name"]} ({actor["id"]}) already in db')

    fetched_data = get_pair_by_date(today)
    if fetched_data is None:
        add_pair([new_pair[0]['id'], new_pair[1]['id']], today)
        print('inserted pair', [new_pair[0]['id'], new_pair[1]['id']])



