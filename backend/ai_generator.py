import anthropic
from typing import List, Optional, Dict, Any

class AIGenerator:
    """Handles interactions with Anthropic's Claude API for generating responses"""
    
    # Static system prompt to avoid rebuilding on each call
    SYSTEM_PROMPT = """ You are an AI assistant specialized in course materials and educational content with access to a comprehensive search tool for course information.

Search Tool Usage:
- Use the search tool for questions about specific course content or detailed educational materials
- **You can make multiple searches** to gather comprehensive information for complex queries
- For comparisons, multi-part questions, or cross-references, search each component separately
- Always search first before providing answers about course content
- Synthesize search results into accurate, fact-based responses
- If search yields no results, state this clearly

Sequential Search Examples:
- **Course comparisons**: Search each course/lesson separately, then compare
- **Cross-references**: Search for course outlines first, then search for specific topics
- **Multi-part queries**: Break down into separate searches as needed

Response Protocol:
- **General knowledge questions**: Answer using existing knowledge without searching
- **Course-specific questions**: Search first, then answer
- **Complex queries**: Use multiple searches to gather all needed information
- **No meta-commentary**: Provide direct answers without explaining your search process

All responses must be:
1. **Comprehensive** - Gather all necessary information through searches
2. **Educational** - Maintain instructional value
3. **Clear** - Use accessible language  
4. **Example-supported** - Include relevant examples when they aid understanding
Provide complete, well-informed answers based on your searches.
"""
    
    def __init__(self, api_key: str, model: str, max_tool_rounds: int = 3):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.max_tool_rounds = max_tool_rounds  # Maximum number of tool calling rounds
        
        # Pre-build base API parameters
        self.base_params = {
            "model": self.model,
            "temperature": 0,
            "max_tokens": 800
        }
    
    def generate_response(self, query: str,
                         conversation_history: Optional[str] = None,
                         tools: Optional[List] = None,
                         tool_manager=None) -> str:
        """
        Generate AI response with sequential tool usage support.
        
        Args:
            query: The user's question or request
            conversation_history: Previous messages for context
            tools: Available tools the AI can use
            tool_manager: Manager to execute tools
            
        Returns:
            Generated response as string
        """
        
        # Build system content efficiently
        system_content = (
            f"{self.SYSTEM_PROMPT}\n\nPrevious conversation:\n{conversation_history}"
            if conversation_history 
            else self.SYSTEM_PROMPT
        )
        
        # Initialize conversation with user query
        messages = [{"role": "user", "content": query}]
        
        # Handle sequential tool calling
        if tools and tool_manager:
            return self._handle_sequential_tool_calling(messages, system_content, tools, tool_manager)
        
        # Simple response without tools
        api_params = {
            **self.base_params,
            "messages": messages,
            "system": system_content
        }
        
        response = self.client.messages.create(**api_params)
        return response.content[0].text
    
    def _handle_sequential_tool_calling(self, messages: List[Dict], system_content: str, 
                                      tools: List[Dict], tool_manager) -> str:
        """
        Handle multiple rounds of tool calling until Claude provides a final answer.
        
        Args:
            messages: Conversation messages
            system_content: System prompt content
            tools: Available tools
            tool_manager: Manager to execute tools
            
        Returns:
            Final response after all tool calls complete
        """
        round_count = 0
        
        while round_count < self.max_tool_rounds:
            round_count += 1
            
            # Prepare API call with tools available
            api_params = {
                **self.base_params,
                "messages": messages,
                "system": system_content,
                "tools": tools,
                "tool_choice": {"type": "auto"}
            }
            
            # Get response from Claude
            response = self.client.messages.create(**api_params)
            
            # Add Claude's response to conversation
            messages.append({"role": "assistant", "content": response.content})
            
            # Check if Claude wants to use tools
            if response.stop_reason == "tool_use":
                # Execute all tool calls in this round
                tool_results = self._execute_tool_calls(response, tool_manager)
                
                if tool_results:
                    # Add tool results to conversation
                    messages.append({"role": "user", "content": tool_results})
                    
                    # Continue to next round - Claude can decide to use more tools or provide final answer
                    continue
            
            # Claude provided a final answer (no tool use or max rounds reached)
            # Extract text content from the response
            text_content = ""
            for content_block in response.content:
                if hasattr(content_block, 'text'):
                    text_content += content_block.text
                elif content_block.type == "text":
                    text_content += content_block.text
            
            return text_content if text_content else "I apologize, but I couldn't generate a proper response."
        
        # If we've reached max rounds, get a final response without tools
        final_params = {
            **self.base_params,
            "messages": messages + [{"role": "user", "content": "Please provide your final answer based on the information gathered."}],
            "system": system_content
        }
        
        final_response = self.client.messages.create(**final_params)
        return final_response.content[0].text
    
    def _execute_tool_calls(self, response, tool_manager) -> List[Dict[str, Any]]:
        """
        Execute all tool calls from a Claude response.
        
        Args:
            response: Claude's response containing tool calls
            tool_manager: Manager to execute tools
            
        Returns:
            List of tool results formatted for Claude
        """
        tool_results = []
        
        for content_block in response.content:
            if content_block.type == "tool_use":
                try:
                    # Execute the tool
                    tool_result = tool_manager.execute_tool(
                        content_block.name, 
                        **content_block.input
                    )
                    
                    # Format result for Claude
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content_block.id,
                        "content": tool_result
                    })
                    
                except Exception as e:
                    # Handle tool execution errors gracefully
                    error_message = f"Tool execution failed: {str(e)}"
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content_block.id,
                        "content": error_message
                    })
        
        return tool_results
    
    def _handle_tool_execution(self, initial_response, base_params: Dict[str, Any], tool_manager):
        """
        Legacy method for single-round tool execution (kept for backward compatibility).
        New implementation uses _handle_sequential_tool_calling.
        
        Args:
            initial_response: The response containing tool use requests
            base_params: Base API parameters
            tool_manager: Manager to execute tools
            
        Returns:
            Final response text after tool execution
        """
        # Start with existing messages
        messages = base_params["messages"].copy()
        
        # Add AI's tool use response
        messages.append({"role": "assistant", "content": initial_response.content})
        
        # Execute all tool calls and collect results
        tool_results = self._execute_tool_calls(initial_response, tool_manager)
        
        # Add tool results as single message
        if tool_results:
            messages.append({"role": "user", "content": tool_results})
        
        # Prepare final API call without tools (legacy behavior)
        final_params = {
            **self.base_params,
            "messages": messages,
            "system": base_params["system"]
        }
        
        # Get final response
        final_response = self.client.messages.create(**final_params)
        return final_response.content[0].text