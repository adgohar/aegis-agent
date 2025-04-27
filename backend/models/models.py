from enum import Enum

from pydantic import BaseModel
from typing import List, Optional, Dict


# Location Model
class Location(BaseModel):
    geographic_scope: Optional[str] = None  # E.g., "Global", "Asia", "North America"
    country: Optional[str] = None  # Country name, e.g., "China"
    region: Optional[str] = None  # Region name, e.g., "Guangdong Province"
    city: Optional[str] = None  # City name, e.g., "Shenzhen"
    coordinates: Optional[List[float]] = None  # Latitude and longitude, e.g., [22.5431, 114.0579]


# Node Model
class Node(BaseModel):
    id: str
    type: str  # e.g., 'Factory', 'Warehouse'
    location: Location


# Edge Model
class Edge(BaseModel):
    source: str  # Node ID
    destination: str  # Node ID
    transportMode: str  # e.g., 'Truck', 'Ship'


# Supply Chain Model
class SupplyChain(BaseModel):
    id: str
    companyName: str
    description: str
    nodes: List[Node]
    edges: List[Edge]


class Risk(BaseModel):
    class_name: str  # Main category, e.g., "Geopolitical"
    families: Optional[List[str]] = None  # Subcategories, e.g., ["Corruption & Crime", "Political Violence"]


class EventRiskAssessment(BaseModel):
    is_relevant: bool  # True if the event is relevant to the supply chain
    likelihood: Optional[float] = None  # Probability (logarithmic scale)
    impact: Optional[float] = None  # Severity of impact (logarithmic scale)
    risk_score: Optional[float] = None  # Combined risk score (normalized to 0–1)
    reason: Optional[str] = None  # Explanation from GPT


class Event(BaseModel):
    id: str
    supply_chain_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    risk_categories: Optional[List[Risk]] = None  # Risk classifications with classes and families
    timestamp: str  # ISO 8601 format of publication date
    location: Optional[Location] = None
    source_name: Optional[str] = None  # Name of the news source
    author: Optional[str] = None  # Author of the article
    url: str  # Direct URL to the article
    risk_assessment: Optional[EventRiskAssessment] = None  # Risk Assessment of the event
    is_event: bool  # Whether this is a valid event


# Define Geopolitical Risk Categories as an Enum
class GeopoliticalRiskCategory(str, Enum):
    BUSINESS_ENVIRONMENT = "Business Environment (Country Risk)"
    CORRUPTION_CRIME = "Corruption & Crime"
    GOVERNMENT_POLICY = "Government Business Policy"
    CHANGE_IN_GOVERNMENT = "Change in Government"
    POLITICAL_VIOLENCE = "Political Violence"
    INTERSTATE_CONFLICT = "Interstate Conflict"


# Risk Score Model
class RiskScore(BaseModel):
    supply_chain_id: str  # Link to the relevant supply chain
    scores: Dict[GeopoliticalRiskCategory, float]  # Risk scores per category
