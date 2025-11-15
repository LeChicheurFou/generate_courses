import os
import base64
from mistralai import Mistral
from fpdf import FPDF
from PIL import Image
import io
import PyPDF2

class CourseGenerator:
    def __init__(self, api_key):
        self.client = Mistral(api_key=api_key)
        self.model = "pixtral-12b-2409"  # Modèle vision de Mistral
    
    def analyze_image(self, image_file):
        """Analyse l'image et génère un cours détaillé"""
        # Convertir l'image en base64
        img = Image.open(image_file)
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        return self._generate_course_from_base64(img_base64)
    
    def analyze_pdf(self, pdf_file):
        """Analyse un PDF et génère un cours détaillé"""
        # Extraire le texte du PDF
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text_content = ""
        
        for page in pdf_reader.pages:
            text_content += page.extract_text() + "\n"
        
        # Limiter à 4000 caractères pour l'API
        text_content = text_content[:4000]
        
        prompt = f"""Analyse ce contenu extrait d'un PDF et crée un cours structuré et pédagogique.

Contenu du PDF:
{text_content}

Structure attendue:
1. TITRE du cours
2. INTRODUCTION (contexte)
3. CONCEPTS CLÉS (liste à puces)
4. EXPLICATIONS DÉTAILLÉES (paragraphes)
5. EXEMPLES PRATIQUES
6. POINTS À RETENIR

Sois clair, pédagogique et exhaustif."""

        # Appel API Mistral (texte uniquement)
        response = self.client.chat.complete(
            model="mistral-large-latest",
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.choices[0].message.content
    
    def _generate_course_from_base64(self, img_base64):
        """Génère un cours depuis une image en base64"""
        prompt = """Analyse cette image et crée un cours structuré et pédagogique.

Structure attendue:
1. TITRE du cours
2. INTRODUCTION (contexte)
3. CONCEPTS CLÉS (liste à puces)
4. EXPLICATIONS DÉTAILLÉES (paragraphes)
5. EXEMPLES PRATIQUES
6. POINTS À RETENIR

Sois clair, pédagogique et exhaustif."""

        # Appel API Mistral avec vision
        response = self.client.chat.complete(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": f"data:image/png;base64,{img_base64}"
                        }
                    ]
                }
            ]
        )
        
        return response.choices[0].message.content
    
    def generate_pdf(self, content, filename="cours.pdf"):
        """Génère un PDF propre à partir du texte"""
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Utiliser Arial (supporte les accents français)
        pdf.set_font('Arial', '', 12)
        
        # Titre
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'Cours genere par IA', ln=True, align='C')
        pdf.ln(10)
        
        # Contenu
        pdf.set_font('Arial', '', 11)
        
        # Nettoyage et encodage du texte pour PDF
        clean_content = content.encode('latin-1', 'replace').decode('latin-1')
        
        # Découpage du texte en lignes
        for line in clean_content.split('\n'):
            if line.strip():  # Ignorer les lignes vides
                pdf.multi_cell(0, 6, line)
        
        pdf.output(filename)
        return filename