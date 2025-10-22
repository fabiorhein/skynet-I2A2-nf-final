"""
SkyNET-I2A2 - ClassifierAgent
Agente especializado em classificação e validação fiscal
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from uuid import UUID

from ..llm import LLMOrchestrator
from ..memory import MemoryManager
from ...config import settings, AgentSettings


class BusinessRulesTool:
    """Ferramenta para regras de negócio por setor"""
    
    def __init__(self):
        self.agent_settings = AgentSettings()
        self.sector_rules = self._load_sector_rules()
    
    def _load_sector_rules(self) -> Dict[str, Dict[str, Any]]:
        """Carrega regras de negócio por setor"""
        return {
            "industria": {
                "cfop_validos": ["1101", "1102", "2101", "2102", "5101", "5102", "6101", "6102"],
                "cst_validos": ["00", "10", "20", "30", "40", "41", "50", "51", "60", "70", "90"],
                "ncm_obrigatorio": True,
                "ipi_obrigatorio": True,
                "regime_tributario": ["normal", "simples_nacional"]
            },
            "comercio": {
                "cfop_validos": ["1102", "2102", "5102", "6102", "1202", "2202", "5202", "6202"],
                "cst_validos": ["00", "10", "20", "30", "40", "41", "50", "51", "60", "70", "90"],
                "ncm_obrigatorio": True,
                "ipi_obrigatorio": False,
                "regime_tributario": ["normal", "simples_nacional"]
            },
            "servicos": {
                "cfop_validos": ["1202", "2202", "5202", "6202"],
                "cst_validos": ["00", "10", "20", "30", "40", "41", "50", "51", "60", "70", "90"],
                "ncm_obrigatorio": False,
                "ipi_obrigatorio": False,
                "regime_tributario": ["normal", "simples_nacional"]
            },
            "agronegocio": {
                "cfop_validos": ["1101", "1102", "2101", "2102", "5101", "5102", "6101", "6102"],
                "cst_validos": ["00", "10", "20", "30", "40", "41", "50", "51", "60", "70", "90"],
                "ncm_obrigatorio": True,
                "ipi_obrigatorio": False,
                "regime_tributario": ["normal", "simples_nacional"]
            }
        }
    
    async def validate_business_rules(self, document_data: Dict[str, Any], sector: str = "comercio") -> Dict[str, Any]:
        """Valida regras de negócio para o setor"""
        try:
            rules = self.sector_rules.get(sector, self.sector_rules["comercio"])
            validation_results = {
                "sector": sector,
                "is_valid": True,
                "errors": [],
                "warnings": [],
                "score": 100
            }
            
            # Valida CFOP
            cfop = document_data.get("cfop", "")
            if cfop and cfop not in rules["cfop_validos"]:
                validation_results["errors"].append(f"CFOP {cfop} inválido para setor {sector}")
                validation_results["is_valid"] = False
                validation_results["score"] -= 20
            
            # Valida CST
            cst = document_data.get("cst", "")
            if cst and cst not in rules["cst_validos"]:
                validation_results["errors"].append(f"CST {cst} inválido para setor {sector}")
                validation_results["is_valid"] = False
                validation_results["score"] -= 15
            
            # Valida NCM (se obrigatório)
            ncm = document_data.get("ncm", "")
            if rules["ncm_obrigatorio"] and not ncm:
                validation_results["errors"].append(f"NCM obrigatório para setor {sector}")
                validation_results["is_valid"] = False
                validation_results["score"] -= 25
            
            # Valida IPI (se obrigatório)
            ipi = document_data.get("ipi", 0)
            if rules["ipi_obrigatorio"] and ipi == 0:
                validation_results["warnings"].append(f"IPI pode ser obrigatório para setor {sector}")
                validation_results["score"] -= 5
            
            return validation_results
            
        except Exception as e:
            return {
                "sector": sector,
                "is_valid": False,
                "errors": [f"Erro na validação: {str(e)}"],
                "warnings": [],
                "score": 0
            }


class FiscalValidationTool:
    """Ferramenta para validação fiscal"""
    
    def __init__(self):
        self.agent_settings = AgentSettings()
        self.cfop_validator = CFOPValidator()
        self.ncm_validator = NCMValidator()
    
    async def validate_fiscal_data(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida dados fiscais"""
        try:
            validation_results = {
                "is_valid": True,
                "errors": [],
                "warnings": [],
                "score": 100,
                "validations": {}
            }
            
            # Valida CFOP
            cfop_validation = await self.cfop_validator.validate_cfop(document_data.get("cfop", ""))
            validation_results["validations"]["cfop"] = cfop_validation
            if not cfop_validation["is_valid"]:
                validation_results["errors"].extend(cfop_validation["errors"])
                validation_results["is_valid"] = False
                validation_results["score"] -= 20
            
            # Valida NCM
            ncm_validation = await self.ncm_validator.validate_ncm(document_data.get("ncm", ""))
            validation_results["validations"]["ncm"] = ncm_validation
            if not ncm_validation["is_valid"]:
                validation_results["warnings"].extend(ncm_validation["warnings"])
                validation_results["score"] -= 10
            
            # Valida CST
            cst_validation = self._validate_cst(document_data.get("cst", ""))
            validation_results["validations"]["cst"] = cst_validation
            if not cst_validation["is_valid"]:
                validation_results["errors"].extend(cst_validation["errors"])
                validation_results["is_valid"] = False
                validation_results["score"] -= 15
            
            # Valida valores
            values_validation = self._validate_values(document_data)
            validation_results["validations"]["values"] = values_validation
            if not values_validation["is_valid"]:
                validation_results["errors"].extend(values_validation["errors"])
                validation_results["is_valid"] = False
                validation_results["score"] -= 25
            
            return validation_results
            
        except Exception as e:
            return {
                "is_valid": False,
                "errors": [f"Erro na validação fiscal: {str(e)}"],
                "warnings": [],
                "score": 0
            }
    
    def _validate_cst(self, cst: str) -> Dict[str, Any]:
        """Valida CST"""
        valid_csts = ["00", "10", "20", "30", "40", "41", "50", "51", "60", "70", "90"]
        
        if not cst:
            return {"is_valid": False, "errors": ["CST não informado"]}
        
        if cst not in valid_csts:
            return {"is_valid": False, "errors": [f"CST {cst} inválido"]}
        
        return {"is_valid": True, "cst": cst}
    
    def _validate_values(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida valores fiscais"""
        try:
            total = float(document_data.get("total", 0))
            base_icms = float(document_data.get("base_icms", 0))
            valor_icms = float(document_data.get("valor_icms", 0))
            
            if total <= 0:
                return {"is_valid": False, "errors": ["Valor total deve ser maior que zero"]}
            
            if base_icms > total:
                return {"is_valid": False, "errors": ["Base ICMS maior que valor total"]}
            
            if valor_icms > base_icms:
                return {"is_valid": False, "errors": ["Valor ICMS maior que base de cálculo"]}
            
            return {"is_valid": True, "values": {"total": total, "base_icms": base_icms, "valor_icms": valor_icms}}
            
        except (ValueError, TypeError):
            return {"is_valid": False, "errors": ["Valores fiscais inválidos"]}


class CFOPValidator:
    """Validador de CFOP"""
    
    def __init__(self):
        self.cfop_codes = self._load_cfop_codes()
    
    def _load_cfop_codes(self) -> Dict[str, Dict[str, Any]]:
        """Carrega códigos CFOP válidos"""
        return {
            "1101": {"description": "Compra para industrialização", "type": "entrada", "category": "industrializacao"},
            "1102": {"description": "Compra para comercialização", "type": "entrada", "category": "comercializacao"},
            "1202": {"description": "Compra para utilização na prestação de serviços", "type": "entrada", "category": "servicos"},
            "2101": {"description": "Venda de produção do estabelecimento", "type": "saida", "category": "venda_propria"},
            "2102": {"description": "Venda de mercadoria adquirida ou recebida de terceiros", "type": "saida", "category": "venda_terceiros"},
            "5101": {"description": "Entrada de mercadoria ou bem para consumo", "type": "entrada", "category": "consumo"},
            "5102": {"description": "Entrada de mercadoria ou bem para ativo permanente", "type": "entrada", "category": "ativo_permanente"},
            "6101": {"description": "Saída de mercadoria ou bem para consumo", "type": "saida", "category": "consumo"},
            "6102": {"description": "Saída de mercadoria ou bem para ativo permanente", "type": "saida", "category": "ativo_permanente"}
        }
    
    async def validate_cfop(self, cfop: str) -> Dict[str, Any]:
        """Valida código CFOP"""
        if not cfop:
            return {"is_valid": False, "errors": ["CFOP não informado"]}
        
        if cfop not in self.cfop_codes:
            return {"is_valid": False, "errors": [f"CFOP {cfop} não encontrado"]}
        
        cfop_info = self.cfop_codes[cfop]
        return {
            "is_valid": True,
            "cfop": cfop,
            "description": cfop_info["description"],
            "type": cfop_info["type"],
            "category": cfop_info["category"]
        }


class NCMValidator:
    """Validador de NCM"""
    
    def __init__(self):
        self.ncm_categories = self._load_ncm_categories()
    
    def _load_ncm_categories(self) -> Dict[str, Dict[str, Any]]:
        """Carrega categorias NCM"""
        return {
            "01": {"description": "Animais vivos", "category": "animais"},
            "02": {"description": "Carnes e miudezas comestíveis", "category": "carnes"},
            "03": {"description": "Peixes e crustáceos", "category": "peixes"},
            "04": {"description": "Leite e laticínios", "category": "laticinios"},
            "05": {"description": "Outros produtos de origem animal", "category": "outros_animais"},
            "06": {"description": "Árvores e outras plantas vivas", "category": "plantas"},
            "07": {"description": "Legumes, verduras e raízes", "category": "legumes"},
            "08": {"description": "Frutas e nozes", "category": "frutas"},
            "09": {"description": "Café, chá e especiarias", "category": "bebidas"},
            "10": {"description": "Cereais", "category": "cereais"}
        }
    
    async def validate_ncm(self, ncm: str) -> Dict[str, Any]:
        """Valida código NCM"""
        if not ncm:
            return {"is_valid": True, "warnings": ["NCM não informado"]}
        
        if len(ncm) != 8:
            return {"is_valid": False, "warnings": [f"NCM deve ter 8 dígitos, informado: {len(ncm)}"]}
        
        if not ncm.isdigit():
            return {"is_valid": False, "warnings": ["NCM deve conter apenas números"]}
        
        # Valida categoria
        category = ncm[:2]
        if category in self.ncm_categories:
            ncm_info = self.ncm_categories[category]
            return {
                "is_valid": True,
                "ncm": ncm,
                "category": category,
                "description": ncm_info["description"],
                "category_type": ncm_info["category"]
            }
        else:
            return {
                "is_valid": True,
                "ncm": ncm,
                "warnings": [f"Categoria NCM {category} não reconhecida"]
            }


class DocumentClassifier:
    """Classificador de documentos"""
    
    def __init__(self):
        self.classification_rules = self._load_classification_rules()
    
    def _load_classification_rules(self) -> Dict[str, Dict[str, Any]]:
        """Carrega regras de classificação"""
        return {
            "compra": {
                "cfop_patterns": ["1", "2"],
                "keywords": ["compra", "fornecedor", "entrada"],
                "value_threshold": 0
            },
            "venda": {
                "cfop_patterns": ["5", "6"],
                "keywords": ["venda", "cliente", "saida"],
                "value_threshold": 0
            },
            "servico": {
                "cfop_patterns": ["1", "2", "5", "6"],
                "keywords": ["servico", "prestacao", "consultoria"],
                "value_threshold": 0
            },
            "transferencia": {
                "cfop_patterns": ["1", "2", "5", "6"],
                "keywords": ["transferencia", "movimentacao"],
                "value_threshold": 0
            }
        }
    
    async def classify_document(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Classifica documento"""
        try:
            cfop = document_data.get("cfop", "")
            description = document_data.get("description", "").lower()
            value = float(document_data.get("total", 0))
            
            classification_scores = {}
            
            for doc_type, rules in self.classification_rules.items():
                score = 0
                
                # Verifica padrão CFOP
                if cfop and any(cfop.startswith(pattern) for pattern in rules["cfop_patterns"]):
                    score += 40
                
                # Verifica palavras-chave
                keyword_matches = sum(1 for keyword in rules["keywords"] if keyword in description)
                if keyword_matches > 0:
                    score += keyword_matches * 20
                
                # Verifica valor
                if value >= rules["value_threshold"]:
                    score += 10
                
                classification_scores[doc_type] = score
            
            # Determina classificação
            best_classification = max(classification_scores, key=classification_scores.get)
            confidence = classification_scores[best_classification] / 100
            
            return {
                "classification": best_classification,
                "confidence": min(confidence, 1.0),
                "scores": classification_scores,
                "reasoning": self._generate_reasoning(document_data, best_classification, confidence)
            }
            
        except Exception as e:
            return {
                "classification": "unknown",
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _generate_reasoning(self, document_data: Dict[str, Any], classification: str, confidence: float) -> str:
        """Gera explicação da classificação"""
        cfop = document_data.get("cfop", "")
        description = document_data.get("description", "")
        
        reasoning_parts = []
        
        if cfop:
            reasoning_parts.append(f"CFOP {cfop} indica {classification}")
        
        if description:
            reasoning_parts.append(f"Descrição sugere {classification}")
        
        reasoning_parts.append(f"Confiança: {confidence:.1%}")
        
        return " | ".join(reasoning_parts)


class ClassifierAgent:
    """
    Agente Especializado em Classificação e Validação Fiscal
    
    Responsabilidades:
    - Classificar documentos (tipo: compra/venda/serviço)
    - Validar campos fiscais (CFOP, CST, NCM)
    - Aplicar regras de negócio por setor
    - Detectar inconsistências
    """
    
    def __init__(self):
        """Inicializa o ClassifierAgent"""
        self.llm = LLMOrchestrator()
        self.memory = MemoryManager()
        self.agent_settings = AgentSettings()
        
        # Ferramentas
        self.business_rules_tool = BusinessRulesTool()
        self.fiscal_validation_tool = FiscalValidationTool()
        self.document_classifier = DocumentClassifier()
        
        # Templates de prompt
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """Constrói o prompt de sistema para o agente"""
        return f"""
Você é o ClassifierAgent do sistema SkyNET-I2A2, especialista em classificação e validação fiscal.

## SUAS RESPONSABILIDADES:
1. **Classificação de Documentos**: Identificar tipo (compra/venda/serviço/transferência)
2. **Validação Fiscal**: Verificar CFOP, CST, NCM, valores
3. **Regras de Negócio**: Aplicar regras específicas por setor
4. **Detecção de Inconsistências**: Identificar problemas fiscais

## FERRAMENTAS DISPONÍVEIS:
- **BusinessRulesTool**: Regras por setor (Indústria, Comércio, Serviços, Agronegócio)
- **FiscalValidationTool**: Validação de campos fiscais
- **DocumentClassifier**: Classificação automática de documentos

## SETORES SUPORTADOS:
- **Indústria**: CFOPs 1101/1102, IPI obrigatório, NCM obrigatório
- **Comércio**: CFOPs 1102/2102, sem IPI, NCM obrigatório
- **Serviços**: CFOPs 1202/2202, sem IPI, sem NCM
- **Agronegócio**: CFOPs 1101/1102, sem IPI, NCM obrigatório

## VALIDAÇÕES REALIZADAS:
- CFOP: Códigos válidos por setor
- CST: Códigos de situação tributária
- NCM: Código de classificação de mercadorias
- Valores: Consistência entre total, base e impostos

## DIRETRIZES:
- Priorize conformidade fiscal
- Aplique regras específicas por setor
- Documente inconsistências encontradas
- Sugira correções quando possível
- Mantenha histórico de validações

Data/Hora atual: {datetime.now().strftime("%d/%m/%Y %H:%M")}
"""
    
    async def classify_and_validate(self, document_data: Dict[str, Any], user_id: UUID, 
                                  sector: str = "comercio") -> Dict[str, Any]:
        """
        Classifica e valida documento fiscal
        
        Args:
            document_data: Dados do documento
            user_id: ID do usuário
            sector: Setor de atividade
            
        Returns:
            Resultados da classificação e validação
        """
        try:
            start_time = time.time()
            
            # 1. Classifica documento
            classification_result = await self.document_classifier.classify_document(document_data)
            
            # 2. Valida regras de negócio
            business_validation = await self.business_rules_tool.validate_business_rules(
                document_data, sector
            )
            
            # 3. Valida dados fiscais
            fiscal_validation = await self.fiscal_validation_tool.validate_fiscal_data(document_data)
            
            # 4. Gera insights com LLM
            insights = await self._generate_classification_insights(
                document_data, classification_result, business_validation, fiscal_validation, user_id
            )
            
            # 5. Consolida resultados
            results = {
                "classification": classification_result,
                "business_validation": business_validation,
                "fiscal_validation": fiscal_validation,
                "insights": insights,
                "overall_score": self._calculate_overall_score(
                    classification_result, business_validation, fiscal_validation
                )
            }
            
            # Adiciona metadados
            processing_time = (time.time() - start_time) * 1000
            results["metadata"] = {
                "agent": "ClassifierAgent",
                "processing_time_ms": processing_time,
                "sector": sector,
                "timestamp": datetime.now().isoformat(),
                "user_id": str(user_id)
            }
            
            # Salva na memória
            await self.memory.save_classification_result(user_id, results)
            
            return results
            
        except Exception as e:
            error_data = {
                "error": str(e),
                "agent": "ClassifierAgent",
                "timestamp": datetime.now().isoformat(),
                "status": "failed"
            }
            
            await self.memory.save_error(user_id, "classification", str(e))
            return error_data
    
    async def _generate_classification_insights(self, document_data: Dict[str, Any], 
                                               classification: Dict[str, Any],
                                               business_validation: Dict[str, Any],
                                               fiscal_validation: Dict[str, Any],
                                               user_id: UUID) -> Dict[str, Any]:
        """Gera insights sobre classificação e validação"""
        try:
            prompt = f"""
Como especialista em classificação fiscal, analise os seguintes resultados:

DADOS DO DOCUMENTO:
{json.dumps(document_data, ensure_ascii=False, indent=2)}

CLASSIFICAÇÃO:
{json.dumps(classification, ensure_ascii=False, indent=2)}

VALIDAÇÃO DE REGRAS DE NEGÓCIO:
{json.dumps(business_validation, ensure_ascii=False, indent=2)}

VALIDAÇÃO FISCAL:
{json.dumps(fiscal_validation, ensure_ascii=False, indent=2)}

Forneça insights sobre:
1. **Classificação**: Se a classificação está correta e por quê
2. **Conformidade**: Se o documento está em conformidade fiscal
3. **Problemas**: Inconsistências ou erros encontrados
4. **Recomendações**: Sugestões para correção ou melhoria
5. **Riscos**: Possíveis problemas fiscais ou auditoria

Seja específico e técnico, mas claro para tomadores de decisão.
"""
            
            result = await self.llm.route_request(
                task_type="fiscal_validation",
                content=prompt,
                user_id=user_id
            )
            
            return {
                "text": result.get("text", ""),
                "model": result.get("model", ""),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    def _calculate_overall_score(self, classification: Dict[str, Any], 
                                business_validation: Dict[str, Any],
                                fiscal_validation: Dict[str, Any]) -> float:
        """Calcula score geral de classificação e validação"""
        try:
            # Score de classificação (peso 30%)
            classification_score = classification.get("confidence", 0) * 100
            
            # Score de validação de negócio (peso 35%)
            business_score = business_validation.get("score", 0)
            
            # Score de validação fiscal (peso 35%)
            fiscal_score = fiscal_validation.get("score", 0)
            
            # Calcula score ponderado
            overall_score = (
                classification_score * 0.30 +
                business_score * 0.35 +
                fiscal_score * 0.35
            )
            
            return round(overall_score, 2)
            
        except Exception:
            return 0.0
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do agente"""
        try:
            # Testa ferramentas
            business_rules_status = "healthy"
            try:
                await self.business_rules_tool.validate_business_rules({}, "comercio")
            except Exception:
                business_rules_status = "unhealthy"
            
            fiscal_validation_status = "healthy"
            try:
                await self.fiscal_validation_tool.validate_fiscal_data({})
            except Exception:
                fiscal_validation_status = "unhealthy"
            
            classification_status = "healthy"
            try:
                await self.document_classifier.classify_document({})
            except Exception:
                classification_status = "unhealthy"
            
            return {
                "status": "healthy" if all(s == "healthy" for s in [business_rules_status, fiscal_validation_status, classification_status]) else "degraded",
                "business_rules": business_rules_status,
                "fiscal_validation": fiscal_validation_status,
                "classification": classification_status,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# Factory function
def create_classifier_agent() -> ClassifierAgent:
    """Cria instância do ClassifierAgent"""
    return ClassifierAgent()