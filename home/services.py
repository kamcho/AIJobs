import os
from pypdf import PdfReader
from docx import Document

class TextExtractor:
    @staticmethod
    def extract_text(file_path):
        """
        Extracts text from a file based on its extension.
        Supported formats: .pdf, .docx, .txt
        """
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        if ext == '.pdf':
            return TextExtractor._extract_from_pdf(file_path)
        elif ext == '.docx':
            return TextExtractor._extract_from_docx(file_path)
        elif ext == '.txt':
            return TextExtractor._extract_from_txt(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    @staticmethod
    def _extract_from_pdf(file_path):
        text = ""
        try:
            reader = PdfReader(file_path)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        except Exception as e:
            text = f"Error extracting PDF: {str(e)}"
        return text.strip()

    @staticmethod
    def _extract_from_docx(file_path):
        text = ""
        try:
            doc = Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
        except Exception as e:
            text = f"Error extracting DOCX: {str(e)}"
        return text.strip()

    @staticmethod
    def _extract_from_txt(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error extracting TXT: {str(e)}"
