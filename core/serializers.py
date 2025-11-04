from rest_framework_gis.serializers import GeoFeatureModelSerializer
from .models import Property, PointOfInterest

class PropertySerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Property
        geo_field = "location"
        fields = ("id", "name", "address")
class POISerializer(GeoFeatureModelSerializer):
    class Meta:
        model = PointOfInterest
        geo_field = "location"
        fields = ("id", "name", "poi_type")