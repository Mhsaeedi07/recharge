from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CreditRequestViewSet, TransactionViewSet


router = DefaultRouter()
router.register(r'credit-requests', CreditRequestViewSet)
router.register(r'transactions', TransactionViewSet, basename='transaction')

urlpatterns = [
    path('', include(router.urls)),
]