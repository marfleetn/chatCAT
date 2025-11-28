#!/usr/bin/env python3
"""
chatCAT - AI Chat Cataloguing System v2.4
VISUAL UPDATE: Compressed layout, Solid UI, Segmented Controls
"""

import sqlite3
import json
import re
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import traceback

DB_FILE = 'ai_chats.db'


class ChatDatabase:
    def __init__(self, db_file=DB_FILE):
        self.db_file = db_file
        self.init_database()
    
    def init_database(self):
        """Initialise the database with required tables"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                conversation_id TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_message TEXT,
                ai_response TEXT,
                metadata TEXT,
                notes TEXT DEFAULT '',
                tags TEXT DEFAULT '',
                UNIQUE(platform, conversation_id, timestamp)
            )
        ''')
        
        # Tags management table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                color TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert default tags if table is empty
        cursor.execute('SELECT COUNT(*) FROM tags')
        if cursor.fetchone()[0] == 0:
            default_tags = [
                ('important', '#FF6B35'),
                ('work', '#4285F4'),
                ('personal', '#9C27B0'),
                ('reference', '#10A37F'),
                ('tutorial', '#FF8C00'),
                ('code', '#20B2AA'),
                ('idea', '#FFEB3B'),
                ('question', '#FF4081')
            ]
            cursor.executemany('INSERT INTO tags (name, color) VALUES (?, ?)', default_tags)
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_platform ON chats(platform)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON chats(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversation ON chats(platform, conversation_id)')
        
        # Check if FTS table exists and recreate if needed
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chats_fts'")
        fts_exists = cursor.fetchone() is not None
        
        if not fts_exists:
            cursor.execute('''
                CREATE VIRTUAL TABLE IF NOT EXISTS chats_fts 
                USING fts5(user_message, ai_response, notes, tags, content=chats, content_rowid=id)
            ''')
            
            # Populate FTS from existing data
            cursor.execute('''
                INSERT INTO chats_fts(rowid, user_message, ai_response, notes, tags)
                SELECT id, COALESCE(user_message, ''), COALESCE(ai_response, ''), 
                       COALESCE(notes, ''), COALESCE(tags, '')
                FROM chats
            ''')
        
        # Drop existing triggers and recreate
        cursor.execute('DROP TRIGGER IF EXISTS chats_ai')
        cursor.execute('DROP TRIGGER IF EXISTS chats_ad')
        cursor.execute('DROP TRIGGER IF EXISTS chats_au')
        
        cursor.execute('''
            CREATE TRIGGER chats_ai AFTER INSERT ON chats BEGIN
                INSERT INTO chats_fts(rowid, user_message, ai_response, notes, tags)
                VALUES (new.id, COALESCE(new.user_message, ''), COALESCE(new.ai_response, ''), 
                        COALESCE(new.notes, ''), COALESCE(new.tags, ''));
            END
        ''')
        
        cursor.execute('''
            CREATE TRIGGER chats_ad AFTER DELETE ON chats BEGIN
                INSERT INTO chats_fts(chats_fts, rowid, user_message, ai_response, notes, tags)
                VALUES ('delete', old.id, COALESCE(old.user_message, ''), COALESCE(old.ai_response, ''),
                        COALESCE(old.notes, ''), COALESCE(old.tags, ''));
            END
        ''')
        
        cursor.execute('''
            CREATE TRIGGER chats_au AFTER UPDATE ON chats BEGIN
                INSERT INTO chats_fts(chats_fts, rowid, user_message, ai_response, notes, tags)
                VALUES ('delete', old.id, COALESCE(old.user_message, ''), COALESCE(old.ai_response, ''),
                        COALESCE(old.notes, ''), COALESCE(old.tags, ''));
                INSERT INTO chats_fts(rowid, user_message, ai_response, notes, tags)
                VALUES (new.id, COALESCE(new.user_message, ''), COALESCE(new.ai_response, ''),
                        COALESCE(new.notes, ''), COALESCE(new.tags, ''));
            END
        ''')
        
        conn.commit()
        conn.close()
        print(f"✓ Database initialised: {self.db_file}")
    
    def add_chat(self, platform, conversation_id, user_message, ai_response, metadata=None):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO chats 
                (platform, conversation_id, user_message, ai_response, metadata, notes, tags)
                VALUES (?, ?, ?, ?, ?, '', '')
            ''', (platform, conversation_id, user_message, ai_response,
                  json.dumps(metadata) if metadata else None))
            
            conn.commit()
            row_id = cursor.lastrowid
            conn.close()
            return row_id
        except Exception as e:
            conn.close()
            print(f"✗ Error adding chat: {e}")
            raise e
    
    def count_term_occurrences(self, text, search_terms):
        """Count how many times search terms appear in text"""
        if not text or not search_terms:
            return 0
        
        text_lower = text.lower()
        count = 0
        
        for term in search_terms:
            term_lower = term.lower()
            pattern = r'\b' + re.escape(term_lower) + r'\b'
            matches = re.findall(pattern, text_lower)
            count += len(matches)
        
        return count
    
    def update_notes(self, chat_id, notes):
        """Update notes for a chat"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        try:
            # Ensure notes is a string
            notes = notes if notes is not None else ''
            
            cursor.execute('UPDATE chats SET notes = ? WHERE id = ?', (notes, int(chat_id)))
            conn.commit()
            
            rows_affected = cursor.rowcount
            conn.close()
            
            if rows_affected == 0:
                raise Exception(f"No chat found with ID {chat_id}")
            
            print(f"✓ Updated notes for chat ID {chat_id}")
            return True
        except Exception as e:
            conn.close()
            print(f"✗ Error updating notes: {e}")
            traceback.print_exc()
            raise e
    
    def update_tags(self, chat_id, tags):
        """Update tags for a chat (comma-separated string)"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        try:
            # Ensure tags is a string
            tags = tags if tags is not None else ''
            
            cursor.execute('UPDATE chats SET tags = ? WHERE id = ?', (tags, int(chat_id)))
            conn.commit()
            
            rows_affected = cursor.rowcount
            conn.close()
            
            if rows_affected == 0:
                raise Exception(f"No chat found with ID {chat_id}")
            
            print(f"✓ Updated tags for chat ID {chat_id}: {tags}")
            return True
        except Exception as e:
            conn.close()
            print(f"✗ Error updating tags: {e}")
            traceback.print_exc()
            raise e
    
    def get_all_tags(self):
        """Get all available tags"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, color FROM tags ORDER BY name')
        tags = [{'id': row[0], 'name': row[1], 'color': row[2]} for row in cursor.fetchall()]
        conn.close()
        return tags
    
    def add_tag(self, name, color):
        """Add a new tag"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        try:
            cursor.execute('INSERT INTO tags (name, color) VALUES (?, ?)', (name, color))
            conn.commit()
            tag_id = cursor.lastrowid
            conn.close()
            print(f"✓ Created new tag: {name} ({color})")
            return tag_id
        except sqlite3.IntegrityError:
            conn.close()
            print(f"Tag already exists: {name}")
            return None
        except Exception as e:
            conn.close()
            print(f"✗ Error creating tag: {e}")
            raise e
    
    def get_full_chat(self, chat_id):
        """Get full chat details by ID"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, platform, conversation_id, timestamp,
                   user_message, ai_response, metadata, 
                   COALESCE(notes, '') as notes, 
                   COALESCE(tags, '') as tags
            FROM chats
            WHERE id = ?
        ''', (chat_id,))
        
        result = cursor.fetchone()
        conn.close()
        return result
    
    def advanced_search(self, query=None, platforms=None, start_date=None, 
                       end_date=None, tags=None, limit=100, offset=0):
        """Advanced search with relevance ranking"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        where_clauses = []
        params = []
        
        search_terms = []
        if query:
            search_terms = [term.strip() for term in query.replace('"', '').split() if term.strip()]
        
        if query:
            where_clauses.append('c.id IN (SELECT rowid FROM chats_fts WHERE chats_fts MATCH ?)')
            params.append(query)
        
        if platforms and len(platforms) > 0:
            placeholders = ','.join('?' * len(platforms))
            where_clauses.append(f'c.platform IN ({placeholders})')
            params.extend(platforms)
        
        if start_date:
            where_clauses.append('c.timestamp >= ?')
            params.append(start_date)
        
        if end_date:
            where_clauses.append('c.timestamp <= ?')
            params.append(end_date)
        
        if tags and len(tags) > 0:
            tag_conditions = []
            for tag in tags:
                tag_conditions.append('c.tags LIKE ?')
                params.append(f'%{tag}%')
            where_clauses.append('(' + ' OR '.join(tag_conditions) + ')')
        
        where_sql = ' AND '.join(where_clauses) if where_clauses else '1=1'
        
        sql = f'''
            SELECT c.id, c.platform, c.conversation_id, c.timestamp,
                   c.user_message, c.ai_response, 
                   COALESCE(c.notes, '') as notes, 
                   COALESCE(c.tags, '') as tags
            FROM chats c
            WHERE {where_sql}
            ORDER BY c.timestamp DESC
        '''
        
        cursor.execute(sql, params)
        all_results = cursor.fetchall()
        
        if search_terms:
            results_with_scores = []
            for row in all_results:
                user_msg = row[4] or ''
                ai_resp = row[5] or ''
                notes = row[6] or ''
                tags_str = row[7] or ''
                
                user_count = self.count_term_occurrences(user_msg, search_terms)
                ai_count = self.count_term_occurrences(ai_resp, search_terms)
                notes_count = self.count_term_occurrences(notes, search_terms) * 2
                tags_count = self.count_term_occurrences(tags_str, search_terms) * 3
                
                relevance_score = user_count + ai_count + notes_count + tags_count
                results_with_scores.append((row, relevance_score))
            
            results_with_scores.sort(key=lambda x: (-x[1], x[0][3]), reverse=False)
            sorted_results = [item[0] for item in results_with_scores]
        else:
            sorted_results = all_results
        
        total = len(sorted_results)
        paginated_results = sorted_results[offset:offset + limit]
        
        conn.close()
        return paginated_results, total, search_terms
    
    def get_platforms(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT platform FROM chats ORDER BY platform')
        platforms = [row[0] for row in cursor.fetchall()]
        conn.close()
        return platforms
    
    def get_stats(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM chats')
        total = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT platform, COUNT(*) as count 
            FROM chats 
            GROUP BY platform
            ORDER BY count DESC
        ''')
        by_platform = cursor.fetchall()
        
        cursor.execute('SELECT MIN(timestamp), MAX(timestamp) FROM chats')
        min_date, max_date = cursor.fetchone()
        
        conn.close()
        return {
            'total_chats': total,
            'by_platform': dict(by_platform),
            'date_range': {'min': min_date, 'max': max_date}
        }


class ChatCATHandler(BaseHTTPRequestHandler):
    db = ChatDatabase()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            self.serve_dashboard()
        elif parsed_path.path == '/favicon.ico' or parsed_path.path == '/favicon.svg':
            self.serve_favicon()
        elif parsed_path.path == '/app.js':
            self.serve_javascript()
        elif parsed_path.path == '/api/stats':
            self.serve_stats()
        elif parsed_path.path == '/api/platforms':
            self.serve_platforms()
        elif parsed_path.path == '/api/tags':
            self.serve_tags()
        elif parsed_path.path == '/api/search':
            self.serve_advanced_search(parsed_path.query)
        elif parsed_path.path == '/api/chat':
            self.serve_full_chat(parsed_path.query)
        else:
            self.send_error(404)
    
    def do_POST(self):
        if self.path == '/api/add':
            self.handle_add_chat()
        elif self.path == '/api/notes/update':
            self.handle_update_notes()
        elif self.path == '/api/tags/update':
            self.handle_update_tags()
        elif self.path == '/api/tags/add':
            self.handle_add_tag()
        else:
            self.send_error(404)
    
    def handle_update_notes(self):
        """Handle notes update request"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            data = json.loads(post_data.decode('utf-8'))
            chat_id = data.get('chat_id')
            notes = data.get('notes', '')
            
            if not chat_id:
                self.send_json_response({'error': 'Chat ID required'}, 400)
                return
            
            self.db.update_notes(chat_id, notes)
            
            self.send_json_response({
                'status': 'success',
                'message': 'Notes updated'
            })
            
        except json.JSONDecodeError as e:
            print(f"✗ JSON decode error: {e}")
            self.send_json_response({'error': 'Invalid JSON'}, 400)
        except Exception as e:
            print(f"✗ Notes update error: {e}")
            traceback.print_exc()
            self.send_json_response({'error': str(e)}, 500)
    
    def handle_update_tags(self):
        """Handle tags update request"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            data = json.loads(post_data.decode('utf-8'))
            chat_id = data.get('chat_id')
            tags = data.get('tags', [])
            
            if not chat_id:
                self.send_json_response({'error': 'Chat ID required'}, 400)
                return
            
            # Convert list to comma-separated string, filtering empty values
            if isinstance(tags, list):
                tags = [t for t in tags if t]  # Remove empty strings
                tags_str = ','.join(tags)
            else:
                tags_str = tags or ''
            
            self.db.update_tags(chat_id, tags_str)
            
            self.send_json_response({
                'status': 'success',
                'message': 'Tags updated',
                'tags': tags if isinstance(tags, list) else tags_str.split(',')
            })
            
        except json.JSONDecodeError as e:
            print(f"✗ JSON decode error: {e}")
            self.send_json_response({'error': 'Invalid JSON'}, 400)
        except Exception as e:
            print(f"✗ Tags update error: {e}")
            traceback.print_exc()
            self.send_json_response({'error': str(e)}, 500)
    
    def handle_add_tag(self):
        """Handle adding a new tag"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            data = json.loads(post_data.decode('utf-8'))
            name = data.get('name', '').strip().lower()
            color = data.get('color', '#00FF00')
            
            if not name:
                self.send_json_response({'error': 'Tag name required'}, 400)
                return
            
            tag_id = self.db.add_tag(name, color)
            
            if tag_id:
                self.send_json_response({
                    'status': 'success',
                    'message': 'Tag created',
                    'tag': {'id': tag_id, 'name': name, 'color': color}
                })
            else:
                self.send_json_response({'error': 'Tag already exists', 'name': name}, 409)
            
        except json.JSONDecodeError as e:
            print(f"✗ JSON decode error: {e}")
            self.send_json_response({'error': 'Invalid JSON'}, 400)
        except Exception as e:
            print(f"✗ Tag creation error: {e}")
            traceback.print_exc()
            self.send_json_response({'error': str(e)}, 500)
    
    def handle_add_chat(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            data = json.loads(post_data.decode('utf-8'))
            platform = data.get('platform')
            conversation_id = data.get('conversation_id')
            user_message = data.get('user_message')
            ai_response = data.get('ai_response')
            metadata = data.get('metadata')
            
            if not all([platform, user_message, ai_response]):
                self.send_json_response({'error': 'Missing required fields'}, 400)
                return
            
            row_id = self.db.add_chat(platform, conversation_id, user_message, ai_response, metadata)
            
            self.send_json_response({
                'status': 'success',
                'id': row_id,
                'message': 'Chat saved'
            })
            
            print(f"✓ Saved chat from {platform} (ID: {row_id})")
            
        except json.JSONDecodeError:
            self.send_json_response({'error': 'Invalid JSON'}, 400)
        except Exception as e:
            print(f"✗ Add chat error: {e}")
            traceback.print_exc()
            self.send_json_response({'error': str(e)}, 500)
    
    def serve_stats(self):
        stats = self.db.get_stats()
        self.send_json_response(stats)
    
    def serve_platforms(self):
        platforms = self.db.get_platforms()
        self.send_json_response({'platforms': platforms})
    
    def serve_tags(self):
        tags = self.db.get_all_tags()
        self.send_json_response({'tags': tags})
    
    def serve_favicon(self):
        svg = '''<svg width="64" height="64" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
  <circle cx="32" cy="32" r="32" fill="#3C3C3C"/>
  <text x="32" y="42" font-family="'Courier New', monospace" font-size="28" font-weight="bold" fill="#00FF00" text-anchor="middle">CC</text>
</svg>'''
        
        self.send_response(200)
        self.send_header('Content-type', 'image/svg+xml')
        self.send_header('Cache-Control', 'public, max-age=31536000')
        self.end_headers()
        self.wfile.write(svg.encode('utf-8'))
    
    def serve_full_chat(self, query_string):
        """Serve full chat details"""
        params = parse_qs(query_string)
        chat_id = params.get('id', [None])[0]
        
        if not chat_id:
            self.send_json_response({'error': 'Chat ID required'}, 400)
            return
        
        result = self.db.get_full_chat(chat_id)
        
        if not result:
            self.send_json_response({'error': 'Chat not found'}, 404)
            return
        
        tags_str = result[8] if len(result) > 8 else ''
        tags_list = [t.strip() for t in tags_str.split(',') if t.strip()] if tags_str else []
        
        chat = {
            'id': result[0],
            'platform': result[1],
            'conversation_id': result[2],
            'timestamp': result[3],
            'user_message': result[4],
            'ai_response': result[5],
            'metadata': json.loads(result[6]) if result[6] else None,
            'notes': result[7] if len(result) > 7 else '',
            'tags': tags_list
        }
        
        self.send_json_response(chat)
    
    def serve_advanced_search(self, query_string):
        """Serve advanced search results with relevance ranking"""
        params = parse_qs(query_string)
        query = params.get('q', [''])[0] if params.get('q', [''])[0] else None
        platforms = params.get('platforms[]', [])
        tags = params.get('tags[]', [])
        start_date = params.get('start_date', [None])[0]
        end_date = params.get('end_date', [None])[0]
        limit = int(params.get('limit', [50])[0])
        offset = int(params.get('offset', [0])[0])
        
        results, total, search_terms = self.db.advanced_search(
            query=query,
            platforms=platforms if platforms else None,
            start_date=start_date,
            end_date=end_date,
            tags=tags if tags else None,
            limit=limit,
            offset=offset
        )
        
        formatted_results = []
        for r in results:
            user_msg = r[4] or ''
            ai_resp = r[5] or ''
            notes = r[6] or ''
            tags_str = r[7] or ''
            
            relevance = 0
            if search_terms:
                relevance = self.db.count_term_occurrences(user_msg, search_terms) + \
                           self.db.count_term_occurrences(ai_resp, search_terms) + \
                           self.db.count_term_occurrences(notes, search_terms) * 2 + \
                           self.db.count_term_occurrences(tags_str, search_terms) * 3
            
            tags_list = [t.strip() for t in tags_str.split(',') if t.strip()] if tags_str else []
            
            formatted_results.append({
                'id': r[0],
                'platform': r[1],
                'conversation_id': r[2],
                'timestamp': r[3],
                'user_message': user_msg,
                'ai_response': ai_resp,
                'notes': notes,
                'tags': tags_list,
                'relevance': relevance
            })
        
        self.send_json_response({
            'query': query,
            'search_terms': search_terms,
            'platforms': platforms,
            'start_date': start_date,
            'end_date': end_date,
            'count': len(formatted_results),
            'total': total,
            'offset': offset,
            'limit': limit,
            'results': formatted_results
        })
    
    def serve_dashboard(self):
        """Serve the fully branded chatCAT dashboard"""
        html = '''<!DOCTYPE html>
<html>
<head>
    <title>chatCAT - Organise Your AI Conversations</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="icon" type="image/svg+xml" href="/favicon.svg">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        
        :root {
            --bg-dark: #3C3C3C;
            --bg-darker: #2A2A2A;
            --bg-lighter: #4A4A4A;
            --text-primary: #FFFFFF;
            --text-secondary: #AAAAAA;
            --text-muted: #777777;
            --accent-green: #00FF00;
            --accent-dim: #00AA00;
            --border-white: #FFFFFF;
            --border-gray: #555555;
            --border-subtle: #444444;
        }
        
        body {
            font-family: 'Courier New', 'Consolas', 'Monaco', monospace;
            background: var(--bg-dark);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 15px;
            line-height: 1.6;
        }
        
        .container { max-width: 1300px; margin: 0 auto; }
        
        /* --- COMPRESSED TOP SECTION --- */
        .top-section {
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .brand-header {
            background: var(--bg-darker);
            padding: 20px;
            border: 2px solid var(--border-white);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            min-height: 120px;
        }
        
        .brand-name {
            font-size: 38px;
            font-weight: 700;
            letter-spacing: 4px;
            color: var(--accent-green);
            text-shadow: 0 0 10px rgba(0, 255, 0, 0.5);
            margin-bottom: 5px;
        }
        
        .tagline {
            color: var(--text-secondary);
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .stats {
            background: var(--bg-darker);
            padding: 15px 20px;
            border: 2px solid var(--border-white);
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        
        .stats h2, .search-section h2, .results-header h2 {
            color: var(--accent-green);
            font-size: 14px;
            font-weight: 600;
            padding-bottom: 5px;
            display: block;
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-bottom: 10px;
            opacity: 0.8;
        }
        
        .stat-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
        }
        
        /* CLEAN DASHBOARD STYLE (No box borders, focus on number) */
        .stat-item {
            background: var(--bg-lighter);
            padding: 10px 15px;
            border-radius: 4px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        
        .stat-label {
            font-size: 10px;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 2px;
        }
        
        .stat-value {
            font-size: 26px;
            font-weight: 700;
            color: var(--accent-green);
            line-height: 1;
        }
        
        /* --- CLEAN SEARCH SECTION --- */
        .search-section {
            background: var(--bg-darker);
            padding: 20px;
            /* Removed heavy border, using simple top border if needed or just background contrast */
            margin-bottom: 20px;
            border-top: 2px solid var(--border-subtle);
        }
        
        .filter-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 30px;
            margin-bottom: 20px;
            align-items: end;
        }
        
        .filter-group { display: flex; flex-direction: column; }
        
        .filter-label {
            font-weight: 600;
            margin-bottom: 8px;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-secondary);
        }
        
        /* MINIMALIST INPUTS */
        input[type="text"], input[type="date"] {
            padding: 10px 0;
            border: none;
            border-bottom: 2px solid var(--border-gray);
            background: transparent;
            color: var(--text-primary);
            font-size: 16px;
            font-family: inherit;
            width: 100%;
            transition: border 0.3s;
        }
        
        input:focus {
            outline: none;
            border-bottom-color: var(--accent-green);
        }
        
        /* SEGMENTED CONTROL FOR DATES */
        .segmented-control {
            display: flex;
            border: 1px solid var(--border-gray);
            border-radius: 4px;
            overflow: hidden;
            background: var(--bg-lighter);
        }
        
        .segmented-control button {
            flex: 1;
            background: transparent;
            color: var(--text-secondary);
            border: none;
            border-right: 1px solid var(--border-gray);
            padding: 8px 5px;
            font-size: 11px;
            cursor: pointer;
            transition: all 0.2s;
            text-transform: uppercase;
            font-weight: 600;
            margin: 0;
        }
        
        .segmented-control button:last-child { border-right: none; }
        
        .segmented-control button:hover {
            background: rgba(255,255,255,0.05);
            color: var(--text-primary);
        }
        
        .segmented-control button.active {
            background: var(--accent-green);
            color: var(--bg-dark);
            text-shadow: none;
        }

        .platform-options {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            padding-top: 5px;
        }
        
        .platform-option {
            display: flex;
            align-items: center;
            cursor: pointer;
        }
        
        .platform-option label {
            cursor: pointer;
            font-size: 13px;
            color: var(--text-primary);
        }
        
        .platform-option input[type="checkbox"] {
            width: 16px;
            height: 16px;
            margin-right: 8px;
            accent-color: var(--accent-green);
            cursor: pointer;
        }
        
        .action-bar {
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            margin-top: 25px;
            padding-top: 20px;
            border-top: 1px solid var(--border-subtle);
        }

        /* PRIMARY SEARCH BUTTON */
        .btn-primary {
            background: var(--accent-green);
            color: var(--bg-dark);
            border: none;
            padding: 12px 35px;
            font-weight: 800;
            font-size: 14px;
            letter-spacing: 1px;
            cursor: pointer;
            text-transform: uppercase;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .btn-primary:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 15px rgba(0,255,0,0.3);
        }
        
        .btn-secondary {
            background: transparent;
            color: var(--text-secondary);
            border: 1px solid var(--border-gray);
            padding: 10px 20px;
            font-size: 12px;
            cursor: pointer;
            text-transform: uppercase;
            transition: all 0.2s;
            margin-left: 10px;
        }
        
        .btn-secondary:hover {
            border-color: var(--text-primary);
            color: var(--text-primary);
        }
        
        /* --- RESULTS SECTION --- */
        .results {
            padding: 0 20px;
        }
        
        .results-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            border-bottom: 1px solid var(--border-gray);
            padding-bottom: 10px;
        }
        
        .chat-item {
            border-bottom: 1px solid var(--border-subtle);
            padding: 20px 0;
            cursor: pointer;
            transition: background 0.2s;
        }
        
        .chat-item:hover {
            background: rgba(255,255,255,0.02);
        }
        
        .chat-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            flex-wrap: wrap;
            gap: 8px;
        }
        
        .chat-badges {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            align-items: center;
        }
        
        .platform-badge {
            font-size: 12px;
            font-weight: 700;
            color: var(--accent-green);
            text-transform: uppercase;
        }
        
        .relevance-badge {
            display: inline-block;
            background: var(--bg-lighter);
            color: var(--text-secondary);
            padding: 2px 6px;
            font-size: 10px;
            border-radius: 3px;
        }
        
        .tag-badge {
            display: inline-block;
            padding: 2px 6px;
            font-size: 10px;
            font-weight: 600;
            border: 1px solid;
            text-transform: uppercase;
            border-radius: 3px;
        }
        
        .timestamp {
            color: var(--text-muted);
            font-size: 11px;
        }
        
        .preview-text {
            color: var(--text-secondary);
            font-size: 13px;
            margin-bottom: 5px;
            overflow: hidden;
            white-space: nowrap;
            text-overflow: ellipsis;
        }
        
        .highlight {
            background: rgba(0, 255, 0, 0.2);
            color: white;
            padding: 0 2px;
        }
        
        .active-filters {
            font-size: 12px;
            color: var(--text-secondary);
            margin-bottom: 15px;
            padding-left: 20px;
        }
        
        .filter-tag {
            color: var(--accent-green);
            margin-right: 10px;
        }
        
        /* PAGINATION */
        .pagination {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        
        .pagination button {
            background: transparent;
            border: none;
            color: var(--text-secondary);
            cursor: pointer;
            font-family: inherit;
        }
        .pagination button:hover { color: var(--accent-green); }
        
        /* MODAL (Kept mostly same, just slight cleanups) */
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.85);
            backdrop-filter: blur(2px);
        }
        
        .modal-content {
            background: var(--bg-dark);
            margin: 5vh auto;
            border: 1px solid var(--border-gray);
            box-shadow: 0 20px 50px rgba(0,0,0,0.5);
            width: 90%;
            max-width: 800px;
            max-height: 90vh;
            display: flex;
            flex-direction: column;
        }
        
        .modal-header {
            padding: 20px;
            border-bottom: 1px solid var(--border-gray);
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: var(--bg-darker);
        }
        
        .modal-title { font-size: 16px; color: var(--accent-green); text-transform: uppercase; }
        .close { color: var(--text-secondary); font-size: 24px; cursor: pointer; }
        .close:hover { color: var(--text-primary); }
        
        .modal-body { padding: 30px; overflow-y: auto; flex: 1; }
        
        .chat-full .user-message {
            color: var(--text-primary);
            margin-bottom: 20px;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border-subtle);
        }
        
        .chat-full .ai-response {
            color: var(--text-secondary);
            line-height: 1.8;
            margin-bottom: 30px;
        }
        
        .label {
            font-size: 10px;
            text-transform: uppercase;
            color: var(--accent-green);
            margin-bottom: 5px;
            letter-spacing: 1px;
        }

        /* Tags & Notes common styles */
        .tags-section, .notes-section { margin-top: 30px; padding-top: 20px; border-top: 1px dashed var(--border-gray); }
        .section-header { display: flex; justify-content: space-between; margin-bottom: 15px; }
        .section-header h3 { font-size: 14px; color: var(--text-primary); }
        
        .tags-container { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 15px; }
        .tag-chip {
            padding: 4px 10px;
            font-size: 11px;
            font-weight: 600;
            border: 1px solid;
            cursor: pointer;
            border-radius: 12px;
            text-transform: uppercase;
        }
        .tag-chip:hover { opacity: 0.8; }
        
        .notes-textarea {
            width: 100%;
            min-height: 100px;
            padding: 10px;
            background: var(--bg-lighter);
            border: 1px solid var(--border-gray);
            color: var(--text-primary);
            font-family: inherit;
        }
        
        .loading-message { text-align: center; color: var(--text-muted); padding: 20px; font-size: 12px; }
        
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: var(--bg-dark); }
        ::-webkit-scrollbar-thumb { background: var(--border-gray); border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--text-secondary); }
        
        @media (max-width: 1024px) {
            .top-section { grid-template-columns: 1fr; }
            .stat-grid { grid-template-columns: repeat(2, 1fr); }
            .filter-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="top-section">
            <div class="brand-header">
                <div class="brand-name">chatCAT</div>
                <div class="tagline">Organise Your AI Conversations</div>
            </div>
            
            <div class="stats" id="stats">
                <div class="stat-grid" id="stat-grid">
                    <div class="loading-message">● LOADING STATS...</div>
                </div>
            </div>
        </div>
        
        <div class="search-section">
            <div class="filter-grid">
                
                <div class="filter-group">
                    <div style="margin-bottom: 25px;">
                        <label class="filter-label">Search Query</label>
                        <input type="text" id="search-query" placeholder="Type to search content, notes, or tags...">
                    </div>
                    
                    <div>
                        <label class="filter-label">Time Period</label>
                        <div class="segmented-control" id="date-controls">
                            <button onclick="setDateRange('today', this)">Today</button>
                            <button onclick="setDateRange('week', this)">7d</button>
                            <button onclick="setDateRange('month', this)">30d</button>
                            <button onclick="setDateRange('3months', this)">3M</button>
                            <button onclick="setDateRange('year', this)">1Y</button>
                            <button onclick="setDateRange('all', this)" class="active">All</button>
                        </div>
                        <div style="display: none;">
                            <input type="date" id="start-date">
                            <input type="date" id="end-date">
                        </div>
                    </div>
                </div>
                
                <div class="filter-group">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <label class="filter-label">Platforms</label>
                        <div style="font-size: 10px;">
                            <a href="#" onclick="selectAllPlatforms(); return false;" style="color: var(--text-secondary); text-decoration: none;">All</a> / 
                            <a href="#" onclick="deselectAllPlatforms(); return false;" style="color: var(--text-secondary); text-decoration: none;">None</a>
                        </div>
                    </div>
                    <div class="platform-options" id="platform-options">
                        <div class="loading-message">LOADING...</div>
                    </div>
                </div>
            </div>
            
            <div class="action-bar">
                <div id="active-filters-container"></div>
                <div>
                    <button class="btn-secondary" onclick="exportResults()">Export</button>
                    <button class="btn-secondary" onclick="clearFilters()">Clear</button>
                    <button class="btn-primary" onclick="performSearch()">Search</button>
                </div>
            </div>
        </div>
        
        <div class="results">
            <div class="results-header">
                <h2>Results <span style="color: var(--text-secondary); font-size: 12px; margin-left: 10px;" id="result-count"></span></h2>
                <div class="pagination" id="pagination">
                    <button onclick="prevPage()">←</button>
                    <span class="page-info" id="page-info" style="font-size: 12px;"></span>
                    <button onclick="nextPage()">→</button>
                </div>
            </div>
            <div id="results-container">
                <p class="empty-message" style="text-align: center; color: var(--text-muted); padding: 40px;">
                    Waiting for input...
                </p>
            </div>
        </div>
    </div>
    
    <div id="chatModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <div class="modal-title">Conversation Details</div>
                <span class="close" onclick="closeModal()">&times;</span>
            </div>
            <div class="modal-body" id="modal-body">
                <div class="loading-message">LOADING CHAT...</div>
            </div>
        </div>
    </div>
    
    <script src="/app.js"></script>
</body>
</html>'''
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def serve_javascript(self):
        """Serve external JavaScript file"""
        js_content = r'''// chatCAT Dashboard JavaScript v2.4
let currentPage = 0;
let pageSize = 50;
let totalResults = 0;
let availablePlatforms = [];
let availableTags = [];
let currentResults = [];
let currentSearchTerms = [];
let currentChatTags = [];
let currentChatId = null;

function showError(container, message) {
    container.innerHTML = `<div class="error-message" style="color: #ff4444; padding: 10px;">✗ ${message}</div>`;
}

async function loadStats() {
    const container = document.getElementById('stat-grid');
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        let html = `
            <div class="stat-item">
                <div class="stat-value">${data.total_chats.toLocaleString()}</div>
                <div class="stat-label">Total Chats</div>
            </div>
        `;
        
        for (const [platform, count] of Object.entries(data.by_platform)) {
            html += `
                <div class="stat-item">
                    <div class="stat-value">${count.toLocaleString()}</div>
                    <div class="stat-label">${platform}</div>
                </div>
            `;
        }
        
        container.innerHTML = html;
    } catch (error) {
        console.error(error);
    }
}

async function loadPlatforms() {
    const container = document.getElementById('platform-options');
    try {
        const response = await fetch('/api/platforms');
        const data = await response.json();
        availablePlatforms = data.platforms;
        
        if (availablePlatforms.length === 0) {
            container.innerHTML = '<span style="color:#777">No platforms</span>';
            return;
        }
        
        container.innerHTML = availablePlatforms.map(platform => `
            <div class="platform-option">
                <input type="checkbox" id="platform-${platform}" value="${platform}" checked>
                <label for="platform-${platform}">${platform}</label>
            </div>
        `).join('');
    } catch (error) {
        console.error(error);
    }
}

async function loadTags() {
    try {
        const response = await fetch('/api/tags');
        const data = await response.json();
        availableTags = data.tags;
    } catch (error) {
        console.error(error);
    }
}

function selectAllPlatforms() {
    document.querySelectorAll('#platform-options input').forEach(cb => cb.checked = true);
}

function deselectAllPlatforms() {
    document.querySelectorAll('#platform-options input').forEach(cb => cb.checked = false);
}

function setDateRange(range, btnElement) {
    // UI Update for Segmented Control
    document.querySelectorAll('.segmented-control button').forEach(b => b.classList.remove('active'));
    if(btnElement) btnElement.classList.add('active');

    const today = new Date();
    const endDate = today.toISOString().split('T')[0];
    let startDate;
    
    switch(range) {
        case 'today': startDate = endDate; break;
        case 'week': startDate = new Date(Date.now() - 7*24*60*60*1000).toISOString().split('T')[0]; break;
        case 'month': startDate = new Date(Date.now() - 30*24*60*60*1000).toISOString().split('T')[0]; break;
        case '3months': startDate = new Date(Date.now() - 90*24*60*60*1000).toISOString().split('T')[0]; break;
        case 'year': startDate = new Date(Date.now() - 365*24*60*60*1000).toISOString().split('T')[0]; break;
        case 'all':
            document.getElementById('start-date').value = '';
            document.getElementById('end-date').value = '';
            return;
    }
    
    document.getElementById('start-date').value = startDate;
    document.getElementById('end-date').value = endDate;
}

function getSelectedPlatforms() {
    return Array.from(document.querySelectorAll('#platform-options input:checked')).map(cb => cb.value);
}

function highlightTerms(text, terms) {
    if (!text) return '';
    if (!terms || terms.length === 0) return escapeHtml(text);
    
    let result = escapeHtml(text);
    const sortedTerms = [...terms].sort((a, b) => b.length - a.length);
    
    for (const term of sortedTerms) {
        const escapedTerm = term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const regex = new RegExp(`\\b(${escapedTerm})\\b`, 'gi');
        result = result.replace(regex, '<span class="highlight">$1</span>');
    }
    
    return result;
}

function getTagColor(tagName) {
    const tag = availableTags.find(t => t.name === tagName);
    return tag ? tag.color : '#00FF00';
}

function renderTagBadges(tags) {
    if (!tags || tags.length === 0) return '';
    return tags.filter(t => t && t.trim()).map(tag => {
        const color = getTagColor(tag);
        return `<span class="tag-badge" style="color: ${color}; border-color: ${color};">${escapeHtml(tag)}</span>`;
    }).join('');
}

async function performSearch(page = 0) {
    currentPage = page;
    const container = document.getElementById('results-container');
    
    try {
        container.innerHTML = '<div class="loading-message">SEARCHING...</div>';
        
        const query = document.getElementById('search-query').value;
        const platforms = getSelectedPlatforms();
        const startDate = document.getElementById('start-date').value;
        const endDate = document.getElementById('end-date').value;
        
        let url = `/api/search?limit=${pageSize}&offset=${page * pageSize}`;
        if (query) url += `&q=${encodeURIComponent(query)}`;
        if (startDate) url += `&start_date=${startDate}`;
        if (endDate) url += `&end_date=${endDate}`;
        platforms.forEach(p => url += `&platforms[]=${encodeURIComponent(p)}`);
        
        const response = await fetch(url);
        const data = await response.json();
        
        currentResults = data.results;
        totalResults = data.total;
        currentSearchTerms = data.search_terms || [];
        
        displayResults(data.results);
        displayActiveFilters(query, platforms, startDate, endDate);
        updatePagination();
    } catch (error) {
        showError(container, error.message);
    }
}

function displayActiveFilters(query, platforms, startDate, endDate) {
    const container = document.getElementById('active-filters-container');
    const filters = [];
    
    if (query) filters.push(`"${query}"`);
    if (platforms.length < availablePlatforms.length) filters.push(`${platforms.length} Platforms`);
    if (startDate) filters.push(`Date Filter Active`);
    
    if (filters.length === 0) {
        container.innerHTML = '';
        return;
    }
    
    container.innerHTML = `
        <div class="active-filters" style="padding:0; margin:0;">
            Found ${totalResults} results for: <span style="color:white">${filters.join(', ')}</span>
        </div>
    `;
}

function displayResults(results) {
    document.getElementById('result-count').textContent = `(${totalResults})`;
    
    if (results.length === 0) {
        document.getElementById('results-container').innerHTML = 
            '<p class="empty-message" style="text-align: center; color: #777; padding: 40px;">No matches found.</p>';
        return;
    }
    
    const html = results.map(chat => {
        const userPreview = highlightTerms(chat.user_message.substring(0, 150), currentSearchTerms);
        const aiPreview = highlightTerms(chat.ai_response.substring(0, 150), currentSearchTerms);
        
        return `
        <div class="chat-item" onclick="openChatModal(${chat.id})">
            <div class="chat-header">
                <div>
                    <span class="platform-badge">${escapeHtml(chat.platform)}</span>
                    ${chat.notes ? '<span style="font-size:10px; margin-left:5px;">📝</span>' : ''}
                    ${chat.tags && chat.tags.length ? '<span style="font-size:10px; margin-left:5px;">🏷️</span>' : ''}
                </div>
                <span class="timestamp">${new Date(chat.timestamp).toLocaleDateString()}</span>
            </div>
            
            <div class="preview-text"><strong>You:</strong> ${userPreview}...</div>
            <div class="preview-text"><strong>AI:</strong> ${aiPreview}...</div>
            
            <div style="margin-top: 5px;">
             ${renderTagBadges(chat.tags)}
            </div>
        </div>
    `;
    }).join('');
    
    document.getElementById('results-container').innerHTML = html;
}

async function openChatModal(chatId) {
    const modal = document.getElementById('chatModal');
    const modalBody = document.getElementById('modal-body');
    
    modal.style.display = 'block';
    modalBody.innerHTML = '<div class="loading-message">LOADING...</div>';
    currentChatId = chatId;
    
    try {
        const response = await fetch(`/api/chat?id=${chatId}`);
        const chat = await response.json();
        currentChatTags = (chat.tags || []).filter(t => t && t.trim());
        
        const userFull = highlightTerms(chat.user_message, currentSearchTerms);
        const aiFull = highlightTerms(chat.ai_response, currentSearchTerms);
        const notesHighlighted = chat.notes ? highlightTerms(chat.notes, currentSearchTerms) : '';
        
        modalBody.innerHTML = `
            <div class="chat-full">
                <div class="label">YOU</div>
                <div class="user-message">${userFull}</div>
                
                <div class="label">AI (${chat.platform})</div>
                <div class="ai-response">${aiFull}</div>
                
                <div class="tags-section">
                    <div class="section-header"><h3>Tags</h3></div>
                    <div id="current-tags-container" class="tags-container">
                        ${renderCurrentTagsSection()}
                    </div>
                    
                    <div style="margin-top:10px; font-size:11px; color:#777">Available:</div>
                    <div class="tags-container" id="available-tags-container">
                        ${renderAvailableTagsSection()}
                    </div>
                    
                    <div style="display:flex; gap:5px; margin-top:10px;">
                        <input type="text" id="new-tag-name" placeholder="New tag..." style="flex:1; padding:5px; background: #444; border:none; color:white;">
                        <input type="color" id="new-tag-color" value="#00FF00" style="width:30px; border:none; padding:0;">
                        <button class="btn-secondary" style="padding: 2px 10px;" onclick="createAndAddTag()">+</button>
                    </div>
                </div>
                
                <div class="notes-section">
                    <div class="section-header"><h3>Notes</h3></div>
                    <textarea id="notes-textarea" class="notes-textarea" placeholder="Add private notes...">${chat.notes || ''}</textarea>
                    <div style="margin-top:10px; text-align:right;">
                        <span id="notes-status" style="margin-right:10px; font-size:11px;"></span>
                        <button class="btn-primary" style="font-size:11px; padding: 6px 15px;" onclick="saveNotes()">Save Note</button>
                    </div>
                </div>
            </div>
        `;
        
    } catch (error) {
        showError(modalBody, error.message);
    }
}

function renderCurrentTagsSection() {
    if (currentChatTags.length === 0) return '<span style="font-size:11px; color:#777">No tags</span>';
    return currentChatTags.map(tag => {
        const color = getTagColor(tag);
        return `<span class="tag-chip" style="color:${color}; border-color:${color}" onclick="removeTagFromChat('${tag}')">${tag} ×</span>`;
    }).join('');
}

function renderAvailableTagsSection() {
    const unassignedTags = availableTags.filter(t => !currentChatTags.includes(t.name));
    if (unassignedTags.length === 0) return '';
    return unassignedTags.map(tag => 
        `<span class="tag-chip" style="color:${tag.color}; border-color:${tag.color}; opacity:0.5" onclick="addTagToChat('${tag.name}')">+ ${tag.name}</span>`
    ).join('');
}

async function addTagToChat(tagName) {
    if (currentChatTags.includes(tagName)) return;
    currentChatTags.push(tagName);
    await saveTagsToServer();
    refreshTagsUI();
}

async function removeTagFromChat(tagName) {
    currentChatTags = currentChatTags.filter(t => t !== tagName);
    await saveTagsToServer();
    refreshTagsUI();
}

function refreshTagsUI() {
    document.getElementById('current-tags-container').innerHTML = renderCurrentTagsSection();
    document.getElementById('available-tags-container').innerHTML = renderAvailableTagsSection();
}

async function saveTagsToServer() {
    await fetch('/api/tags/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chat_id: currentChatId, tags: currentChatTags })
    });
}

async function createAndAddTag() {
    const name = document.getElementById('new-tag-name').value.trim().toLowerCase();
    const color = document.getElementById('new-tag-color').value;
    if(!name) return;
    
    await fetch('/api/tags/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, color })
    });
    
    availableTags.push({id:0, name, color});
    addTagToChat(name);
    document.getElementById('new-tag-name').value = '';
}

async function saveNotes() {
    const notes = document.getElementById('notes-textarea').value;
    const btn = document.querySelector('#notes-textarea + div button');
    const originalText = btn.textContent;
    btn.textContent = 'Saving...';
    
    await fetch('/api/notes/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chat_id: currentChatId, notes: notes })
    });
    
    btn.textContent = 'Saved!';
    setTimeout(() => btn.textContent = originalText, 1000);
}

function closeModal() {
    document.getElementById('chatModal').style.display = 'none';
    currentChatId = null;
}

window.onclick = function(event) {
    if (event.target == document.getElementById('chatModal')) closeModal();
}

function updatePagination() {
    const totalPages = Math.ceil(totalResults / pageSize) || 1;
    document.getElementById('page-info').textContent = `${currentPage + 1} / ${totalPages}`;
}

function prevPage() { if (currentPage > 0) performSearch(currentPage - 1); }
function nextPage() {
    const totalPages = Math.ceil(totalResults / pageSize);
    if (currentPage < totalPages - 1) performSearch(currentPage + 1);
}

function clearFilters() {
    document.getElementById('search-query').value = '';
    setDateRange('all', document.querySelector('.segmented-control button:last-child'));
    selectAllPlatforms();
    document.getElementById('results-container').innerHTML = 
        '<p class="empty-message" style="text-align: center; color: #777; padding: 40px;">Filters cleared.</p>';
    document.getElementById('result-count').textContent = '';
    document.getElementById('active-filters-container').innerHTML = '';
}

function exportResults() {
    if (currentResults.length === 0) return alert('No results');
    const csv = [
        ['Platform', 'Timestamp', 'User Message', 'AI Response'],
        ...currentResults.map(r => [
            r.platform, r.timestamp, 
            r.user_message.replace(/"/g, '""'), 
            r.ai_response.replace(/"/g, '""')
        ])
    ].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');
    
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }));
    a.download = 'chatcat_export.csv';
    a.click();
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

window.addEventListener('DOMContentLoaded', async function() {
    await loadTags();
    loadStats();
    loadPlatforms();
});
'''
        
        self.send_response(200)
        self.send_header('Content-type', 'application/javascript; charset=utf-8')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(js_content.encode('utf-8'))
    
    def send_json_response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def log_message(self, format, *args):
        return


def run_server(port=8765):
    server_address = ('', port)
    httpd = HTTPServer(server_address, ChatCATHandler)
    
    print(f"""
═══════════════════════════════════════════════
         chatCAT v2.4 - Visual Update
═══════════════════════════════════════════════

■ Dashboard: http://localhost:{port}

✓ UPDATES:
  • Compressed Top Layout
  • Segmented Date Controls
  • Solid Green "Search" Action
  • Cleaner Data Hierarchy

▶ Press Ctrl+C to stop the server.
""")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n✓ chatCAT server stopped")


if __name__ == '__main__':
    run_server()