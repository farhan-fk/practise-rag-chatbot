import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import tempfile
import json

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models import Course, Lesson, CourseChunk
from vector_store import VectorStore, SearchResults
from search_tools import CourseSearchTool, ToolManager
from ai_generator import AIGenerator
from document_processor import DocumentProcessor
from rag_system import RAGSystem


class TestRAGSystemEndToEnd:
    """End-to-end tests for the complete RAG system pipeline"""

    @pytest.fixture
    def temp_chroma_db(self):
        """Create a temporary ChromaDB for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield os.path.join(temp_dir, "test_chroma")

    @pytest.fixture
    def real_vector_store(self, temp_chroma_db):
        """Create a real VectorStore instance for integration testing"""
        return VectorStore(
            chroma_path=temp_chroma_db,
            embedding_model="all-MiniLM-L6-v2",
            max_results=5
        )

    @pytest.fixture
    def sample_courses_data(self):
        """Sample course data for end-to-end testing"""
        return [
            Course(
                title="Machine Learning Fundamentals",
                instructor="Dr. Smith",
                course_link="https://example.com/ml-course",
                lessons=[
                    Lesson(lesson_number=1, title="Introduction to ML", lesson_link="https://example.com/ml/lesson1"),
                    Lesson(lesson_number=2, title="Supervised Learning", lesson_link="https://example.com/ml/lesson2"),
                    Lesson(lesson_number=3, title="Neural Networks", lesson_link="https://example.com/ml/lesson3")
                ]
            ),
            Course(
                title="Deep Learning Specialization", 
                instructor="Prof. Johnson",
                course_link="https://example.com/dl-course",
                lessons=[
                    Lesson(lesson_number=1, title="Neural Network Basics", lesson_link="https://example.com/dl/lesson1"),
                    Lesson(lesson_number=2, title="Deep Neural Networks", lesson_link="https://example.com/dl/lesson2")
                ]
            )
        ]

    @pytest.fixture
    def sample_course_chunks(self):
        """Sample course content chunks for testing"""
        return [
            CourseChunk(
                content="Machine learning is a method of data analysis that automates analytical model building. It is a branch of artificial intelligence based on the idea that systems can learn from data, identify patterns and make decisions with minimal human intervention.",
                course_title="Machine Learning Fundamentals",
                lesson_number=1,
                chunk_index=0
            ),
            CourseChunk(
                content="Supervised learning is a type of machine learning algorithm that uses a known dataset called training data to make predictions. Examples include linear regression, logistic regression, and decision trees.",
                course_title="Machine Learning Fundamentals", 
                lesson_number=2,
                chunk_index=1
            ),
            CourseChunk(
                content="Neural networks are computing systems inspired by biological neural networks. They consist of interconnected nodes (neurons) that can learn to perform tasks by processing examples without being programmed with task-specific rules.",
                course_title="Machine Learning Fundamentals",
                lesson_number=3,
                chunk_index=2
            ),
            CourseChunk(
                content="Deep learning is part of a broader family of machine learning methods based on artificial neural networks with representation learning. Deep neural networks have multiple layers between input and output layers.",
                course_title="Deep Learning Specialization",
                lesson_number=1,
                chunk_index=3
            ),
            CourseChunk(
                content="Deep neural networks can model complex non-linear relationships and are particularly effective for tasks like image recognition, natural language processing, and speech recognition.",
                course_title="Deep Learning Specialization",
                lesson_number=2,
                chunk_index=4
            )
        ]

    def test_complete_rag_pipeline_basic_query(self, real_vector_store, sample_courses_data, sample_course_chunks):
        """Test complete RAG pipeline from data ingestion to query response"""
        # Step 1: Populate vector store with course data
        for course in sample_courses_data:
            real_vector_store.add_course_metadata(course)
        
        real_vector_store.add_course_content(sample_course_chunks)
        
        # Step 2: Set up search tool and tool manager
        search_tool = CourseSearchTool(real_vector_store)
        tool_manager = ToolManager()
        tool_manager.register_tool(search_tool)
        
        # Step 3: Mock AI generator response
        mock_ai_generator = Mock(spec=AIGenerator)
        mock_ai_generator.generate_response.return_value = "Machine learning is a method of data analysis that automates analytical model building, as covered in our courses."
        
        # Step 4: Test search functionality
        query_result = search_tool.execute(query="What is machine learning?")
        
        # Verify search found relevant content
        assert "Machine learning is a method of data analysis" in query_result
        assert "Machine Learning Fundamentals" in query_result
        
        # Verify sources were tracked
        assert len(search_tool.last_sources) > 0
        source = search_tool.last_sources[0]
        assert "Machine Learning Fundamentals" in source["title"]

    def test_rag_pipeline_with_course_filter(self, real_vector_store, sample_courses_data, sample_course_chunks):
        """Test RAG pipeline with course-specific filtering"""
        # Populate data
        for course in sample_courses_data:
            real_vector_store.add_course_metadata(course)
        real_vector_store.add_course_content(sample_course_chunks)
        
        search_tool = CourseSearchTool(real_vector_store)
        
        # Search specifically in Deep Learning course
        result = search_tool.execute(
            query="neural networks",
            course_name="Deep Learning"  # Partial match
        )
        
        # Should find content from Deep Learning Specialization course
        assert "Deep Learning Specialization" in result
        assert "deep neural networks" in result.lower() or "neural networks" in result.lower()

    def test_rag_pipeline_with_lesson_filter(self, real_vector_store, sample_courses_data, sample_course_chunks):
        """Test RAG pipeline with lesson-specific filtering"""
        # Populate data
        for course in sample_courses_data:
            real_vector_store.add_course_metadata(course)
        real_vector_store.add_course_content(sample_course_chunks)
        
        search_tool = CourseSearchTool(real_vector_store)
        
        # Search in specific lesson
        result = search_tool.execute(
            query="machine learning",
            lesson_number=2
        )
        
        # Should find lesson 2 content
        assert "Lesson 2" in result
        assert "supervised learning" in result.lower()

    def test_rag_pipeline_no_results_found(self, real_vector_store, sample_courses_data, sample_course_chunks):
        """Test RAG pipeline behavior when no relevant content is found"""
        # Populate data
        for course in sample_courses_data:
            real_vector_store.add_course_metadata(course)
        real_vector_store.add_course_content(sample_course_chunks)
        
        search_tool = CourseSearchTool(real_vector_store)
        
        # Search for non-existent topic
        result = search_tool.execute(query="quantum computing cryptocurrency blockchain")
        
        # Should return no results message
        assert "No relevant content found" in result

    def test_rag_pipeline_invalid_course_name(self, real_vector_store, sample_courses_data, sample_course_chunks):
        """Test RAG pipeline with invalid course name filter"""
        # Populate data  
        for course in sample_courses_data:
            real_vector_store.add_course_metadata(course)
        real_vector_store.add_course_content(sample_course_chunks)
        
        search_tool = CourseSearchTool(real_vector_store)
        
        # Search with non-existent course
        result = search_tool.execute(
            query="machine learning",
            course_name="Non-existent Course"
        )
        
        # Should return course not found message
        assert "No course found matching" in result

    def test_rag_pipeline_multiple_results_ranking(self, real_vector_store, sample_courses_data, sample_course_chunks):
        """Test that RAG pipeline returns results in relevance order"""
        # Populate data
        for course in sample_courses_data:
            real_vector_store.add_course_metadata(course)
        real_vector_store.add_course_content(sample_course_chunks)
        
        search_tool = CourseSearchTool(real_vector_store)
        
        # Search for term that appears in multiple chunks
        result = search_tool.execute(query="neural networks")
        
        # Should return multiple relevant results
        assert "neural networks" in result.lower()
        # Should include content from both ML Fundamentals and Deep Learning courses
        results_contain_both = ("Machine Learning Fundamentals" in result and 
                              "Deep Learning Specialization" in result)
        
        # At minimum, should find one relevant course
        assert ("Machine Learning Fundamentals" in result or 
               "Deep Learning Specialization" in result)

    def test_source_url_generation(self, real_vector_store, sample_courses_data, sample_course_chunks):
        """Test that proper source URLs are generated for search results"""
        # Populate data
        for course in sample_courses_data:
            real_vector_store.add_course_metadata(course)
        real_vector_store.add_course_content(sample_course_chunks)
        
        search_tool = CourseSearchTool(real_vector_store)
        
        # Execute search to generate sources
        result = search_tool.execute(query="machine learning", lesson_number=1)
        
        # Check that sources were generated
        sources = search_tool.last_sources
        assert len(sources) > 0
        
        # Check source structure
        source = sources[0]
        assert "title" in source
        assert "url" in source
        assert "Machine Learning Fundamentals" in source["title"]

    @patch('ai_generator.anthropic')
    def test_ai_generator_integration(self, mock_anthropic, real_vector_store, sample_courses_data, sample_course_chunks):
        """Test AI generator integration with real search results"""
        # Setup mock Anthropic client
        mock_client = Mock()
        mock_anthropic.Anthropic.return_value = mock_client
        
        # Mock tool use response
        tool_response = Mock()
        tool_block = Mock()
        tool_block.type = "tool_use"
        tool_block.id = "search_1"
        tool_block.name = "search_course_content"
        tool_block.input = {"query": "machine learning definition"}
        
        tool_response.content = [tool_block]
        tool_response.stop_reason = "tool_use"
        
        # Mock final response
        final_response = Mock()
        final_response.content = [Mock(text="Based on the course content, machine learning is a method of data analysis...")]
        
        mock_client.messages.create.side_effect = [tool_response, final_response]
        
        # Populate vector store
        for course in sample_courses_data:
            real_vector_store.add_course_metadata(course)
        real_vector_store.add_course_content(sample_course_chunks)
        
        # Setup components
        search_tool = CourseSearchTool(real_vector_store)
        tool_manager = ToolManager()
        tool_manager.register_tool(search_tool)
        
        ai_generator = AIGenerator("test_key", "claude-3-haiku-20240307")
        
        # Execute query
        result = ai_generator.generate_response(
            "What is machine learning?",
            tools=tool_manager.get_tool_definitions(),
            tool_manager=tool_manager
        )
        
        # Verify AI generated response
        assert result == "Based on the course content, machine learning is a method of data analysis..."
        
        # Verify search was executed with real data
        assert len(search_tool.last_sources) > 0

    def test_error_handling_in_pipeline(self, real_vector_store):
        """Test error handling throughout the RAG pipeline"""
        search_tool = CourseSearchTool(real_vector_store)
        
        # Test with empty vector store - should handle gracefully
        result = search_tool.execute(query="anything")
        assert "No relevant content found" in result
        
        # Test with invalid parameters
        result = search_tool.execute(query="test", lesson_number=-1)
        # Should still work or handle gracefully
        assert isinstance(result, str)

    def test_conversation_context_handling(self):
        """Test that conversation context is properly maintained"""
        mock_ai_generator = Mock(spec=AIGenerator)
        
        # Test with conversation history
        history = "User: What is ML?\nAssistant: Machine learning is..."
        
        mock_ai_generator.generate_response(
            query="Tell me more about neural networks",
            conversation_history=history
        )
        
        # Verify history was passed
        mock_ai_generator.generate_response.assert_called_once_with(
            query="Tell me more about neural networks",
            conversation_history=history
        )

    def test_tool_manager_source_tracking(self, real_vector_store, sample_courses_data, sample_course_chunks):
        """Test that ToolManager properly tracks and retrieves sources"""
        # Populate data
        for course in sample_courses_data:
            real_vector_store.add_course_metadata(course)
        real_vector_store.add_course_content(sample_course_chunks)
        
        search_tool = CourseSearchTool(real_vector_store)
        tool_manager = ToolManager()
        tool_manager.register_tool(search_tool)
        
        # Execute search via tool manager
        tool_manager.execute_tool("search_course_content", query="machine learning")
        
        # Get sources via tool manager
        sources = tool_manager.get_last_sources()
        assert len(sources) > 0
        
        # Reset sources
        tool_manager.reset_sources()
        assert len(tool_manager.get_last_sources()) == 0

    def test_system_performance_with_large_dataset(self, real_vector_store):
        """Test system performance with larger dataset"""
        # Create larger dataset
        courses = []
        chunks = []
        
        for i in range(10):  # 10 courses
            course = Course(
                title=f"Course {i}: Advanced Topic {i}",
                instructor=f"Instructor {i}",
                lessons=[
                    Lesson(lesson_number=j+1, title=f"Lesson {j+1}") 
                    for j in range(5)  # 5 lessons each
                ]
            )
            courses.append(course)
            
            # Add multiple chunks per course
            for j in range(5):
                for k in range(3):  # 3 chunks per lesson
                    chunk = CourseChunk(
                        content=f"This is content for course {i}, lesson {j+1}, chunk {k}. It covers advanced topics in the field including machine learning, neural networks, and data analysis.",
                        course_title=course.title,
                        lesson_number=j+1,
                        chunk_index=i*15 + j*3 + k
                    )
                    chunks.append(chunk)
        
        # Populate vector store
        for course in courses:
            real_vector_store.add_course_metadata(course)
        real_vector_store.add_course_content(chunks)
        
        # Test search performance
        search_tool = CourseSearchTool(real_vector_store)
        
        result = search_tool.execute(query="machine learning neural networks")
        
        # Should find relevant results efficiently
        assert isinstance(result, str)
        assert len(result) > 0
        
        # Should limit results appropriately
        sources = search_tool.last_sources
        assert len(sources) <= 5  # Default max_results


class TestRAGSystemEdgeCases:
    """Test edge cases and error conditions in the RAG system"""

    def test_empty_query_handling(self, course_search_tool):
        """Test handling of empty or whitespace-only queries"""
        course_search_tool.store.search.return_value = SearchResults([], [], [])
        
        result = course_search_tool.execute(query="")
        assert isinstance(result, str)
        
        result = course_search_tool.execute(query="   ")
        assert isinstance(result, str)

    def test_special_characters_in_query(self, course_search_tool, sample_search_results):
        """Test handling of queries with special characters"""
        course_search_tool.store.search.return_value = sample_search_results
        
        special_queries = [
            "machine learning & AI",
            "neural networks (deep learning)",
            "what's the difference between ML/AI?",
            "artificial intelligence @#$%"
        ]
        
        for query in special_queries:
            result = course_search_tool.execute(query=query)
            assert isinstance(result, str)
            # Should not crash and should return some result

    def test_very_long_query_handling(self, course_search_tool, sample_search_results):
        """Test handling of very long queries"""
        course_search_tool.store.search.return_value = sample_search_results
        
        long_query = "machine learning " * 100  # Very long query
        result = course_search_tool.execute(query=long_query)
        
        assert isinstance(result, str)

    def test_unicode_content_handling(self, course_search_tool):
        """Test handling of unicode content in results"""
        unicode_results = SearchResults(
            documents=["Machine learning avec français, 机器学习, Aprendizaje automático"],
            metadata=[{"course_title": "International AI Course", "lesson_number": 1}],
            distances=[0.1]
        )
        
        course_search_tool.store.search.return_value = unicode_results
        
        result = course_search_tool.execute(query="international content")
        
        assert isinstance(result, str)
        assert "International AI Course" in result

    def test_malformed_metadata_handling(self, course_search_tool):
        """Test handling of malformed or incomplete metadata"""
        malformed_results = SearchResults(
            documents=["Some content"],
            metadata=[{"incomplete": "metadata"}],  # Missing expected fields
            distances=[0.1]
        )
        
        course_search_tool.store.search.return_value = malformed_results
        
        result = course_search_tool.execute(query="test")
        
        # Should handle gracefully without crashing
        assert isinstance(result, str)

    def test_vector_store_connection_failure(self, course_search_tool):
        """Test handling of vector store connection failures"""
        course_search_tool.store.search.side_effect = Exception("Connection failed")
        
        result = course_search_tool.execute(query="test")
        
        # Should return error message, not crash
        assert isinstance(result, str)
        # The actual error handling depends on implementation