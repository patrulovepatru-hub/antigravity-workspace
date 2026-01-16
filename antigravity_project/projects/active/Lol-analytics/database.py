import sqlite3
import json
from contextlib import contextmanager
from config import DATABASE_PATH


def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_database():
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS champions (
                id INTEGER PRIMARY KEY,
                key TEXT UNIQUE,
                name TEXT NOT NULL,
                title TEXT,
                tags TEXT,
                stats_json TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                gold_total INTEGER,
                stats_json TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS runes (
                id INTEGER PRIMARY KEY,
                key TEXT,
                name TEXT NOT NULL,
                tree TEXT,
                slot INTEGER
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS summoners (
                puuid TEXT PRIMARY KEY,
                summoner_id TEXT,
                name TEXT,
                tier TEXT,
                rank TEXT,
                league_points INTEGER,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                id TEXT PRIMARY KEY,
                game_version TEXT,
                queue_id INTEGER,
                game_duration INTEGER,
                game_start_timestamp INTEGER,
                patch TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS match_participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id TEXT NOT NULL,
                puuid TEXT,
                champion_id INTEGER NOT NULL,
                team_id INTEGER,
                win BOOLEAN,
                kills INTEGER,
                deaths INTEGER,
                assists INTEGER,
                role TEXT,
                lane TEXT,
                item0 INTEGER,
                item1 INTEGER,
                item2 INTEGER,
                item3 INTEGER,
                item4 INTEGER,
                item5 INTEGER,
                item6 INTEGER,
                summoner1_id INTEGER,
                summoner2_id INTEGER,
                perk_primary_style INTEGER,
                perk_sub_style INTEGER,
                perks_json TEXT,
                FOREIGN KEY (match_id) REFERENCES matches(id),
                FOREIGN KEY (champion_id) REFERENCES champions(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS champion_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                champion_id INTEGER NOT NULL,
                role TEXT,
                games_played INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                bans INTEGER DEFAULT 0,
                total_games_analyzed INTEGER DEFAULT 0,
                patch TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (champion_id) REFERENCES champions(id),
                UNIQUE(champion_id, role, patch)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS builds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                champion_id INTEGER NOT NULL,
                role TEXT,
                items_json TEXT,
                runes_json TEXT,
                games_count INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                patch TEXT,
                FOREIGN KEY (champion_id) REFERENCES champions(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS team_compositions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                champions_json TEXT,
                games_count INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                patch TEXT
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_match_participants_match ON match_participants(match_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_match_participants_champion ON match_participants(champion_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_champion_stats_patch ON champion_stats(patch)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_matches_patch ON matches(patch)")


def insert_champion(champion_data):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO champions (id, key, name, title, tags, stats_json)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            int(champion_data.get('key', 0)),
            champion_data.get('id', ''),
            champion_data.get('name', ''),
            champion_data.get('title', ''),
            json.dumps(champion_data.get('tags', [])),
            json.dumps(champion_data.get('stats', {}))
        ))


def insert_item(item_id, item_data):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO items (id, name, description, gold_total, stats_json)
            VALUES (?, ?, ?, ?, ?)
        """, (
            int(item_id),
            item_data.get('name', ''),
            item_data.get('description', ''),
            item_data.get('gold', {}).get('total', 0),
            json.dumps(item_data.get('stats', {}))
        ))


def insert_rune(rune_data, tree_name, slot):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO runes (id, key, name, tree, slot)
            VALUES (?, ?, ?, ?, ?)
        """, (
            rune_data.get('id'),
            rune_data.get('key', ''),
            rune_data.get('name', ''),
            tree_name,
            slot
        ))


def insert_match(match_data):
    with get_db() as conn:
        cursor = conn.cursor()
        info = match_data.get('info', {})
        game_version = info.get('gameVersion', '')
        patch = '.'.join(game_version.split('.')[:2]) if game_version else ''

        cursor.execute("""
            INSERT OR IGNORE INTO matches (id, game_version, queue_id, game_duration, game_start_timestamp, patch)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            match_data.get('metadata', {}).get('matchId'),
            game_version,
            info.get('queueId'),
            info.get('gameDuration'),
            info.get('gameStartTimestamp'),
            patch
        ))

        match_id = match_data.get('metadata', {}).get('matchId')
        for participant in info.get('participants', []):
            perks = participant.get('perks', {})
            cursor.execute("""
                INSERT OR IGNORE INTO match_participants
                (match_id, puuid, champion_id, team_id, win, kills, deaths, assists,
                 role, lane, item0, item1, item2, item3, item4, item5, item6,
                 summoner1_id, summoner2_id, perk_primary_style, perk_sub_style, perks_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                match_id,
                participant.get('puuid'),
                participant.get('championId'),
                participant.get('teamId'),
                participant.get('win'),
                participant.get('kills'),
                participant.get('deaths'),
                participant.get('assists'),
                participant.get('teamPosition', participant.get('role', '')),
                participant.get('lane', ''),
                participant.get('item0'),
                participant.get('item1'),
                participant.get('item2'),
                participant.get('item3'),
                participant.get('item4'),
                participant.get('item5'),
                participant.get('item6'),
                participant.get('summoner1Id'),
                participant.get('summoner2Id'),
                perks.get('styles', [{}])[0].get('style') if perks.get('styles') else None,
                perks.get('styles', [{}, {}])[1].get('style') if len(perks.get('styles', [])) > 1 else None,
                json.dumps(perks)
            ))


def get_champion_by_id(champion_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM champions WHERE id = ?", (champion_id,))
        return cursor.fetchone()


def get_all_champions():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM champions ORDER BY name")
        return cursor.fetchall()


def get_matches_count():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM matches")
        return cursor.fetchone()['count']


if __name__ == "__main__":
    init_database()
    print("Base de datos inicializada correctamente.")
