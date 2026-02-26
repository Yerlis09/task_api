# Create your models here.
from django.db import models
from django.utils import timezone


class TaskStatus(models.TextChoices):
    """Estados permitidos para una tarea (choices)."""
    PENDING = "pending", "Pending"
    COMPLETED = "completed", "Completed"
    POSTPONED = "postponed", "Postponed"

class TaskQuerySet(models.QuerySet):
    """QuerySet personalizado para facilitar consultas de tareas (soft delete)."""
    def alive(self):
        """Retorna solo tareas activas (no eliminadas)."""
        return self.filter(deleted_at__isnull=True)

    def deleted(self):
        """Retorna solo tareas eliminadas (soft delete)."""
        return self.filter(deleted_at__isnull=False)

class Task(models.Model):
    """Modelo principal de tareas con auditoría y eliminación lógica."""
    id = models.BigAutoField(primary_key=True)

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=TaskStatus.choices,
        default=TaskStatus.PENDING,
    )

    due_date = models.DateTimeField(null=True, blank=True)

    # Audit
    created_by_name = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Soft delete
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = TaskQuerySet.as_manager()

    class Meta:
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["due_date"]),
            models.Index(fields=["deleted_at"]),
            models.Index(fields=["created_at"]),
        ]
        ordering = ["-created_at"]

    def soft_delete(self):
        """Marca la tarea como eliminada (soft delete) asignando `deleted_at`."""
        if self.deleted_at is None:
            self.deleted_at = timezone.now()
            self.save(update_fields=["deleted_at", "updated_at"])