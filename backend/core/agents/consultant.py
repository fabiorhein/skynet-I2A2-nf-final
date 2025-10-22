"""
SkyNET-I2A2 - ConsultantAgent
Agente especializado em insights e consultoria
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


class LLMReasoner:
    """Ferramenta de raciocínio avançado com LLM"""
    
    def __init__(self):
        self.agent_settings = AgentSettings()
    
    async def analyze_context(self, context: Dict[str, Any], question: str, 
                             user_id: UUID) -> Dict[str, Any]:
        """Analisa contexto e gera raciocínio"""
        try:
            # Prepara contexto estruturado
            context_summary = self._prepare_context_summary(context)
            
            prompt = f"""
Como consultor especializado, analise o seguinte contexto e responda à pergunta:

CONTEXTO:
{json.dumps(context_summary, ensure_ascii=False, indent=2)}

PERGUNTA:
{question}

Forneça uma análise estruturada incluindo:
1. **Análise do Contexto**: Principais pontos relevantes
2. **Raciocínio**: Lógica aplicada para chegar à conclusão
3. **Evidências**: Dados e fatos que suportam a resposta
4. **Limitações**: O que não pode ser determinado
5. **Confiança**: Nível de certeza da resposta (0-100%)

Seja preciso, técnico e baseado em evidências.
"""
            
            result = await self.llm.route_request(
                task_type="insights",
                content=prompt,
                user_id=user_id
            )
            
            return {
                "reasoning": result.get("text", ""),
                "model": result.get("model", ""),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    def _prepare_context_summary(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Prepara resumo do contexto"""
        summary = {
            "data_analysis": context.get("analysis_results", {}),
            "document_classification": context.get("classification_results", {}),
            "visualizations": context.get("visualization_results", {}),
            "user_question": context.get("user_question", ""),
            "session_history": context.get("session_history", [])
        }
        
        # Remove dados muito grandes
        for key, value in summary.items():
            if isinstance(value, dict) and len(str(value)) > 1000:
                summary[key] = {"summary": "Dados extensos disponíveis", "size": len(str(value))}
        
        return summary


class InsightGenerator:
    """Gerador de insights especializados"""
    
    def __init__(self):
        self.agent_settings = AgentSettings()
    
    async def generate_insights(self, analysis_data: Dict[str, Any], 
                               user_id: UUID, insight_type: str = "business") -> Dict[str, Any]:
        """Gera insights baseados em análise"""
        try:
            # Prepara dados para análise
            data_summary = self._prepare_analysis_summary(analysis_data)
            
            prompt = f"""
Como consultor especializado em {insight_type}, analise os seguintes dados e gere insights acionáveis:

DADOS DE ANÁLISE:
{json.dumps(data_summary, ensure_ascii=False, indent=2)}

Gere insights estruturados incluindo:

## 1. PRINCIPAIS DESCOBERTAS
- 3-5 descobertas mais importantes
- Evidências que suportam cada descoberta

## 2. PADRÕES E TENDÊNCIAS
- Padrões identificados nos dados
- Tendências observadas
- Sazonalidade ou ciclos

## 3. OPORTUNIDADES
- Oportunidades de melhoria identificadas
- Potencial de crescimento
- Áreas de otimização

## 4. RISCOS E ALERTAS
- Riscos identificados
- Alertas importantes
- Pontos de atenção

## 5. RECOMENDAÇÕES
- Ações específicas recomendadas
- Priorização das ações
- Próximos passos sugeridos

## 6. IMPACTO ESPERADO
- Impacto potencial das recomendações
- Métricas para acompanhar
- Timeline sugerido

Seja específico, acionável e baseado em evidências dos dados.
"""
            
            result = await self.llm.route_request(
                task_type="insights",
                content=prompt,
                user_id=user_id
            )
            
            return {
                "insights": result.get("text", ""),
                "insight_type": insight_type,
                "model": result.get("model", ""),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    def _prepare_analysis_summary(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepara resumo dos dados de análise"""
        summary = {
            "data_shape": analysis_data.get("metadata", {}).get("data_shape", "unknown"),
            "analysis_type": analysis_data.get("metadata", {}).get("analysis_type", "unknown"),
            "key_statistics": analysis_data.get("pandas_analysis", {}).get("descriptive_stats", {}),
            "correlations": analysis_data.get("correlation_analysis", {}).get("high_correlation_pairs", []),
            "outliers": analysis_data.get("outlier_analysis", {}),
            "processing_time": analysis_data.get("metadata", {}).get("processing_time_ms", 0)
        }
        
        return summary


class ReportBuilder:
    """Construtor de relatórios"""
    
    def __init__(self):
        self.agent_settings = AgentSettings()
    
    async def build_report(self, analysis_data: Dict[str, Any], 
                             insights: Dict[str, Any], user_id: UUID) -> Dict[str, Any]:
        """Constrói relatório executivo"""
        try:
            # Prepara dados do relatório
            report_data = self._prepare_report_data(analysis_data, insights)
            
            prompt = f"""
Como consultor sênior, crie um relatório executivo baseado na seguinte análise:

DADOS DA ANÁLISE:
{json.dumps(report_data, ensure_ascii=False, indent=2)}

INSIGHTS GERADOS:
{json.dumps(insights, ensure_ascii=False, indent=2)}

Crie um relatório estruturado com:

# RELATÓRIO EXECUTIVO - ANÁLISE DE DADOS

## RESUMO EXECUTIVO
- Principais conclusões (3-4 pontos)
- Impacto no negócio
- Recomendações prioritárias

## METODOLOGIA
- Abordagem utilizada
- Dados analisados
- Limitações identificadas

## PRINCIPAIS DESCOBERTAS
- Descobertas mais relevantes
- Evidências e métricas
- Significância estatística

## ANÁLISE DETALHADA
- Padrões identificados
- Correlações importantes
- Outliers e anomalias

## RECOMENDAÇÕES
- Ações prioritárias
- Implementação sugerida
- Métricas de acompanhamento

## PRÓXIMOS PASSOS
- Análises adicionais sugeridas
- Monitoramento contínuo
- Revisão periódica

Seja claro, objetivo e focado em valor de negócio.
"""
            
            result = await self.llm.route_request(
                task_type="report_generation",
                content=prompt,
                user_id=user_id
            )
            
            return {
                "report": result.get("text", ""),
                "model": result.get("model", ""),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    def _prepare_report_data(self, analysis_data: Dict[str, Any], 
                           insights: Dict[str, Any]) -> Dict[str, Any]:
        """Prepara dados para o relatório"""
        return {
            "analysis_summary": {
                "data_shape": analysis_data.get("metadata", {}).get("data_shape", "unknown"),
                "processing_time": analysis_data.get("metadata", {}).get("processing_time_ms", 0),
                "analysis_type": analysis_data.get("metadata", {}).get("analysis_type", "unknown")
            },
            "statistics": analysis_data.get("pandas_analysis", {}).get("descriptive_stats", {}),
            "correlations": analysis_data.get("correlation_analysis", {}).get("high_correlation_pairs", []),
            "outliers": analysis_data.get("outlier_analysis", {}),
            "insights": insights.get("insights", "")
        }


class RecommendationEngine:
    """Motor de recomendações"""
    
    def __init__(self):
        self.agent_settings = AgentSettings()
    
    async def generate_recommendations(self, analysis_data: Dict[str, Any], 
                                      user_id: UUID) -> Dict[str, Any]:
        """Gera recomendações baseadas na análise"""
        try:
            # Analisa dados para gerar recomendações
            data_insights = self._analyze_data_for_recommendations(analysis_data)
            
            prompt = f"""
Como consultor especializado, analise os seguintes dados e gere recomendações específicas:

DADOS ANALISADOS:
{json.dumps(data_insights, ensure_ascii=False, indent=2)}

Gere recomendações estruturadas:

## RECOMENDAÇÕES PRIORITÁRIAS
- 3-5 recomendações mais importantes
- Justificativa para cada recomendação
- Impacto esperado

## RECOMENDAÇÕES TÉCNICAS
- Melhorias na qualidade dos dados
- Otimizações técnicas
- Ferramentas ou processos sugeridos

## RECOMENDAÇÕES DE NEGÓCIO
- Oportunidades de crescimento
- Otimizações operacionais
- Estratégias sugeridas

## IMPLEMENTAÇÃO
- Passos para implementação
- Recursos necessários
- Timeline sugerido

## MÉTRICAS DE SUCESSO
- KPIs para acompanhar
- Benchmarks sugeridos
- Revisão periódica

Seja específico, acionável e baseado em evidências.
"""
            
            result = await self.llm.route_request(
                task_type="recommendations",
                content=prompt,
                user_id=user_id
            )
            
            return {
                "recommendations": result.get("text", ""),
                "model": result.get("model", ""),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    def _analyze_data_for_recommendations(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analisa dados para gerar recomendações"""
        return {
            "data_quality": {
                "missing_values": analysis_data.get("pandas_analysis", {}).get("basic_info", {}).get("null_counts", {}),
                "duplicates": analysis_data.get("pandas_analysis", {}).get("basic_info", {}).get("duplicate_rows", 0)
            },
            "statistical_insights": analysis_data.get("pandas_analysis", {}).get("descriptive_stats", {}),
            "correlations": analysis_data.get("correlation_analysis", {}).get("high_correlation_pairs", []),
            "outliers": analysis_data.get("outlier_analysis", {}),
            "processing_metadata": analysis_data.get("metadata", {})
        }


class ConsultantAgent:
    """
    Agente Especializado em Insights e Consultoria
    
    Responsabilidades:
    - Interpretar resultados técnicos
    - Gerar insights e recomendações
    - Responder perguntas contextualizadas
    - Preparar relatórios
    """
    
    def __init__(self):
        """Inicializa o ConsultantAgent"""
        self.llm = LLMOrchestrator()
        self.memory = MemoryManager()
        self.agent_settings = AgentSettings()
        
        # Ferramentas
        self.llm_reasoner = LLMReasoner()
        self.insight_generator = InsightGenerator()
        self.report_builder = ReportBuilder()
        self.recommendation_engine = RecommendationEngine()
        
        # Templates de prompt
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """Constrói o prompt de sistema para o agente"""
        return f"""
Você é o ConsultantAgent do sistema SkyNET-I2A2, especialista em insights e consultoria.

## SUAS RESPONSABILIDADES:
1. **Interpretação**: Traduzir resultados técnicos em insights de negócio
2. **Consultoria**: Fornecer recomendações acionáveis
3. **Relatórios**: Criar relatórios executivos
4. **Raciocínio**: Aplicar lógica avançada para análise

## FERRAMENTAS DISPONÍVEIS:
- **LLMReasoner**: Raciocínio avançado com LLM
- **InsightGenerator**: Geração de insights especializados
- **ReportBuilder**: Criação de relatórios executivos
- **RecommendationEngine**: Motor de recomendações

## TIPOS DE CONSULTORIA:
- **Análise de Dados**: Insights de EDA e estatísticas
- **Validação Fiscal**: Conformidade e compliance
- **Visualização**: Interpretação de gráficos
- **Estratégia**: Recomendações de negócio

## DIRETRIZES:
- Priorize insights acionáveis
- Baseie-se em evidências dos dados
- Seja específico e técnico
- Forneça contexto e justificativas
- Sugira próximos passos
- Mantenha foco em valor de negócio

Data/Hora atual: {datetime.now().strftime("%d/%m/%Y %H:%M")}
"""
    
    async def provide_consultation(self, context: Dict[str, Any], user_id: UUID, 
                                  consultation_type: str = "general") -> Dict[str, Any]:
        """
        Fornece consultoria baseada no contexto
        
        Args:
            context: Contexto da consultoria
            user_id: ID do usuário
            consultation_type: Tipo de consultoria
            
        Returns:
            Resultados da consultoria
        """
        try:
            start_time = time.time()
            
            # 1. Gera insights
            insights = await self.insight_generator.generate_insights(
                context, user_id, consultation_type
            )
            
            # 2. Gera recomendações
            recommendations = await self.recommendation_engine.generate_recommendations(
                context, user_id
            )
            
            # 3. Constrói relatório
            report = await self.report_builder.build_report(
                context, insights, user_id
            )
            
            # 4. Responde perguntas específicas se houver
            qa_response = None
            if context.get("user_question"):
                qa_response = await self.llm_reasoner.analyze_context(
                    context, context.get("user_question", ""), user_id
                )
            
            # 5. Consolida resultados
            results = {
                "insights": insights,
                "recommendations": recommendations,
                "report": report,
                "qa_response": qa_response,
                "consultation_type": consultation_type
            }
            
            # Adiciona metadados
            processing_time = (time.time() - start_time) * 1000
            results["metadata"] = {
                "agent": "ConsultantAgent",
                "processing_time_ms": processing_time,
                "consultation_type": consultation_type,
                "timestamp": datetime.now().isoformat(),
                "user_id": str(user_id)
            }
            
            # Salva na memória
            await self.memory.save_consultation_result(user_id, results)
            
            return results
            
        except Exception as e:
            error_data = {
                "error": str(e),
                "agent": "ConsultantAgent",
                "timestamp": datetime.now().isoformat(),
                "status": "failed"
            }
            
            await self.memory.save_error(user_id, "consultation", str(e))
            return error_data
    
    async def answer_question(self, question: str, context: Dict[str, Any], 
                            user_id: UUID) -> Dict[str, Any]:
        """Responde pergunta específica"""
        try:
            # Usa LLMReasoner para análise contextual
            reasoning = await self.llm_reasoner.analyze_context(
                context, question, user_id
            )
            
            return {
                "question": question,
                "answer": reasoning,
                "context_used": bool(context),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "question": question,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def generate_summary(self, analysis_results: List[Dict[str, Any]], 
                              user_id: UUID) -> Dict[str, Any]:
        """Gera resumo executivo de múltiplas análises"""
        try:
            # Prepara resumo das análises
            analyses_summary = []
            for result in analysis_results:
                analyses_summary.append({
                    "agent": result.get("metadata", {}).get("agent", "unknown"),
                    "type": result.get("metadata", {}).get("analysis_type", "unknown"),
                    "processing_time": result.get("metadata", {}).get("processing_time_ms", 0),
                    "status": result.get("status", "completed")
                })
            
            prompt = f"""
Como consultor sênior, crie um resumo executivo das seguintes análises realizadas:

ANÁLISES REALIZADAS:
{json.dumps(analyses_summary, ensure_ascii=False, indent=2)}

Crie um resumo estruturado incluindo:

# RESUMO EXECUTIVO - ANÁLISES REALIZADAS

## VISÃO GERAL
- Número de análises realizadas
- Tipos de análises
- Tempo total de processamento

## PRINCIPAIS RESULTADOS
- Resultados mais importantes
- Descobertas significativas
- Padrões identificados

## INSIGHTS CONSOLIDADOS
- Insights gerais das análises
- Tendências observadas
- Oportunidades identificadas

## RECOMENDAÇÕES GERAIS
- Ações prioritárias
- Próximos passos
- Monitoramento sugerido

## PRÓXIMAS ANÁLISES
- Análises adicionais recomendadas
- Dados necessários
- Timeline sugerido

Seja conciso, claro e focado em valor de negócio.
"""
            
            result = await self.llm.route_request(
                task_type="summary",
                content=prompt,
                user_id=user_id
            )
            
            return {
                "summary": result.get("text", ""),
                "analyses_count": len(analysis_results),
                "model": result.get("model", ""),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do agente"""
        try:
            # Testa LLM
            llm_status = "healthy"
            try:
                # Teste básico do LLM
                await self.llm.route_request(
                    task_type="health_check",
                    content="Teste de saúde",
                    user_id=UUID("00000000-0000-0000-0000-000000000000")
                )
            except Exception:
                llm_status = "unhealthy"
            
            # Testa memória
            memory_status = "healthy"
            try:
                await self.memory.health_check()
            except Exception:
                memory_status = "unhealthy"
            
            return {
                "status": "healthy" if llm_status == "healthy" and memory_status == "healthy" else "degraded",
                "llm": llm_status,
                "memory": memory_status,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# Factory function
def create_consultant_agent() -> ConsultantAgent:
    """Cria instância do ConsultantAgent"""
    return ConsultantAgent()