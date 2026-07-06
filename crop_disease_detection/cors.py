from django.conf import settings
from django.http import HttpResponse


class CredentialedCorsMiddleware:
    """Ensure browser preflight requests include credentials for trusted origins."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        origin = request.headers.get("Origin")

        if self._is_allowed_origin(origin) and request.method == "OPTIONS":
            response = HttpResponse(status=200)
        else:
            response = self.get_response(request)

        if self._is_allowed_origin(origin):
            response["Access-Control-Allow-Origin"] = origin
            response["Access-Control-Allow-Credentials"] = "true"
            response["Access-Control-Expose-Headers"] = "*"
            if request.method == "OPTIONS":
                response["Access-Control-Allow-Methods"] = "DELETE, GET, OPTIONS, PATCH, POST, PUT"
                requested_headers = request.headers.get("Access-Control-Request-Headers")
                response["Access-Control-Allow-Headers"] = requested_headers or ", ".join(settings.CORS_ALLOW_HEADERS)
                response["Access-Control-Max-Age"] = "600"
            vary = response.get("Vary")
            response["Vary"] = "Origin" if not vary else f"{vary}, Origin"

        return response

    @staticmethod
    def _is_allowed_origin(origin):
        if not origin:
            return False
        return origin in getattr(settings, "CORS_ALLOWED_ORIGINS", [])
