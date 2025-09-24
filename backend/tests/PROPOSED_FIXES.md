# RAG System Component Fixes

## High Priority Fixes

### 1. Fix ChromaDB Metadata None Value Handling

**File**: `backend/vector_store.py`  
**Method**: `add_course_metadata()`
**Issue**: ChromaDB rejects None values in metadata

#### Current Problematic Code:
```python
self.course_catalog.add(
    documents=[course_text],
    metadatas=[{
        "title": course.title,
        "instructor": course.instructor,  # Can be None - CRASHES!
        "course_link": course.course_link,  # Can be None - CRASHES!
        "lessons_json": json.dumps(lessons_metadata),
        "lesson_count": len(course.lessons)
    }],
    ids=[course.title]
)
```

#### Proposed Fix:
```python
def add_course_metadata(self, course: Course):
    """Add course information to the catalog for semantic search"""
    import json

    course_text = course.title
    
    # Build lessons metadata and serialize as JSON string
    lessons_metadata = []
    for lesson in course.lessons:
        lessons_metadata.append({
            "lesson_number": lesson.lesson_number,
            "lesson_title": lesson.title,
            "lesson_link": lesson.lesson_link
        })
    
    # Filter out None values to prevent ChromaDB errors
    metadata = {
        "title": course.title,
        "lessons_json": json.dumps(lessons_metadata),
        "lesson_count": len(course.lessons)
    }
    
    # Add optional fields only if they exist
    if course.instructor is not None:
        metadata["instructor"] = course.instructor
    if course.course_link is not None:
        metadata["course_link"] = course.course_link
    
    self.course_catalog.add(
        documents=[course_text],
        metadatas=[metadata],
        ids=[course.title]
    )
```

### 2. Fix Course Name Resolution Logic

**File**: `backend/vector_store.py`
**Method**: `_resolve_course_name()`
**Issue**: Incorrect indexing and no similarity threshold checking

#### Current Problematic Code:
```python
def _resolve_course_name(self, course_name: str) -> Optional[str]:
    """Use vector search to find best matching course by name"""
    try:
        results = self.course_catalog.query(
            query_texts=[course_name],
            n_results=1
        )
        
        if results['documents'][0] and results['metadatas'][0]:
            # Return the title (which is now the ID)
            return results['metadatas'][0][0]['title']  # WRONG INDEXING!
    except Exception as e:
        print(f"Error resolving course name: {e}")
    
    return None
```

#### Proposed Fix:
```python
def _resolve_course_name(self, course_name: str) -> Optional[str]:
    """Use vector search to find best matching course by name"""
    try:
        results = self.course_catalog.query(
            query_texts=[course_name],
            n_results=1
        )
        
        # Check if we got results
        if (results['documents'] and results['documents'][0] and 
            results['metadatas'] and results['metadatas'][0] and
            results['distances'] and results['distances'][0]):
            
            # Check similarity threshold (lower distance = more similar)
            distance = results['distances'][0][0]
            if distance < 0.5:  # Similarity threshold - adjust as needed
                # Correct indexing: first result, first metadata entry
                return results['metadatas'][0][0]['title']
            else:
                print(f"Course name '{course_name}' not similar enough (distance: {distance})")
                
    except Exception as e:
        print(f"Error resolving course name: {e}")
    
    return None
```

### 3. Add Search Relevance Threshold

**File**: `backend/vector_store.py`
**Method**: `search()`
**Issue**: No minimum relevance threshold for "no results"

#### Enhanced Search Method:
```python
def search(self, 
           query: str,
           course_name: Optional[str] = None,
           lesson_number: Optional[int] = None,
           limit: Optional[int] = None,
           min_similarity: float = 0.7) -> SearchResults:
    """
    Main search interface that handles course resolution and content search.
    
    Args:
        query: What to search for in course content
        course_name: Optional course name/title to filter by
        lesson_number: Optional lesson number to filter by
        limit: Maximum results to return
        min_similarity: Minimum similarity threshold (lower distance)
        
    Returns:
        SearchResults object with documents and metadata
    """
    # Step 1: Resolve course name if provided
    course_title = None
    if course_name:
        course_title = self._resolve_course_name(course_name)
        if not course_title:
            return SearchResults.empty(f"No course found matching '{course_name}'")
    
    # Step 2: Build filter for content search
    filter_dict = self._build_filter(course_title, lesson_number)
    
    # Step 3: Search course content
    search_limit = limit if limit is not None else self.max_results
    
    try:
        results = self.course_content.query(
            query_texts=[query],
            n_results=search_limit,
            where=filter_dict
        )
        
        search_results = SearchResults.from_chroma(results)
        
        # Filter results by similarity threshold
        if search_results.distances:
            filtered_docs = []
            filtered_metadata = []
            filtered_distances = []
            
            for doc, meta, dist in zip(search_results.documents, 
                                     search_results.metadata,
                                     search_results.distances):
                if dist <= min_similarity:  # Lower distance = more similar
                    filtered_docs.append(doc)
                    filtered_metadata.append(meta)
                    filtered_distances.append(dist)
            
            # Return filtered results
            return SearchResults(
                documents=filtered_docs,
                metadata=filtered_metadata, 
                distances=filtered_distances
            )
        
        return search_results
        
    except Exception as e:
        return SearchResults.empty(f"Search error: {str(e)}")
```

### 4. Improve Resource Management for ChromaDB

**File**: `backend/vector_store.py`
**Class**: `VectorStore`
**Issue**: ChromaDB connections not properly cleaned up

#### Add Cleanup Methods:
```python
class VectorStore:
    """Vector storage using ChromaDB for course content and metadata"""
    
    def __init__(self, chroma_path: str, embedding_model: str, max_results: int = 5):
        # ... existing init code ...
        self._client_initialized = True
    
    def close(self):
        """Properly close ChromaDB client and cleanup resources"""
        try:
            if hasattr(self, '_client_initialized') and self._client_initialized:
                # Reset collections first
                self.course_catalog = None
                self.course_content = None
                
                # Close client if it has a close method
                if hasattr(self.client, 'close'):
                    self.client.close()
                elif hasattr(self.client, 'reset'):
                    self.client.reset()
                
                self._client_initialized = False
                
        except Exception as e:
            print(f"Error closing vector store: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        if hasattr(self, '_client_initialized'):
            self.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup"""
        self.close()
```

## Medium Priority Fixes

### 5. Enhanced Error Handling in CourseSearchTool

**File**: `backend/search_tools.py`
**Method**: `execute()`
**Issue**: Better error handling and logging

#### Enhanced Execute Method:
```python
def execute(self, query: str, course_name: Optional[str] = None, lesson_number: Optional[int] = None) -> str:
    """
    Execute the search tool with given parameters.
    
    Args:
        query: What to search for
        course_name: Optional course filter
        lesson_number: Optional lesson filter
        
    Returns:
        Formatted search results or error message
    """
    
    try:
        # Use the vector store's unified search interface
        results = self.store.search(
            query=query,
            course_name=course_name,
            lesson_number=lesson_number
        )
        
        # Handle errors
        if results.error:
            return results.error
        
        # Handle empty results
        if results.is_empty():
            filter_info = ""
            if course_name:
                filter_info += f" in course '{course_name}'"
            if lesson_number:
                filter_info += f" in lesson {lesson_number}"
            return f"No relevant content found{filter_info}."
        
        # Format and return results
        return self._format_results(results)
        
    except Exception as e:
        error_msg = f"Search execution failed: {str(e)}"
        print(error_msg)  # Log for debugging
        return error_msg
```

### 6. Improved Test Fixtures for Resource Management

**File**: `backend/tests/conftest.py`
**Issue**: Better ChromaDB cleanup in tests

#### Enhanced Test Fixtures:
```python
@pytest.fixture
def real_vector_store(self, temp_chroma_db):
    """Create a real VectorStore instance for integration testing"""
    store = None
    try:
        store = VectorStore(
            chroma_path=temp_chroma_db,
            embedding_model="all-MiniLM-L6-v2",
            max_results=5
        )
        yield store
    finally:
        if store:
            try:
                store.close()
            except Exception as e:
                print(f"Error closing vector store in fixture: {e}")
            
            # Additional cleanup - force close any remaining handles
            import time
            import gc
            gc.collect()
            time.sleep(0.1)  # Allow file handles to close
```

## Implementation Priority

### Phase 1 (Critical - Implement First)
1. **ChromaDB Metadata Fix** - Prevents crashes
2. **Course Name Resolution Fix** - Fixes core search functionality

### Phase 2 (Important - Implement Second) 
3. **Search Relevance Threshold** - Improves search quality
4. **Resource Management** - Prevents resource leaks

### Phase 3 (Enhancement - Implement Third)
5. **Enhanced Error Handling** - Improves debugging
6. **Test Fixture Improvements** - Stabilizes test suite

## Validation Strategy

After implementing fixes, run the test suite to verify:

```bash
# Test individual components
pytest backend/tests/test_search_tools.py -v
pytest backend/tests/test_ai_generator.py -v

# Test end-to-end functionality
pytest backend/tests/test_end_to_end.py -v --tb=short

# Run full test suite
pytest backend/tests/ -v
```

Expected results after fixes:
- All CourseSearchTool tests should continue passing
- All AI Generator tests should continue passing  
- End-to-end tests should pass without the current failures
- No ChromaDB resource cleanup errors
- Proper "no results found" behavior for irrelevant queries
- Correct course name filtering behavior

## Testing the Fixes

To validate each fix:

1. **Metadata Fix**: Create courses with None values - should not crash
2. **Course Resolution**: Search with invalid course name - should return "not found"
3. **Relevance Threshold**: Search for unrelated topics - should return "no results"
4. **Resource Cleanup**: Run tests multiple times - should not have file handle errors

This comprehensive fix plan addresses all the identified issues while maintaining the existing functionality that's working correctly.