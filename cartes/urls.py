from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'cartes', views.CarteRFIDViewSet)
router.register(r'historique-statuts', views.HistoriqueStatutsCarteViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
