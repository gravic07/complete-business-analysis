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


class CompanySize(models.TextChoices):
    MICRO = "1_4", "1-4"
    SMALL = "5_19", "5-19"
    MEDIUM = "20_49", "20-49"
    LARGE = "50_100", "50-100"
    ENTERPRISE = "101_plus", "101+"


class RevenueRange(models.TextChoices):
    UNDER_1M = "under_1m", "$1 million or less"
    FROM_1M_TO_2_5M = "1m_2_5m", "$1 million - $2.5 million"
    FROM_2_5M_TO_10M = "2_5m_10m", "$2.5 million - $10 million"
    FROM_10M_TO_50M = "10m_50m", "$10 million - $50 million"
    OVER_50M = "over_50m", "$50+ million"


class CorporateStyle(models.TextChoices):
    FAMILY_OWNED = "family_owned", "Family-Owned"
    SOLE_PROPRIETORSHIP = "sole_proprietorship", "Sole Proprietorship"
    BOARD_GOVERNED = "board_governed", "Board-governed / Corporate"
    PARTNERSHIP = "partnership", "Partnership"


class Client(BaseModel):
    """A client business and their primary contact."""

    business_name = models.CharField(max_length=255)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    title = models.CharField(max_length=255)
    industry = models.CharField(
        max_length=50,
        choices=IndustryType,
    )
    company_size = models.CharField(
        max_length=20,
        choices=CompanySize,
    )
    revenue = models.CharField(
        max_length=20,
        choices=RevenueRange,
    )
    corporate_style = models.CharField(
        max_length=25,
        choices=CorporateStyle,
    )

    def __str__(self) -> str:
        return f"{self.business_name} — {self.first_name} {self.last_name}"

    def business_profile_context(self) -> str:
        """Format Business Profile fields as a short context string for LLM prompts."""
        return (
            f"{self.get_company_size_display()} employees, "
            f"{self.get_revenue_display()} revenue, "
            f"{self.get_corporate_style_display()}"
        )
