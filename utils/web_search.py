"""
Web Search Module for M&A Investment Teaser Generation

Search Strategy:
- Images: Unsplash API (high-quality stock photos, no API key required)
- Text Searches: Tavily API (better for business/research queries)
  - Tavily: Free tier 1,000 searches/month (get key at https://tavily.com)
  - Requires TAVILY_API_KEY in .env file

All searches use AI-generated queries based on company data for better relevance.
"""

import os
import json
import requests
from typing import List, Dict, Optional, Tuple
from PIL import Image
import io
import time
import random
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def clean_json_string(json_string):
    """Cleans the LLM output to ensure it is valid JSON."""
    if "```" in json_string:
        json_string = json_string.replace("```json", "").replace("```", "")
    return json_string.strip()

def generate_search_queries(company_name: str, company_data: str, search_type: str) -> List[str]:
    """
    Uses LLM to generate intelligent search queries based on company data.
    
    Args:
        company_name: Actual company name (will be anonymized in queries)
        company_data: Extracted text from company documents
        search_type: Type of search ("images", "certifications", "business_info", "partners")
    
    Returns:
        List of search query strings
    """
    print(f"🤖 Generating {search_type} search queries using AI...")
    
    llm = ChatGoogleGenerativeAI(
        model="models/gemini-2.5-flash-lite",
        temperature=0.7,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
    
    prompt_template = """
    You are a research assistant helping to find information about a company for an M&A investment teaser.
    
    Company Name: {company_name}
    Company Data Summary: {company_data}
    
    Task: Generate 3-5 specific search queries for finding {search_type} information.
    
    IMPORTANT RULES:
    1. For images: Generate queries for generic, anonymized images (NO company logos or names)
       - Focus on: products, manufacturing facilities, R&D labs, packaging
       - Use generic terms like "specialty chemicals manufacturing facility" not "{company_name} factory"
    2. For certifications: Extract certification names mentioned in data, or generate queries for industry-standard certifications
    3. For business_info: Generate queries about market trends, industry analysis, growth opportunities
    4. For partners: Generate queries about business partnerships, clients, suppliers in the industry
    
    Return ONLY a JSON array of query strings, no other text:
    ["query 1", "query 2", "query 3"]
    """
    
    prompt = PromptTemplate(
        input_variables=["company_name", "company_data", "search_type"],
        template=prompt_template
    )
    
    try:
        # Truncate company_data if too long (keep first 2000 chars for context)
        truncated_data = company_data[:2000] if len(company_data) > 2000 else company_data
        
        chain = prompt | llm
        response = chain.invoke({
            "company_name": company_name,
            "company_data": truncated_data,
            "search_type": search_type
        })
        
        content = response.content if hasattr(response, 'content') else str(response)
        cleaned_json = clean_json_string(content)
        queries = json.loads(cleaned_json)
        
        if isinstance(queries, list) and len(queries) > 0:
            print(f"✅ Generated {len(queries)} queries")
            return queries[:5]  # Limit to 5 queries max
        else:
            print("⚠️  LLM returned invalid format, using fallback queries")
            return generate_fallback_queries(search_type)
            
    except Exception as e:
        print(f"⚠️  Query generation error: {e}, using fallback")
        return generate_fallback_queries(search_type)

def generate_fallback_queries(search_type: str) -> List[str]:
    """Fallback queries if LLM generation fails."""
    fallbacks = {
        "images": ["generic manufacturing products stock photo", "industrial facility interior"],
        "certifications": ["ISO 9001 certification", "industry certifications"],
        "business_info": ["industry market trends", "sector growth analysis"],
        "partners": ["business partnerships", "industry collaborations"]
    }
    return fallbacks.get(search_type, ["general search"])

def search_text_tavily(query: str, max_results: int = 5) -> List[Dict]:
    """
    Search using Tavily API - better for business/research queries.
    Free tier: 1,000 searches/month
    Get API key at https://tavily.com (free signup)
    
    Args:
        query: Search query string
        max_results: Maximum number of results
    
    Returns:
        List of search results with 'title', 'body', 'href' keys
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        print("   ⚠️  TAVILY_API_KEY not found. Skipping search.")
        return []
    
    url = "https://api.tavily.com/search"
    headers = {"Content-Type": "application/json"}
    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "max_results": max_results,
        "include_answer": True,
        "include_raw_content": False
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for item in data.get('results', []):
            results.append({
                'title': item.get('title', ''),
                'body': item.get('content', ''),
                'href': item.get('url', '')
            })
        
        return results
    except requests.exceptions.RequestException as e:
        print(f"   ⚠️  Tavily API error: {e}")
        return []
    except Exception as e:
        print(f"   ⚠️  Tavily unexpected error: {e}")
        return []

def search_images(company_name: str, company_data: str, max_results: int = 5) -> Tuple[List[Dict], List[Dict]]:
    """
    Searches for high-quality, generic stock images using Unsplash API.
    No API key required for basic usage - perfect for presentation-quality images.
    
    Args:
        company_name: Company name (for context, not used in queries)
        company_data: Extracted company data
        max_results: Maximum images per query
    
    Returns:
        Tuple of (images list, citations list)
    """
    print(f"🖼️  Searching for high-quality stock images (Unsplash)...")
    
    # Generate queries using LLM
    queries = generate_search_queries(company_name, company_data, "images")
    queries = queries[:2]  # Use first 2 queries
    
    all_results = []
    citations = []
    
    # Optional: Use Unsplash API key if available (increases rate limit)
    # Get free key at https://unsplash.com/developers
    unsplash_key = os.getenv("UNSPLASH_ACCESS_KEY", None)
    
    for i, query in enumerate(queries):
        print(f"   🔍 Query {i+1}/{len(queries)}: '{query}'")
        
        try:
            # Unsplash API endpoint
            url = "https://api.unsplash.com/search/photos"
            headers = {
                "Accept-Version": "v1"
            }
            
            # Add Authorization header if API key is available
            if unsplash_key:
                headers["Authorization"] = f"Client-ID {unsplash_key}"
            
            params = {
                "query": query,
                "per_page": max_results,
                "orientation": "landscape",  # Better for presentations
                "content_filter": "high"  # High quality only
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            for photo in data.get('results', []):
                # Use 'regular' size for good quality without being too large
                image_url = photo['urls']['regular']
                # Store full resolution URL for actual download if needed
                download_url = photo['urls']['full']
                
                # Get description or alt text
                title = photo.get('description') or photo.get('alt_description') or 'Stock Photo'
                photographer = photo['user']['name']
                photographer_url = photo['user']['links']['html']
                
                all_results.append({
                    'url': image_url,
                    'download_url': download_url,  # Full resolution for download
                    'title': title,
                    'source': photo['links']['html'],
                    'photographer': photographer,
                    'photographer_url': photographer_url,
                    'type': 'generic'
                })
                citations.append({
                    'type': 'image',
                    'url': image_url,
                    'source': photo['links']['html'],
                    'description': f"Stock photo from Unsplash: {query}",
                    'photographer': photographer,
                    'photographer_url': photographer_url
                })
            
            # Small delay between queries (no rate limit issues with Unsplash)
            if i < len(queries) - 1:
                time.sleep(0.5)
            
        except requests.exceptions.RequestException as e:
            print(f"   ⚠️  Unsplash API error: {e}")
            continue
        except Exception as e:
            print(f"   ⚠️  Unexpected error: {e}")
            continue
    
    print(f"✅ Found {len(all_results)} high-quality images")
    return all_results[:max_results * 2], citations

def search_certifications(company_name: str, company_data: str) -> Tuple[List[Dict], List[Dict]]:
    """
    Searches for certifications mentioned in company data or relevant to the industry.
    
    Args:
        company_name: Company name
        company_data: Extracted company data
    
    Returns:
        Tuple of (certifications list, citations list)
    """
    print(f"🏆 Searching for certifications...")
    
    certifications = []
    citations = []
    
    # First, extract certifications from company data
    company_data_lower = company_data.lower()
    common_certs = [
        "ISO 9001", "ISO 14001", "ISO 22000", "ISO 13485", "ISO 45001",
        "GMP", "WHO-GMP", "USFDA", "CE Mark", "FSSAI", "BIS", "BRC",
        "FSSC 22000", "HACCP", "OHSAS 18001", "IATF 16949", "TS 16949",
        "USDA Organic", "Non-GMO", "RoHS", "FCC", "AEO", "GDP", "C-TPAT"
    ]
    
    found_certs = []
    for cert in common_certs:
        if cert.lower() in company_data_lower:
            found_certs.append(cert)
            certifications.append({
                'name': cert,
                'description': f"{cert} certification standard",
                'verified': True,
                'source': 'company_data'
            })
            citations.append({
                'type': 'certification',
                'name': cert,
                'source': 'company_data',
                'description': f"Certification mentioned in provided company data"
            })
    
    # Skip web search for certifications if we already found some (to avoid rate limits)
    # Only search if we found very few certifications
    if len(found_certs) == 0:
        queries = generate_search_queries(company_name, company_data, "certifications")
        
        try:
            # Only use first query
            if queries:
                query = queries[0]
                print(f"   🔍 Query: '{query}'")
                
                # Use Tavily for search
                results = search_text_tavily(query, max_results=3)
                
                for result in results:
                    body_lower = result.get('body', '').lower()
                    # Try to extract certification names from results
                    for cert in common_certs:
                        if cert.lower() in body_lower and cert not in found_certs:
                            found_certs.append(cert)
                            certifications.append({
                                'name': cert,
                                'description': result.get('body', '')[:200],
                                'verified': False,
                                'source': result.get('href', '')
                            })
                            citations.append({
                                'type': 'certification',
                                'name': cert,
                                'source': result.get('href', ''),
                                'description': f"Information about {cert} certification"
                            })
                            break
                    
        except Exception as e:
            print(f"⚠️  Certification web search error: {e}")
    
    print(f"✅ Found {len(certifications)} certifications")
    return certifications, citations

def search_business_info(company_name: str, company_data: str, max_results: int = 5) -> Dict:
    """
    Searches for business information like market trends, partners, industry insights.
    
    Args:
        company_name: Company name
        company_data: Extracted company data
        max_results: Maximum results per query
    
    Returns:
        Dict with 'market_info', 'partners', 'trends' and citations
    """
    print(f"📊 Searching for business information...")
    
    results = {
        'market_info': [],
        'partners': [],
        'trends': [],
        'citations': []
    }
    
    # Generate queries for business info (limit to 1 query each to avoid rate limits)
    business_queries = generate_search_queries(company_name, company_data, "business_info")
    partner_queries = generate_search_queries(company_name, company_data, "partners")
    
    try:
        # Search for market information (only 1 query)
        if business_queries:
            query = business_queries[0]
            print(f"   🔍 Query: '{query}'")
            
            # Use Tavily for search
            search_results = search_text_tavily(query, max_results=max_results)
            
            for result in search_results:
                results['market_info'].append({
                    'title': result.get('title', ''),
                    'snippet': result.get('body', '')[:300],
                    'url': result.get('href', '')
                })
                results['citations'].append({
                    'type': 'market_info',
                    'url': result.get('href', ''),
                    'description': result.get('title', '')
                })
            
            # Small delay before next search
            time.sleep(1)
        
        # Search for partners information (only 1 query)
        if partner_queries:
            query = partner_queries[0]
            print(f"   🔍 Query: '{query}'")
            
            # Try Tavily first
            search_results = search_text_tavily(query, max_results=max_results)
            
            
            for result in search_results:
                results['partners'].append({
                    'title': result.get('title', ''),
                    'snippet': result.get('body', '')[:300],
                    'url': result.get('href', '')
                })
                results['citations'].append({
                    'type': 'partner',
                    'url': result.get('href', ''),
                    'description': result.get('title', '')
                })
        
        print(f"✅ Found {len(results['market_info'])} market info items and {len(results['partners'])} partner items")
        return results
        
    except Exception as e:
        print(f"❌ Business info search failed: {e}")
        return results

def download_image(image_url: str, save_path: str, max_size_mb: float = 2.0) -> bool:
    """
    Downloads an image from URL and validates it.
    
    Args:
        image_url: URL of the image
        save_path: Local path to save the image
        max_size_mb: Maximum file size in MB
    
    Returns:
        True if successful, False otherwise
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(image_url, headers=headers, timeout=10, stream=True)
        response.raise_for_status()
        
        # Check file size
        content_length = response.headers.get('content-length')
        if content_length and int(content_length) > max_size_mb * 1024 * 1024:
            print(f"⚠️  Image too large ({int(content_length) / 1024 / 1024:.2f} MB), skipping...")
            return False
        
        # Download and validate image
        image_data = response.content
        img = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary (for JPEG compatibility)
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        # Resize if too large (max 1920x1080 for PPT)
        max_dimension = 1920
        if img.width > max_dimension or img.height > max_dimension:
            img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
        
        # Save image
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        img.save(save_path, 'JPEG', quality=85, optimize=True)
        
        print(f"✅ Downloaded image: {os.path.basename(save_path)}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to download image from {image_url}: {e}")
        return False

def get_web_data_for_company(company_name: str, company_data: str) -> Dict:
    """
    Main function to gather all web data for a company using AI-generated queries.
    
    Args:
        company_name: Actual company name (used for context, anonymized in queries)
        company_data: Raw extracted text from company documents
    
    Returns:
        Comprehensive dict with images, certifications, business info, and citations
    """
    print(f"\n🌐 Starting comprehensive web search for company...")
    print("=" * 60)
    
    web_data = {
        'images': [],
        'certifications': [],
        'business_info': {},
        'citations': []
    }
    
    # 1. Search for images
    print("\n📸 Step 1/3: Searching for images...")
    images, img_citations = search_images(company_name, company_data, max_results=3)
    web_data['images'] = images
    web_data['citations'].extend(img_citations)
    
    # Wait between major search types
    print("\n⏳ Waiting before next search type...")
    time.sleep(random.uniform(10, 15))
    
    # 2. Search for certifications
    print("\n🏆 Step 2/3: Searching for certifications...")
    certs, cert_citations = search_certifications(company_name, company_data)
    web_data['certifications'] = certs
    web_data['citations'].extend(cert_citations)
    
    # Wait between major search types
    print("\n⏳ Waiting before next search type...")
    time.sleep(random.uniform(10, 15))
    
    # 3. Search for business information
    print("\n📊 Step 3/3: Searching for business information...")
    business_info = search_business_info(company_name, company_data)
    web_data['business_info'] = business_info
    web_data['citations'].extend(business_info.get('citations', []))
    
    print("=" * 60)
    print(f"✅ Web search complete. Found:")
    print(f"   - {len(web_data['images'])} images")
    print(f"   - {len(web_data['certifications'])} certifications")
    print(f"   - {len(web_data['citations'])} total citations")
    
    return web_data
