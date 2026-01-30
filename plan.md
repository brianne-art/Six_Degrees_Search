# Wikipedia Chain Finder - Implementation Plan

## Phase 1: Project Setup & Basic Structure

### Goals1
Establish the project foundation with a working Flask server that serves static files.

### Tasks
1. Create the project directory structure:
   ```
   project/
   ├── app.py
   ├── static/
   │   ├── index.html
   │   ├── style.css
   │   └── script.js
   └── requirements.txt
   ```
2. Create `requirements.txt` with dependencies:
   - Flask
   - requests
   - flask-cors
3. Create minimal `app.py` with Flask app that serves static files
4. Create placeholder `index.html` with basic page structure
5. Create empty `style.css` and `script.js` files

### Testing Checklist
- [ ] `pip install -r requirements.txt` completes without errors
- [ ] `python app.py` starts the Flask server without errors
- [ ] Visiting `http://localhost:5000` displays the placeholder HTML page
- [ ] Static CSS and JS files are served correctly (check browser dev tools)

---

## Phase 2: Wikipedia API Integration

### Goals
Build reliable functions to interact with the Wikipedia API for article validation and link retrieval.

### Tasks
1. Create a `wikipedia_api.py` module (or functions in `app.py`) with:
   - `normalize_title(title)` - Convert spaces to underscores, capitalize first letter
   - `article_exists(title)` - Validate article exists using Wikipedia API
   - `get_outgoing_links(title)` - Fetch all links from an article (with pagination)
   - `get_incoming_links(title)` - Fetch all backlinks to an article (with pagination)
2. Implement proper error handling for API failures
3. Filter links to namespace 0 only (main articles)
4. Handle Wikipedia API rate limiting gracefully

### API Details
- Base URL: `https://en.wikipedia.org/w/api.php`
- Outgoing links: `action=query&prop=links&pllimit=max&plnamespace=0&titles=TITLE`
- Backlinks: `action=query&list=backlinks&bllimit=max&blnamespace=0&bltitle=TITLE`
- Validation: `action=query&titles=TITLE` (check for "missing" key)

### Testing Checklist
- [ ] `normalize_title("hello world")` returns `"Hello_world"`
- [ ] `article_exists("Python_(programming_language)")` returns `True`
- [ ] `article_exists("Xyzzy_nonexistent_article_12345")` returns `False`
- [ ] `get_outgoing_links("Apple")` returns a list of article titles (non-empty)
- [ ] `get_incoming_links("Apple")` returns a list of article titles (non-empty)
- [ ] All returned links are in namespace 0 (no "File:", "Category:", etc.)
- [ ] Functions handle pagination (test with an article that has many links)
- [ ] Functions return empty list or raise appropriate error on API failure

---

## Phase 3: Bidirectional Search Algorithm

### Goals
Implement the core bidirectional BFS algorithm that finds the shortest path between two articles.

### Tasks
1. Create search module/function with the following components:
   - Initialize data structures:
     - `forward_visited`: dict mapping article → parent
     - `backward_visited`: dict mapping article → parent
     - `forward_frontier`: set of articles at current depth
     - `backward_frontier`: set of articles at current depth
2. Implement `expand_forward(frontier, visited)`:
   - For each article in frontier, get outgoing links
   - Add new articles to visited with parent reference
   - Return new frontier (newly discovered articles)
3. Implement `expand_backward(frontier, visited)`:
   - For each article in frontier, get incoming links (backlinks)
   - Add new articles to visited with parent reference
   - Return new frontier
4. Implement `find_intersection(forward_visited, backward_visited)`:
   - Return any article that exists in both visited sets
5. Implement `reconstruct_path(meeting_point, forward_visited, backward_visited)`:
   - Build path from start to meeting point using forward_visited
   - Build path from meeting point to end using backward_visited
   - Combine paths (avoid duplicating meeting point)
6. Implement main `find_path(start, end)` function:
   - Validate both articles exist
   - Handle edge case: start == end (return single-element path)
   - Initialize frontiers with start and end articles
   - Alternate between forward and backward expansion
   - Check for intersection after each expansion
   - Stop at max depth 3 per direction
   - Return path or None if not found

### Algorithm Pseudocode
```
forward_visited = {start: None}   # Depth 0: just the start article
backward_visited = {end: None}    # Depth 0: just the end article
forward_frontier = {start}
backward_frontier = {end}

# Check for direct link before entering the loop (1-link path = 2 articles)
start_links = get_outgoing_links(start)
if end in start_links:
    return [start, end]

# Max depth 3 per direction = up to 6 total links = 7 articles max
# Depth 1: 1 link from start + 1 link from end = paths up to 3 articles
# Depth 2: 2 links from start + 2 links from end = paths up to 5 articles
# Depth 3: 3 links from start + 3 links from end = paths up to 7 articles
for depth in range(1, 4):  # depth = 1, 2, 3
    # Expand forward by one level
    forward_frontier = expand_forward(forward_frontier, forward_visited)
    if intersection := find_intersection(forward_visited, backward_visited):
        return reconstruct_path(intersection, ...)

    # Expand backward by one level
    backward_frontier = expand_backward(backward_frontier, backward_visited)
    if intersection := find_intersection(forward_visited, backward_visited):
        return reconstruct_path(intersection, ...)

return None  # No path found
```

### Pagination Guidance
When expanding a frontier, you must fetch all links for each article in the frontier before moving to the next depth level. Implementation approach:

1. **Batch processing**: For each article in the current frontier, call `get_outgoing_links()` or `get_incoming_links()` which internally handles Wikipedia API pagination
2. **Build next frontier**: Collect all newly discovered articles (not already in visited) into the next frontier
3. **Update visited**: For each new article, record its parent (the article it was discovered from)
4. **Complete the level**: Only after ALL articles in the current frontier have been fully expanded should you check for intersection and proceed to the next depth

```python
def expand_forward(frontier, visited):
    next_frontier = set()
    for article in frontier:
        links = get_outgoing_links(article)  # Handles pagination internally
        for link in links:
            if link not in visited:
                visited[link] = article  # Record parent
                next_frontier.add(link)
    return next_frontier
```

### Testing Checklist
- [ ] `find_path("Apple", "Apple")` returns `["Apple"]` (same article)
- [ ] `find_path("Python_(programming_language)", "Computer")` returns a valid path
- [ ] Path starts with exact start article and ends with exact end article
- [ ] Each consecutive pair in path has a valid Wikipedia link between them
- [ ] `find_path("Article_A", "Nonexistent_Article")` raises/returns appropriate error
- [ ] Algorithm terminates within reasonable time (not infinite loop)
- [ ] Paths returned are at most 7 articles long
- [ ] Test with known short paths (e.g., articles that directly link to each other)
- [ ] Direct link detection works (e.g., "Python_(programming_language)" → "Guido_van_Rossum" returns 2-article path)

---

## Phase 4: Flask API Endpoint

### Goals
Create the REST API endpoint that connects the search algorithm to HTTP requests.

### Tasks
1. Implement `POST /find-path` endpoint in `app.py`:
   - Parse JSON request body
   - Extract `start` and `end` fields
   - Validate input (both fields required, non-empty)
   - Call search algorithm
   - Return appropriate JSON response
2. Implement error handling:
   - 400: Missing or invalid input
   - 404: Article not found
   - 404: No path found within limit
   - 500: Wikipedia API errors
3. Add CORS headers if needed (flask-cors)
4. Ensure proper JSON content-type headers

### Response Formats
```json
// Success (200)
{"success": true, "path": ["A", "B", "C"], "length": 3}

// Article not found (404)
{"success": false, "error": "Start article 'XYZ' does not exist"}

// No path found (404)
{"success": false, "error": "No path found within 7 articles"}

// Invalid input (400)
{"success": false, "error": "Both start and end articles required"}

// Server error (500)
{"success": false, "error": "Error accessing Wikipedia API"}
```

### Testing Checklist
- [ ] POST to `/find-path` with valid articles returns 200 with path
- [ ] Response includes `success: true`, `path` array, and `length` field
- [ ] POST with missing `start` field returns 400 with error message
- [ ] POST with missing `end` field returns 400 with error message
- [ ] POST with empty string fields returns 400 with error message
- [ ] POST with nonexistent start article returns 404 with descriptive error
- [ ] POST with nonexistent end article returns 404 with descriptive error
- [ ] POST with valid articles but no path within limit returns 404
- [ ] Invalid JSON body returns 400
- [ ] Response headers include `Content-Type: application/json`
- [ ] Test with curl or Postman to verify raw HTTP behavior

---

## Phase 5: Frontend Implementation

### Goals
Build the user interface that allows users to input articles and view results.

### Tasks
1. Update `index.html`:
   - Add page title and header
   - Create form with two text inputs ("Start Article", "End Article")
   - Add "Find Path" submit button
   - Add loading indicator element (hidden by default)
   - Add results container element
   - Add error message container element
2. Implement `style.css`:
   - Center-aligned layout
   - Clean, readable form styling
   - Input field styling
   - Button styling (normal, hover, disabled states)
   - Loading spinner animation
   - Success result styling (list of links)
   - Error message styling (red/warning colors)
   - Responsive design for mobile
3. Implement `script.js`:
   - Form submission handler (prevent default)
   - Input validation (check non-empty, trim whitespace)
   - Show/hide loading indicator
   - Make fetch request to `/find-path` API
   - Parse JSON response
   - Display success results as clickable Wikipedia links
   - Display error messages
   - Clear previous results on new search
   - Disable submit button during search

### UI States
1. **Initial**: Empty form, no results
2. **Loading**: Form disabled, spinner visible, no results
3. **Success**: Form enabled, results list visible with clickable links
4. **Error**: Form enabled, error message visible in warning style

### Testing Checklist
- [ ] Page loads with form visible and properly styled
- [ ] Clicking "Find Path" with empty fields shows client-side validation error
- [ ] Clicking "Find Path" with valid input shows loading spinner
- [ ] Submit button is disabled during search
- [ ] Successful search displays numbered list of article titles
- [ ] Each article title is a clickable link to Wikipedia
- [ ] Links open in new tab and use correct Wikipedia URL format
- [ ] Path length is displayed (e.g., "Found path with 4 articles")
- [ ] Failed search displays error message in error styling
- [ ] Starting new search clears previous results
- [ ] UI is responsive on mobile viewport sizes
- [ ] Loading spinner is clearly visible during long searches

---

## Phase 6: Integration Testing & Edge Cases

### Goals
Ensure the complete application works reliably with various inputs and edge cases.

### Tasks
1. Test edge cases:
   - Same start and end article
   - Articles with special characters (parentheses, quotes, etc.)
   - Articles with spaces in titles
   - Very common articles (may have many links)
   - Disambiguation pages
2. Test error scenarios:
   - Network disconnection during search
   - Wikipedia API temporarily unavailable
   - Very long article titles
3. Performance verification:
   - Ensure searches complete within reasonable time
   - Verify no memory leaks during repeated searches
4. Cross-browser testing:
   - Test in Chrome, Firefox, Safari (if available)
5. Final code cleanup:
   - Remove debug logging
   - Add appropriate comments
   - Verify all error messages are user-friendly

### Testing Checklist
- [ ] Search for "Albert Einstein" → "Physics" finds a path
- [ ] Search for "Python (programming language)" → "Java (programming language)" works
- [ ] Search for same article as start and end returns single-element path
- [ ] Articles with spaces work correctly (e.g., "New York City")
- [ ] Server handles malformed requests gracefully (no crashes)
- [ ] Multiple consecutive searches work without issues
- [ ] Application works after server restart
- [ ] No console errors in browser during normal operation
- [ ] Error messages are clear and helpful to users

---

## Phase 7: Database Caching Layer

### Goals
Add a persistent SQLite database to cache page links and reduce Wikipedia API calls. Subsequent searches will use cached data when available, dramatically improving performance.

### Tasks
1. Create database module (`database.py`):
   - Initialize SQLite database (`wikipedia_cache.db`)
   - Create `pages` table (id, title, last_fetched)
   - Create `links` table (source_page_id, target_page_title)
   - Add appropriate indexes for fast lookups

2. Implement cache operations:
   - `is_page_cached(title)` - Check if page exists in database
   - `get_cached_links(title)` - Get outgoing links from cache
   - `get_cached_backlinks(title)` - Get incoming links from cache
   - `cache_page_links(title, links)` - Store page and its links

3. Update `wikipedia_api.py` to use cache:
   - **Forward links**: Check cache first, only call API if not cached
   - **Backward links**: Query cache + always call API (hybrid approach)
   - Cache any newly discovered links from API responses

4. Database initialization:
   - Create database file on first run
   - Initialize tables at application startup
   - Handle missing database gracefully

### Database Schema
```sql
-- pages table
CREATE TABLE pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT UNIQUE NOT NULL,
    last_fetched TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_title ON pages(title);

-- links table
CREATE TABLE links (
    source_page_id INTEGER NOT NULL,
    target_page_title TEXT NOT NULL,
    FOREIGN KEY (source_page_id) REFERENCES pages(id),
    PRIMARY KEY (source_page_id, target_page_title)
);
CREATE INDEX idx_source ON links(source_page_id);
CREATE INDEX idx_target ON links(target_page_title);
```

### Cache Strategy

**Forward Links (Outgoing)**:
1. Check if page title exists in `pages` table
2. If cached: Return links from `links` table (no API call)
3. If not cached: Fetch from API, cache results, return links

**Backward Links (Incoming)** - Hybrid Approach:
1. Query database for any cached backlinks
2. Also fetch backlinks from Wikipedia API
3. Cache any newly discovered link relationships
4. Return combined results

*Rationale*: The database only contains backlinks we've previously encountered. Always calling the API ensures search completeness while gradually building the cache.

### Error Handling
- Database corruption: Delete and recreate
- Database locked: Retry with backoff
- Insert failures: Log error, continue search (don't crash)
- Fallback: If database fails, operate in API-only mode

### Testing Checklist
- [ ] Database file is created on first run
- [ ] Tables and indexes are created correctly
- [ ] First search for an article calls Wikipedia API
- [ ] Second search for same article uses cache (no API call for forward links)
- [ ] Cached links match what was returned from API
- [ ] Backlinks hybrid approach works (cache + API combined)
- [ ] Database errors don't crash the application
- [ ] Search still works if database file is deleted (recreates it)
- [ ] Performance improvement is measurable on repeated searches

### Performance Verification
Run the same search twice and compare:
- First run: Count API calls made
- Second run: Verify reduced API calls (forward links should be cached)

---

## Final Deliverables

Upon completion of all phases, the project should include:

1. **`app.py`**: Flask backend with `/find-path` endpoint
2. **`wikipedia_api.py`**: Wikipedia API integration with caching
3. **`search.py`**: Bidirectional search algorithm
4. **`database.py`**: SQLite caching layer
5. **`static/index.html`**: Frontend HTML structure
6. **`static/style.css`**: Styling for the UI
7. **`static/script.js`**: Frontend JavaScript logic
8. **`requirements.txt`**: Python dependencies
9. **`wikipedia_cache.db`**: SQLite cache database (auto-generated)

The application should:
- Find shortest paths between Wikipedia articles (up to 7 articles / 6 links)
- Provide clear feedback during search (loading indicator)
- Display results as clickable Wikipedia links
- Handle errors gracefully with informative messages
- Work reliably across multiple searches
- Cache Wikipedia data for improved performance on repeated searches
