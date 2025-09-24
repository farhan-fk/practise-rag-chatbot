import pytest
from unittest.mock import Mock, patch, MagicMock
from search_tools import CourseSearchTool, ToolManager
from vector_store import SearchResults
from .conftest import TestDataHelper


class TestCourseSearchTool:
    """Test suite for CourseSearchTool execute method validation"""

    def test_get_tool_definition(self, course_search_tool):
        """Test that tool definition is correctly structured"""
        definition = course_search_tool.get_tool_definition()
        
        assert definition["name"] == "search_course_content"
        assert "description" in definition
        assert "input_schema" in definition
        
        schema = definition["input_schema"]
        assert schema["type"] == "object"
        assert "query" in schema["properties"]
        assert "course_name" in schema["properties"]
        assert "lesson_number" in schema["properties"]
        assert schema["required"] == ["query"]

    def test_execute_successful_search_basic(self, course_search_tool, sample_search_results):
        """Test successful basic search execution"""
        course_search_tool.store.search.return_value = sample_search_results
        
        result = course_search_tool.execute(query="machine learning")
        
        # Verify store.search was called correctly
        course_search_tool.store.search.assert_called_once_with(
            query="machine learning",
            course_name=None,
            lesson_number=None
        )
        
        # Verify result formatting
        assert "Introduction to Machine Learning" in result
        assert "Lesson 1" in result
        assert "This is sample content about machine learning basics." in result

    def test_execute_successful_search_with_course_filter(self, course_search_tool, sample_search_results):
        """Test successful search with course name filter"""
        course_search_tool.store.search.return_value = sample_search_results
        
        result = course_search_tool.execute(
            query="neural networks",
            course_name="Machine Learning"
        )
        
        course_search_tool.store.search.assert_called_once_with(
            query="neural networks",
            course_name="Machine Learning",
            lesson_number=None
        )
        
        assert isinstance(result, str)
        assert len(result) > 0

    def test_execute_successful_search_with_lesson_filter(self, course_search_tool, sample_search_results):
        """Test successful search with lesson number filter"""
        course_search_tool.store.search.return_value = sample_search_results
        
        result = course_search_tool.execute(
            query="algorithms",
            lesson_number=2
        )
        
        course_search_tool.store.search.assert_called_once_with(
            query="algorithms",
            course_name=None,
            lesson_number=2
        )
        
        assert isinstance(result, str)

    def test_execute_successful_search_with_both_filters(self, course_search_tool, sample_search_results):
        """Test successful search with both course and lesson filters"""
        course_search_tool.store.search.return_value = sample_search_results
        
        result = course_search_tool.execute(
            query="supervised learning",
            course_name="ML Course",
            lesson_number=3
        )
        
        course_search_tool.store.search.assert_called_once_with(
            query="supervised learning",
            course_name="ML Course",
            lesson_number=3
        )
        
        assert isinstance(result, str)

    def test_execute_empty_results(self, course_search_tool, empty_search_results):
        """Test handling of empty search results"""
        course_search_tool.store.search.return_value = empty_search_results
        
        result = course_search_tool.execute(query="nonexistent topic")
        
        assert "No relevant content found" in result

    def test_execute_empty_results_with_filters(self, course_search_tool, empty_search_results):
        """Test empty results message includes filter information"""
        course_search_tool.store.search.return_value = empty_search_results
        
        result = course_search_tool.execute(
            query="nonexistent topic",
            course_name="Test Course",
            lesson_number=5
        )
        
        assert "No relevant content found" in result
        assert "Test Course" in result
        assert "lesson 5" in result

    def test_execute_error_handling(self, course_search_tool, error_search_results):
        """Test handling of search errors"""
        course_search_tool.store.search.return_value = error_search_results
        
        result = course_search_tool.execute(query="test query")
        
        assert result == "Database connection failed"

    def test_execute_stores_sources(self, course_search_tool, sample_search_results):
        """Test that sources are correctly stored for UI retrieval"""
        course_search_tool.store.search.return_value = sample_search_results
        
        # Mock the _get_lesson_url method to return a URL
        course_search_tool._get_lesson_url = Mock(return_value="https://example.com/lesson1")
        
        result = course_search_tool.execute(query="test")
        
        # Check that sources were stored
        assert len(course_search_tool.last_sources) == 1
        source = course_search_tool.last_sources[0]
        assert source["title"] == "Introduction to Machine Learning - Lesson 1"
        assert source["url"] == "https://example.com/lesson1"

    def test_format_results_single_document(self, course_search_tool):
        """Test formatting of single document result"""
        results = SearchResults(
            documents=["Content about AI fundamentals."],
            metadata=[{"course_title": "AI Basics", "lesson_number": 1}],
            distances=[0.1]
        )
        
        course_search_tool._get_lesson_url = Mock(return_value="https://test.com")
        formatted = course_search_tool._format_results(results)
        
        assert "[AI Basics - Lesson 1]" in formatted
        assert "Content about AI fundamentals." in formatted

    def test_format_results_multiple_documents(self, course_search_tool):
        """Test formatting of multiple document results"""
        results = TestDataHelper.create_search_results_with_multiple_courses()
        
        course_search_tool._get_lesson_url = Mock(return_value="https://test.com")
        formatted = course_search_tool._format_results(results)
        
        # Check all courses are included
        assert "Machine Learning Basics" in formatted
        assert "Artificial Intelligence" in formatted  
        assert "Data Science Fundamentals" in formatted
        
        # Check proper separation
        assert formatted.count("\n\n") >= 2  # Multiple documents separated by double newlines

    def test_format_results_missing_metadata(self, course_search_tool):
        """Test formatting with missing metadata fields"""
        results = SearchResults(
            documents=["Content without full metadata."],
            metadata=[{"course_title": "Test Course"}],  # Missing lesson_number
            distances=[0.1]
        )
        
        course_search_tool._get_lesson_url = Mock(return_value=None)
        formatted = course_search_tool._format_results(results)
        
        assert "[Test Course]" in formatted  # No lesson number
        assert "Content without full metadata." in formatted

    def test_get_lesson_url_success(self, course_search_tool):
        """Test successful lesson URL retrieval"""
        # Mock the course catalog query
        mock_catalog = Mock()
        mock_catalog.get.return_value = {
            'metadatas': [{'lessons_json': '[{"lesson_number": 1, "lesson_link": "https://test.com/lesson1"}]'}]
        }
        course_search_tool.store.course_catalog = mock_catalog
        
        url = course_search_tool._get_lesson_url("Test Course", 1)
        
        assert url == "https://test.com/lesson1"

    def test_get_lesson_url_missing_course(self, course_search_tool):
        """Test lesson URL retrieval with missing course"""
        mock_catalog = Mock()
        mock_catalog.get.return_value = {'metadatas': [None]}
        course_search_tool.store.course_catalog = mock_catalog
        
        url = course_search_tool._get_lesson_url("Missing Course", 1)
        
        assert url is None

    def test_get_lesson_url_invalid_json(self, course_search_tool):
        """Test lesson URL retrieval with invalid JSON"""
        mock_catalog = Mock()
        mock_catalog.get.return_value = {
            'metadatas': [{'lessons_json': 'invalid json'}]
        }
        course_search_tool.store.course_catalog = mock_catalog
        
        url = course_search_tool._get_lesson_url("Test Course", 1)
        
        assert url is None

    def test_get_lesson_url_no_lesson_number(self, course_search_tool):
        """Test lesson URL retrieval without lesson number"""
        url = course_search_tool._get_lesson_url("Test Course", None)
        assert url is None

    def test_execute_parameter_types(self, course_search_tool, sample_search_results):
        """Test execute method handles different parameter types correctly"""
        course_search_tool.store.search.return_value = sample_search_results
        
        # Test with integer lesson_number
        course_search_tool.execute(query="test", lesson_number=1)
        
        # Test with string course_name
        course_search_tool.execute(query="test", course_name="Test Course")
        
        # All should work without errors
        assert course_search_tool.store.search.call_count == 2

    def test_source_tracking_across_multiple_calls(self, course_search_tool, sample_search_results):
        """Test that sources are properly updated across multiple search calls"""
        course_search_tool.store.search.return_value = sample_search_results
        course_search_tool._get_lesson_url = Mock(return_value="https://test.com")
        
        # First call
        course_search_tool.execute(query="first query")
        first_sources = course_search_tool.last_sources.copy()
        
        # Second call - should replace sources
        course_search_tool.execute(query="second query") 
        second_sources = course_search_tool.last_sources
        
        # Sources should be updated, not accumulated
        assert len(second_sources) == 1
        assert first_sources[0] == second_sources[0]  # Same mock data


class TestToolManager:
    """Test suite for ToolManager functionality"""

    def test_register_tool(self, course_search_tool):
        """Test tool registration"""
        manager = ToolManager()
        manager.register_tool(course_search_tool)
        
        assert "search_course_content" in manager.tools
        assert manager.tools["search_course_content"] == course_search_tool

    def test_register_tool_without_name(self):
        """Test registration of tool without name raises error"""
        manager = ToolManager()
        mock_tool = Mock()
        mock_tool.get_tool_definition.return_value = {"description": "Test tool"}  # No name
        
        with pytest.raises(ValueError, match="Tool must have a 'name'"):
            manager.register_tool(mock_tool)

    def test_get_tool_definitions(self, course_search_tool):
        """Test retrieval of all tool definitions"""
        manager = ToolManager()
        manager.register_tool(course_search_tool)
        
        definitions = manager.get_tool_definitions()
        
        assert len(definitions) == 1
        assert definitions[0]["name"] == "search_course_content"

    def test_execute_tool_success(self, course_search_tool, sample_search_results):
        """Test successful tool execution via manager"""
        course_search_tool.store.search.return_value = sample_search_results
        
        manager = ToolManager()
        manager.register_tool(course_search_tool)
        
        result = manager.execute_tool("search_course_content", query="test query")
        
        assert isinstance(result, str)
        assert len(result) > 0

    def test_execute_tool_not_found(self):
        """Test execution of non-existent tool"""
        manager = ToolManager()
        
        result = manager.execute_tool("nonexistent_tool", query="test")
        
        assert result == "Tool 'nonexistent_tool' not found"

    def test_get_last_sources(self, course_search_tool, sample_search_results):
        """Test retrieval of sources from last search"""
        course_search_tool.store.search.return_value = sample_search_results
        course_search_tool._get_lesson_url = Mock(return_value="https://test.com")
        
        manager = ToolManager()
        manager.register_tool(course_search_tool)
        
        # Execute search to generate sources
        manager.execute_tool("search_course_content", query="test")
        
        sources = manager.get_last_sources()
        assert len(sources) == 1
        assert sources[0]["title"] == "Introduction to Machine Learning - Lesson 1"

    def test_reset_sources(self, course_search_tool, sample_search_results):
        """Test resetting sources across all tools"""
        course_search_tool.store.search.return_value = sample_search_results
        course_search_tool._get_lesson_url = Mock(return_value="https://test.com")
        
        manager = ToolManager()
        manager.register_tool(course_search_tool)
        
        # Generate sources
        manager.execute_tool("search_course_content", query="test")
        assert len(manager.get_last_sources()) > 0
        
        # Reset sources
        manager.reset_sources()
        assert len(manager.get_last_sources()) == 0