from django.http import HttpRequest, JsonResponse


def health(request: HttpRequest) -> JsonResponse:
    """Liveness endpoint for Docker and CI."""
    return JsonResponse({"healthy": True})
