from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'cartes', views.CarteRFIDViewSet)
router.register(r'historique-statuts', views.HistoriqueStatutsCarteViewSet)
# router.register(r'client/cards', views.ClientCarteRFIDViewSet, basename='client-cards')

urlpatterns = [
    path('', include(router.urls)),
    path('client/cards/', views.ClientCarteRFIDViewSet.as_view({'get': 'list'})),
]
