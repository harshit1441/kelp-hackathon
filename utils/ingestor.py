import os
import pandas as pd
import pdfplumber

def ingest_company_data(folder_path):
    """
    Reads all PDF, Excel, and Text files in a folder and returns a single combined string.
    """
    combined_text = ""
    
    # Check if folder exists
    if not os.path.exists(folder_path):
        return f"Error: Folder not found at {folder_path}"

    print(f"📂 Scanning folder: {folder_path}...")

    files = os.listdir(folder_path)
    if not files:
        return "Warning: No files found in this folder."

    for filename in files:
        file_path = os.path.join(folder_path, filename)
        
        # SKIP SYSTEM FILES (like .DS_Store on Mac)
        if filename.startswith('.'):
            continue

        try:
            # --- HANDLE TEXT / README FILES (Your current case) ---
            if filename.lower().endswith(('.txt', '.md')):
                print(f"   -> Reading Text: {filename}")
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    combined_text += f"\n\n--- FILE: {filename} ---\n{content}"

            # --- HANDLE PDF FILES (Mandatory Requirement) ---
            elif filename.lower().endswith('.pdf'):
                print(f"   -> Reading PDF: {filename}")
                with pdfplumber.open(file_path) as pdf:
                    text = ""
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                    combined_text += f"\n\n--- FILE: {filename} (PDF Content) ---\n{text}"

            # --- HANDLE EXCEL FILES (Mandatory Requirement) ---
            elif filename.lower().endswith(('.xlsx', '.xls')):
                print(f"   -> Reading Excel: {filename}")
                xls = pd.ExcelFile(file_path)
                for sheet_name in xls.sheet_names:
                    df = pd.read_excel(xls, sheet_name=sheet_name)
                    # Convert Table to String so LLM can read it
                    table_text = df.to_string(index=False)
                    combined_text += f"\n\n--- FILE: {filename} | SHEET: {sheet_name} ---\n{table_text}"

        except Exception as e:
            print(f"   ⚠️ Error reading {filename}: {e}")

    return combined_text