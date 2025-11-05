"""
Internet Search Agent - DuckDuckGo Integration
Searches official websites for insurance policies
100% Free - No API key needed!
Version: 1.0
"""

import logging
from typing import Dict, List
from datetime import datetime
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)


class InternetSearchAgent:
    """
    Agent to search internet for insurance policies
    Uses DuckDuckGo - Free, no API key required
    """
    
    def __init__(self):
        """Initialize search agent"""
        self.ddg = DDGS()
        logger.info("✅ Internet Search Agent initialized (DuckDuckGo)")
    
    def search_policies(self, disease: str, procedure: str, icd_code: str = None) -> Dict:
        """
        Search internet for insurance policies
        
        Args:
            disease: Disease name (e.g., "chronic lower back pain")
            procedure: Procedure name (e.g., "Lumbar MRI")
            icd_code: ICD-10 code (e.g., "M54.5")
            
        Returns:
            Dict with search results
        """
        
        try:
            logger.info(f"🔍 Searching internet for: {procedure} policy")
            
            # Build search queries
            queries = self._build_search_queries(disease, procedure, icd_code)
            
            all_results = []
            
            for query in queries:
                try:
                    logger.info(f"   Query: {query}")
                    
                    # Search with DuckDuckGo
                    results = self.ddg.text(
                        query,
                        max_results=3,
                        region='wt-wt'  # worldwide
                    )
                    
                    if results:
                        logger.info(f"   ✅ Found {len(results)} results")
                        all_results.extend(results)
                    else:
                        logger.warning(f"   ⚠️ No results for: {query}")
                
                except Exception as e:
                    logger.warning(f"   ⚠️ Search failed for '{query}': {e}")
                    continue
            
            # Format results
            formatted = self._format_results(all_results, procedure)
            
            logger.info(f"✅ Search complete: {len(formatted['policies'])} policies found")
            
            return formatted
        
        except Exception as e:
            logger.error(f"❌ Error in search: {e}")
            return {
                "policies": [],
                "search_queries": [],
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _build_search_queries(self, disease: str, procedure: str, icd_code: str) -> List[str]:
        """Build search queries targeting official policy sites"""
        
        queries = []
        
        # Query 1: CMS NCD
        queries.append(f"site:cms.gov {procedure} coverage policy")
        
        # Query 2: Medicare
        queries.append(f"site:medicare.gov {procedure} coverage criteria")
        
        # Query 3: General policy search
        queries.append(f"{procedure} insurance coverage policy chronic pain")
        
        # Query 4: ICD specific
        if icd_code:
            queries.append(f"{procedure} {icd_code} medical necessity criteria")
        
        return queries
    
    def _format_results(self, results: List[Dict], procedure: str) -> Dict:
        """Format search results for display"""
        
        formatted_policies = []
        seen_urls = set()
        
        for result in results:
            try:
                url = result.get('href', '')
                
                # Skip duplicates
                if url in seen_urls:
                    continue
                
                seen_urls.add(url)
                
                # Only keep relevant domains
                if not self._is_relevant_domain(url):
                    continue
                
                # Extract and clean data
                title = result.get('title', 'Policy Document')
                snippet = result.get('body', '')
                
                # Clean text
                snippet = self._clean_text(snippet, max_len=200)
                
                policy = {
                    "source": self._extract_source(url),
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                    "domain": self._extract_domain(url),
                    "fetch_timestamp": datetime.now().isoformat(),
                    "source_type": "INTERNET_SEARCH"
                }
                
                formatted_policies.append(policy)
                
            except Exception as e:
                logger.warning(f"Error formatting result: {e}")
                continue
        
        return {
            "policies": formatted_policies,
            "total_found": len(formatted_policies),
            "timestamp": datetime.now().isoformat(),
            "search_method": "DuckDuckGo Internet Search"
        }
    
    def _is_relevant_domain(self, url: str) -> bool:
        """Check if URL is from relevant/trusted domain"""
        
        trusted_domains = [
            'cms.gov',
            'medicare.gov',
            'medicaid.gov',
            'nih.gov',
            'ncbi.nlm.nih.gov',
            'cdc.gov',
            'fda.gov',
            'ahrq.gov',
            'healthcare.gov'
        ]
        
        return any(domain in url.lower() for domain in trusted_domains)
    
    def _extract_source(self, url: str) -> str:
        """Extract source name from URL"""
        
        if 'cms.gov' in url:
            return "CMS National Coverage"
        elif 'medicare.gov' in url:
            return "Medicare Official"
        elif 'nih.gov' in url or 'ncbi.nlm.nih.gov' in url:
            return "NIH Medical Guidelines"
        elif 'medicaid.gov' in url:
            return "Medicaid Coverage"
        else:
            return "Healthcare Policy"
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return url.split('/')[2] if '/' in url else url
    
    def _clean_text(self, text: str, max_len: int = 200) -> str:
        """Clean and format text"""
        
        if not text:
            return ""
        
        # Remove extra whitespace
        text = " ".join(text.split())
        
        # Fix common OCR errors
        text = text.replace("sub ject", "subject")
        text = text.replace("conservativ e", "conservative")
        text = text.replace("in tervention", "intervention")
        
        # Limit length
        if len(text) > max_len:
            text = text[:max_len].rsplit(' ', 1)[0] + "..."
        
        return text.strip()
