import django_filters

from .models import Task, TaskStatus


class TaskFilter(django_filters.FilterSet):
    """Filtros disponibles para el endpoint de listado de tareas."""
    status = django_filters.ChoiceFilter(
        choices=TaskStatus.choices,
        help_text="Filtra por estado: pending | completed | postponed",
    )

    due_from = django_filters.IsoDateTimeFilter(
        field_name="due_date",
        lookup_expr="gte",
        help_text="Filtra por due_date desde (ISO 8601). Ej: 2030-02-20T00:00:00-05:00",
    )
    due_to = django_filters.IsoDateTimeFilter(
        field_name="due_date",
        lookup_expr="lte",
        help_text="Filtra por due_date hasta (ISO 8601). Ej: 2030-02-25T23:59:59-05:00",
    )

    class Meta:
        """Configura qué modelo se filtra y qué campos expone el filtro."""
        model = Task
        fields = ["status", "due_from", "due_to"]      