from rest_framework import status as http_status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """
    Manejador global de errores para DRF.

    - Devuelve un formato de error estándar en toda la API.
    - Si DRF no maneja la excepción: responde 500 (internal_error).
    - Si DRF la maneja: mantiene el status y envuelve response.data (request_error).
    """
    response = exception_handler(exc, context)

    if response is None:
        return Response(
            {
                "error": {
                    "code": "internal_error",
                    "message": "Unexpected server error.",
                    "details": None,
                }
            },
            status=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Normalize DRF error formats
    message = "Request validation failed."
    details = response.data

    return Response(
        {
            "error": {
                "code": "request_error",
                "message": message,
                "details": details,
            }
        },
        status=response.status_code,
    )