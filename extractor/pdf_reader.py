import pdfplumber
from typing import Union, List


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extracts text from a PDF file using pdfplumber.
    
    Args:
        file_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text from the PDF
    """
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error reading PDF: {str(e)}")
        raise
    
    return text


def extract_text_from_bytes(pdf_bytes: bytes) -> str:
    """
    Extracts text from PDF bytes using pdfplumber.
    
    Args:
        pdf_bytes (bytes): PDF content as bytes
        
    Returns:
        str: Extracted text from the PDF
    """
    text = ""
    try:
        with pdfplumber.open(pdf_bytes) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error reading PDF from bytes: {str(e)}")
        raise
    
    return text


def read_file_content(file_path: str) -> str:
    """
    Reads content from either a text file or PDF file based on extension.
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        str: Content of the file
    """
    if file_path.lower().endswith('.pdf'):
        return extract_text_from_pdf(file_path)
    else:
        # Assume it's a text file
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()


if __name__ == "__main__":
    # Test the functions
    print("PDF Reader module loaded successfully.")