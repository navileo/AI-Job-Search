from pypdf import PdfReader

def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF file.
    """
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None

def save_text_to_file(text, file_path):
    """
    Saves text to a file.
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text)
        return True
    except Exception as e:
        print(f"Error writing file: {e}")
        return False
