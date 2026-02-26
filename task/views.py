from django.utils import timezone
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from .filters import TaskFilter
from .models import Task
from .serializers import TaskSerializer, TaskStatusSerializer


@extend_schema_view(
    list=extend_schema(
        tags=["Tasks"],
        summary="Listar tareas",
        description=(
            "Retorna la lista de tareas.\n\n"
            "- Por defecto **excluye** tareas eliminadas (soft delete).\n"
            "- Puedes incluir eliminadas con `include_deleted=true`.\n"
            "- Soporta filtros, búsqueda y ordenamiento si están habilitados."
        ),
        parameters=[
            OpenApiParameter(
                name="include_deleted",
                type=bool,
                location=OpenApiParameter.QUERY,
                description="Si es `true`, incluye tareas eliminadas (soft delete). Default: false.",
            ),
        ],
    ),
    create=extend_schema(
        tags=["Tasks"],
        summary="Crear tarea",
        description="Crea una nueva tarea con validaciones de estado y fechas.",
        examples=[
            OpenApiExample(
                "Ejemplo de creación",
                value={
                    "title": "Comprar mercado",
                    "description": "Leche, huevos, café",
                    "status": "pending",
                    "due_date": "2030-02-25T18:00:00-05:00",
                    "created_by_name": "Yerlys",
                },
                request_only=True,
            ),
        ],
    ),
    retrieve=extend_schema(
        tags=["Tasks"],
        summary="Consultar tarea por ID",
        description="Retorna el detalle de una tarea específica por su `id`.",
    ),
    update=extend_schema(
        tags=["Tasks"],
        summary="Actualizar tarea completa (PUT)",
        description="Actualiza todos los campos de la tarea (recomendado usar PATCH si es parcial).",
    ),
    partial_update=extend_schema(
        tags=["Tasks"],
        summary="Actualizar tarea parcial (PATCH)",
        description="Actualiza parcialmente campos de la tarea. Aplica validaciones de fechas y estado.",
    ),
    destroy=extend_schema(
        tags=["Tasks"],
        summary="Eliminar tarea (soft delete)",
        description=(
            "Elimina una tarea de forma lógica.\n\n"
            "- No se borra físicamente.\n"
            "- Se marca `deleted_at`.\n"
            "- Retorna **204 No Content**."
        ),
    ),
)
class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    queryset = Task.objects.all()  # necesario para retrieve/update/destroy
    search_fields = ["title", "description", "created_by_name"]
    ordering_fields = ["created_at", "due_date", "status"]
    filterset_class = TaskFilter

    def get_queryset(self):
        """Retorna queryset base; por defecto excluye tareas eliminadas (deleted_at IS NULL)."""
        qs = super().get_queryset()
        include_deleted = self.request.query_params.get("include_deleted", "false").lower() == "true"
        if not include_deleted:
            qs = qs.filter(deleted_at__isnull=True)
        return qs

    def get_object(self):
        """Obtiene una tarea por id; si está eliminada y no se pide include_deleted=true, responde 404."""
        obj = super().get_object()
        if obj.deleted_at is not None and self.request.query_params.get("include_deleted", "false").lower() != "true":
            raise NotFound("Task not found.")
        return obj

    def destroy(self, request, *args, **kwargs):
        """Eliminación lógica: marca deleted_at y responde 204."""
        task = self.get_object()
        task.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        tags=["Tasks"],
        summary="Cambiar estado de una tarea",
        description=(
            "Endpoint dedicado para cambiar **solo** el `status`.\n\n"
            "Estados permitidos: `pending`, `completed`, `postponed`."
        ),
        request=TaskStatusSerializer,
        responses=TaskSerializer,
        examples=[
            OpenApiExample(
                "Cambiar a completada",
                value={"status": "completed"},
                request_only=True,
            )
        ],
    )
    @action(detail=True, methods=["patch"], url_path="status")
    def change_status(self, request, pk=None):
        """Cambia únicamente el estado de la tarea (pending/completed/postponed) y responde la tarea actualizada."""
        task = self.get_object()
        serializer = TaskStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        task.status = serializer.validated_data["status"]
        task.save(update_fields=["status", "updated_at"])

        return Response(TaskSerializer(task).data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Tasks"],
        summary="Listar tareas próximas a vencer",
        description=(
            "Retorna tareas con `due_date` próximo según un criterio.\n\n"
            "**Criterio:** por defecto próximas a vencer en **7 días**.\n"
            "Se puede ajustar con `within_days`.\n"
            "Excluye tareas `completed`."
        ),
        parameters=[
            OpenApiParameter(
                name="within_days",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Número de días hacia adelante. Default: 7.",
            ),
        ],
        responses=TaskSerializer(many=True),
    )
    @action(detail=False, methods=["get"], url_path="upcoming")
    def upcoming(self, request):
        """
            Lista tareas próximas a vencer.

            Criterio:
            - No eliminadas
            - Con due_date
            - due_date entre [now, now + within_days]
            - Excluye status=completed
        """
        within_days_raw = request.query_params.get("within_days", "7")

        try:
            within_days = int(within_days_raw)
        except (TypeError, ValueError):
            raise ValidationError({"within_days": "Debe ser un entero. Ej: 1, 2, 7"})

        if within_days < 0:
            raise ValidationError({"within_days": "No puede ser negativo."})

        now = timezone.now()
        until = now + timezone.timedelta(days=within_days)

        qs = (
            self.get_queryset()
            .filter(
                due_date__isnull=False,
                due_date__gte=now,
                due_date__lte=until,
            )
            .exclude(status="completed")
            .order_by("due_date")
        )

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = TaskSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = TaskSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)