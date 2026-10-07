"""Django models for the teams application."""

from django.db import models

from complete_business_analysis_tool.core.models import BaseModel


class Team(BaseModel):
    name = models.CharField(max_length=255)

    class Meta(BaseModel.Meta):
        ordering = ["name"]

    def __str__(self):
        return self.name
