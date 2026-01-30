# Wikipedia Chain Finder - Project Specification

## 1. Project Overview
Build a web application that finds the shortest path between two Wikipedia articles by following links between them. Uses bidirectional iterative deepening search to efficiently find paths up to 7 articles long (6 links).

## 2. Architecture
- **Frontend**: HTML, CSS, vanilla JavaScript (no frameworks)
- **Backend**: Python Flask REST API
- **Single-threaded**: One search process at a time
- **No caching**: Fresh API calls each time

## 3. API Specification

### Endpoint: `POST /find-path`

**Request Body**:
```json
{
  "start": "Article_Title",
  "end": "Article_Title"
}
```

**Success Response** (200):
```json
{
  "success": true,
  "path": ["Article_1", "Article_2", "Article_3", "Article_4"],
  "length": 4
}
```

**Error Responses**:
- **404**: Article not found
```json
  {"success": false, "error": "Start article 'XYZ' does not exist"}
```
- **404**: No path found
```json
  {"success": false, "error": "No path found within 7 articles"}
```
- **400**: Invalid input
```json
  {"success": false, "error": "Both start and end articles required"}
```
- **500**: API or server error
```json
  {"success": false, "error": "Error accessing Wikipedia API"}
```

## 4. Algorithm: Bidirectional Iterative Deepening Search

### Strategy:
- Run two breadth-first searches simultaneously
- Forward search: Start article → outgoing links
- Backward search: End article → incoming links (backlinks)
- Alternate between expanding forward and backward frontiers
- Check for intersection after each expansion

### Data Structures:
- `forward_visited`: dict mapping article → parent article (for path reconstruction)
- `backward_visited`: dict mapping article → parent article
- `forward_frontier`: current depth level being explored (forward)
- `backward_frontier`: current depth level being explored (backward)

### Termination:
- **Success**: When forward and backward visited sets share a common article
- **Failure**: When depth reaches 3 in each direction (allowing max 6 links / 7 articles total)

### Path Reconstruction:
When meeting at article M:
1. Build forward path: Start → ... → M (using forward_visited parents)
2. Build backward path: M → ... → End (using backward_visited parents)
3. Combine: Forward path + backward path (excluding duplicate M)

### Depth Calculation:
- Depth 0: Start and End articles only
- Depth 1: Direct links from Start/End
- Depth 2: Links from those links
- Depth 3: Maximum depth (creates paths of up to 7 articles)

## 5. Wikipedia API Integration

### Forward Search - Get Outgoing Links:
- Endpoint: `https://en.wikipedia.org/w/api.php`
- Action: `query`
- Parameters: `prop=links`, `pllimit=max`, `plnamespace=0`
- Continue fetching if results are paginated

### Backward Search - Get Incoming Links:
- Endpoint: `https://en.wikipedia.org/w/api.php`
- Action: `query`
- Parameters: `list=backlinks`, `bllimit=max`, `blnamespace=0`
- Continue fetching if results are paginated

### Article Validation:
- Check if article exists before starting search
- Use `action=query&titles=ArticleName` to verify

### Link Filtering:
- Only include namespace 0 (main article space)
- Exclude: File:, Category:, Template:, Talk:, Wikipedia:, Help:, Portal:, etc.

### Normalization:
- Convert spaces to underscores for API calls
- Capitalize first letter of article titles
- Handle URL encoding as needed

## 6. Frontend Requirements

### UI Elements:
- Two text input boxes labeled "Start Article" and "End Article"
- "Find Path" submit button
- Loading indicator (spinner/message) while search runs
- Results display area

### User Interactions:
1. User enters start and end article titles
2. Click "Find Path" button
3. Show loading indicator
4. Display results or error message

### Results Display:
- **Success**: Show ordered list of article titles as clickable links to Wikipedia
  - Format: `https://en.wikipedia.org/wiki/Article_Name`
  - Display number of articles in path
- **Error**: Show error message in red/warning styling
- Clear previous results when new search starts

### Input Validation:
- Check that both fields are non-empty before submitting
- Trim whitespace from inputs
- Show client-side error if fields are empty

### Styling:
- Clean, simple design
- Center-aligned form
- Responsive layout
- Loading spinner that's clearly visible
- Distinguishable success vs error states

## 7. Technical Constraints

- Maximum path length: 7 articles (6 links)
- Maximum search depth: 3 per direction
- No caching of results or link data
- Single-threaded execution
- No database; all data from Wikipedia API

## 8. Error Handling

### Client-Side:
- Empty input fields → show validation message
- Network errors → show "Connection error" message

### Server-Side:
- Article doesn't exist → return 404 with descriptive message
- No path within limit → return 404 with "No path found within 7 articles"
- Wikipedia API errors → return 500 with generic error
- Rate limiting → return 500 with "Service temporarily unavailable"
- Invalid JSON input → return 400 with "Invalid request format"

## 9. Implementation Notes

### Python Dependencies:
- Flask (web framework)
- requests (HTTP client for Wikipedia API)
- flask-cors (if frontend served separately)

### File Structure:
```
project/
├── app.py              # Flask backend
├── static/
│   ├── index.html      # Frontend HTML
│   ├── style.css       # Styling
│   └── script.js       # Frontend JavaScript
└── requirements.txt    # Python dependencies
```

### Search Efficiency:
- Alternate between forward and backward search to balance exploration
- Stop immediately when intersection found
- Process all links at current depth before going deeper (BFS within each level)

## 10. Extension: Database Caching Layer

### Overview
Add a persistent SQLite database to cache page links and dramatically reduce Wikipedia API calls. The cache stores relationships between pages (which pages link to which) so that repeated searches can use local data instead of making redundant API requests.

### Database Schema

**SQLite Database**: `wikipedia_cache.db`

**pages table**:
```sql
CREATE TABLE pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT UNIQUE NOT NULL,
    last_fetched TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_title ON pages(title);
```

**links table**:
```sql
CREATE TABLE links (
    source_page_id INTEGER NOT NULL,
    target_page_title TEXT NOT NULL,
    FOREIGN KEY (source_page_id) REFERENCES pages(id),
    PRIMARY KEY (source_page_id, target_page_title)
);

CREATE INDEX idx_source ON links(source_page_id);
CREATE INDEX idx_target ON links(target_page_title);
```

### Cache Lookup Strategy

**For Forward Links (Outgoing Links)**:
1. Check if page title exists in `pages` table
2. If cached:
   - Query `links` table WHERE `source_page_id = page_id`
   - Return cached links immediately (no API call)
3. If not cached:
   - Fetch links from Wikipedia API
   - Insert page into `pages` table
   - Insert all links into `links` table
   - Return links for search

**For Backward Links (Incoming Links/Backlinks)**:
1. Query database for cached backlinks:
   - JOIN `pages` and `links` tables
   - Find all pages WHERE `target_page_title = article_name`
2. Also fetch backlinks from Wikipedia API (to get complete set)
3. For each backlink returned by API:
   - If the linking page doesn't exist in `pages` table, add it
   - If the link relationship doesn't exist in `links` table, add it
4. Return combined list of all backlinks (cached + newly discovered from API)

**Rationale for hybrid backlink approach**: The database only contains backlinks we've previously encountered. Wikipedia has many more backlinks that we haven't cached yet. By always calling the API for backlinks and caching new discoveries, we gradually build a more complete database while ensuring search completeness.

### Database Operations

**Check if page is cached**:
```sql
SELECT id FROM pages WHERE title = ?
```

**Get outgoing links**:
```sql
SELECT target_page_title FROM links WHERE source_page_id = ?
```

**Get incoming links (backlinks)**:
```sql
SELECT p.title 
FROM pages p
JOIN links l ON p.id = l.source_page_id
WHERE l.target_page_title = ?
```

**Cache new page**:
```sql
INSERT OR IGNORE INTO pages (title) VALUES (?);
```

**Cache link relationship**:
```sql
INSERT OR IGNORE INTO links (source_page_id, target_page_title) 
VALUES (?, ?);
```

### Implementation Details

**Database Initialization**:
- Create empty database on first run
- Database file location: same directory as `app.py`
- Initialize tables if they don't exist at application startup

**Cache Growth**:
- Allow database to grow indefinitely (no size limits)
- No cache eviction policy
- No cleanup of old entries

**Cache Freshness**:
- Never refresh cached data (no expiration)
- Once links are cached, use them forever
- Assume Wikipedia link structure is stable enough for this use case

**On-Demand Fetching**:
- Fetch pages from API as they're encountered during search
- Don't pre-fetch or batch-fetch multiple pages
- Each uncached page triggers one API call when needed

**Database Connection**:
- Use connection pooling or persistent connection
- Close database properly on application shutdown
- Handle SQLite locking for concurrent access (though single-threaded, still good practice)

### Performance Benefits

**Before Caching**:
- Every article requires an API call
- Search with 100 articles explored = 100+ API calls
- Slow performance, high API load

**After Caching**:
- First search: Same API calls (builds cache)
- Subsequent searches: Mostly cached data
- Popular articles (common in searches) quickly become fully cached
- API calls only for new, uncached articles

**Expected Speedup**:
- Cold cache (first run): No speedup
- Warm cache (after several searches): 50-90% reduction in API calls
- Hot cache (well-used system): 90%+ reduction in API calls

### Additional Python Dependencies

Add to `requirements.txt`:
- sqlite3 (built into Python, no separate install needed)

### Error Handling

**Database Errors**:
- If database file is corrupted: Delete and recreate
- If database is locked: Retry with exponential backoff
- If insert fails: Log error but continue search (don't crash)
- Fallback: If database operations fail, fall back to API-only mode

**Migration Path**:
- Version 1 (no caching) can be upgraded by adding database layer
- No changes needed to API contract or frontend
- Backward compatible: can run without database if needed