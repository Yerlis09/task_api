from rest_framework import serializers

from .models import Task, TaskStatus


class TaskSerializer(serializers.ModelSerializer):
    title = serializers.CharField(help_text="Título corto de la tarea.")
    description = serializers.CharField(
        required=False, allow_blank=True, help_text="Descripción opcional."
    )
    status = serializers.ChoiceField(
        choices=TaskStatus.choices, help_text="Estado de la tarea."
    )
    due_date = serializers.DateTimeField(
        required=False, allow_null=True, help_text="Fecha/hora de vencimiento (ISO 8601)."
    )
    created_by_name = serializers.CharField(
        help_text="Nombre de quien crea la tarea (sin auth)."
    )

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "status",
            "due_date",
            "created_by_name",
            "created_at",
            "updated_at",
            "deleted_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "deleted_at"]


class TaskStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=TaskStatus.choices,
        help_text="Nuevo estado de la tarea."
    )