import warnings
warnings.filterwarnings("ignore", message="resource_tracker: There appear to be.*")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os

from config import config
from rag_system import RAGSystem
from web_browser_tool import web_browser_tool

# Initialize FastAPI app
app = FastAPI(title="Course Materials RAG System", root_path="")

# Add trusted host middleware for proxy
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]
)

# Enable CORS with proper settings for proxy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Initialize RAG system
rag_system = RAGSystem(config)

# Pydantic models for request/response
class QueryRequest(BaseModel):
    """Request model for course queries"""
    query: str
    session_id: Optional[str] = None

class SourceInfo(BaseModel):
    """Source information with title and optional URL"""
    title: str
    url: Optional[str] = None

class QueryResponse(BaseModel):
    """Response model for course queries"""
    answer: str
    sources: List[SourceInfo]
    session_id: str

class WebBrowseRequest(BaseModel):
    """Request model for web browsing"""
    url: str
    extract_content: bool = True
    search_terms: Optional[List[str]] = None

class WebBrowseResponse(BaseModel):
    """Response model for web browsing"""
    success: bool
    url: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    links: Optional[List[Dict[str, str]]] = None
    error: Optional[str] = None

class CourseStats(BaseModel):
    """Response model for course statistics"""
    total_courses: int
    course_titles: List[str]

# API Endpoints

@app.post("/api/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Process a query and return response with sources"""
    try:
        # Create session if not provided
        session_id = request.session_id
        if not session_id:
            session_id = rag_system.session_manager.create_session()
        
        # Process query using RAG system
        answer, sources = rag_system.query(request.query, session_id)
        
        # Convert sources to SourceInfo objects
        source_objects = []
        for source in sources:
            if isinstance(source, dict):
                source_objects.append(SourceInfo(
                    title=source.get("title", "Unknown Source"),
                    url=source.get("url")
                ))
            else:
                # Fallback for string sources (backward compatibility)
                source_objects.append(SourceInfo(title=str(source)))
        
        return QueryResponse(
            answer=answer,
            sources=source_objects,
            session_id=session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/courses", response_model=CourseStats)
async def get_course_stats():
    """Get course analytics and statistics"""
    try:
        analytics = rag_system.get_course_analytics()
        return CourseStats(
            total_courses=analytics["total_courses"],
            course_titles=analytics["course_titles"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/web/browse", response_model=WebBrowseResponse)
async def browse_web_content(request: WebBrowseRequest):
    """Browse web content using Playwright MCP"""
    try:
        if request.search_terms:
            result = await web_browser_tool.search_content(request.url, request.search_terms)
        else:
            result = await web_browser_tool.browse_url(request.url, request.extract_content)
        
        if result.get("success"):
            return WebBrowseResponse(
                success=True,
                url=result.get("url"),
                title=result.get("title"),
                content=result.get("content"),
                links=result.get("links")
            )
        else:
            return WebBrowseResponse(
                success=False,
                error=result.get("error", "Unknown error occurred")
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/web/extract-course")
async def extract_course_content(request: WebBrowseRequest):
    """Extract structured course content from URL"""
    try:
        result = await web_browser_tool.extract_course_content(request.url)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a specific session and its history"""
    try:
        rag_system.session_manager.delete_session(session_id)
        return {"message": "Session deleted successfully", "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup_event():
    """Load initial documents on startup and initialize web browser"""
    # Initialize web browser tool
    try:
        await web_browser_tool.initialize()
        print("Web browser tool initialized successfully")
    except Exception as e:
        print(f"Warning: Could not initialize web browser tool: {e}")
    
    # Load documents
    import os
    docs_path = os.path.join(os.path.dirname(__file__), "..", "docs")
    print(f"Looking for docs at: {docs_path}")
    if os.path.exists(docs_path):
        print("Loading initial documents...")
        try:
            courses, chunks = rag_system.add_course_folder(docs_path, clear_existing=False)
            print(f"Loaded {courses} courses with {chunks} chunks")
        except Exception as e:
            print(f"Error loading documents: {e}")
    else:
        print(f"Docs path not found: {docs_path}")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    try:
        await web_browser_tool.close()
        print("Web browser tool cleaned up")
    except Exception as e:
        print(f"Error during web browser cleanup: {e}")

# Custom static file handler with no-cache headers for development
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from pathlib import Path


class DevStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        if isinstance(response, FileResponse):
            # Add no-cache headers for development
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response
    
    
# Serve static files for the frontend
import os
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)