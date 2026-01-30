import sqlite3
import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'wikipedia_cache.db')


def get_connection():
    """Get a database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize the database with required tables and indexes."""
    conn = get_connection()
    cursor = conn.cursor()

    # Create pages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT UNIQUE NOT NULL,
            last_fetched TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create index on title for fast lookups
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_title ON pages(title)')

    # Create links table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS links (
            source_page_id INTEGER NOT NULL,
            target_page_title TEXT NOT NULL,
            FOREIGN KEY (source_page_id) REFERENCES pages(id),
            PRIMARY KEY (source_page_id, target_page_title)
        )
    ''')

    # Create indexes for fast lookups
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_source ON links(source_page_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_target ON links(target_page_title)')

    conn.commit()
    conn.close()


def is_page_cached(title):
    """Check if a page's outgoing links are cached."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM pages WHERE title = ?', (title,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


def get_page_id(title):
    """Get the page ID for a title, or None if not cached."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM pages WHERE title = ?', (title,))
    result = cursor.fetchone()
    conn.close()
    return result['id'] if result else None


def get_cached_links(title):
    """Get cached outgoing links for a page. Returns None if not cached."""
    conn = get_connection()
    cursor = conn.cursor()

    # Get page ID
    cursor.execute('SELECT id FROM pages WHERE title = ?', (title,))
    page = cursor.fetchone()

    if not page:
        conn.close()
        return None

    # Get all outgoing links
    cursor.execute(
        'SELECT target_page_title FROM links WHERE source_page_id = ?',
        (page['id'],)
    )
    links = [row['target_page_title'] for row in cursor.fetchall()]
    conn.close()
    return links


def get_cached_backlinks(title):
    """Get cached incoming links (backlinks) for a page."""
    conn = get_connection()
    cursor = conn.cursor()

    # Find all pages that link to this title
    cursor.execute('''
        SELECT p.title
        FROM pages p
        JOIN links l ON p.id = l.source_page_id
        WHERE l.target_page_title = ?
    ''', (title,))

    backlinks = [row['title'] for row in cursor.fetchall()]
    conn.close()
    return backlinks


def cache_page_links(title, links):
    """Cache a page and its outgoing links."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Insert or ignore the page
        cursor.execute(
            'INSERT OR IGNORE INTO pages (title) VALUES (?)',
            (title,)
        )

        # Get the page ID
        cursor.execute('SELECT id FROM pages WHERE title = ?', (title,))
        page_id = cursor.fetchone()['id']

        # Insert all links
        for link in links:
            cursor.execute(
                'INSERT OR IGNORE INTO links (source_page_id, target_page_title) VALUES (?, ?)',
                (page_id, link)
            )

        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Database error while caching: {e}")
    finally:
        conn.close()


def cache_backlink(source_title, target_title):
    """Cache a single backlink relationship (source links to target)."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Ensure source page exists
        cursor.execute(
            'INSERT OR IGNORE INTO pages (title) VALUES (?)',
            (source_title,)
        )

        # Get source page ID
        cursor.execute('SELECT id FROM pages WHERE title = ?', (source_title,))
        source_id = cursor.fetchone()['id']

        # Insert the link relationship
        cursor.execute(
            'INSERT OR IGNORE INTO links (source_page_id, target_page_title) VALUES (?, ?)',
            (source_id, target_title)
        )

        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Database error while caching backlink: {e}")
    finally:
        conn.close()


# Initialize database on module import
init_database()
