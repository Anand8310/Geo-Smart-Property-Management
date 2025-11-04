from django.urls import path
from .views import PropertyListAPIView, POIListAPIView, NeighborhoodAnalyticsAPIView, get_market_rate_api_view


urlpatterns = [
    path('properties/', PropertyListAPIView.as_view(), name='property-list'),
    path('pois/', POIListAPIView.as_view(), name='poi-list'),
    path('analytics/', NeighborhoodAnalyticsAPIView.as_view(), name='neighborhood-analytics'),
    path('market-rate/', get_market_rate_api_view, name='market-rate-api'),
]