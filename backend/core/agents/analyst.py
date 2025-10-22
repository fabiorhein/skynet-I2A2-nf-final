"""
SkyNET-I2A2 - AnalystAgent
Agente especializado em análise exploratória de dados (EDA)
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Tuple
from uuid import UUID

import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import pearsonr, spearmanr
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ..llm import LLMOrchestrator
from ..memory import MemoryManager
from ...config import settings, AgentSettings


class PandasAnalyzer:
    """Ferramenta para análise com Pandas"""
    
    def __init__(self):
        self.agent_settings = AgentSettings()
        self.max_rows = self.agent_settings.MAX_ROWS_ANALYSIS
    
    async def analyze_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Análise completa do DataFrame"""
        try:
            start_time = time.time()
            
            # Informações básicas
            basic_info = {
                "shape": df.shape,
                "columns": list(df.columns),
                "dtypes": df.dtypes.to_dict(),
                "memory_usage": df.memory_usage(deep=True).sum(),
                "null_counts": df.isnull().sum().to_dict(),
                "duplicate_rows": df.duplicated().sum()
            }
            
            # Estatísticas descritivas
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns
            
            descriptive_stats = {}
            
            # Estatísticas numéricas
            if len(numeric_cols) > 0:
                numeric_df = df[numeric_cols]
                descriptive_stats["numeric"] = {
                    "count": numeric_df.count().to_dict(),
                    "mean": numeric_df.mean().to_dict(),
                    "std": numeric_df.std().to_dict(),
                    "min": numeric_df.min().to_dict(),
                    "max": numeric_df.max().to_dict(),
                    "median": numeric_df.median().to_dict(),
                    "q25": numeric_df.quantile(0.25).to_dict(),
                    "q75": numeric_df.quantile(0.75).to_dict(),
                    "skewness": numeric_df.skew().to_dict(),
                    "kurtosis": numeric_df.kurtosis().to_dict()
                }
            
            # Estatísticas categóricas
            if len(categorical_cols) > 0:
                categorical_stats = {}
                for col in categorical_cols:
                    categorical_stats[col] = {
                        "unique_count": df[col].nunique(),
                        "most_frequent": df[col].mode().iloc[0] if not df[col].mode().empty else None,
                        "frequency": df[col].value_counts().head(10).to_dict()
                    }
                descriptive_stats["categorical"] = categorical_stats
            
            processing_time = (time.time() - start_time) * 1000
            
            return {
                "basic_info": basic_info,
                "descriptive_stats": descriptive_stats,
                "processing_time_ms": processing_time,
                "analysis_type": "pandas_eda"
            }
            
        except Exception as e:
            raise Exception(f"Erro na análise Pandas: {str(e)}")


class StatisticalTools:
    """Ferramentas estatísticas avançadas"""
    
    def __init__(self):
        self.agent_settings = AgentSettings()
        self.correlation_threshold = self.agent_settings.CORRELATION_THRESHOLD
    
    async def calculate_correlations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calcula correlações entre variáveis numéricas"""
        try:
            numeric_df = df.select_dtypes(include=[np.number])
            
            if len(numeric_df.columns) < 2:
                return {"message": "Dados insuficientes para análise de correlação"}
            
            # Correlação de Pearson
            pearson_corr = numeric_df.corr()
            
            # Correlação de Spearman
            spearman_corr = numeric_df.corr(method='spearman')
            
            # Pairs com alta correlação
            high_corr_pairs = []
            for i in range(len(pearson_corr.columns)):
                for j in range(i+1, len(pearson_corr.columns)):
                    col1, col2 = pearson_corr.columns[i], pearson_corr.columns[j]
                    pearson_val = pearson_corr.iloc[i, j]
                    spearman_val = spearman_corr.iloc[i, j]
                    
                    if abs(pearson_val) >= self.correlation_threshold:
                        high_corr_pairs.append({
                            "variables": [col1, col2],
                            "pearson": round(pearson_val, 4),
                            "spearman": round(spearman_val, 4),
                            "strength": "strong" if abs(pearson_val) >= 0.7 else "moderate"
                        })
            
            return {
                "pearson_matrix": pearson_corr.to_dict(),
                "spearman_matrix": spearman_corr.to_dict(),
                "high_correlation_pairs": high_corr_pairs,
                "correlation_threshold": self.correlation_threshold
            }
            
        except Exception as e:
            raise Exception(f"Erro no cálculo de correlações: {str(e)}")
    
    async def normality_tests(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Testes de normalidade para variáveis numéricas"""
        try:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            normality_results = {}
            
            for col in numeric_cols:
                data = df[col].dropna()
                if len(data) < 3:
                    continue
                
                # Shapiro-Wilk (para amostras pequenas)
                if len(data) <= 5000:
                    shapiro_stat, shapiro_p = stats.shapiro(data)
                    shapiro_result = {
                        "statistic": round(shapiro_stat, 4),
                        "p_value": round(shapiro_p, 4),
                        "is_normal": shapiro_p > 0.05
                    }
                else:
                    shapiro_result = {"message": "Amostra muito grande para Shapiro-Wilk"}
                
                # Kolmogorov-Smirnov
                ks_stat, ks_p = stats.kstest(data, 'norm', args=(data.mean(), data.std()))
                ks_result = {
                    "statistic": round(ks_stat, 4),
                    "p_value": round(ks_p, 4),
                    "is_normal": ks_p > 0.05
                }
                
                normality_results[col] = {
                    "shapiro_wilk": shapiro_result,
                    "kolmogorov_smirnov": ks_result,
                    "sample_size": len(data)
                }
            
            return normality_results
            
        except Exception as e:
            raise Exception(f"Erro nos testes de normalidade: {str(e)}")


class OutlierDetector:
    """Detector de outliers usando IQR e Z-Score"""
    
    def __init__(self):
        self.agent_settings = AgentSettings()
        self.method = self.agent_settings.OUTLIER_METHOD
    
    async def detect_outliers(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detecta outliers usando método configurado"""
        try:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            outlier_results = {}
            
            for col in numeric_cols:
                data = df[col].dropna()
                if len(data) < 4:
                    continue
                
                outliers = {}
                
                if self.method == "iqr":
                    outliers.update(self._detect_iqr_outliers(data, col))
                elif self.method == "zscore":
                    outliers.update(self._detect_zscore_outliers(data, col))
                else:
                    # Ambos os métodos
                    outliers.update(self._detect_iqr_outliers(data, col))
                    outliers.update(self._detect_zscore_outliers(data, col))
                
                outlier_results[col] = outliers
            
            return outlier_results
            
        except Exception as e:
            raise Exception(f"Erro na detecção de outliers: {str(e)}")
    
    def _detect_iqr_outliers(self, data: pd.Series, col_name: str) -> Dict[str, Any]:
        """Detecta outliers usando IQR"""
        Q1 = data.quantile(0.25)
        Q3 = data.quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers = data[(data < lower_bound) | (data > upper_bound)]
        
        return {
            "iqr_outliers": {
                "count": len(outliers),
                "percentage": round(len(outliers) / len(data) * 100, 2),
                "indices": outliers.index.tolist(),
                "values": outliers.tolist(),
                "bounds": {"lower": lower_bound, "upper": upper_bound},
                "q1": Q1,
                "q3": Q3,
                "iqr": IQR
            }
        }
    
    def _detect_zscore_outliers(self, data: pd.Series, col_name: str) -> Dict[str, Any]:
        """Detecta outliers usando Z-Score"""
        z_scores = np.abs(stats.zscore(data))
        outliers = data[z_scores > 3]
        
        return {
            "zscore_outliers": {
                "count": len(outliers),
                "percentage": round(len(outliers) / len(data) * 100, 2),
                "indices": outliers.index.tolist(),
                "values": outliers.tolist(),
                "z_scores": z_scores[z_scores > 3].tolist()
            }
        }


class CorrelationAnalyzer:
    """Analisador de correlações avançado"""
    
    def __init__(self):
        self.agent_settings = AgentSettings()
    
    async def analyze_relationships(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Análise avançada de relacionamentos"""
        try:
            numeric_df = df.select_dtypes(include=[np.number])
            
            if len(numeric_df.columns) < 2:
                return {"message": "Dados insuficientes para análise de relacionamentos"}
            
            # Matriz de correlação
            corr_matrix = numeric_df.corr()
            
            # Encontra pares com alta correlação
            high_corr_pairs = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    col1, col2 = corr_matrix.columns[i], corr_matrix.columns[j]
                    corr_value = corr_matrix.iloc[i, j]
                    
                    if abs(corr_value) >= 0.5:
                        high_corr_pairs.append({
                            "var1": col1,
                            "var2": col2,
                            "correlation": round(corr_value, 4),
                            "strength": self._classify_correlation(abs(corr_value))
                        })
            
            # Ordena por força da correlação
            high_corr_pairs.sort(key=lambda x: abs(x["correlation"]), reverse=True)
            
            return {
                "correlation_matrix": corr_matrix.to_dict(),
                "high_correlation_pairs": high_corr_pairs,
                "summary": {
                    "total_pairs": len(high_corr_pairs),
                    "strong_correlations": len([p for p in high_corr_pairs if abs(p["correlation"]) >= 0.7]),
                    "moderate_correlations": len([p for p in high_corr_pairs if 0.5 <= abs(p["correlation"]) < 0.7])
                }
            }
            
        except Exception as e:
            raise Exception(f"Erro na análise de relacionamentos: {str(e)}")
    
    def _classify_correlation(self, abs_corr: float) -> str:
        """Classifica força da correlação"""
        if abs_corr >= 0.9:
            return "very_strong"
        elif abs_corr >= 0.7:
            return "strong"
        elif abs_corr >= 0.5:
            return "moderate"
        elif abs_corr >= 0.3:
            return "weak"
        else:
            return "very_weak"


class AnalystAgent:
    """
    Agente Especializado em Análise de Dados
    
    Responsabilidades:
    - Análise exploratória de CSV
    - Gerar estatísticas descritivas
    - Detectar correlações e outliers
    - Interpretação com LLM
    """
    
    def __init__(self):
        """Inicializa o AnalystAgent"""
        self.llm = LLMOrchestrator()
        self.memory = MemoryManager()
        self.agent_settings = AgentSettings()
        
        # Ferramentas
        self.pandas_analyzer = PandasAnalyzer()
        self.statistical_tools = StatisticalTools()
        self.outlier_detector = OutlierDetector()
        self.correlation_analyzer = CorrelationAnalyzer()
        
        # Templates de prompt
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """Constrói o prompt de sistema para o agente"""
        return f"""
Você é o AnalystAgent do sistema SkyNET-I2A2, especialista em análise exploratória de dados (EDA).

## SUAS RESPONSABILIDADES:
1. **Análise Exploratória**: EDA completa e automatizada
2. **Estatísticas Descritivas**: Médias, medianas, desvios, quartis
3. **Detecção de Outliers**: IQR, Z-Score, anomalias
4. **Análise de Correlações**: Relacionamentos entre variáveis
5. **Interpretação**: Insights baseados em dados

## FERRAMENTAS DISPONÍVEIS:
- **PandasAnalyzer**: Manipulação e análise de dados
- **StatisticalTools**: Testes estatísticos avançados
- **OutlierDetector**: Detecção de anomalias
- **CorrelationAnalyzer**: Análise de relacionamentos

## TIPOS DE ANÁLISE:
- Estatísticas descritivas
- Testes de normalidade
- Análise de correlações
- Detecção de outliers
- Análise de distribuições
- Análise temporal (se aplicável)

## DIRETRIZES:
- Priorize insights acionáveis
- Use visualizações quando apropriado
- Explique significância estatística
- Identifique padrões e tendências
- Sugira próximos passos de análise

Data/Hora atual: {datetime.now().strftime("%d/%m/%Y %H:%M")}
"""
    
    async def analyze_data(self, data: Union[pd.DataFrame, Dict], user_id: UUID, 
                          analysis_type: str = "eda") -> Dict[str, Any]:
        """
        Realiza análise exploratória de dados
        
        Args:
            data: DataFrame ou dados em formato dict
            user_id: ID do usuário
            analysis_type: Tipo de análise (eda, statistical, etc.)
            
        Returns:
            Resultados da análise
        """
        try:
            start_time = time.time()
            
            # Converte dados se necessário
            if isinstance(data, dict):
                df = pd.DataFrame(data)
            else:
                df = data.copy()
            
            # Validação básica
            if df.empty:
                raise Exception("DataFrame vazio")
            
            if len(df) > self.agent_settings.MAX_ROWS_ANALYSIS:
                df = df.sample(n=self.agent_settings.MAX_ROWS_ANALYSIS)
            
            # Executa análises
            results = {}
            
            # 1. Análise básica com Pandas
            pandas_analysis = await self.pandas_analyzer.analyze_dataframe(df)
            results["pandas_analysis"] = pandas_analysis
            
            # 2. Análise estatística
            if len(df.select_dtypes(include=[np.number]).columns) > 0:
                statistical_analysis = await self.statistical_tools.calculate_correlations(df)
                results["statistical_analysis"] = statistical_analysis
                
                # Testes de normalidade
                normality_tests = await self.statistical_tools.normality_tests(df)
                results["normality_tests"] = normality_tests
            
            # 3. Detecção de outliers
            outlier_analysis = await self.outlier_detector.detect_outliers(df)
            results["outlier_analysis"] = outlier_analysis
            
            # 4. Análise de correlações
            correlation_analysis = await self.correlation_analyzer.analyze_relationships(df)
            results["correlation_analysis"] = correlation_analysis
            
            # 5. Geração de insights com LLM
            insights = await self._generate_insights(results, df, user_id)
            results["insights"] = insights
            
            # 6. Sugestões de visualizações
            visualization_suggestions = await self._suggest_visualizations(df, results)
            results["visualization_suggestions"] = visualization_suggestions
            
            # Adiciona metadados
            processing_time = (time.time() - start_time) * 1000
            results["metadata"] = {
                "agent": "AnalystAgent",
                "processing_time_ms": processing_time,
                "analysis_type": analysis_type,
                "data_shape": df.shape,
                "timestamp": datetime.now().isoformat(),
                "user_id": str(user_id)
            }
            
            # Salva na memória
            await self.memory.save_analysis_result(user_id, results)
            
            return results
            
        except Exception as e:
            error_data = {
                "error": str(e),
                "agent": "AnalystAgent",
                "timestamp": datetime.now().isoformat(),
                "status": "failed"
            }
            
            await self.memory.save_error(user_id, "analysis", str(e))
            return error_data
    
    async def _generate_insights(self, analysis_results: Dict, df: pd.DataFrame, user_id: UUID) -> Dict[str, Any]:
        """Gera insights usando LLM"""
        try:
            # Prepara resumo dos dados para o LLM
            data_summary = {
                "shape": df.shape,
                "columns": list(df.columns),
                "numeric_columns": list(df.select_dtypes(include=[np.number]).columns),
                "categorical_columns": list(df.select_dtypes(include=['object', 'category']).columns),
                "missing_values": df.isnull().sum().to_dict(),
                "basic_stats": analysis_results.get("pandas_analysis", {}).get("descriptive_stats", {})
            }
            
            prompt = f"""
Como especialista em análise de dados, analise os seguintes resultados de EDA e forneça insights acionáveis:

DADOS:
{json.dumps(data_summary, ensure_ascii=False, indent=2)}

ANÁLISE ESTATÍSTICA:
{json.dumps(analysis_results.get("statistical_analysis", {}), ensure_ascii=False, indent=2)}

OUTLIERS DETECTADOS:
{json.dumps(analysis_results.get("outlier_analysis", {}), ensure_ascii=False, indent=2)}

CORRELAÇÕES:
{json.dumps(analysis_results.get("correlation_analysis", {}), ensure_ascii=False, indent=2)}

Forneça:
1. **Principais descobertas** (3-5 pontos principais)
2. **Padrões identificados** (tendências, sazonalidade, etc.)
3. **Anomalias importantes** (outliers significativos)
4. **Relacionamentos relevantes** (correlações fortes)
5. **Recomendações** (próximos passos, análises adicionais)
6. **Alertas** (problemas de qualidade dos dados)

Seja específico e use linguagem clara para tomadores de decisão.
"""
            
            result = await self.llm.route_request(
                task_type="data_analysis",
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
    
    async def _suggest_visualizations(self, df: pd.DataFrame, analysis_results: Dict) -> List[Dict[str, Any]]:
        """Sugere visualizações baseadas nos dados"""
        try:
            suggestions = []
            
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns
            
            # Histogramas para variáveis numéricas
            for col in numeric_cols[:5]:  # Máximo 5 histogramas
                suggestions.append({
                    "type": "histogram",
                    "column": col,
                    "title": f"Distribuição de {col}",
                    "description": "Mostra a distribuição dos valores"
                })
            
            # Box plots para detectar outliers
            for col in numeric_cols[:3]:  # Máximo 3 box plots
                suggestions.append({
                    "type": "box",
                    "column": col,
                    "title": f"Box Plot de {col}",
                    "description": "Detecta outliers e quartis"
                })
            
            # Scatter plots para correlações
            high_corr_pairs = analysis_results.get("correlation_analysis", {}).get("high_correlation_pairs", [])
            for pair in high_corr_pairs[:3]:  # Máximo 3 scatter plots
                suggestions.append({
                    "type": "scatter",
                    "x": pair["var1"],
                    "y": pair["var2"],
                    "title": f"Correlação: {pair['var1']} vs {pair['var2']}",
                    "description": f"Correlação {pair['strength']}: {pair['correlation']}"
                })
            
            # Gráficos de barras para categóricas
            for col in categorical_cols[:3]:  # Máximo 3 gráficos de barras
                suggestions.append({
                    "type": "bar",
                    "column": col,
                    "title": f"Frequência de {col}",
                    "description": "Mostra distribuição das categorias"
                })
            
            return suggestions
            
        except Exception as e:
            return [{"error": str(e)}]
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do agente"""
        try:
            # Testa bibliotecas
            pandas_status = "healthy"
            try:
                pd.DataFrame({"test": [1, 2, 3]})
            except Exception:
                pandas_status = "unhealthy"
            
            numpy_status = "healthy"
            try:
                np.array([1, 2, 3])
            except Exception:
                numpy_status = "unhealthy"
            
            scipy_status = "healthy"
            try:
                stats.normaltest([1, 2, 3])
            except Exception:
                scipy_status = "unhealthy"
            
            return {
                "status": "healthy" if all(s == "healthy" for s in [pandas_status, numpy_status, scipy_status]) else "degraded",
                "pandas": pandas_status,
                "numpy": numpy_status,
                "scipy": scipy_status,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# Factory function
def create_analyst_agent() -> AnalystAgent:
    """Cria instância do AnalystAgent"""
    return AnalystAgent()