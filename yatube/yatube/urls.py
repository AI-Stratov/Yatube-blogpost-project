from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("posts.urls", namespace="posts")),
    path("admin/", admin.site.urls),
    path("about/", include("about.urls", namespace="about")),
    path("auth/", include("users.urls")),
    path("auth/", include("django.contrib.auth.urls")),
]

handler404 = 'core.views.page_not_found'
handler403 = 'core.views.csrf_failure'
handler500 = 'core.views.server_error'
