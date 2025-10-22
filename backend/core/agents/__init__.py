"""
SkyNET-I2A2 - Agentes Autônomos
Sistema de agentes especializados para análise fiscal e de dados
"""

from .coordinator import CoordinatorAgent, create_coordinator_agent
from .extraction import ExtractionAgent, create_extraction_agent
from .analyst import AnalystAgent, create_analyst_agent
from .classifier import ClassifierAgent, create_classifier_agent
from .visualizer import VisualizationAgent, create_visualization_agent
from .consultant import ConsultantAgent, create_consultant_agent

__all__ = [
    # Coordenador
    "CoordinatorAgent",
    "create_coordinator_agent",
    
    # Agentes especializados
    "ExtractionAgent",
    "create_extraction_agent",
    
    "AnalystAgent", 
    "create_analyst_agent",
    
    "ClassifierAgent",
    "create_classifier_agent",
    
    "VisualizationAgent",
    "create_visualization_agent",
    
    "ConsultantAgent",
    "create_consultant_agent"
]