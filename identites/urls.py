from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'personnes', views.PersonneViewSet)
router.register(r'entreprises', views.EntrepriseViewSet)
router.register(r'utilisateurs', views.UtilisateurViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
