"""
SkyNET-I2A2 - VisualizationAgent
Agente especializado em geração de gráficos e visualizações
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from uuid import UUID
import base64
import io

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
import kaleido

from ..llm import LLMOrchestrator
from ..memory import MemoryManager
from ...config import settings, AgentSettings


class PlotlyBuilder:
    """Construtor de gráficos Plotly"""
    
    def __init__(self):
        self.agent_settings = AgentSettings()
        self.width = self.agent_settings.CHART_WIDTH
        self.height = self.agent_settings.CHART_HEIGHT
        self.theme = self.agent_settings.CHART_THEME
        self.max_categories = self.agent_settings.MAX_CATEGORIES_PIE
    
    async def create_histogram(self, data: pd.Series, title: str = "", 
                              bins: int = 30) -> Dict[str, Any]:
        """Cria histograma"""
        try:
            fig = px.histogram(
                data, 
                title=title or f"Distribuição de {data.name}",
                nbins=bins,
                width=self.width,
                height=self.height
            )
            
            fig.update_layout(
                template=self.theme,
                showlegend=True,
                font=dict(size=12)
            )
            
            return {
                "chart_type": "histogram",
                "plotly_json": fig.to_dict(),
                "html": fig.to_html(include_plotlyjs='cdn'),
                "title": title
            }
            
        except Exception as e:
            raise Exception(f"Erro ao criar histograma: {str(e)}")
    
    async def create_box_plot(self, data: pd.DataFrame, column: str, 
                             title: str = "") -> Dict[str, Any]:
        """Cria box plot"""
        try:
            fig = px.box(
                data, 
                y=column,
                title=title or f"Box Plot de {column}",
                width=self.width,
                height=self.height
            )
            
            fig.update_layout(
                template=self.theme,
                showlegend=True,
                font=dict(size=12)
            )
            
            return {
                "chart_type": "box",
                "plotly_json": fig.to_dict(),
                "html": fig.to_html(include_plotlyjs='cdn'),
                "title": title
            }
            
        except Exception as e:
            raise Exception(f"Erro ao criar box plot: {str(e)}")
    
    async def create_scatter_plot(self, data: pd.DataFrame, x: str, y: str, 
                                 title: str = "", color: str = None) -> Dict[str, Any]:
        """Cria scatter plot"""
        try:
            fig = px.scatter(
                data, 
                x=x, 
                y=y,
                color=color,
                title=title or f"Correlação: {x} vs {y}",
                width=self.width,
                height=self.height
            )
            
            fig.update_layout(
                template=self.theme,
                showlegend=True,
                font=dict(size=12)
            )
            
            return {
                "chart_type": "scatter",
                "plotly_json": fig.to_dict(),
                "html": fig.to_html(include_plotlyjs='cdn'),
                "title": title
            }
            
        except Exception as e:
            raise Exception(f"Erro ao criar scatter plot: {str(e)}")
    
    async def create_bar_chart(self, data: pd.Series, title: str = "") -> Dict[str, Any]:
        """Cria gráfico de barras"""
        try:
            # Limita categorias para gráfico de pizza
            if len(data) > self.max_categories:
                top_data = data.head(self.max_categories)
                others = data.iloc[self.max_categories:].sum()
                top_data['Outros'] = others
                data = top_data
            
            fig = px.bar(
                x=data.index,
                y=data.values,
                title=title or f"Frequência de {data.name}",
                width=self.width,
                height=self.height
            )
            
            fig.update_layout(
                template=self.theme,
                showlegend=True,
                font=dict(size=12)
            )
            
            return {
                "chart_type": "bar",
                "plotly_json": fig.to_dict(),
                "html": fig.to_html(include_plotlyjs='cdn'),
                "title": title
            }
            
        except Exception as e:
            raise Exception(f"Erro ao criar gráfico de barras: {str(e)}")
    
    async def create_pie_chart(self, data: pd.Series, title: str = "") -> Dict[str, Any]:
        """Cria gráfico de pizza"""
        try:
            # Limita categorias
            if len(data) > self.max_categories:
                top_data = data.head(self.max_categories)
                others = data.iloc[self.max_categories:].sum()
                top_data['Outros'] = others
                data = top_data
            
            fig = px.pie(
                values=data.values,
                names=data.index,
                title=title or f"Distribuição de {data.name}",
                width=self.width,
                height=self.height
            )
            
            fig.update_layout(
                template=self.theme,
                showlegend=True,
                font=dict(size=12)
            )
            
            return {
                "chart_type": "pie",
                "plotly_json": fig.to_dict(),
                "html": fig.to_html(include_plotlyjs='cdn'),
                "title": title
            }
            
        except Exception as e:
            raise Exception(f"Erro ao criar gráfico de pizza: {str(e)}")
    
    async def create_correlation_heatmap(self, data: pd.DataFrame, title: str = "") -> Dict[str, Any]:
        """Cria heatmap de correlação"""
        try:
            numeric_data = data.select_dtypes(include=[np.number])
            corr_matrix = numeric_data.corr()
            
            fig = px.imshow(
                corr_matrix,
                title=title or "Matriz de Correlação",
                width=self.width,
                height=self.height,
                color_continuous_scale='RdBu'
            )
            
            fig.update_layout(
                template=self.theme,
                font=dict(size=12)
            )
            
            return {
                "chart_type": "heatmap",
                "plotly_json": fig.to_dict(),
                "html": fig.to_html(include_plotlyjs='cdn'),
                "title": title
            }
            
        except Exception as e:
            raise Exception(f"Erro ao criar heatmap: {str(e)}")
    
    async def create_time_series(self, data: pd.DataFrame, date_col: str, value_col: str, 
                                title: str = "") -> Dict[str, Any]:
        """Cria série temporal"""
        try:
            fig = px.line(
                data,
                x=date_col,
                y=value_col,
                title=title or f"Série Temporal: {value_col}",
                width=self.width,
                height=self.height
            )
            
            fig.update_layout(
                template=self.theme,
                showlegend=True,
                font=dict(size=12)
            )
            
            return {
                "chart_type": "time_series",
                "plotly_json": fig.to_dict(),
                "html": fig.to_html(include_plotlyjs='cdn'),
                "title": title
            }
            
        except Exception as e:
            raise Exception(f"Erro ao criar série temporal: {str(e)}")


class ChartExporter:
    """Exportador de gráficos"""
    
    def __init__(self):
        self.agent_settings = AgentSettings()
    
    async def export_to_png(self, plotly_json: Dict[str, Any], filename: str = None) -> str:
        """Exporta gráfico para PNG"""
        try:
            fig = go.Figure(plotly_json)
            
            if filename is None:
                filename = f"chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            
            # Exporta para PNG
            img_bytes = pio.to_image(fig, format="png", width=self.agent_settings.CHART_WIDTH, 
                                   height=self.agent_settings.CHART_HEIGHT)
            
            # Converte para base64
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            
            return {
                "filename": filename,
                "base64": img_base64,
                "format": "png",
                "size_bytes": len(img_bytes)
            }
            
        except Exception as e:
            raise Exception(f"Erro ao exportar PNG: {str(e)}")
    
    async def export_to_pdf(self, plotly_json: Dict[str, Any], filename: str = None) -> str:
        """Exporta gráfico para PDF"""
        try:
            fig = go.Figure(plotly_json)
            
            if filename is None:
                filename = f"chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            # Exporta para PDF
            pdf_bytes = pio.to_image(fig, format="pdf", width=self.agent_settings.CHART_WIDTH, 
                                   height=self.agent_settings.CHART_HEIGHT)
            
            # Converte para base64
            pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
            
            return {
                "filename": filename,
                "base64": pdf_base64,
                "format": "pdf",
                "size_bytes": len(pdf_bytes)
            }
            
        except Exception as e:
            raise Exception(f"Erro ao exportar PDF: {str(e)}")


class DashboardGenerator:
    """Gerador de dashboards"""
    
    def __init__(self):
        self.agent_settings = AgentSettings()
    
    async def create_dashboard(self, charts: List[Dict[str, Any]], 
                              title: str = "Dashboard", layout: str = "grid") -> Dict[str, Any]:
        """Cria dashboard com múltiplos gráficos"""
        try:
            if layout == "grid":
                # Layout em grade 2x2
                rows = 2
                cols = 2
            else:
                # Layout em linha
                rows = 1
                cols = len(charts)
            
            fig = make_subplots(
                rows=rows, 
                cols=cols,
                subplot_titles=[chart.get("title", f"Gráfico {i+1}") for i in range(len(charts))],
                specs=[[{"type": "scatter"} for _ in range(cols)] for _ in range(rows)]
            )
            
            # Adiciona gráficos ao dashboard
            for i, chart in enumerate(charts):
                row = (i // cols) + 1
                col = (i % cols) + 1
                
                if row <= rows and col <= cols:
                    chart_data = chart.get("plotly_json", {})
                    if "data" in chart_data:
                        for trace in chart_data["data"]:
                            fig.add_trace(trace, row=row, col=col)
            
            fig.update_layout(
                title=title,
                template=self.agent_settings.CHART_THEME,
                showlegend=True,
                font=dict(size=12)
            )
            
            return {
                "dashboard_type": "multi_chart",
                "plotly_json": fig.to_dict(),
                "html": fig.to_html(include_plotlyjs='cdn'),
                "title": title,
                "charts_count": len(charts)
            }
            
        except Exception as e:
            raise Exception(f"Erro ao criar dashboard: {str(e)}")


class ThemeManager:
    """Gerenciador de temas visuais"""
    
    def __init__(self):
        self.available_themes = [
            "plotly", "plotly_white", "plotly_dark", "ggplot2", 
            "seaborn", "simple_white", "presentation"
        ]
    
    def get_theme_config(self, theme: str = "plotly_white") -> Dict[str, Any]:
        """Retorna configuração do tema"""
        theme_configs = {
            "plotly_white": {
                "template": "plotly_white",
                "colors": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"],
                "background": "white",
                "grid": True
            },
            "plotly_dark": {
                "template": "plotly_dark",
                "colors": ["#00cc96", "#ffa15a", "#ff6692", "#b6e880", "#ff97ff"],
                "background": "black",
                "grid": True
            },
            "seaborn": {
                "template": "seaborn",
                "colors": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"],
                "background": "white",
                "grid": True
            }
        }
        
        return theme_configs.get(theme, theme_configs["plotly_white"])


class VisualizationAgent:
    """
    Agente Especializado em Visualizações
    
    Responsabilidades:
    - Gerar gráficos interativos (Plotly)
    - Exportar para PNG/PDF
    - Criar dashboards customizados
    """
    
    def __init__(self):
        """Inicializa o VisualizationAgent"""
        self.llm = LLMOrchestrator()
        self.memory = MemoryManager()
        self.agent_settings = AgentSettings()
        
        # Ferramentas
        self.plotly_builder = PlotlyBuilder()
        self.chart_exporter = ChartExporter()
        self.dashboard_generator = DashboardGenerator()
        self.theme_manager = ThemeManager()
        
        # Templates de prompt
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """Constrói o prompt de sistema para o agente"""
        return f"""
Você é o VisualizationAgent do sistema SkyNET-I2A2, especialista em geração de gráficos e visualizações.

## SUAS RESPONSABILIDADES:
1. **Geração de Gráficos**: Criar visualizações interativas com Plotly
2. **Export de Imagens**: Converter gráficos para PNG/PDF
3. **Dashboards**: Criar painéis com múltiplos gráficos
4. **Temas Visuais**: Aplicar estilos consistentes

## FERRAMENTAS DISPONÍVEIS:
- **PlotlyBuilder**: Criação de gráficos Plotly
- **ChartExporter**: Export para PNG/PDF
- **DashboardGenerator**: Criação de dashboards
- **ThemeManager**: Gerenciamento de temas

## TIPOS DE GRÁFICOS SUPORTADOS:
- **Histogramas**: Distribuição de dados
- **Box Plots**: Detecção de outliers
- **Scatter Plots**: Correlações
- **Gráficos de Barras**: Frequências
- **Gráficos de Pizza**: Proporções
- **Heatmaps**: Matrizes de correlação
- **Séries Temporais**: Dados temporais

## DIRETRIZES:
- Priorize clareza e legibilidade
- Use cores consistentes e acessíveis
- Adicione títulos e legendas descritivas
- Otimize para diferentes tamanhos de tela
- Mantenha performance com grandes datasets

Data/Hora atual: {datetime.now().strftime("%d/%m/%Y %H:%M")}
"""
    
    async def create_visualizations(self, data: Union[pd.DataFrame, Dict], 
                                   suggestions: List[Dict[str, Any]], 
                                   user_id: UUID) -> Dict[str, Any]:
        """
        Cria visualizações baseadas em sugestões
        
        Args:
            data: DataFrame ou dados
            suggestions: Lista de sugestões de gráficos
            user_id: ID do usuário
            
        Returns:
            Gráficos criados
        """
        try:
            start_time = time.time()
            
            # Converte dados se necessário
            if isinstance(data, dict):
                df = pd.DataFrame(data)
            else:
                df = data.copy()
            
            # Cria gráficos baseados nas sugestões
            charts = []
            
            for suggestion in suggestions:
                try:
                    chart = await self._create_chart_from_suggestion(df, suggestion)
                    if chart:
                        charts.append(chart)
                except Exception as e:
                    # Log erro mas continua com outros gráficos
                    print(f"Erro ao criar gráfico {suggestion.get('type', 'unknown')}: {str(e)}")
                    continue
            
            # Cria dashboard se múltiplos gráficos
            dashboard = None
            if len(charts) > 1:
                dashboard = await self.dashboard_generator.create_dashboard(charts)
            
            # Gera insights sobre visualizações
            insights = await self._generate_visualization_insights(charts, user_id)
            
            # Adiciona metadados
            processing_time = (time.time() - start_time) * 1000
            results = {
                "charts": charts,
                "dashboard": dashboard,
                "insights": insights,
                "metadata": {
                    "agent": "VisualizationAgent",
                    "processing_time_ms": processing_time,
                    "charts_count": len(charts),
                    "timestamp": datetime.now().isoformat(),
                    "user_id": str(user_id)
                }
            }
            
            # Salva na memória
            await self.memory.save_visualization_result(user_id, results)
            
            return results
            
        except Exception as e:
            error_data = {
                "error": str(e),
                "agent": "VisualizationAgent",
                "timestamp": datetime.now().isoformat(),
                "status": "failed"
            }
            
            await self.memory.save_error(user_id, "visualization", str(e))
            return error_data
    
    async def _create_chart_from_suggestion(self, df: pd.DataFrame, 
                                           suggestion: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Cria gráfico baseado em sugestão"""
        try:
            chart_type = suggestion.get("type", "")
            title = suggestion.get("title", "")
            
            if chart_type == "histogram":
                column = suggestion.get("column", "")
                if column in df.columns:
                    return await self.plotly_builder.create_histogram(
                        df[column], title
                    )
            
            elif chart_type == "box":
                column = suggestion.get("column", "")
                if column in df.columns:
                    return await self.plotly_builder.create_box_plot(
                        df, column, title
                    )
            
            elif chart_type == "scatter":
                x = suggestion.get("x", "")
                y = suggestion.get("y", "")
                if x in df.columns and y in df.columns:
                    return await self.plotly_builder.create_scatter_plot(
                        df, x, y, title
                    )
            
            elif chart_type == "bar":
                column = suggestion.get("column", "")
                if column in df.columns:
                    value_counts = df[column].value_counts()
                    return await self.plotly_builder.create_bar_chart(
                        value_counts, title
                    )
            
            elif chart_type == "pie":
                column = suggestion.get("column", "")
                if column in df.columns:
                    value_counts = df[column].value_counts()
                    return await self.plotly_builder.create_pie_chart(
                        value_counts, title
                    )
            
            elif chart_type == "heatmap":
                return await self.plotly_builder.create_correlation_heatmap(
                    df, title
                )
            
            return None
            
        except Exception as e:
            print(f"Erro ao criar gráfico: {str(e)}")
            return None
    
    async def export_chart(self, plotly_json: Dict[str, Any], 
                          format_type: str = "png", filename: str = None) -> Dict[str, Any]:
        """Exporta gráfico para formato específico"""
        try:
            if format_type.lower() == "png":
                return await self.chart_exporter.export_to_png(plotly_json, filename)
            elif format_type.lower() == "pdf":
                return await self.chart_exporter.export_to_pdf(plotly_json, filename)
            else:
                raise Exception(f"Formato não suportado: {format_type}")
                
        except Exception as e:
            raise Exception(f"Erro ao exportar gráfico: {str(e)}")
    
    async def _generate_visualization_insights(self, charts: List[Dict[str, Any]], 
                                             user_id: UUID) -> Dict[str, Any]:
        """Gera insights sobre visualizações"""
        try:
            chart_summaries = []
            for chart in charts:
                chart_summaries.append({
                    "type": chart.get("chart_type", ""),
                    "title": chart.get("title", "")
                })
            
            prompt = f"""
Como especialista em visualização de dados, analise os seguintes gráficos criados:

GRÁFICOS CRIADOS:
{json.dumps(chart_summaries, ensure_ascii=False, indent=2)}

Forneça insights sobre:
1. **Qualidade das Visualizações**: Se os gráficos são apropriados para os dados
2. **Padrões Visuais**: Principais padrões identificados visualmente
3. **Recomendações**: Sugestões para melhorar as visualizações
4. **Próximos Passos**: Gráficos adicionais que podem ser úteis
5. **Melhores Práticas**: Dicas de design e legibilidade

Seja específico e técnico sobre visualização de dados.
"""
            
            result = await self.llm.route_request(
                task_type="visualization",
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
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do agente"""
        try:
            # Testa Plotly
            plotly_status = "healthy"
            try:
                import plotly.graph_objects as go
                fig = go.Figure()
            except Exception:
                plotly_status = "unhealthy"
            
            # Testa Kaleido (export)
            kaleido_status = "healthy"
            try:
                import kaleido
            except Exception:
                kaleido_status = "unhealthy"
            
            # Testa Pandas
            pandas_status = "healthy"
            try:
                pd.DataFrame({"test": [1, 2, 3]})
            except Exception:
                pandas_status = "unhealthy"
            
            return {
                "status": "healthy" if all(s == "healthy" for s in [plotly_status, kaleido_status, pandas_status]) else "degraded",
                "plotly": plotly_status,
                "kaleido": kaleido_status,
                "pandas": pandas_status,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# Factory function
def create_visualization_agent() -> VisualizationAgent:
    """Cria instância do VisualizationAgent"""
    return VisualizationAgent()