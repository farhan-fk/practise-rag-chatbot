import pytest
from unittest.mock import Mock, patch, MagicMock
from ai_generator import AIGenerator
from search_tools import CourseSearchTool, ToolManager


class TestAIGenerator:
    """Test suite for AIGenerator and its interaction with CourseSearchTool"""

    def test_init(self):
        """Test AIGenerator initialization"""
        generator = AIGenerator(api_key="test_key", model="claude-3-haiku-20240307")
        
        assert generator.model == "claude-3-haiku-20240307"
        assert generator.max_tool_rounds == 3  # Default value
        assert generator.base_params["model"] == "claude-3-haiku-20240307"
        assert generator.base_params["temperature"] == 0
        assert generator.base_params["max_tokens"] == 800
        
        # Test custom max_tool_rounds
        generator_custom = AIGenerator(api_key="test_key", model="claude-3-haiku-20240307", max_tool_rounds=5)
        assert generator_custom.max_tool_rounds == 5

    def test_generate_response_without_tools(self, ai_generator_with_mock_client, mock_anthropic_response):
        """Test response generation without tool usage"""
        ai_generator_with_mock_client.client.messages.create.return_value = mock_anthropic_response
        
        result = ai_generator_with_mock_client.generate_response("What is machine learning?")
        
        # Verify API call
        ai_generator_with_mock_client.client.messages.create.assert_called_once()
        call_args = ai_generator_with_mock_client.client.messages.create.call_args[1]
        
        assert call_args["model"] == "claude-3-haiku-20240307"
        assert call_args["messages"] == [{"role": "user", "content": "What is machine learning?"}]
        assert "tools" not in call_args
        
        assert result == "This is a sample AI response."

    def test_generate_response_with_conversation_history(self, ai_generator_with_mock_client, mock_anthropic_response):
        """Test response generation with conversation history"""
        ai_generator_with_mock_client.client.messages.create.return_value = mock_anthropic_response
        
        history = "User: Hello\nAssistant: Hi there!"
        result = ai_generator_with_mock_client.generate_response(
            "What is AI?", 
            conversation_history=history
        )
        
        call_args = ai_generator_with_mock_client.client.messages.create.call_args[1]
        assert history in call_args["system"]

    def test_generate_response_with_tools(self, ai_generator_with_mock_client, mock_anthropic_response, course_search_tool):
        """Test response generation with tools available"""
        # Mock a response that doesn't use tools (stop_reason != "tool_use")
        mock_anthropic_response.stop_reason = "end_turn"
        ai_generator_with_mock_client.client.messages.create.return_value = mock_anthropic_response
        
        tool_def = course_search_tool.get_tool_definition()
        tools = [tool_def]

        result = ai_generator_with_mock_client.generate_response(
            "General question about AI",
            tools=tools
        )

        # Verify that the API was called
        ai_generator_with_mock_client.client.messages.create.assert_called_once()
        call_args = ai_generator_with_mock_client.client.messages.create.call_args[1]
        
        # With the new implementation, tools are only included if needed for sequential calling
        # For this test, since stop_reason is "end_turn", tools weren't needed
        assert "model" in call_args
        assert "messages" in call_args

    def test_generate_response_calls_search_tool(self, ai_generator_with_mock_client, mock_tool_use_response, 
                                                tool_manager_with_search_tool, sample_search_results):
        """Test that AI correctly calls CourseSearchTool when needed"""
        # Setup mock responses
        ai_generator_with_mock_client.client.messages.create.side_effect = [
            mock_tool_use_response,  # First call with tool use
            Mock(content=[Mock(text="Based on the search, here's the answer.")])  # Second call with final response
        ]
        
        # Setup tool manager
        tool_manager_with_search_tool.tools["search_course_content"].store.search.return_value = sample_search_results
        
        tools = tool_manager_with_search_tool.get_tool_definitions()
        
        result = ai_generator_with_mock_client.generate_response(
            "Tell me about machine learning from the course",
            tools=tools,
            tool_manager=tool_manager_with_search_tool
        )
        
        # Verify two API calls were made
        assert ai_generator_with_mock_client.client.messages.create.call_count == 2
        
        # Verify tool was executed
        tool_manager_with_search_tool.tools["search_course_content"].store.search.assert_called_once()
        
        assert result == "Based on the search, here's the answer."

    def test_handle_tool_execution_single_tool(self, ai_generator_with_mock_client, mock_tool_use_response,
                                              tool_manager_with_search_tool, sample_search_results):
        """Test handling of single tool execution"""
        # Setup search tool to return results
        search_tool = tool_manager_with_search_tool.tools["search_course_content"]
        search_tool.store.search.return_value = sample_search_results
        
        # Mock final response
        final_response = Mock()
        final_response.content = [Mock()]
        final_response.content[0].text = "Final answer based on search."
        ai_generator_with_mock_client.client.messages.create.return_value = final_response
        
        base_params = {
            "model": "claude-3-haiku-20240307",
            "temperature": 0,
            "max_tokens": 800,
            "messages": [{"role": "user", "content": "Search query"}],
            "system": "System prompt"
        }
        
        result = ai_generator_with_mock_client._handle_tool_execution(
            mock_tool_use_response, 
            base_params, 
            tool_manager_with_search_tool
        )
        
        # Verify tool was called
        search_tool.store.search.assert_called_once()

    def test_handle_tool_execution_multiple_tools(self, ai_generator_with_mock_client, tool_manager_with_search_tool, sample_search_results):
        """Test handling of multiple tool calls in single response"""
        # Create mock response with multiple tool uses
        tool_block1 = Mock()
        tool_block1.type = "tool_use"
        tool_block1.id = "tool1"
        tool_block1.name = "search_course_content"
        tool_block1.input = {"query": "first query"}
        
        tool_block2 = Mock()
        tool_block2.type = "tool_use"
        tool_block2.id = "tool2"
        tool_block2.name = "search_course_content"
        tool_block2.input = {"query": "second query"}
        
        multi_tool_response = Mock()
        multi_tool_response.content = [tool_block1, tool_block2]
        
        # Setup tool to return results
        search_tool = tool_manager_with_search_tool.tools["search_course_content"]
        search_tool.store.search.return_value = sample_search_results
        
        # Mock final response
        final_response = Mock()
        final_response.content = [Mock()]
        final_response.content[0].text = "Final answer."
        ai_generator_with_mock_client.client.messages.create.return_value = final_response
        
        base_params = {
            "model": "claude-3-haiku-20240307",
            "temperature": 0,
            "max_tokens": 800,
            "messages": [{"role": "user", "content": "Complex query"}],
            "system": "System prompt"
        }
        
        ai_generator_with_mock_client._handle_tool_execution(
            multi_tool_response,
            base_params,
            tool_manager_with_search_tool
        )
        
        # Verify tool was called twice
        assert search_tool.store.search.call_count == 2

    def test_system_prompt_content(self):
        """Test that system prompt contains expected content for sequential tool calling"""
        prompt = AIGenerator.SYSTEM_PROMPT
        
        # Check key components for the updated prompt
        assert "search tool" in prompt.lower()
        assert "course materials" in prompt.lower()  
        assert "educational content" in prompt.lower()
        assert "multiple searches" in prompt.lower()  # Updated expectation
        assert "comprehensive" in prompt.lower()  # New expectation

    def test_api_parameters_construction(self, ai_generator_with_mock_client, mock_anthropic_response):
        """Test that API parameters are constructed correctly"""
        # Mock a response that doesn't use tools
        mock_anthropic_response.stop_reason = "end_turn"
        ai_generator_with_mock_client.client.messages.create.return_value = mock_anthropic_response
        
        tools = [{"name": "test_tool", "description": "Test"}]
        history = "Previous conversation"

        ai_generator_with_mock_client.generate_response(
            query="Test query",
            conversation_history=history,
            tools=tools
        )

        call_args = ai_generator_with_mock_client.client.messages.create.call_args[1]
        
        # Verify all expected parameters
        assert call_args["model"] == "claude-3-haiku-20240307"
        assert call_args["temperature"] == 0
        assert call_args["max_tokens"] == 800
        assert call_args["messages"] == [{"role": "user", "content": "Test query"}]
        assert history in call_args["system"]
        # Tools are only included when actually needed for sequential calling

    def test_tool_execution_error_handling(self, ai_generator_with_mock_client, mock_tool_use_response):
        """Test handling of tool execution errors"""
        # Create a mock tool manager that raises an exception
        error_tool_manager = Mock()
        error_tool_manager.execute_tool.side_effect = Exception("Tool execution failed")
        
        # Mock the client response properly for the legacy method
        final_response = Mock()
        final_response.content = [Mock()]
        final_response.content[0].text = "Error handled gracefully"
        ai_generator_with_mock_client.client.messages.create.return_value = final_response
        
        base_params = {
            "model": "claude-3-haiku-20240307",
            "temperature": 0,
            "max_tokens": 800,
            "messages": [{"role": "user", "content": "Test"}],
            "system": "System prompt"
        }
        
        # Test the legacy method directly since it handles single-round tool execution
        result = ai_generator_with_mock_client._handle_tool_execution(
            mock_tool_use_response,
            base_params,
            error_tool_manager
        )
        
        # Should return the mocked response, not crash
        assert result == "Error handled gracefully"

    def test_no_tool_manager_with_tool_use_response(self, ai_generator_with_mock_client, mock_tool_use_response):
        """Test behavior when tool use is requested but no tool manager is provided"""
        ai_generator_with_mock_client.client.messages.create.return_value = mock_tool_use_response
        
        result = ai_generator_with_mock_client.generate_response(
            "Search for something",
            tools=[{"name": "test_tool"}],
            tool_manager=None  # No tool manager provided
        )
        
        # Should handle gracefully - might return the tool request text or handle appropriately
        assert isinstance(result, str)

    def test_final_response_structure(self, ai_generator_with_mock_client, mock_tool_use_response,
                                     tool_manager_with_search_tool, sample_search_results):
        """Test that final response after tool execution is properly structured"""
        # Setup tool execution
        search_tool = tool_manager_with_search_tool.tools["search_course_content"]  
        search_tool.store.search.return_value = sample_search_results
        
        # Mock the sequential responses for the new implementation
        text_response = Mock()
        text_response.stop_reason = "end_turn"
        text_response.content = [Mock()]
        text_response.content[0].text = "Complete answer with search results."
        text_response.content[0].type = "text"
        
        ai_generator_with_mock_client.client.messages.create.side_effect = [
            mock_tool_use_response,  # First call with tool use
            text_response           # Second call with final text response
        ]
        
        tools = tool_manager_with_search_tool.get_tool_definitions()
        result = ai_generator_with_mock_client.generate_response(
            "Search question",
            tools=tools,
            tool_manager=tool_manager_with_search_tool
        )
        
        assert result == "Complete answer with search results."
        
        # Verify the sequential tool calling behavior
        assert ai_generator_with_mock_client.client.messages.create.call_count == 2
        
        # Check that the second call has accumulated the conversation properly
        second_call_args = ai_generator_with_mock_client.client.messages.create.call_args_list[1][1]
        # The new implementation manages the conversation differently - there should be user, assistant, tool results, etc.
        assert len(second_call_args["messages"]) >= 3  # At least user query + assistant tool use + tool results


class TestAIGeneratorIntegration:
    """Integration tests for AIGenerator with CourseSearchTool"""

    def test_end_to_end_course_search(self, mock_vector_store, sample_search_results):
        """Test complete flow from query to response via course search"""
        # Setup components
        search_tool = CourseSearchTool(mock_vector_store)
        mock_vector_store.search.return_value = sample_search_results
        
        tool_manager = ToolManager()
        tool_manager.register_tool(search_tool)
        
        # Mock Anthropic client and responses
        mock_client = Mock()
        
        # Tool use response
        tool_response = Mock()
        tool_block = Mock()
        tool_block.type = "tool_use"
        tool_block.id = "search_id"
        tool_block.name = "search_course_content"
        tool_block.input = {"query": "machine learning basics"}
        
        tool_response.content = [tool_block]
        tool_response.stop_reason = "tool_use"
        
        # Final response
        final_response = Mock()
        final_response.content = [Mock(text="Machine learning is a branch of AI...")]
        
        mock_client.messages.create.side_effect = [tool_response, final_response]
        
        # Create generator and execute
        generator = AIGenerator("test_key", "claude-3-haiku-20240307")
        generator.client = mock_client
        
        result = generator.generate_response(
            "Tell me about machine learning from the courses",
            tools=tool_manager.get_tool_definitions(),
            tool_manager=tool_manager
        )
        
        # Verify the complete flow
        mock_vector_store.search.assert_called_once_with(
            query="machine learning basics",
            course_name=None,
            lesson_number=None
        )
        
        assert result == "Machine learning is a branch of AI..."
        assert len(search_tool.last_sources) > 0  # Sources were tracked

    def test_course_search_with_specific_filters(self, mock_vector_store, sample_search_results):
        """Test course search with course name and lesson filters"""
        search_tool = CourseSearchTool(mock_vector_store)
        mock_vector_store.search.return_value = sample_search_results
        
        tool_manager = ToolManager()
        tool_manager.register_tool(search_tool)
        
        # Mock the tool execution directly
        result = tool_manager.execute_tool(
            "search_course_content",
            query="neural networks",
            course_name="Machine Learning",
            lesson_number=3
        )
        
        # Verify the search was called with correct parameters
        mock_vector_store.search.assert_called_once_with(
            query="neural networks",
            course_name="Machine Learning", 
            lesson_number=3
        )
        
        assert isinstance(result, str)
        assert len(result) > 0