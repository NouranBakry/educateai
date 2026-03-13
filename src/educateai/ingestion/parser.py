# parses files that we get in upload endpoint

import os
from typing import List, Dict, Any
import PyPdf2
import docx

def parse_uploaded_file(file_path: str) -> Dict[str, Any]:
    """
    Parses the uploaded file and extracts relevant information.

    Args:
        file_path (str): The path to the uploaded file.

    Returns:
        Dict[str, Any]: A dictionary containing the extracted information.
    """
    file_extension = os.path.splitext(file_path)[1]
    if file_extension == ".txt":
        text = extract_text_from_file(file_path)
        return {"text": text}
    elif file_extension == ".pdf":
        text = extract_text_from_pdf(file_path)
        return {"text": text}
    elif file_extension == ".docx":
        text = extract_text_from_docx(file_path)
        return {"text": text}
    else:
        raise ValueError("Unsupported file type")

def extract_text_from_file(file_path: str) -> str:
    """
    Extracts text from the given file.

    Args:
        file_path (str): The path to the file. 
        
    Returns:
        str: The extracted text.
    """     
    with open(file_path, "r") as f:
        text = f.read()
    return text

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extracts text from a PDF file.

    Args:
        file_path (str): The path to the PDF file.
        
    Returns:
        str: The extracted text.
    """ 
    with open(file_path, "rb") as f:
        reader = PyPdf2.PdfReader(f)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    return text

def extract_text_from_docx(file_path: str) -> str:
    """
    Extracts text from a DOCX file.

    Args:
        file_path (str): The path to the DOCX file. 
        
    Returns:
        str: The extracted text.
    """
    from docx import Document
    document = Document(file_path)
    text = ""
    for paragraph in document.paragraphs:
        text += paragraph.text + "\n"
    return text