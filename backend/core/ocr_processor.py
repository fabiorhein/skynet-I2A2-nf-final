# Tesseract + LayoutLM

"""
OCR Processor Module
Processamento de OCR para documentos fiscais (PDF, imagens)
"""

import asyncio
from typing import Dict, Any, Optional
import tempfile
import os
from pathlib import Path

try:
    import pytesseract
    from PIL import Image
    import pdf2image
    HAS_OCR = True
except ImportError:
    HAS_OCR = False
    # Define dummy classes para evitar erros de importação
    class Image:
        pass
    pytesseract = None
    pdf2image = None


class OCRProcessor:
    """Processador OCR para documentos fiscais"""

    def __init__(self):
        if not HAS_OCR:
            print("⚠️ OCR dependencies not installed. Install with: pip install pytesseract pillow pdf2image")
        self.tesseract_available = HAS_OCR

    async def process_file(self, file_path: str) -> str:
        """
        Processa arquivo e extrai texto via OCR

        Args:
            file_path: Caminho do arquivo (PDF, PNG, JPG, JPEG)

        Returns:
            Texto extraído do documento
        """
        try:
            if not self.tesseract_available:
                return "OCR não disponível. Instale as dependências necessárias."

            file_extension = Path(file_path).suffix.lower()

            if file_extension == '.pdf':
                return await self._process_pdf(file_path)
            elif file_extension in ['.png', '.jpg', '.jpeg']:
                return await self._process_image(file_path)
            else:
                return f"Formato de arquivo não suportado: {file_extension}"

        except Exception as e:
            return f"Erro no processamento OCR: {str(e)}"

    async def _process_pdf(self, pdf_path: str) -> str:
        """Processa PDF e extrai texto"""
        if not HAS_OCR:
            return "OCR não disponível. Instale as dependências: pip install pytesseract pillow pdf2image"

        try:
            # Converter PDF para imagens
            images = pdf2image.convert_from_path(pdf_path)

            all_text = []
            for i, image in enumerate(images):
                # Extrair texto de cada página
                text = pytesseract.image_to_string(image, lang='por')
                if text.strip():
                    all_text.append(f"--- Página {i+1} ---\n{text}")

            return "\n\n".join(all_text)

        except Exception as e:
            return f"Erro ao processar PDF: {str(e)}"

    async def _process_image(self, image_path: str) -> str:
        """Processa imagem e extrai texto"""
        if not HAS_OCR:
            return "OCR não disponível. Instale as dependências: pip install pytesseract pillow pdf2image"

        try:
            # Abrir imagem
            image = Image.open(image_path)

            # Extrair texto
            text = pytesseract.image_to_string(image, lang='por')

            return text

        except Exception as e:
            return f"Erro ao processar imagem: {str(e)}"

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Pré-processamento de imagem para melhorar OCR"""
        try:
            # Converter para RGB se necessário
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Melhorar contraste (opcional)
            # image = ImageEnhance.Contrast(image).enhance(2.0)

            return image

        except Exception:
            return image

    async def extract_structured_data(self, text: str) -> Dict[str, Any]:
        """
        Extrai dados estruturados do texto via regex

        Args:
            text: Texto extraído via OCR

        Returns:
            Dict com dados estruturados
        """
        try:
            import re

            # Padrões regex para extração
            patterns = {
                'cnpj': r'(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})',
                'cpf': r'(\d{3}\.\d{3}\.\d{3}-\d{2})',
                'valor': r'R\$\s*([0-9.,]+)',
                'data': r'(\d{2}/\d{2}/\d{4})',
                'hora': r'(\d{2}:\d{2}:\d{2})',
                'numero_nf': r'(?:NFE|NFCE|CTE)[-\s]*(\d+)',
                'chave_nf': r'(\d{44})'
            }

            extracted = {}
            for field, pattern in patterns.items():
                match = re.search(pattern, text.upper())
                if match:
                    extracted[field] = match.group(1)

            # Extrair emitente (primeira ocorrência de CNPJ)
            cnpj_matches = re.findall(patterns['cnpj'], text.upper())
            if cnpj_matches:
                extracted['emitente_cnpj'] = cnpj_matches[0]

            # Extrair destinatário (se houver segundo CNPJ)
            if len(cnpj_matches) > 1:
                extracted['destinatario_cnpj'] = cnpj_matches[1]

            # Calcular valor se encontrado
            if 'valor' in extracted:
                try:
                    valor_str = extracted['valor'].replace('.', '').replace(',', '.')
                    extracted['valor_numerico'] = float(valor_str)
                except:
                    extracted['valor_numerico'] = 0

            return extracted

        except Exception as e:
            return {"error": f"Erro na extração estruturada: {str(e)}"}