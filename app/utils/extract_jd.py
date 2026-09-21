from app.pydantic_models.jd_pydantic_models import JDRequirements
from pathlib import Path
import logging
import re
import unicodedata
import docx 
import pdfplumber
import pymupdf


logger=logging.getLogger(__name__)
def jd_path():
    jd_root=Path(__file__).resolve().parents[2]
    jd_dir=jd_root/"app"/"jd_data"
    jd_files=list(jd_dir.glob("*.docx"))+list(jd_dir.glob("*.pdf"))
    return jd_files

def normalize_text(text):
    text=unicodedata.normalize("NFKD",text)
    text=re.sub(r"\s+"," ",text).strip()
    return text

def extract_docx_text(file_path) -> str:
    # 1. Load the document object
    doc = docx.Document(file_path)
    
    # 2. Initialize a list to hold text lines
    text_accumulator = []
    
    # 3. Loop through every paragraph in the document
    for paragraph in doc.paragraphs:
        # Check if the paragraph actually contains text (skip empty ones)
        if paragraph.text.strip():
            text_accumulator.append(paragraph.text)
            
    # 4. Join all paragraphs back into a single continuous string
    
    text_accumulator="\n".join(text_accumulator)
    
    text_accumulator=normalize_text(text_accumulator)
    return text_accumulator

# def extract_pdf_text(jd_path):
#     text_accumulator=[]
    
   
            
#     with pdfplumber.open(jd_path) as pdf:
#         for page in pdf.pages:
#             text=page.extract_text()
#             text_accumulator.append(text)
#         text_accumulator='/n'.join(text_accumulator)
#         text_accumulator=normalize_text(text_accumulator)
#     return text_accumulator
                    


def extract_pdf_text(file_path: Path) -> str:
    text_accumulator = []
    
    try:
        # Open the PDF using PyMuPDF (fitz)
        with pymupdf.open(file_path) as doc:
            for page in doc:
                text = page.get_text()
                if text and text.strip():
                    text_accumulator.append(text)
    except Exception as e:
        logger.error(f"Failed to parse PDF with PyMuPDF: {file_path}")
        raise ValueError(f"Could not read {file_path.name}. It may be corrupted.") from e
        
    raw_text = "\n".join(text_accumulator)
    return normalize_text(raw_text)                  

    

def extract_jd(jd_path):
    clean_pdf_text=[]
    clean_docx_text=[]
    if not jd_path:
        logger.error("Path does not exist")
        raise TypeError("Please enter a valid path")

    suffix=jd_path.suffix.lower()
    if suffix==".docx":
        return extract_docx_text(jd_path)

    elif suffix==".pdf":
        return extract_pdf_text(jd_path)


    return clean_pdf_text,clean_docx_text

        
if __name__ == "__main__":
    jd_root = Path(__file__).resolve().parents[2]
    jd_dir = jd_root / "app" / "jd_data"
    
    # Correct multi-extension glob collection
    jd_files = list(jd_dir.glob("*.docx")) + list(jd_dir.glob("*.pdf"))
    
    print(f"JD Path: {jd_root}")
    print(f"Total files found: {len(jd_files)}")

    # Check for empty list BEFORE looping
    if not jd_files:
        logger.error("No JD files found in directory.")
    else:
        for file in jd_files:
            logger.info(f"Processing file: {file.name}")
            text = extract_jd(file)
            
            # Use f-string and proper newline escape
            print(f"\n--- File: {file.name} ---\n{text[:300]}...\n")



    

    

    









        





    


