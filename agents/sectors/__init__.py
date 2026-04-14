"""
ULTIMATE CRONUS — Sector Agents
Agentes especializados por setor de mercado.
"""

from .saas_agent import SaasAgent
from .ecommerce_agent import EcommerceAgent
from .health_agent import HealthAgent
from .realestate_agent import RealEstateAgent
from .legal_agent import LegalAgent
from .education_agent import EducationAgent
from .fintech_agent import FintechAgent
from .logistics_agent import LogisticsAgent
from .restaurant_agent import RestaurantAgent
from .agro_agent import AgroAgent

__all__ = [
    "SaasAgent", "EcommerceAgent", "HealthAgent", "RealEstateAgent",
    "LegalAgent", "EducationAgent", "FintechAgent", "LogisticsAgent",
    "RestaurantAgent", "AgroAgent",
]

SECTOR_REGISTRY = {
    "SAAS":       SaasAgent,
    "ECOMMERCE":  EcommerceAgent,
    "HEALTH":     HealthAgent,
    "REALESTATE": RealEstateAgent,
    "LEGAL":      LegalAgent,
    "EDUCATION":  EducationAgent,
    "FINTECH":    FintechAgent,
    "LOGISTICS":  LogisticsAgent,
    "RESTAURANT": RestaurantAgent,
    "AGRO":       AgroAgent,
}
