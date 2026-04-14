"""
ULTIMATE CRONUS — Agents Package
25+ agentes especializados para automação empresarial total.
"""

# Core
from .base_agent import BaseAgent
from .swarm_agent import SwarmAgent
from .radar_agent import RadarAgent
from .hunter_agent import HunterAgent
from .analyst_agent import AnalystAgent
from .scribe_agent import ScribeAgent
from .orchestrator import Orchestrator
from .capital_agent import CapitalAgent
from .ceo_agent import CeoAgent
from .funis_agent import FunisAgent
from .atendimento_agent import AtendimentoAgent

# Strategy & Innovation
from .vision_agent import VisionAgent
from .global_agent import GlobalAgent
from .innovation_agent import InnovationAgent
from .moat_agent import MoatAgent

# Intelligence & Meta
from .self_improvement import SelfImprovementAgent
from .knowledge_graph import KnowledgeGraphAgent

# Sector Agents
from .sectors.saas_agent import SaasAgent
from .sectors.ecommerce_agent import EcommerceAgent
from .sectors.health_agent import HealthAgent
from .sectors.realestate_agent import RealEstateAgent
from .sectors.legal_agent import LegalAgent
from .sectors.education_agent import EducationAgent
from .sectors.fintech_agent import FintechAgent
from .sectors.logistics_agent import LogisticsAgent
from .sectors.restaurant_agent import RestaurantAgent
from .sectors.agro_agent import AgroAgent

__all__ = [
    # Core
    "BaseAgent", "SwarmAgent", "RadarAgent", "HunterAgent",
    "AnalystAgent", "ScribeAgent", "Orchestrator",
    "CapitalAgent", "CeoAgent", "FunisAgent", "AtendimentoAgent",
    # Strategy
    "VisionAgent", "GlobalAgent", "InnovationAgent", "MoatAgent",
    # Intelligence
    "SelfImprovementAgent", "KnowledgeGraphAgent",
    # Sectors
    "SaasAgent", "EcommerceAgent", "HealthAgent", "RealEstateAgent",
    "LegalAgent", "EducationAgent", "FintechAgent", "LogisticsAgent",
    "RestaurantAgent", "AgroAgent",
]

# Registry para o orchestrator carregar agentes dinamicamente
AGENT_REGISTRY = {
    # Core
    "SWARM":          SwarmAgent,
    "RADAR":          RadarAgent,
    "HUNTER":         HunterAgent,
    "ANALYST":        AnalystAgent,
    "SCRIBE":         ScribeAgent,
    "CAPITAL":        CapitalAgent,
    "CEO":            CeoAgent,
    "FUNIS":          FunisAgent,
    "ATENDIMENTO":    AtendimentoAgent,
    # Strategy
    "VISION":         VisionAgent,
    "GLOBAL":         GlobalAgent,
    "INNOVATION":     InnovationAgent,
    "MOAT":           MoatAgent,
    # Intelligence
    "SELF_IMPROVE":   SelfImprovementAgent,
    "KNOWLEDGE_GRAPH":KnowledgeGraphAgent,
    # Sectors
    "SAAS":           SaasAgent,
    "ECOMMERCE":      EcommerceAgent,
    "HEALTH":         HealthAgent,
    "REALESTATE":     RealEstateAgent,
    "LEGAL":          LegalAgent,
    "EDUCATION":      EducationAgent,
    "FINTECH":        FintechAgent,
    "LOGISTICS":      LogisticsAgent,
    "RESTAURANT":     RestaurantAgent,
    "AGRO":           AgroAgent,
}
