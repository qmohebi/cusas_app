from django.contrib.auth.middleware import RemoteUserMiddleware
from django.conf import settings
from django.urls import resolve


class ConditionalRemoteUserMiddleware(RemoteUserMiddleware):
    """
    Only apply RemoteUser authentication on specific URL patterns
    Everywhere else, the user is anonymouse unless manually authenticated"""

    protected_paths = ["/mpce-staff"]

    def process_request(self, request):
        # if any(request.path.startswith(path) for path in self.protected_paths):
        #     return super().process_request(request)

        protected_paths = getattr(settings, "REMOTE_USER_PROTECTED_PATHS", [])
        if any(request.path.startswith(p) for p in protected_paths):
            return super().process_request(request)

        # Or check by view name
        try:
            match = resolve(request.path)
            protected_views = getattr(settings, "REMOTE_USER_PROTECTED_VIEWS", [])
            if match.view_name in protected_views:
                return super().process_request(request)
        except Exception:
            # resolve() can fail on 404s
            pass

        # If neither matched → leave request.user as-is (AnonymousUser)
        return None
