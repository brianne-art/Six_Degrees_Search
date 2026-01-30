from wikipedia_api import (
    normalize_title,
    article_exists,
    get_outgoing_links,
    get_incoming_links
)

MAX_DEPTH = 3  # Max depth per direction (allows paths up to 7 articles / 6 links)


class ArticleNotFoundError(Exception):
    """Raised when a Wikipedia article does not exist."""
    pass


class NoPathFoundError(Exception):
    """Raised when no path is found within the depth limit."""
    pass


def expand_forward(frontier, visited):
    """Expand frontier by one level using outgoing links."""
    next_frontier = set()
    for article in frontier:
        links = get_outgoing_links(article)
        for link in links:
            if link not in visited:
                visited[link] = article  # Record parent
                next_frontier.add(link)
    return next_frontier


def expand_backward(frontier, visited):
    """Expand frontier by one level using incoming links (backlinks)."""
    next_frontier = set()
    for article in frontier:
        links = get_incoming_links(article)
        for link in links:
            if link not in visited:
                visited[link] = article  # Record parent
                next_frontier.add(link)
    return next_frontier


def find_intersection(forward_visited, backward_visited):
    """Find any article that exists in both visited sets."""
    forward_keys = set(forward_visited.keys())
    backward_keys = set(backward_visited.keys())
    intersection = forward_keys & backward_keys
    if intersection:
        return intersection.pop()
    return None


def reconstruct_path(meeting_point, forward_visited, backward_visited):
    """Reconstruct the full path from start to end through the meeting point."""
    # Build forward path: start -> ... -> meeting_point
    forward_path = []
    current = meeting_point
    while current is not None:
        forward_path.append(current)
        current = forward_visited.get(current)
    forward_path.reverse()

    # Build backward path: meeting_point -> ... -> end
    backward_path = []
    current = backward_visited.get(meeting_point)  # Skip meeting_point (already in forward)
    while current is not None:
        backward_path.append(current)
        current = backward_visited.get(current)

    return forward_path + backward_path


def find_path(start, end):
    """
    Find the shortest path between two Wikipedia articles.

    Args:
        start: Starting article title
        end: Ending article title

    Returns:
        List of article titles representing the path

    Raises:
        ArticleNotFoundError: If start or end article doesn't exist
        NoPathFoundError: If no path found within depth limit
    """
    # Normalize titles
    start = normalize_title(start)
    end = normalize_title(end)

    # Validate articles exist
    if not article_exists(start):
        raise ArticleNotFoundError(f"Start article '{start}' does not exist")
    if not article_exists(end):
        raise ArticleNotFoundError(f"End article '{end}' does not exist")

    # Handle same article case
    if start == end:
        return [start]

    # Initialize data structures
    forward_visited = {start: None}   # article -> parent
    backward_visited = {end: None}    # article -> parent
    forward_frontier = {start}
    backward_frontier = {end}

    # Check for direct link before entering the loop
    start_links = get_outgoing_links(start)
    if end in start_links:
        return [start, end]

    # Add start's links to forward_visited for the bidirectional search
    for link in start_links:
        if link not in forward_visited:
            forward_visited[link] = start
    forward_frontier = set(start_links)

    # Bidirectional BFS with max depth 3 per direction
    for depth in range(1, MAX_DEPTH + 1):
        # Check for intersection after forward expansion
        intersection = find_intersection(forward_visited, backward_visited)
        if intersection:
            return reconstruct_path(intersection, forward_visited, backward_visited)

        # Expand backward by one level
        backward_frontier = expand_backward(backward_frontier, backward_visited)

        # Check for intersection after backward expansion
        intersection = find_intersection(forward_visited, backward_visited)
        if intersection:
            return reconstruct_path(intersection, forward_visited, backward_visited)

        # Expand forward by one level (for next iteration)
        if depth < MAX_DEPTH:
            forward_frontier = expand_forward(forward_frontier, forward_visited)

    raise NoPathFoundError("No path found within 7 articles")
