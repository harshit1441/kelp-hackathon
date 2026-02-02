import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def clean_json_string(json_string):
    """
    Cleans the LLM output to ensure it is valid JSON.
    """
    if "```" in json_string:
        json_string = json_string.replace("```json", "").replace("```", "")
    return json_string.strip()

def analyze_data(raw_text):
    """
    Sends the raw text to Gemini and asks for a structured JSON output.
    """
    
    # --- FIX: SWITCH TO GEMINI-PRO (STABLE) ---
    # The error "404 model not found" often happens with new aliases like 'flash'.
    # 'gemini-pro' is the standard v1.0 model and is extremely stable.
    llm = ChatGoogleGenerativeAI(
        model="models/gemini-2.5-flash-lite", 
        temperature=0.2,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )

    prompt_template = """
    You are an expert M&A Analyst at Kelp Global.
    Your task is to analyze the provided raw company data and extract specific information to build a 3-slide "Investment Teaser".
    
    CRITICAL INSTRUCTIONS:
    1. **Anonymize**: Do NOT use the specific company name. Use a generic codename like "Project Alpha" or "Project Apex".
    2. **Factuality**: Only use data present in the provided text. If a metric is missing, estimate it based on context or mark as "N/A".
    3. **Output Format**: You must output ONLY valid JSON. No Markdown formatting, no extra text.
    
    --- RAW DATA START ---
    {raw_text}
    --- RAW DATA END ---

    Return a JSON object with this EXACT structure:
    {{
        "company_name": "Extract the actual company name from the data",
        "company_codename": "Project [Name]",
        "sector": "Detect the sector",
        "business_overview": [
            "Bullet point 1 (What they do)",
            "Bullet point 2 (Capacity/Infra)",
            "Bullet point 3 (Clients/Markets)"
        ],
        "product_portfolio": [
            "Product 1",
            "Product 2",
            "Product 3"
        ],
        "applications": [
            "Application 1",
            "Application 2",
            "Application 3"
        ],
        "financials": {{
            "ebitda": "Find EBITDA Margin %",
            "roce": "Find RoCE %",
            "roe": "Find RoE %",
            "debt": "Find Debt/Equity ratio or debt info",
            "revenue_cagr": "Find Revenue CAGR %"
        }},
        "assumptions": "Key assumptions about the business model or financial projections",
        "metrics_point": "Key metric or growth point to highlight",
        "upcoming_facility": "Information about upcoming facilities or expansion plans",
        "sales": "Sales breakdown or key sales metrics",
        "global_presence": "Information about global presence, exports, or international markets",
        "investment_highlights": [
            "Highlight 1",
            "Highlight 2",
            "Highlight 3"
        ]
    }}
    """
    
    prompt = PromptTemplate(
        input_variables=["raw_text"],
        template=prompt_template
    )

    print("🧠 AI Agent: Analyzing data with Gemini Pro...")
    chain = prompt | llm
    
    try:
        response = chain.invoke({"raw_text": raw_text})
        
        # Handle response content type (sometimes it's an object, sometimes a string)
        content = response.content if hasattr(response, 'content') else str(response)
        
        cleaned_json = clean_json_string(content)
        data = json.loads(cleaned_json)
        
        print(f"✅ Analysis Complete. Codename: {data.get('company_codename')}")
        return data
        
    except json.JSONDecodeError:
        print("❌ JSON Error: AI output was not valid JSON.")
        return {
            "company_name": "Unknown",
            "company_codename": "Project Error",
            "sector": "Error",
            "business_overview": ["AI could not process data."],
            "product_portfolio": [],
            "applications": [],
            "financials": {},
            "assumptions": "N/A",
            "metrics_point": "N/A",
            "upcoming_facility": "N/A",
            "sales": "N/A",
            "global_presence": "N/A",
            "investment_highlights": []
        }
    except Exception as e:
        print(f"❌ API Error: {e}")
        return None