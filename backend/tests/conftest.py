import pytest
from unittest.mock import Mock, MagicMock
from typing import List, Dict, Any
import sys
import os

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models import Course, Lesson, CourseChunk
from vector_store import VectorStore, SearchResults
from search_tools import CourseSearchTool, ToolManager
from ai_generator import AIGenerator


@pytest.fixture
def mock_vector_store():
    """Mock VectorStore for testing"""
    mock_store = Mock(spec=VectorStore)
    return mock_store


@pytest.fixture
def sample_search_results():
    """Sample search results for testing"""
    return SearchResults(
        documents=["This is sample content about machine learning basics."],
        metadata=[{
            "course_title": "Introduction to Machine Learning",
            "lesson_number": 1,
            "chunk_index": 0
        }],
        distances=[0.1]
    )


@pytest.fixture
def empty_search_results():
    """Empty search results for testing"""
    return SearchResults(
        documents=[],
        metadata=[],
        distances=[]
    )


@pytest.fixture
def error_search_results():
    """Search results with error for testing"""
    return SearchResults.empty("Database connection failed")


@pytest.fixture
def course_search_tool(mock_vector_store):
    """CourseSearchTool instance with mocked dependencies"""
    return CourseSearchTool(mock_vector_store)


@pytest.fixture
def sample_course():
    """Sample course data for testing"""
    return Course(
        title="Introduction to Machine Learning",
        instructor="Dr. Smith",
        course_link="https://example.com/ml-course",
        lessons=[
            Lesson(lesson_number=1, title="ML Basics", lesson_link="https://example.com/ml-course/lesson1"),
            Lesson(lesson_number=2, title="Supervised Learning", lesson_link="https://example.com/ml-course/lesson2")
        ]
    )


@pytest.fixture
def sample_course_chunks():
    """Sample course chunks for testing"""
    return [
        CourseChunk(
            content="Machine learning is a subset of artificial intelligence.",
            course_title="Introduction to Machine Learning",
            lesson_number=1,
            chunk_index=0
        ),
        CourseChunk(
            content="Supervised learning uses labeled training data.",
            course_title="Introduction to Machine Learning", 
            lesson_number=2,
            chunk_index=1
        )
    ]


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client for AI generator testing"""
    mock_client = Mock()
    return mock_client


@pytest.fixture
def mock_anthropic_response():
    """Mock Anthropic API response"""
    mock_response = Mock()
    mock_response.content = [Mock(text="This is a sample AI response.")]
    mock_response.stop_reason = "end_turn"
    return mock_response


@pytest.fixture
def mock_tool_use_response():
    """Mock Anthropic response with tool use"""
    mock_response = Mock()
    
    # Mock tool use content block
    tool_block = Mock()
    tool_block.type = "tool_use"
    tool_block.id = "test_tool_id"
    tool_block.name = "search_course_content"
    tool_block.input = {"query": "test query"}
    
    # Mock text content block
    text_block = Mock()
    text_block.type = "text"
    text_block.text = "I'll search for that information."
    
    mock_response.content = [text_block, tool_block]
    mock_response.stop_reason = "tool_use"
    return mock_response


@pytest.fixture
def tool_manager_with_search_tool(course_search_tool):
    """ToolManager with CourseSearchTool registered"""
    manager = ToolManager()
    manager.register_tool(course_search_tool)
    return manager


@pytest.fixture
def ai_generator_with_mock_client(mock_anthropic_client):
    """AIGenerator with mocked Anthropic client"""
    generator = AIGenerator(api_key="test_key", model="claude-3-haiku-20240307")
    generator.client = mock_anthropic_client
    return generator


class TestDataHelper:
    """Helper class for creating test data consistently across tests"""
    
    @staticmethod
    def create_course_with_lessons(title: str, lesson_count: int = 3) -> Course:
        """Create a course with specified number of lessons"""
        lessons = [
            Lesson(
                lesson_number=i+1,
                title=f"Lesson {i+1}: Topic {i+1}",
                lesson_link=f"https://example.com/{title.lower().replace(' ', '-')}/lesson{i+1}"
            ) for i in range(lesson_count)
        ]
        
        return Course(
            title=title,
            instructor="Test Instructor",
            course_link=f"https://example.com/{title.lower().replace(' ', '-')}",
            lessons=lessons
        )
    
    @staticmethod
    def create_search_results_with_multiple_courses() -> SearchResults:
        """Create search results spanning multiple courses"""
        return SearchResults(
            documents=[
                "Content from ML course about neural networks.",
                "Content from AI course about machine learning.", 
                "Content from Data Science course about algorithms."
            ],
            metadata=[
                {"course_title": "Machine Learning Basics", "lesson_number": 3, "chunk_index": 0},
                {"course_title": "Artificial Intelligence", "lesson_number": 1, "chunk_index": 5},
                {"course_title": "Data Science Fundamentals", "lesson_number": 2, "chunk_index": 2}
            ],
            distances=[0.1, 0.15, 0.2]
        )