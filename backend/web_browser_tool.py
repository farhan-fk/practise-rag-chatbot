"""
Web scraping tools using Playwright MCP integration
Provides web browsing capabilities for the RAG system
"""

import asyncio
from typing import Dict, Any, Optional, List
from .playwright_mcp import playwright_mcp
import logging

logger = logging.getLogger(__name__)

class WebBrowserTool:
    """Web browsing tool for RAG system using Playwright MCP"""
    
    def __init__(self):
        self.mcp_server = playwright_mcp
        self.is_ready = False
    
    async def initialize(self):
        """Initialize the web browser tool"""
        try:
            await self.mcp_server.initialize()
            self.is_ready = True
            logger.info("WebBrowserTool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize WebBrowserTool: {e}")
            self.is_ready = False
    
    async def browse_url(self, url: str, extract_text: bool = True) -> Dict[str, Any]:
        """Browse to a URL and extract content"""
        if not self.is_ready:
            await self.initialize()
        
        if not self.is_ready:
            return {"success": False, "error": "Browser tool not ready"}
        
        try:
            # Navigate to URL
            nav_result = await self.mcp_server.navigate_to_url(url)
            if not nav_result.get("success"):
                return nav_result
            
            result = {
                "success": True,
                "url": nav_result["url"],
                "title": nav_result["title"]
            }
            
            # Extract text content if requested
            if extract_text:
                text_result = await self.mcp_server.extract_text()
                if text_result.get("success"):
                    result["content"] = text_result["text"]
                    result["content_length"] = text_result["length"]
            
            # Extract links
            links_result = await self.mcp_server.extract_links()
            if links_result.get("success"):
                result["links"] = links_result["links"]
                result["link_count"] = links_result["count"]
            
            return result
            
        except Exception as e:
            logger.error(f"Error browsing URL {url}: {e}")
            return {"success": False, "error": str(e)}
    
    async def search_content(self, url: str, search_terms: List[str]) -> Dict[str, Any]:
        """Search for specific terms in web content"""
        browse_result = await self.browse_url(url, extract_text=True)
        
        if not browse_result.get("success"):
            return browse_result
        
        content = browse_result.get("content", "").lower()
        
        # Search for terms
        found_terms = []
        term_contexts = {}
        
        for term in search_terms:
            term_lower = term.lower()
            if term_lower in content:
                found_terms.append(term)
                
                # Extract context around the term (50 chars before and after)
                term_index = content.find(term_lower)
                start = max(0, term_index - 50)
                end = min(len(content), term_index + len(term_lower) + 50)
                context = content[start:end].strip()
                term_contexts[term] = context
        
        return {
            "success": True,
            "url": browse_result["url"],
            "title": browse_result["title"],
            "found_terms": found_terms,
            "term_contexts": term_contexts,
            "total_terms_found": len(found_terms)
        }
    
    async def extract_course_content(self, course_url: str) -> Dict[str, Any]:
        """Extract structured content from course pages"""
        browse_result = await self.browse_url(course_url)
        
        if not browse_result.get("success"):
            return browse_result
        
        try:
            # Try to extract structured course information
            course_data = await self.mcp_server.evaluate_javascript("""
                () => {
                    const result = {
                        headings: [],
                        paragraphs: [],
                        code_blocks: [],
                        lists: []
                    };
                    
                    // Extract headings
                    document.querySelectorAll('h1, h2, h3, h4, h5, h6').forEach(h => {
                        result.headings.push({
                            level: h.tagName.toLowerCase(),
                            text: h.innerText.trim()
                        });
                    });
                    
                    // Extract paragraphs
                    document.querySelectorAll('p').forEach(p => {
                        const text = p.innerText.trim();
                        if (text.length > 20) {
                            result.paragraphs.push(text);
                        }
                    });
                    
                    // Extract code blocks
                    document.querySelectorAll('pre, code').forEach(code => {
                        const text = code.innerText.trim();
                        if (text.length > 5) {
                            result.code_blocks.push(text);
                        }
                    });
                    
                    // Extract lists
                    document.querySelectorAll('ul, ol').forEach(list => {
                        const items = Array.from(list.querySelectorAll('li')).map(li => li.innerText.trim());
                        if (items.length > 0) {
                            result.lists.push(items);
                        }
                    });
                    
                    return result;
                }
            """)
            
            if course_data.get("success"):
                return {
                    "success": True,
                    "url": browse_result["url"],
                    "title": browse_result["title"],
                    "structured_content": course_data["result"],
                    "raw_content": browse_result.get("content", "")
                }
            else:
                return {
                    "success": True,
                    "url": browse_result["url"],
                    "title": browse_result["title"],
                    "raw_content": browse_result.get("content", ""),
                    "note": "Could not extract structured content"
                }
                
        except Exception as e:
            logger.error(f"Error extracting course content: {e}")
            return {
                "success": True,
                "url": browse_result["url"],
                "title": browse_result["title"],
                "raw_content": browse_result.get("content", ""),
                "error": str(e)
            }
    
    async def close(self):
        """Clean up browser resources"""
        if self.is_ready:
            await self.mcp_server.close()
            self.is_ready = False

# Global instance
web_browser_tool = WebBrowserTool()