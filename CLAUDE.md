# CLAUDE.md - Complete RAG Chatbot System Reference

> **Purpose**: This file serves as a comprehensive reference for understanding the complete RAG (Retrieval-Augmented Generation) chatbot system. It provides context, architecture, and implementation details for AI assistants working with this codebase.

## 📋 **System Overview**

### **Project Type**: Course Materials RAG Chatbot
### **Architecture**: Full-stack web application with AI-powered Q&A
### **Primary Function**: Answer questions about course materials using semantic search + Claude AI

---

## 🏗️ **Architecture Summary**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Data Layer    │
│   (HTML/CSS/JS) │◄──►│   (FastAPI)     │◄──►│   (ChromaDB)    │
│                 │    │                 │    │                 │
│ • User Interface│    │ • RAG System    │    │ • Vector Store  │
│ • Chat UI       │    │ • AI Integration│    │ • Course Data   │
│ • API Calls     │    │ • Search Tools  │    │ • Embeddings    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  External APIs  │
                       │                 │
                       │ • Anthropic     │
                       │   Claude API    │
                       └─────────────────┘
```

---

## 📁 **File Structure & Components**

### **Root Directory**
- `main.py` - Simple entry point (currently minimal)
- `pyproject.toml` - Python dependencies and project config
- `README.md` - Setup and usage instructions
- `run.sh` - Shell script to start the application
- `.env.example` - Environment variables template
- `uv.lock` - Dependency lock file

### **Backend Directory (`/backend/`)**
- `app.py` - **FastAPI server and API endpoints**
- `rag_system.py` - **Main orchestrator for RAG functionality**
- `ai_generator.py` - **Anthropic Claude API integration**
- `document_processor.py` - **Course document parsing and chunking**
- `vector_store.py` - **ChromaDB integration for semantic search**
- `search_tools.py` - **Tool-based search system for AI**
- `session_manager.py` - **Conversation history management**
- `models.py` - **Pydantic data models**
- `config.py` - **Configuration management**

### **Frontend Directory (`/frontend/`)**
- `index.html` - **Main web interface**
- `script.js` - **JavaScript for chat functionality**
- `style.css` - **UI styling**

### **Documents Directory (`/docs/`)**
- `course1_script.txt` - "Building Towards Computer Use with Anthropic"
- `course2_script.txt` - "MCP: Build Rich-Context AI Apps with Anthropic"
- `course3_script.txt` - Additional course content
- `course4_script.txt` - Additional course content

---

## 🔄 **Complete Request Flow**

### **1. User Interaction** (`frontend/script.js`)
```javascript
// User types query → sendMessage() → POST /api/query
{
  "query": "user question",
  "session_id": "session_123" // optional
}
```

### **2. API Endpoint** (`backend/app.py`)
```python
@app.post("/api/query")
async def query_documents(request: QueryRequest):
    # Session management
    # Forward to RAG system
    # Return structured response
```

### **3. RAG Orchestration** (`backend/rag_system.py`)
```python
def query(self, query: str, session_id: Optional[str] = None):
    # Get conversation history
    # Call AI generator with tools
    # Track sources and update session
```

### **4. AI Processing** (`backend/ai_generator.py`)
```python
def generate_response(self, query, tools=None, tool_manager=None):
    # Build system prompt with context
    # Call Claude API with tools
    # Handle tool execution if needed
```

### **5. Tool Execution** (`backend/search_tools.py`)
```python
def execute(self, query: str, course_name=None, lesson_number=None):
    # Perform semantic search
    # Format results with context
    # Track sources for UI display
```

### **6. Vector Search** (`backend/vector_store.py`)
```python
def search(self, query: str, course_name=None, lesson_number=None):
    # Course name resolution (fuzzy matching)
    # ChromaDB semantic search
    # Return formatted results
```

---

## 🤖 **AI Integration Details**

### **Claude API Configuration**
- **Model**: `claude-sonnet-4-20250514`
- **Temperature**: 0 (deterministic responses)
- **Max Tokens**: 800
- **Tool Usage**: Automatic tool selection

### **System Prompt Strategy**
```python
SYSTEM_PROMPT = """You are an AI assistant specialized in course materials...
- Use search tool for specific course content questions
- One search per query maximum
- Provide direct, educational answers
- Include examples when helpful
"""
```

### **Tool-Based Architecture**
- **Tool Definition**: `search_course_content` with schema
- **Smart Execution**: AI decides when to search vs. direct response
- **Source Tracking**: Automatic source attribution for UI

---

## 🗄️ **Data Processing Pipeline**

### **Document Structure Expected**
```
Course Title: [Course Name]
Course Link: [URL]
Course Instructor: [Instructor Name]

Lesson 0: [Lesson Title]
Lesson Link: [URL]
[Lesson content...]

Lesson 1: [Next Lesson Title]
...
```

### **Processing Steps**
1. **Document Reading** - UTF-8 with fallback encoding
2. **Metadata Extraction** - Course title, instructor, lessons
3. **Content Chunking** - 800 chars with 100 char overlap
4. **Context Enhancement** - Add course/lesson prefixes
5. **Vector Storage** - ChromaDB with embeddings
6. **Dual Collections**:
   - `course_catalog` - Course metadata
   - `course_content` - Searchable chunks

### **Embedding Model**
- **Model**: `all-MiniLM-L6-v2` (384 dimensions)
- **Provider**: Sentence Transformers
- **Search Limit**: 5 most relevant chunks

---

## 🔧 **Configuration & Environment**

### **Required Environment Variables**
```bash
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### **Key Configuration Values** (`backend/config.py`)
```python
ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
MAX_RESULTS = 5
MAX_HISTORY = 2
CHROMA_PATH = "./chroma_db"
```

### **Dependencies** (`pyproject.toml`)
```python
dependencies = [
    "chromadb==1.0.15",
    "anthropic==0.58.2", 
    "sentence-transformers==5.0.0",
    "fastapi==0.116.1",
    "uvicorn==0.35.0",
    "python-multipart==0.0.20",
    "python-dotenv==1.1.1",
]
```

---

## 🎯 **Key Features & Capabilities**

### **Smart Search Features**
- **Course Name Resolution**: Fuzzy matching ("MCP" → full course title)
- **Lesson Filtering**: Search within specific lessons
- **Semantic Search**: Vector similarity, not just keywords
- **Context Preservation**: Chunk overlap maintains coherence

### **Session Management**
- **Conversation History**: Last 2 exchanges remembered
- **Session Persistence**: Maintains context across queries
- **Memory Limit**: Configurable history length

### **UI Features**
- **Real-time Chat**: Async communication
- **Source Display**: Collapsible sources section
- **Loading States**: User feedback during processing
- **Suggested Questions**: Pre-built queries for exploration
- **Course Statistics**: Dynamic course count and titles

### **Error Handling**
- **Graceful Degradation**: Handles missing data/API failures
- **User Feedback**: Clear error messages at each layer
- **Recovery Mechanisms**: Fallback responses when search fails

---

## 🚀 **Running the Application**

### **Development Setup**
```bash
# 1. Install dependencies
uv sync

# 2. Set up environment
echo "ANTHROPIC_API_KEY=your_key" > .env

# 3. Start server
cd backend && uv run uvicorn app:app --reload --port 8000
```

### **Application URLs**
- **Main Interface**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/courses

### **Expected Startup Sequence**
1. Load course documents from `/docs/`
2. Process and chunk content
3. Build vector embeddings
4. Start FastAPI server
5. Serve frontend at root URL

---

## 🔍 **API Endpoints**

### **POST /api/query**
```json
{
  "query": "What is MCP?",
  "session_id": "optional_session_id"
}
```
**Response:**
```json
{
  "answer": "MCP (Model Context Protocol) is...",
  "sources": ["Course Title - Lesson 1", "Course Title - Lesson 2"],
  "session_id": "session_123"
}
```

### **GET /api/courses**
```json
{
  "total_courses": 4,
  "course_titles": [
    "Building Towards Computer Use with Anthropic",
    "MCP: Build Rich-Context AI Apps with Anthropic",
    ...
  ]
}
```

---

## 🎨 **Frontend Implementation**

### **Chat Interface Features**
- **Message History**: Persistent chat display
- **Markdown Rendering**: Rich text responses using marked.js
- **Source Attribution**: Clickable, collapsible sources
- **Auto-scroll**: Smooth scroll to new messages
- **Input Management**: Disable during processing

### **JavaScript Architecture**
```javascript
// Global state management
let currentSessionId = null;

// Core functions
async function sendMessage()     // Handle user input
function addMessage()           // Display messages
async function loadCourseStats() // Update sidebar
```

---

## 📊 **Performance Characteristics**

### **Response Times** (Typical)
- **Direct Response**: ~1-2 seconds
- **With Search**: ~3-5 seconds
- **Document Loading**: ~10-30 seconds (startup)

### **Scalability Considerations**
- **Vector Store**: ChromaDB handles thousands of chunks efficiently
- **Session Memory**: Limited to prevent memory bloat
- **Concurrent Users**: FastAPI async handling
- **API Rate Limits**: Anthropic API constraints apply

---

## 🛠️ **Development Guidelines**

### **When Working with This Codebase:**

1. **Understanding Flow**: Always trace user query → API → RAG → AI → Tools → Vector Store
2. **Session Context**: Consider conversation history in responses
3. **Error Handling**: Check each layer for graceful failures
4. **Source Tracking**: Ensure UI gets proper source attribution
5. **Tool Integration**: AI decides when to search vs. direct response

### **Key Extension Points**
- **New Tools**: Add to `search_tools.py` following Tool interface
- **New Data Sources**: Extend `document_processor.py` for different formats
- **UI Enhancements**: Modify `frontend/` files for new features
- **AI Behavior**: Adjust system prompt in `ai_generator.py`

---

## 🧪 **Testing & Validation**

### **Sample Queries for Testing**
- Course overview: "What is the outline of the MCP course?"
- Specific content: "What was covered in lesson 5 of the MCP course?"
- Cross-course: "Are there any courses about chatbots?"
- Technical: "How does RAG work according to the courses?"

### **Expected Behaviors**
- **Course Resolution**: "MCP" should match full course title
- **Source Attribution**: Always show which course/lesson
- **Context Awareness**: Follow-up questions use conversation history
- **Graceful Failures**: Handle missing content with helpful messages

---

## 🎯 **AI Assistant Usage Notes**

### **For AI Assistants Working with This Code:**

1. **Always Reference This File**: Use CLAUDE.md for complete context
2. **Understand the Flow**: Follow the request pipeline when debugging
3. **Consider All Layers**: Frontend → API → RAG → AI → Tools → Data
4. **Preserve Architecture**: Maintain tool-based, async design patterns
5. **Test Thoroughly**: Verify changes work end-to-end

### **Common Modification Patterns**
- **Adding Features**: Extend existing components rather than rewrite
- **Configuration Changes**: Use `config.py` for system settings
- **UI Updates**: Maintain async patterns and error handling
- **API Changes**: Update both backend and frontend consistently

---

## 📚 **Related Documentation**

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **ChromaDB Docs**: https://docs.trychroma.com/
- **Anthropic API**: https://docs.anthropic.com/
- **Sentence Transformers**: https://www.sbert.net/

---

**Last Updated**: September 24, 2025
**Version**: 1.0
**Maintainer**: AI Assistant (Claude)

> **Note**: This file serves as the primary reference for understanding the complete RAG chatbot system. Always consult this file when working with the codebase to maintain consistency and understand the full context of the application.