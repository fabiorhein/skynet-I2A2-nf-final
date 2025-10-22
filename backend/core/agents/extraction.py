"""
SkyNET-I2A2 - ExtractionAgent
Agente especializado em extração de dados de documentos fiscais
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from uuid import UUID
from pathlib import Path

import pytesseract
from pdf2image import convert_from_path
import PyPDF2
from lxml import etree
import pandas as pd

from ..llm import LLMOrchestrator
from ..memory import MemoryManager
from ...config import settings, AgentSettings


class OCRExtractionTool:
    """Ferramenta para extração de texto via OCR"""
    
    def __init__(self):
        self.agent_settings = AgentSettings()
        self.language = self.agent_settings.OCR_LANGUAGE
        self.confidence_threshold = self.agent_settings.OCR_CONFIDENCE_THRESHOLD
        self.dpi = self.agent_settings.PDF_DPI
    
    async def extract_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Extrai texto de PDF usando OCR"""
        try:
            start_time = time.time()
            
            # Converte PDF para imagens
            images = convert_from_path(
                pdf_path, 
                dpi=self.dpi,
                first_page=1,
                last_page=None
            )
            
            extracted_text = []
            confidence_scores = []
            
            for i, image in enumerate(images):
                # OCR com Tesseract
                data = pytesseract.image_to_data(
                    image, 
                    lang=self.language,
                    output_type=pytesseract.Output.DICT
                )
                
                # Filtra texto com confiança mínima
                page_text = []
                for j in range(len(data['text'])):
                    if int(data['conf'][j]) > (self.confidence_threshold * 100):
                        text = data['text'][j].strip()
                        if text:
                            page_text.append(text)
                
                page_text_combined = ' '.join(page_text)
                extracted_text.append(page_text_combined)
                
                # Calcula confiança média da página
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                confidence_scores.append(avg_confidence / 100)
            
            processing_time = (time.time() - start_time) * 1000
            
            return {
                "text": '\n\n'.join(extracted_text),
                "pages_count": len(images),
                "confidence_scores": confidence_scores,
                "average_confidence": sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0,
                "processing_time_ms": processing_time,
                "method": "tesseract_ocr"
            }
            
        except Exception as e:
            raise Exception(f"Erro na extração OCR: {str(e)}")
    
    async def extract_from_image(self, image_path: str) -> Dict[str, Any]:
        """Extrai texto de imagem"""
        try:
            start_time = time.time()
            
            # OCR direto da imagem
            data = pytesseract.image_to_data(
                image_path,
                lang=self.language,
                output_type=pytesseract.Output.DICT
            )
            
            # Filtra texto com confiança mínima
            extracted_text = []
            confidences = []
            
            for i in range(len(data['text'])):
                if int(data['conf'][i]) > (self.confidence_threshold * 100):
                    text = data['text'][i].strip()
                    if text:
                        extracted_text.append(text)
                        confidences.append(int(data['conf'][i]))
            
            text_combined = ' '.join(extracted_text)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            processing_time = (time.time() - start_time) * 1000
            
            return {
                "text": text_combined,
                "confidence": avg_confidence / 100,
                "processing_time_ms": processing_time,
                "method": "tesseract_ocr"
            }
            
        except Exception as e:
            raise Exception(f"Erro na extração de imagem: {str(e)}")


class XMLParsingTool:
    """Ferramenta para parsing de XML de documentos fiscais"""
    
    def __init__(self):
        self.namespaces = {
            'nfe': 'http://www.portalfiscal.inf.br/nfe',
            'cte': 'http://www.portalfiscal.inf.br/cte',
            'nfc': 'http://www.portalfiscal.inf.br/nfce'
        }
    
    async def parse_nfe(self, xml_path: str) -> Dict[str, Any]:
        """Parse XML de NFe"""
        try:
            tree = etree.parse(xml_path)
            root = tree.getroot()
            
            # Remove namespace para facilitar parsing
            for elem in root.iter():
                if elem.tag.startswith('{'):
                    elem.tag = elem.tag.split('}')[1]
            
            # Extrai dados principais
            inf_nfe = root.find('.//infNFe')
            if inf_nfe is None:
                raise Exception("Estrutura XML inválida - infNFe não encontrado")
            
            # Dados do emitente
            emit = inf_nfe.find('.//emit')
            emissor = {}
            if emit is not None:
                emissor = {
                    "cnpj": emit.findtext('CNPJ', ''),
                    "nome": emit.findtext('xNome', ''),
                    "fantasia": emit.findtext('xFant', ''),
                    "endereco": self._extract_endereco(emit)
                }
            
            # Dados do destinatário
            dest = inf_nfe.find('.//dest')
            destinatario = {}
            if dest is not None:
                destinatario = {
                    "cnpj": dest.findtext('CNPJ', ''),
                    "cpf": dest.findtext('CPF', ''),
                    "nome": dest.findtext('xNome', ''),
                    "endereco": self._extract_endereco(dest)
                }
            
            # Dados da NFe
            ide = inf_nfe.find('.//ide')
            nfe_data = {}
            if ide is not None:
                nfe_data = {
                    "numero": ide.findtext('nNF', ''),
                    "serie": ide.findtext('serie', ''),
                    "data_emissao": ide.findtext('dhEmi', ''),
                    "chave_acesso": inf_nfe.get('Id', '').replace('NFe', ''),
                    "modelo": ide.findtext('mod', ''),
                    "tipo_emissao": ide.findtext('tpEmis', ''),
                    "finalidade": ide.findtext('finNFe', '')
                }
            
            # Totalizadores
            total = inf_nfe.find('.//total')
            valores = {}
            if total is not None:
                icms_tot = total.find('.//ICMSTot')
                if icms_tot is not None:
                    valores = {
                        "total_produtos": float(icms_tot.findtext('vProd', '0').replace(',', '.')),
                        "total_servicos": float(icms_tot.findtext('vServ', '0').replace(',', '.')),
                        "total_geral": float(icms_tot.findtext('vNF', '0').replace(',', '.')),
                        "base_icms": float(icms_tot.findtext('vBC', '0').replace(',', '.')),
                        "valor_icms": float(icms_tot.findtext('vICMS', '0').replace(',', '.')),
                        "base_icms_st": float(icms_tot.findtext('vBCST', '0').replace(',', '.')),
                        "valor_icms_st": float(icms_tot.findtext('vST', '0').replace(',', '.')),
                        "valor_ipi": float(icms_tot.findtext('vIPI', '0').replace(',', '.')),
                        "valor_pis": float(icms_tot.findtext('vPIS', '0').replace(',', '.')),
                        "valor_cofins": float(icms_tot.findtext('vCOFINS', '0').replace(',', '.'))
                    }
            
            # Itens
            itens = []
            dets = inf_nfe.findall('.//det')
            for det in dets:
                prod = det.find('.//prod')
                if prod is not None:
                    item = {
                        "codigo": prod.findtext('cProd', ''),
                        "descricao": prod.findtext('xProd', ''),
                        "ncm": prod.findtext('NCM', ''),
                        "cfop": prod.findtext('CFOP', ''),
                        "unidade": prod.findtext('uCom', ''),
                        "quantidade": float(prod.findtext('qCom', '0').replace(',', '.')),
                        "valor_unitario": float(prod.findtext('vUnCom', '0').replace(',', '.')),
                        "valor_total": float(prod.findtext('vProd', '0').replace(',', '.'))
                    }
                    
                    # Impostos do item
                    imposto = det.find('.//imposto')
                    if imposto is not None:
                        icms = imposto.find('.//ICMS')
                        if icms is not None:
                            item["icms"] = {
                                "cst": icms.findtext('CST', ''),
                                "base_calculo": float(icms.findtext('vBC', '0').replace(',', '.')),
                                "aliquota": float(icms.findtext('pICMS', '0').replace(',', '.')),
                                "valor": float(icms.findtext('vICMS', '0').replace(',', '.'))
                            }
                    
                    itens.append(item)
            
            return {
                "tipo_documento": "NFe",
                "emissor": emissor,
                "destinatario": destinatario,
                "dados_nfe": nfe_data,
                "valores": valores,
                "itens": itens,
                "status": "parsed_successfully"
            }
            
        except Exception as e:
            raise Exception(f"Erro no parsing XML NFe: {str(e)}")
    
    def _extract_endereco(self, element) -> Dict[str, str]:
        """Extrai dados de endereço"""
        ender = element.find('.//enderEmit') or element.find('.//enderDest')
        if ender is not None:
            return {
                "logradouro": ender.findtext('xLgr', ''),
                "numero": ender.findtext('nro', ''),
                "complemento": ender.findtext('xCpl', ''),
                "bairro": ender.findtext('xBairro', ''),
                "municipio": ender.findtext('xMun', ''),
                "uf": ender.findtext('UF', ''),
                "cep": ender.findtext('CEP', ''),
                "pais": ender.findtext('xPais', '')
            }
        return {}


class DocumentValidationTool:
    """Ferramenta para validação de documentos"""
    
    def __init__(self):
        self.agent_settings = AgentSettings()
    
    async def validate_document(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida documento extraído"""
        try:
            validation_results = {
                "is_valid": True,
                "errors": [],
                "warnings": [],
                "score": 100
            }
            
            # Validações básicas
            if not extracted_data.get("text") and not extracted_data.get("dados_nfe"):
                validation_results["errors"].append("Nenhum conteúdo extraído")
                validation_results["is_valid"] = False
                validation_results["score"] = 0
            
            # Validações específicas para NFe
            if "dados_nfe" in extracted_data:
                nfe_data = extracted_data["dados_nfe"]
                
                # Valida chave de acesso
                chave = nfe_data.get("chave_acesso", "")
                if len(chave) != 44:
                    validation_results["warnings"].append("Chave de acesso inválida")
                    validation_results["score"] -= 10
                
                # Valida CNPJ do emitente
                cnpj_emit = extracted_data.get("emissor", {}).get("cnpj", "")
                if not self._validate_cnpj(cnpj_emit):
                    validation_results["warnings"].append("CNPJ do emitente inválido")
                    validation_results["score"] -= 5
            
            # Validações de texto extraído
            if "text" in extracted_data:
                text = extracted_data["text"]
                if len(text.strip()) < 50:
                    validation_results["warnings"].append("Texto extraído muito curto")
                    validation_results["score"] -= 5
                
                # Verifica se contém informações fiscais
                fiscal_keywords = ["nfe", "nfce", "cte", "cfop", "ncm", "icms", "ipi"]
                text_lower = text.lower()
                found_keywords = [kw for kw in fiscal_keywords if kw in text_lower]
                
                if len(found_keywords) < 2:
                    validation_results["warnings"].append("Poucos indicadores fiscais encontrados")
                    validation_results["score"] -= 10
            
            return validation_results
            
        except Exception as e:
            return {
                "is_valid": False,
                "errors": [f"Erro na validação: {str(e)}"],
                "warnings": [],
                "score": 0
            }
    
    def _validate_cnpj(self, cnpj: str) -> bool:
        """Valida CNPJ básico"""
        if not cnpj or len(cnpj) != 14:
            return False
        
        # Remove formatação
        cnpj = ''.join(filter(str.isdigit, cnpj))
        return len(cnpj) == 14


class ExtractionAgent:
    """
    Agente Especializado em Extração de Dados
    
    Responsabilidades:
    - Processar documentos fiscais (PDF, XML)
    - Executar OCR com Tesseract + LayoutLM
    - Parser XML de NFe/NFCe/CTe
    - Retornar JSON estruturado
    """
    
    def __init__(self):
        """Inicializa o ExtractionAgent"""
        self.llm = LLMOrchestrator()
        self.memory = MemoryManager()
        self.agent_settings = AgentSettings()
        
        # Ferramentas
        self.ocr_tool = OCRExtractionTool()
        self.xml_tool = XMLParsingTool()
        self.validation_tool = DocumentValidationTool()
        
        # Templates de prompt
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """Constrói o prompt de sistema para o agente"""
        return f"""
Você é o ExtractionAgent do sistema SkyNET-I2A2, especialista em extração de dados de documentos fiscais.

## SUAS RESPONSABILIDADES:
1. **OCR Avançado**: Extrair texto de PDFs e imagens com alta precisão
2. **Parsing XML**: Processar NFe/NFCe/CTe estruturados
3. **Validação**: Verificar integridade e qualidade dos dados extraídos
4. **Estruturação**: Organizar dados em formato JSON padronizado

## FERRAMENTAS DISPONÍVEIS:
- **OCRExtractionTool**: Tesseract + LayoutLM para OCR
- **XMLParsingTool**: Parser especializado em documentos fiscais
- **DocumentValidationTool**: Validação de integridade

## TIPOS DE DOCUMENTOS SUPORTADOS:
- NFe (Nota Fiscal Eletrônica)
- NFCe (Nota Fiscal do Consumidor Eletrônica)  
- CTe (Conhecimento de Transporte Eletrônico)
- PDFs escaneados
- Imagens (JPG, PNG)

## DIRETRIZES:
- Priorize precisão sobre velocidade
- Valide dados fiscais conforme legislação brasileira
- Mantenha estrutura consistente nos retornos
- Documente problemas de extração
- Use cache quando apropriado

Data/Hora atual: {datetime.now().strftime("%d/%m/%Y %H:%M")}
"""
    
    async def process_document(self, file_path: str, file_type: str, user_id: UUID) -> Dict[str, Any]:
        """
        Processa documento fiscal
        
        Args:
            file_path: Caminho do arquivo
            file_type: Tipo do arquivo (pdf, xml, jpg, png)
            user_id: ID do usuário
            
        Returns:
            Dados extraídos estruturados
        """
        try:
            start_time = time.time()
            
            # Determina método de extração baseado no tipo
            if file_type.lower() == 'xml':
                extracted_data = await self._process_xml(file_path)
            elif file_type.lower() in ['pdf', 'jpg', 'jpeg', 'png']:
                extracted_data = await self._process_ocr(file_path, file_type)
            else:
                raise Exception(f"Tipo de arquivo não suportado: {file_type}")
            
            # Valida dados extraídos
            validation = await self.validation_tool.validate_document(extracted_data)
            extracted_data["validation"] = validation
            
            # Melhora extração com LLM se necessário
            if validation["score"] < 70:
                enhanced_data = await self._enhance_with_llm(extracted_data, user_id)
                extracted_data.update(enhanced_data)
            
            # Adiciona metadados
            processing_time = (time.time() - start_time) * 1000
            extracted_data["metadata"] = {
                "agent": "ExtractionAgent",
                "processing_time_ms": processing_time,
                "file_type": file_type,
                "timestamp": datetime.now().isoformat(),
                "user_id": str(user_id)
            }
            
            # Salva na memória
            await self.memory.save_extraction_result(user_id, extracted_data)
            
            return extracted_data
            
        except Exception as e:
            error_data = {
                "error": str(e),
                "agent": "ExtractionAgent",
                "timestamp": datetime.now().isoformat(),
                "status": "failed"
            }
            
            await self.memory.save_error(user_id, "extraction", str(e))
            return error_data
    
    async def _process_xml(self, xml_path: str) -> Dict[str, Any]:
        """Processa arquivo XML"""
        try:
            return await self.xml_tool.parse_nfe(xml_path)
        except Exception as e:
            raise Exception(f"Erro no processamento XML: {str(e)}")
    
    async def _process_ocr(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """Processa arquivo via OCR"""
        try:
            if file_type.lower() == 'pdf':
                return await self.ocr_tool.extract_from_pdf(file_path)
            else:
                return await self.ocr_tool.extract_from_image(file_path)
        except Exception as e:
            raise Exception(f"Erro no processamento OCR: {str(e)}")
    
    async def _enhance_with_llm(self, extracted_data: Dict[str, Any], user_id: UUID) -> Dict[str, Any]:
        """Melhora extração usando LLM"""
        try:
            text = extracted_data.get("text", "")
            if not text:
                return {}
            
            prompt = f"""
Analise o seguinte texto extraído de documento fiscal e melhore a estruturação dos dados:

TEXTO EXTRAÍDO:
{text}

Retorne um JSON estruturado com:
- Dados do emitente (nome, CNPJ, endereço)
- Dados do destinatário (nome, CNPJ/CPF, endereço)  
- Dados do documento (número, data, valor total)
- Itens (descrição, quantidade, valor unitário, CFOP, NCM)
- Impostos (ICMS, IPI, PIS, COFINS)

Seja preciso e mantenha conformidade com legislação fiscal brasileira.
"""
            
            result = await self.llm.route_request(
                task_type="document_analysis",
                content=prompt,
                user_id=user_id
            )
            
            # Tenta fazer parse do JSON retornado
            try:
                enhanced_data = json.loads(result.get("text", "{}"))
                return {"llm_enhanced": enhanced_data}
            except json.JSONDecodeError:
                return {"llm_enhanced": {"raw_response": result.get("text", "")}}
                
        except Exception as e:
            return {"llm_enhanced": {"error": str(e)}}
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do agente"""
        try:
            # Testa OCR
            ocr_status = "healthy"
            try:
                # Teste básico do Tesseract
                pytesseract.get_tesseract_version()
            except Exception:
                ocr_status = "unhealthy"
            
            # Testa XML parsing
            xml_status = "healthy"
            try:
                etree.parse
            except Exception:
                xml_status = "unhealthy"
            
            return {
                "status": "healthy" if ocr_status == "healthy" and xml_status == "healthy" else "degraded",
                "ocr": ocr_status,
                "xml_parsing": xml_status,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# Factory function
def create_extraction_agent() -> ExtractionAgent:
    """Cria instância do ExtractionAgent"""
    return ExtractionAgent()