import os
import sys
from dotenv import load_dotenv

# Import our custom modules from the 'utils' package
from utils.ingestor import ingest_company_data
from utils.agent import analyze_data
from utils.web_search import get_web_data_for_company
from utils.generator import create_presentation

# Load API Keys (specifically GOOGLE_API_KEY)
load_dotenv()

def run_pipeline(company_folder_name):
    """
    Orchestrates the full process:
    1. Read Data -> 2. AI Analysis -> 3. Web Search -> 4. Generate PPT
    """
    print(f"\n🚀 STARTING PIPELINE FOR: {company_folder_name}")
    print("=" * 50)

    # --- SETUP PATHS ---
    # Define where inputs live and where outputs go
    base_dir = os.getcwd()
    input_dir = os.path.join(base_dir, "data", "input", company_folder_name)
    output_dir = os.path.join(base_dir, "data", "output")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Define final PPT output path
    output_pptx_path = os.path.join(output_dir, f"{company_folder_name}_Teaser.pptx")

    # --- STEP 1: INGESTION ---
    print(f"\n📂 Step 1: Ingesting documents from '{input_dir}'...")
    raw_text = ingest_company_data(input_dir)
    
    if not raw_text or len(raw_text) < 50:
        print("❌ CRITICAL FAILURE: No text extracted. Check your input folder path.")
        return

    print(f"   -> Success! Extracted {len(raw_text)} characters of text.")

    # --- STEP 2: AI ANALYSIS ---
    print(f"\n🧠 Step 2: Sending data to Gemini (Agent)...")
    structured_data = analyze_data(raw_text)
    
    if not structured_data:
        print("❌ CRITICAL FAILURE: AI Agent failed to return data.")
        return

    codename = structured_data.get('company_codename', 'Unknown Project')
    company_name = structured_data.get('company_name', company_folder_name)
    print(f"   -> Success! Analysis complete for '{codename}'.")

    # --- STEP 3: WEB SEARCH ---
    print(f"\n🌐 Step 3: Gathering web data (images, certifications, business info)...")
    try:
        web_data = get_web_data_for_company(company_name, raw_text)
        # Add web data to structured_data for use in presentation
        structured_data['web_data'] = web_data
        print(f"   -> Success! Web search complete.")
    except Exception as e:
        print(f"⚠️  Web search error: {e}")
        print(f"   -> Continuing without web data...")
        structured_data['web_data'] = {
            'images': [],
            'certifications': [],
            'business_info': {},
            'citations': []
        }

    # --- STEP 4: GENERATION ---
    print(f"\n🎨 Step 4: Generating PowerPoint slides...")
    try:
        create_presentation(structured_data, output_pptx_path)
        print(f"   -> Success! PPT Saved.")
    except Exception as e:
        print(f"❌ GENERATOR ERROR: {e}")
        return

    print("=" * 50)
    print(f"✅ PIPELINE COMPLETE. Output file:\n   {output_pptx_path}")
    print("=" * 50)

if __name__ == "__main__":
    # --- USAGE INSTRUCTIONS ---
    # You can run this file in two ways:
    # 1. python main.py                  (Runs default test)
    # 2. python main.py "Kalyani_Forge"  (Runs specific folder)

    if len(sys.argv) > 1:
        # User provided a folder name in command line
        target_company = sys.argv[1]
    else:
        # Default test folder (CHANGE THIS to match your actual folder name)
        target_company = "Test_Company"

    # Check if the folder actually exists before running
    if os.path.exists(os.path.join("data", "input", target_company)):
        run_pipeline(target_company)
    else:
        print(f"❌ Error: The folder 'data/input/{target_company}' does not exist.")
        print("   Please create it and put your PDF/Text files inside.")