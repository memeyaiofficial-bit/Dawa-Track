"""
Middleware for the audit app.

Logs all HTTP requests for audit trail and compliance.
"""
import logging

logger = logging.getLogger('audit')


class AuditLoggingMiddleware:
    """Middleware that logs all incoming requests for audit purposes."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log the incoming request
        if request.method not in ('GET', 'HEAD', 'OPTIONS'):
            logger.info(
                'Audit: %s %s from %s user=%s',
                request.method,
                request.path,
                request.META.get('REMOTE_ADDR'),
                request.user.email if request.user.is_authenticated else 'anonymous',
            )

        response = self.get_response(request)
        return response
