"""Django models for the clients application."""

from django.db import models

from complete_business_analysis_tool.core.models import BaseModel


class IndustryType(models.TextChoices):
    AGRICULTURE = "agriculture", "Agriculture"
    AUTOMOTIVE = "automotive", "Automotive"
    CONSTRUCTION = "construction", "Construction"
    EDUCATION = "education", "Education"
    ENERGY_UTILITIES = "energy_utilities", "Energy & Utilities"
    FINANCE = "finance", "Finance & Banking"
    FOOD_BEVERAGE = "food_beverage", "Food & Beverage"
    GOVERNMENT = "government", "Government & Public Sector"
    HEALTHCARE = "healthcare", "Healthcare & Life Sciences"
    HOSPITALITY = "hospitality", "Hospitality & Tourism"
    INSURANCE = "insurance", "Insurance"
    LEGAL = "legal", "Legal Services"
    LOGISTICS = "logistics", "Logistics & Transportation"
    MANUFACTURING = "manufacturing", "Manufacturing"
    MEDIA = "media", "Media & Entertainment"
    NONPROFIT = "nonprofit", "Non-Profit & NGO"
    PROFESSIONAL_SERVICES = "professional_services", "Professional Services"
    REAL_ESTATE = "real_estate", "Real Estate"
    RETAIL = "retail", "Retail & E-Commerce"
    TECHNOLOGY = "technology", "Technology & Software"
    TELECOMMUNICATIONS = "telecommunications", "Telecommunications"
    OTHER = "other", "Other"


class Client(BaseModel):
    """A client business and their primary contact."""

    business_name = models.CharField(max_length=255)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    title = models.CharField(max_length=255)
    industry = models.CharField(
        max_length=50,
        choices=IndustryType.choices,
    )

    def __str__(self) -> str:
        return f"{self.business_name} — {self.first_name} {self.last_name}"
