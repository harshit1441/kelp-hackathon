"""
Simple test script to see the output of web_search.py
Uses the full pipeline (ingestor + agent) like main.py, but only displays results.
Run this file to test the web search functionality independently.
"""

import os
import sys
from dotenv import load_dotenv

# Import our custom modules from the 'utils' package
from utils.ingestor import ingest_company_data
from utils.agent import analyze_data
from utils.web_search import get_web_data_for_company

# Load environment variables
load_dotenv()

def test_web_search(company_folder_name):
    """
    Test the web search functionality using the full pipeline.
    Similar to main.py but only displays results without generating PPT.
    """
    print("=" * 70)
    print("🧪 TESTING WEB SEARCH MODULE (Full Pipeline)")
    print("=" * 70)
    
    # --- SETUP PATHS ---
    base_dir = os.getcwd()
    input_dir = os.path.join(base_dir, "data", "input", company_folder_name)
    
    # Check if folder exists
    if not os.path.exists(input_dir):
        print(f"❌ Error: The folder 'data/input/{company_folder_name}' does not exist.")
        print("   Please create it and put your PDF/Text files inside.")
        return None
    
    # --- STEP 1: INGESTION ---
    print(f"\n📂 Step 1: Ingesting documents from '{input_dir}'...")
    raw_text = ingest_company_data(input_dir)
    
    if not raw_text or len(raw_text) < 50:
        print("❌ CRITICAL FAILURE: No text extracted. Check your input folder path.")
        return None
    
    print(f"   ✅ Success! Extracted {len(raw_text)} characters of text.")
    
    # --- STEP 2: AI ANALYSIS ---
    print(f"\n🧠 Step 2: Sending data to Gemini (Agent)...")
    structured_data = analyze_data(raw_text)
    
    if not structured_data:
        print("❌ CRITICAL FAILURE: AI Agent failed to return data.")
        return None
    
    codename = structured_data.get('company_codename', 'Unknown Project')
    company_name = structured_data.get('company_name', company_folder_name)
    sector = structured_data.get('sector', 'Unknown')
    
    print(f"   ✅ Success! Analysis complete for '{codename}'.")
    print(f"   📋 Company Name: {company_name}")
    print(f"   🏭 Sector: {sector}")
    
    # --- STEP 3: WEB SEARCH ---
    print(f"\n🌐 Step 3: Gathering web data (images, certifications, business info)...")
    print("   ⚠️  Note: This may take a while due to rate limiting...")
    
    try:
        web_data = get_web_data_for_company(company_name, raw_text)
        print(f"   ✅ Success! Web search complete.")
    except Exception as e:
        print(f"   ⚠️  Web search error: {e}")
        print(f"   -> Continuing with partial results...")
        web_data = {
            'images': [],
            'certifications': [],
            'business_info': {},
            'citations': []
        }
    
    # --- DISPLAY RESULTS ---
    print("\n" + "=" * 70)
    print("📊 WEB SEARCH RESULTS")
    print("=" * 70)
    
    # Company Info
    print(f"\n📋 COMPANY INFORMATION:")
    print(f"   Name: {company_name}")
    print(f"   Codename: {codename}")
    print(f"   Sector: {sector}")
    
    # Images
    print(f"\n🖼️  IMAGES FOUND: {len(web_data['images'])}")
    if web_data['images']:
        for i, img in enumerate(web_data['images'][:5], 1):  # Show first 5
            title = img.get('title', 'No title')
            url = img.get('url', 'N/A')
            print(f"   {i}. {title[:60]}")
            if len(url) > 80:
                print(f"      URL: {url[:80]}...")
            else:
                print(f"      URL: {url}")
    else:
        print("   (No images found - may be due to rate limiting)")
    
    # Certifications
    print(f"\n🏆 CERTIFICATIONS FOUND: {len(web_data['certifications'])}")
    if web_data['certifications']:
        for i, cert in enumerate(web_data['certifications'], 1):
            verified = "✓" if cert.get('verified') else "?"
            name = cert.get('name', 'Unknown')
            source = cert.get('source', 'N/A')
            print(f"   {i}. {verified} {name}")
            if source != 'company_data' and len(source) > 60:
                print(f"      Source: {source[:60]}...")
            elif source != 'company_data':
                print(f"      Source: {source}")
    else:
        print("   (No certifications found)")
    
    # Business Info
    business_info = web_data.get('business_info', {})
    market_info = business_info.get('market_info', [])
    partners = business_info.get('partners', [])
    trends = business_info.get('trends', [])
    
    print(f"\n📈 MARKET INFORMATION: {len(market_info)} items")
    if market_info:
        for i, info in enumerate(market_info[:3], 1):  # Show first 3
            title = info.get('title', 'No title')
            snippet = info.get('snippet', '')
            url = info.get('url', 'N/A')
            print(f"   {i}. {title[:60]}")
            if snippet:
                print(f"      {snippet[:100]}...")
            if url and url != 'N/A':
                print(f"      URL: {url[:60]}...")
    else:
        print("   (No market information found - may be due to rate limiting)")
    
    print(f"\n🤝 PARTNERS INFORMATION: {len(partners)} items")
    if partners:
        for i, partner in enumerate(partners[:3], 1):  # Show first 3
            title = partner.get('title', 'No title')
            snippet = partner.get('snippet', '')
            url = partner.get('url', 'N/A')
            print(f"   {i}. {title[:60]}")
            if snippet:
                print(f"      {snippet[:100]}...")
            if url and url != 'N/A':
                print(f"      URL: {url[:60]}...")
    else:
        print("   (No partner information found - may be due to rate limiting)")
    
    # Citations
    print(f"\n📚 TOTAL CITATIONS: {len(web_data['citations'])}")
    if web_data['citations']:
        citation_types = {}
        for citation in web_data['citations']:
            cit_type = citation.get('type', 'unknown')
            citation_types[cit_type] = citation_types.get(cit_type, 0) + 1
        
        print("   Citation breakdown:")
        for cit_type, count in citation_types.items():
            print(f"      - {cit_type}: {count}")
    else:
        print("   (No citations found)")
    
    # Structured Data Summary
    print(f"\n📊 STRUCTURED DATA SUMMARY:")
    print(f"   Business Overview Points: {len(structured_data.get('business_overview', []))}")
    print(f"   Investment Highlights: {len(structured_data.get('investment_highlights', []))}")
    
    financials = structured_data.get('financials', {})
    if financials:
        print(f"   Financials:")
        for key, value in financials.items():
            print(f"      - {key}: {value}")
    
    print("\n" + "=" * 70)
    print("✅ TEST COMPLETE")
    print("=" * 70)
    
    return {
        'structured_data': structured_data,
        'web_data': web_data
    }

if __name__ == "__main__":
    # Check if API keys are set
    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠️  WARNING: GOOGLE_API_KEY not found in environment variables.")
        print("   Please set it in your .env file or environment.")
        print("   Continuing anyway...\n")
    
    if not os.getenv("TAVILY_API_KEY"):
        print("⚠️  WARNING: TAVILY_API_KEY not found. Text searches will be skipped.")
        print("   Get free API key at https://tavily.com (1,000 free searches/month)")
        print("   Add to .env: TAVILY_API_KEY=your_key_here\n")
    
    # Get company folder name from command line or use default
    if len(sys.argv) > 1:
        target_company = sys.argv[1]
    else:
        # List available companies
        input_dir = os.path.join("data", "input")
        if os.path.exists(input_dir):
            companies = [d for d in os.listdir(input_dir) 
                        if os.path.isdir(os.path.join(input_dir, d)) and not d.startswith('.')]
            if companies:
                print("📂 Available companies:")
                for i, company in enumerate(companies, 1):
                    print(f"   {i}. {company}")
                print(f"\n💡 Usage: python test_web_search.py <company_folder_name>")
                print(f"   Example: python test_web_search.py {companies[0]}\n")
                target_company = companies[0]  # Use first available
                print(f"   Using default: {target_company}\n")
            else:
                print("❌ No company folders found in data/input/")
                print("   Please create a folder with company data first.")
                sys.exit(1)
        else:
            print("❌ Error: 'data/input' directory does not exist.")
            sys.exit(1)
    
    # Run the test
    result = test_web_search(target_company)
    
    if result:
        print("\n💡 Tip: This test uses the same pipeline as main.py")
        print("   but only displays results without generating PPT.")
        print("\n⚠️  Note: Make sure TAVILY_API_KEY is set in .env for text searches.")
