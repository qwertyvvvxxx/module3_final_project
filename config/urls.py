from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from graphene_django.views import GraphQLView

from apps.analytics.schema import schema
from apps.core.admin import analytics_view
from apps.core.views import health


class StaffGraphQLView(GraphQLView):
    """Only staff members may run analytics queries; everyone else gets 403."""

    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_authenticated and request.user.is_staff):
            from django.http import JsonResponse

            return JsonResponse(
                {"errors": [{"message": "Доступ лише для співробітників."}]}, status=403
            )
        return super().dispatch(request, *args, **kwargs)


urlpatterns = [
    path("admin/analytics/", analytics_view, name="admin_analytics"),
    path("admin/", admin.site.urls),
    path("health/", health, name="health"),
    path("graphql/", csrf_exempt(StaffGraphQLView.as_view(schema=schema)), name="graphql"),
    path("", include("apps.catalog.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("", include("apps.orders.urls")),
    path("", include("apps.reviews.urls")),
    path("delivery/", include("apps.delivery.urls")),
    path("staff/", include("apps.staff.urls")),
    path("api/", include("apps.api.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
