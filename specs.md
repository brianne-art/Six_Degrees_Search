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