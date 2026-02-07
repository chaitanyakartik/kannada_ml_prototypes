#python pdf_to_json.py /Users/chaitanyakartik/Projects/TTS/prototype/voicebot/data/pdfs /Users/chaitanyakartik/Projects/TTS/prototype/voicebot/data/master.json

import os
import json
import argparse
from pathlib import Path
from pypdf import PdfReader

def extract_text_from_pdf(pdf_path):
    """Extracts text from a single PDF file."""
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        return None

def main(input_folder, output_json_path):
    input_path = Path(input_folder)
    output_path = Path(output_json_path)
    
    # 1. create the individual json_data folder
    individual_json_dir = input_path / "json_data"
    individual_json_dir.mkdir(exist_ok=True)

    all_data = []

    # 2. Iterate through all files in the folder
    print(f"Scanning folder: {input_path}...")
    
    files = list(input_path.glob("*.pdf"))
    if not files:
        print("No PDF files found in the input folder.")
        return

    for pdf_file in files:
        print(f"Processing: {pdf_file.name}")
        
        # Extract text
        content = extract_text_from_pdf(pdf_file)
        
        if content is not None:
            file_data = {
                "filename": pdf_file.name,
                "filepath": str(pdf_file.absolute()),
                "content": content
            }
            
            # Add to master list
            all_data.append(file_data)

            # Write individual JSON file
            individual_file_name = pdf_file.stem + ".json"
            individual_file_path = individual_json_dir / individual_file_name
            
            with open(individual_file_path, 'w', encoding='utf-8') as f:
                json.dump(file_data, f, indent=4, ensure_ascii=False)

    # 3. Write the master JSON file
    # Ensure the directory for the output file exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=4, ensure_ascii=False)

    print(f"\nSuccess! Processed {len(all_data)} files.")
    print(f"Master JSON saved to: {output_path}")
    print(f"Individual JSONs saved to: {individual_json_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract text from PDFs to JSON.")
    parser.add_argument("input_folder", help="Path to the folder containing PDF files")
    parser.add_argument("output_json_file", help="Path where the master JSON file will be saved")
    
    args = parser.parse_args()
    
    main(args.input_folder, args.output_json_file)



