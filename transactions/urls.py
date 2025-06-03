from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'transactions', views.TransactionViewSet)
router.register(r'rechargements', views.RechargementViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('client/', include([
        path('payments/detailed-history/', views.TransactionViewSet.as_view({'get': 'detailed_history'})),
        path('payments/statistics/', views.TransactionViewSet.as_view({'get': 'statistics'})),
        path('payments/export/', views.TransactionViewSet.as_view({'get': 'export'})),
        path('payments/transactions/<uuid:pk>/receipt/', views.TransactionViewSet.as_view({'get': 'receipt'})),
        path('payments/transactions/<uuid:pk>/refund/', views.TransactionViewSet.as_view({'post': 'request_refund'})),
        path('payments/history/', views.TransactionViewSet.as_view({'get': 'detailed_history'})),
    ])),
]
