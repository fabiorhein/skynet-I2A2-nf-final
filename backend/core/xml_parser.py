# Parse NFe/NFCe/CTe

"""
XML Parser Module
Parser para documentos fiscais brasileiros (NFe, NFCe, CTe)
"""

import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional
import re
import json
from datetime import datetime
import asyncio


class XMLParser:
    """Parser para documentos fiscais XML"""

    def __init__(self):
        self.namespaces = {
            'nfe': 'http://www.portalfiscal.inf.br/nfe',
            'nfce': 'http://www.portalfiscal.inf.br/nfce',
            'cte': 'http://www.portalfiscal.inf.br/cte'
        }

    async def parse_xml(self, xml_content: str) -> Dict[str, Any]:
        """
        Parse XML de documento fiscal

        Args:
            xml_content: Conteúdo XML ou caminho do arquivo

        Returns:
            Dict com dados extraídos
        """
        try:
            # Se for caminho de arquivo, ler o conteúdo
            if isinstance(xml_content, str) and xml_content.endswith('.xml'):
                with open(xml_content, 'r', encoding='utf-8') as f:
                    xml_content = f.read()

            # Parse do XML
            root = ET.fromstring(xml_content)

            # Detectar tipo de documento
            doc_type = self._detect_document_type(root)

            # Extrair dados baseado no tipo
            if doc_type == 'nfe':
                return await self._parse_nfe(root)
            elif doc_type == 'nfce':
                return await self._parse_nfce(root)
            elif doc_type == 'cte':
                return await self._parse_cte(root)
            else:
                return await self._parse_generic(root)

        except Exception as e:
            return {
                "success": False,
                "error": f"Erro ao parsear XML: {str(e)}",
                "document_type": "unknown"
            }

    async def parse_text(self, text: str) -> Dict[str, Any]:
        """
        Parse texto extraído via OCR

        Args:
            text: Texto extraído do documento

        Returns:
            Dict com dados extraídos
        """
        try:
            # Usar regex para extrair informações básicas
            extracted_data = self._extract_from_text(text)

            return {
                "success": True,
                "document_type": extracted_data.get("document_type", "unknown"),
                "document_number": extracted_data.get("document_number"),
                "total_value": extracted_data.get("total_value", 0),
                "date": extracted_data.get("date"),
                "issuer": extracted_data.get("issuer"),
                "recipient": extracted_data.get("recipient"),
                "items": extracted_data.get("items", []),
                "taxes": extracted_data.get("taxes", {}),
                "validation_status": "extracted",
                "validation_notes": "Dados extraídos via OCR"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Erro ao parsear texto: {str(e)}",
                "document_type": "unknown"
            }

    def _detect_document_type(self, root: ET.Element) -> str:
        """Detecta tipo de documento baseado no XML"""
        # Verificar namespaces e elementos específicos
        if 'nfe' in str(ET.tostring(root, encoding='unicode')):
            return 'nfe'
        elif 'nfce' in str(ET.tostring(root, encoding='unicode')):
            return 'nfce'
        elif 'cte' in str(ET.tostring(root, encoding='unicode')):
            return 'cte'
        else:
            return 'generic'

    async def _parse_nfe(self, root: ET.Element) -> Dict[str, Any]:
        """Parse NFe (Nota Fiscal Eletrônica)"""
        try:
            # Namespace NFe
            ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}

            # Dados básicos
            inf_nfe = root.find('.//nfe:infNFe', ns)
            if inf_nfe is None:
                inf_nfe = root.find('.//infNFe')

            if inf_nfe is None:
                return self._parse_generic(root)

            # Número da NFe
            nfe_number = inf_nfe.get('Id', '').replace('NFe', '') if inf_nfe.get('Id') else ''

            # Emitente
            emit = root.find('.//nfe:emit', ns)
            if emit is None:
                emit = root.find('.//emit')

            issuer_name = ''
            issuer_cnpj = ''
            if emit is not None:
                issuer_name = self._get_text(emit.find('.//nfe:xNome', ns)) or self._get_text(emit.find('.//xNome'))
                issuer_cnpj = self._get_text(emit.find('.//nfe:CNPJ', ns)) or self._get_text(emit.find('.//CNPJ'))

            # Destinatário
            dest = root.find('.//nfe:dest', ns)
            if dest is None:
                dest = root.find('.//dest')

            recipient_name = ''
            recipient_cnpj = ''
            if dest is not None:
                recipient_name = self._get_text(dest.find('.//nfe:xNome', ns)) or self._get_text(dest.find('.//xNome'))
                recipient_cnpj = self._get_text(dest.find('.//nfe:CNPJ', ns)) or self._get_text(dest.find('.//CNPJ'))

            # Valor total
            total = root.find('.//nfe:total', ns)
            if total is None:
                total = root.find('.//total')

            total_value = 0
            if total is not None:
                icms_total = self._get_text(total.find('.//nfe:ICMSTot', ns)) or self._get_text(total.find('.//ICMSTot'))
                if icms_total:
                    # Extrair valor total do texto
                    total_match = re.search(r'vNF["\s]*=[\s]*["\s]*([0-9,\.]+)', icms_total)
                    if total_match:
                        total_value = float(total_match.group(1).replace(',', '.'))

            # Data de emissão
            date = ''
            ide = root.find('.//nfe:ide', ns)
            if ide is None:
                ide = root.find('.//ide')

            if ide is not None:
                date = self._get_text(ide.find('.//nfe:dhEmi', ns)) or self._get_text(ide.find('.//dhEmi'))

            # Itens
            items = []
            dets = root.findall('.//nfe:det', ns)
            if not dets:
                dets = root.findall('.//det')

            for det in dets:
                item = {
                    'product': self._get_text(det.find('.//nfe:xProd', ns)) or self._get_text(det.find('.//xProd')),
                    'quantity': self._get_text(det.find('.//nfe:qCom', ns)) or self._get_text(det.find('.//qCom')),
                    'unit_price': self._get_text(det.find('.//nfe:vUnCom', ns)) or self._get_text(det.find('.//vUnCom')),
                    'total': self._get_text(det.find('.//nfe:vProd', ns)) or self._get_text(det.find('.//vProd'))
                }
                items.append(item)

            # Impostos
            taxes = {}
            icms_total = root.find('.//nfe:ICMSTot', ns)
            if icms_total is None:
                icms_total = root.find('.//ICMSTot')

            if icms_total is not None:
                taxes = {
                    'icms': self._get_text(icms_total.find('.//nfe:vICMS', ns)) or self._get_text(icms_total.find('.//vICMS')),
                    'ipi': self._get_text(icms_total.find('.//nfe:vIPI', ns)) or self._get_text(icms_total.find('.//vIPI')),
                    'pis': self._get_text(icms_total.find('.//nfe:vPIS', ns)) or self._get_text(icms_total.find('.//vPIS')),
                    'cofins': self._get_text(icms_total.find('.//nfe:vCOFINS', ns)) or self._get_text(icms_total.find('.//vCOFINS'))
                }

            return {
                "success": True,
                "document_type": "nfe",
                "document_number": nfe_number,
                "total_value": total_value,
                "date": date,
                "issuer": issuer_name,
                "issuer_cnpj": issuer_cnpj,
                "recipient": recipient_name,
                "recipient_cnpj": recipient_cnpj,
                "items": items,
                "taxes": taxes,
                "validation_status": "processed",
                "validation_notes": "NFe processada com sucesso"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Erro ao parsear NFe: {str(e)}",
                "document_type": "nfe"
            }

    async def _parse_nfce(self, root: ET.Element) -> Dict[str, Any]:
        """Parse NFCe (Nota Fiscal de Consumidor Eletrônica)"""
        try:
            # Similar ao NFe mas com estrutura específica da NFCe
            return await self._parse_nfe(root)  # Reutiliza lógica similar
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro ao parsear NFCe: {str(e)}",
                "document_type": "nfce"
            }

    async def _parse_cte(self, root: ET.Element) -> Dict[str, Any]:
        """Parse CTe (Conhecimento de Transporte Eletrônico)"""
        try:
            # Namespace CTe
            ns = {'cte': 'http://www.portalfiscal.inf.br/cte'}

            # Dados básicos similares ao NFe
            inf_cte = root.find('.//cte:infCte', ns)
            if inf_cte is None:
                inf_cte = root.find('.//infCte')

            if inf_cte is None:
                return self._parse_generic(root)

            # Implementação específica para CTe seria aqui
            return {
                "success": True,
                "document_type": "cte",
                "document_number": inf_cte.get('Id', '').replace('CTe', '') if inf_cte.get('Id') else '',
                "total_value": 0,  # Implementar extração específica
                "date": "",  # Implementar extração específica
                "issuer": "",  # Implementar extração específica
                "recipient": "",  # Implementar extração específica
                "validation_status": "processed",
                "validation_notes": "CTe processado (funcionalidade básica)"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Erro ao parsear CTe: {str(e)}",
                "document_type": "cte"
            }

    async def _parse_generic(self, root: ET.Element) -> Dict[str, Any]:
        """Parse genérico para outros tipos de documento"""
        try:
            return {
                "success": True,
                "document_type": "generic",
                "document_number": "",
                "total_value": 0,
                "date": "",
                "issuer": "",
                "recipient": "",
                "validation_status": "processed",
                "validation_notes": "Documento genérico processado"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro ao parsear documento genérico: {str(e)}",
                "document_type": "generic"
            }

    def _extract_from_text(self, text: str) -> Dict[str, Any]:
        """Extrai informações básicas de texto via regex"""
        extracted = {}

        # Detectar tipo de documento
        if 'NFE' in text.upper() or 'NOTA FISCAL' in text.upper():
            extracted['document_type'] = 'nfe'
        elif 'NFCE' in text.upper():
            extracted['document_type'] = 'nfce'
        elif 'CTE' in text.upper() or 'CONHECIMENTO' in text.upper():
            extracted['document_type'] = 'cte'
        else:
            extracted['document_type'] = 'unknown'

        # Extrair número do documento
        doc_number_match = re.search(r'(?:NFE|NFCE|CTE)[-\s]*(\d+)', text.upper())
        if doc_number_match:
            extracted['document_number'] = doc_number_match.group(1)

        # Extrair valor total
        value_match = re.search(r'R\$\s*([0-9.,]+)', text.replace(',', '.'))
        if value_match:
            try:
                extracted['total_value'] = float(value_match.group(1).replace('.', '').replace(',', '.'))
            except:
                extracted['total_value'] = 0

        # Extrair data
        date_match = re.search(r'(\d{2}/\d{2}/\d{4})', text)
        if date_match:
            extracted['date'] = date_match.group(1)

        # Extrair emitente (CNPJ)
        cnpj_match = re.search(r'(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})', text)
        if cnpj_match:
            extracted['issuer_cnpj'] = cnpj_match.group(1)

        return extracted

    def _get_text(self, element: Optional[ET.Element]) -> str:
        """Extrai texto de elemento XML"""
        if element is None:
            return ""
        return element.text or ""

    def _clean_number(self, text: str) -> float:
        """Limpa e converte texto para número"""
        if not text:
            return 0.0

        # Remove caracteres não numéricos exceto . e ,
        cleaned = re.sub(r'[^\d.,]', '', text)

        # Converte para float
        try:
            # Substitui , por . se for separador decimal
            if ',' in cleaned and '.' in cleaned:
                # Determinar qual é separador de milhares e decimal
                if cleaned.count(',') == 1 and cleaned.count('.') > 1:
                    cleaned = cleaned.replace('.', '').replace(',', '.')
                else:
                    cleaned = cleaned.replace(',', '')
            else:
                cleaned = cleaned.replace(',', '.')

            return float(cleaned)
        except:
            return 0.0