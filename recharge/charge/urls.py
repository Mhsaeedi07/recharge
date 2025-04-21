from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PhoneNumberViewSet, ChargeSaleViewSet


router = DefaultRouter()
router.register(r'phone-numbers', PhoneNumberViewSet)
router.register(r'charges', ChargeSaleViewSet, basename='charge')

urlpatterns = [
    path('', include(router.urls)),
]