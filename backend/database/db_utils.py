import sqlite3
import os
from definitions import ROOT_DIR, DATABASE

#DATABASE = os.path.join(ROOT_DIR, 'backend/database/database.db')

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def add_actor(actor):
    db = get_db()
    db.execute(
        '''
        INSERT INTO actors (id, name, profile_path)
        VALUES (?, ?, ?)
        ''',
        (
            int(actor['id']),
            actor['name'],
            actor['profile_path']
        )
    )
    db.commit()

def add_pair(pair, date):
    db = get_db()
    pair.sort()
    db.execute(
        '''
        INSERT INTO pairs (actor1_id, actor2_id, date)
        VALUES (?, ?, ?)
        ''',
        (
            int(pair[0]),
            int(pair[1]),
            date
        )
    )
    db.commit()

def fetch_actor_data(actor_id):
    print('database used:', DATABASE)
    db = get_db()
    return db.execute('SELECT * FROM actors WHERE id = ?', (actor_id,)).fetchone()

def is_pair_used(pair):
    db = get_db()
    pair.sort()
    return db.execute(
        'SELECT * FROM pairs WHERE actor1_id = ? AND actor2_id = ?',
        (int(pair[0]), int(pair[1]))
    ).fetchone() is not None

def get_pair_by_date(date):
    db = get_db()
    return db.execute(
        'SELECT actor1_id, actor2_id FROM pairs WHERE date = ?',
        (date,)
    ).fetchone()

def get_all_pairs():
    db = get_db()
    return db.execute(
        'SELECT actor1_id, actor2_id, date FROM pairs'
    ).fetchall()

def get_num_pairs():
    db = get_db()
    return db.execute(
        'SELECT COUNT(*) FROM pairs'
    ).fetchone()

