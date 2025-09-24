# RAG Chatbot Query Processing Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                 🌐 FRONTEND (script.js)                              │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  👤 User Input                                                                      │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐                        │
│  │ Text Input  │ -> │ Send Button  │ -> │ Event Listener  │                        │
│  └─────────────┘    └──────────────┘    └─────────────────┘                        │
│                                                 │                                    │
│  🔄 UI State Management                         ▼                                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                     │
│  │ Disable Input   │  │ Show Loading    │  │ Add User Msg    │                     │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                     │
│                                                 │                                    │
│  📡 HTTP Request                               ▼                                    │
│  ┌─────────────────────────────────────────────────────────────────┐               │
│  │ POST /api/query                                                 │               │
│  │ {                                                               │               │
│  │   "query": "user question",                                     │               │
│  │   "session_id": "session_123"                                   │               │
│  │ }                                                               │               │
│  └─────────────────────────────────────────────────────────────────┘               │
└─────────────────────────────────────────┬───────────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              🚀 FASTAPI SERVER (app.py)                             │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  📨 Request Reception                                                               │
│  ┌─────────────────────────────────────────────────────────────────┐               │
│  │ @app.post("/api/query")                                         │               │
│  │ async def query_documents(request: QueryRequest)                │               │
│  └─────────────────────────────────────────────────────────────────┘               │
│                                          │                                          │
│  🔑 Session Management                   ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐               │
│  │ if not session_id:                                              │               │
│  │     session_id = rag_system.session_manager.create_session()    │               │
│  └─────────────────────────────────────────────────────────────────┘               │
│                                          │                                          │
│  🎯 Query Forwarding                     ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐               │
│  │ answer, sources = rag_system.query(request.query, session_id)   │               │
│  └─────────────────────────────────────────────────────────────────┘               │
└─────────────────────────────────────────┬───────────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        🧠 RAG SYSTEM ORCHESTRATION (rag_system.py)                  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  📝 Query Processing Entry                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐               │
│  │ def query(self, query: str, session_id: Optional[str] = None):   │               │
│  │     prompt = f"Answer this question: {query}"                   │               │
│  └─────────────────────────────────────────────────────────────────┘               │
│                                          │                                          │
│  📚 History Retrieval                    ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐               │
│  │ history = session_manager.get_conversation_history(session_id)   │               │
│  └─────────────────────────────────────────────────────────────────┘               │
│                                          │                                          │
│  🔧 Tool Preparation                     ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐               │
│  │ tools = tool_manager.get_tool_definitions()                     │               │
│  └─────────────────────────────────────────────────────────────────┘               │
│                                          │                                          │
│  🤖 AI Response Generation               ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐               │
│  │ response = ai_generator.generate_response(                      │               │
│  │     query=prompt,                                               │               │
│  │     conversation_history=history,                               │               │
│  │     tools=tools,                                                │               │
│  │     tool_manager=tool_manager                                   │               │
│  │ )                                                               │               │
│  └─────────────────────────────────────────────────────────────────┘               │
└─────────────────────────────────────────┬───────────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           🤖 AI GENERATOR (ai_generator.py)                          │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  🧩 System Prompt + Context                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐               │
│  │ SYSTEM_PROMPT = "You are an AI assistant specialized in..."     │               │
│  │ + Previous conversation history                                 │               │
│  └─────────────────────────────────────────────────────────────────┘               │
│                                          │                                          │
│  🔗 Claude API Call                      ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐               │
│  │ response = client.messages.create(                              │               │
│  │     model="claude-sonnet-4-20250514",                          │               │
│  │     messages=[{"role": "user", "content": query}],             │               │
│  │     system=system_content,                                      │               │
│  │     tools=tools,                                                │               │
│  │     tool_choice={"type": "auto"}                                │               │
│  │ )                                                               │               │
│  └─────────────────────────────────────────────────────────────────┘               │
│                                          │                                          │
│  ❓ Tool Usage Decision                  ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐               │
│  │ if response.stop_reason == "tool_use":                          │───┐           │
│  │     return _handle_tool_execution()                             │   │           │
│  │ else:                                                           │   │           │
│  │     return response.content[0].text                             │   │           │
│  └─────────────────────────────────────────────────────────────────┘   │           │
└─────────────────────────────────────────────────────────────────────────┼───────────┘
                                                                          │
                                                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         🔧 TOOL EXECUTION (search_tools.py)                         │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  🛠️ Tool Manager                                                                   │
│  ┌─────────────────────────────────────────────────────────────────┐               │
│  │ def execute_tool(self, tool_name: str, **kwargs):               │               │
│  │     return self.tools[tool_name].execute(**kwargs)              │               │
│  └─────────────────────────────────────────────────────────────────┘               │
│                                          │                                          │
│  🔍 Course Search Tool                   ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐               │
│  │ Tool Definition:                                                │               │
│  │ {                                                               │               │
│  │   "name": "search_course_content",                              │               │
│  │   "description": "Search course materials...",                 │               │
│  │   "input_schema": {                                             │               │
│  │     "properties": {                                             │               │
│  │       "query": {"type": "string"},                             │               │
│  │       "course_name": {"type": "string"},                       │               │
│  │       "lesson_number": {"type": "integer"}                     │               │
│  │     }                                                           │               │
│  │   }                                                             │               │
│  │ }                                                               │               │
│  └─────────────────────────────────────────────────────────────────┘               │
│                                          │                                          │
│  ⚡ Tool Execution                       ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐               │
│  │ def execute(self, query, course_name=None, lesson_number=None): │               │
│  │     results = self.store.search(                                │               │
│  │         query=query,                                            │               │
│  │         course_name=course_name,                                │               │
│  │         lesson_number=lesson_number                             │               │
│  │     )                                                           │               │
│  │     return self._format_results(results)                       │               │
│  └─────────────────────────────────────────────────────────────────┘               │
└─────────────────────────────────────────┬───────────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        🗄️ VECTOR STORE SEARCH (vector_store.py)                     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  🎯 Smart Search Process                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐               │
│  │ 1. Course Name Resolution (fuzzy matching)                      │               │
│  │    ┌───────────────────────────────────────────────┐            │               │
│  │    │ "MCP" -> "MCP: Build Rich-Context AI Apps..." │            │               │
│  │    └───────────────────────────────────────────────┘            │               │
│  │                                                                 │               │
│  │ 2. Filter Building                                              │               │
│  │    ┌───────────────────────────────────────────────┐            │               │
│  │    │ {"course_title": "resolved_name",              │            │               │
│  │    │  "lesson_number": 5}                           │            │               │
│  │    └───────────────────────────────────────────────┘            │               │
│  │                                                                 │               │
│  │ 3. Vector Similarity Search                                     │               │
│  │    ┌───────────────────────────────────────────────┐            │               │
│  │    │ ChromaDB Semantic Search:                     │            │               │
│  │    │ - Convert query to 384D vector                │            │               │
│  │    │ - Find top 5 similar chunks                   │            │               │
│  │    │ - Apply course/lesson filters                 │            │               │
│  │    └───────────────────────────────────────────────┘            │               │
│  └─────────────────────────────────────────────────────────────────┘               │
│                                          │                                          │
│  🔍 ChromaDB Query                       ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐               │
│  │ results = self.course_content.query(                            │               │
│  │     query_texts=[query],                                        │               │
│  │     n_results=5,                                                │               │
│  │     where=filter_dict                                           │               │
│  │ )                                                               │               │
│  └─────────────────────────────────────────────────────────────────┘               │
│                                          │                                          │
│  📊 Results Structure                    ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐               │
│  │ SearchResults:                                                  │               │
│  │ - documents: ["chunk1", "chunk2", ...]                         │               │
│  │ - metadata: [{"course_title": "...", "lesson_number": ...}, ]  │               │
│  │ - distances: [0.2, 0.4, 0.6, ...]                             │               │
│  └─────────────────────────────────────────────────────────────────┘               │
└─────────────────────────────────────────┬───────────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                      🔄 RESPONSE ASSEMBLY & FORMATTING                              │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  📝 Results Formatting                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐               │
│  │ def _format_results(self, results):                             │               │
│  │     formatted = []                                              │               │
│  │     sources = []                                                │               │
│  │                                                                 │               │
│  │     for doc, meta in zip(results.documents, results.metadata): │               │
│  │         course_title = meta.get('course_title')                │               │
│  │         lesson_num = meta.get('lesson_number')                 │               │
│  │                                                                 │               │
│  │         header = f"[{course_title} - Lesson {lesson_num}]"     │               │
│  │         sources.append(f"{course_title} - Lesson {lesson_num}")│               │
│  │         formatted.append(f"{header}\n{doc}")                   │               │
│  │                                                                 │               │
│  │     self.last_sources = sources                                 │               │
│  │     return "\n\n".join(formatted)                              │               │
│  └─────────────────────────────────────────────────────────────────┘               │
│                                          │                                          │
│  🔙 Return to AI Generator               ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐               │
│  │ Tool Result: "[Course Title - Lesson X]\nRelevant content..."   │               │
│  └─────────────────────────────────────────────────────────────────┘               │
└─────────────────────────────────────────┬───────────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                      🤖 FINAL AI RESPONSE GENERATION                                │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  🔧 Tool Results Integration                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐               │
│  │ messages.append({                                               │               │
│  │     "role": "assistant",                                        │               │
│  │     "content": initial_response.content                         │               │
│  │ })                                                              │               │
│  │                                                                 │               │
│  │ tool_results.append({                                           │               │
│  │     "type": "tool_result",                                      │               │
│  │     "tool_use_id": content_block.id,                           │               │
│  │     "content": tool_result                                      │               │
│  │ })                                                              │               │
│  └─────────────────────────────────────────────────────────────────┘               │
│                                          │                                          │
│  🎯 Final Claude API Call                ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐               │
│  │ final_response = client.messages.create(                        │               │
│  │     messages=updated_messages_with_tool_results                 │               │
│  │ )                                                               │               │
│  │                                                                 │               │
│  │ return final_response.content[0].text                           │               │
│  └─────────────────────────────────────────────────────────────────┘               │
└─────────────────────────────────────────┬───────────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                    📝 SESSION & HISTORY MANAGEMENT                                  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  💾 Conversation Storage                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐               │
│  │ session_manager.add_exchange(                                   │               │
│  │     session_id,                                                 │               │
│  │     user_query,                                                 │               │
│  │     ai_response                                                 │               │
│  │ )                                                               │               │
│  └─────────────────────────────────────────────────────────────────┘               │
│                                          │                                          │
│  🏷️ Source Tracking                     ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐               │
│  │ sources = tool_manager.get_last_sources()                       │               │
│  │ tool_manager.reset_sources()                                    │               │
│  └─────────────────────────────────────────────────────────────────┘               │
│                                          │                                          │
│  📤 Response Return                      ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐               │
│  │ return (response, sources)                                      │               │
│  └─────────────────────────────────────────────────────────────────┘               │
└─────────────────────────────────────────┬───────────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        📤 RESPONSE RETURN PATH                                      │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  🚀 FastAPI Response                                                               │
│  ┌─────────────────────────────────────────────────────────────────┐               │
│  │ return QueryResponse(                                           │               │
│  │     answer=answer,                                              │               │
│  │     sources=sources,                                            │               │
│  │     session_id=session_id                                       │               │
│  │ )                                                               │               │
│  └─────────────────────────────────────────────────────────────────┘               │
│                                          │                                          │
│  📡 HTTP Response                        ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐               │
│  │ {                                                               │               │
│  │   "answer": "Based on the course materials...",                │               │
│  │   "sources": ["Course Title - Lesson 1", "Course Title..."],   │               │
│  │   "session_id": "session_123"                                   │               │
│  │ }                                                               │               │
│  └─────────────────────────────────────────────────────────────────┘               │
└─────────────────────────────────────────┬───────────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        🎨 FRONTEND UI UPDATES                                       │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  📨 Response Handling                                                              │
│  ┌─────────────────────────────────────────────────────────────────┐               │
│  │ const data = await response.json();                             │               │
│  │                                                                 │               │
│  │ // Update session ID if new                                     │               │
│  │ if (!currentSessionId) {                                        │               │
│  │     currentSessionId = data.session_id;                         │               │
│  │ }                                                               │               │
│  └─────────────────────────────────────────────────────────────────┘               │
│                                          │                                          │
│  🎭 UI State Updates                     ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐               │
│  │ 1. Remove loading message                                       │               │
│  │ 2. Add AI response with markdown rendering                      │               │
│  │ 3. Add collapsible sources section                              │               │
│  │ 4. Auto-scroll to new message                                   │               │
│  │ 5. Re-enable input for next query                               │               │
│  └─────────────────────────────────────────────────────────────────┘               │
│                                          │                                          │
│  ✅ Ready for Next Query                 ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐               │
│  │ chatInput.disabled = false;                                     │               │
│  │ sendButton.disabled = false;                                    │               │
│  │ chatInput.focus();                                              │               │
│  └─────────────────────────────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────────────────────────────┘

====================================================================================
                                  🔄 DATA FLOW SUMMARY
====================================================================================

1. 👤 USER QUERY → 🌐 Frontend captures input & sends POST request
2. 🚀 FASTAPI → 🧠 Routes to RAG system with session management  
3. 🧠 RAG SYSTEM → 🤖 Prepares context & calls AI with tools
4. 🤖 AI GENERATOR → 🔧 Decides to use search tool for course content
5. 🔧 TOOL EXECUTION → 🗄️ Performs semantic search in vector store
6. 🗄️ VECTOR STORE → 🔍 ChromaDB finds relevant course chunks
7. 🔄 RESULTS → 🤖 AI generates final response with context
8. 📝 STORAGE → 💾 Updates conversation history & tracks sources
9. 📤 RESPONSE → 🌐 Returns structured JSON with answer & sources
10. 🎨 UI UPDATE → ✅ Displays response with sources & enables next query

====================================================================================
                                   🎯 KEY FEATURES
====================================================================================

🔄 Asynchronous Processing    📚 Conversation Memory    🔍 Semantic Search
🎯 Smart Course Matching     🏷️ Source Attribution     🛠️ Tool-Based Architecture  
⚡ Real-time UI Feedback    📊 Session Management      🎨 Markdown Rendering
```