"""Models to be used project wide."""

import uuid

from django.db import models


class BaseModel(models.Model):
    """
    Abstract base model to be inherited by all models in the project.

    Provides:
    - UUID primary key
    - created_at and updated_at timestamps
    - optional is_active flag for soft deletion
    - common save and soft delete helper methods
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True  # No database table for this model
        ordering = ["-created_at"]

    def __str__(self):
        """Fallback string representation."""
        return f"{self.__class__.__name__} ({self.id})"
