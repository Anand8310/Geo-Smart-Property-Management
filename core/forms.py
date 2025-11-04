# core/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db.models import Avg
from .models import (Profile, MaintenanceRequest, Property, Message,
                     ForSaleResidentialDetails, ForRentResidentialDetails, LandPlotDetails,
                     ForRentCommercialDetails, ForSaleCommercialDetails, PGGuestHouseDetails,
                       Tenancy, VendorProfile, Expense, Review, ViewingAppointment, Scene, Hotspot)

class CustomUserCreationForm(UserCreationForm):
    role = forms.ChoiceField(choices=Profile.ROLE_CHOICES)
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email',)

class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = ['name', 'category', 'address', 'description', 
                  'image1', 'image2', 'image3', 'location']
        # This is the key: we use a hidden input that our manual map will control.
        widgets = {
            'location': forms.HiddenInput(),
        }

class MaintenanceRequestForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # Get the user from the view
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            # Find the properties this user is an active tenant of
            active_tenancies = Tenancy.objects.filter(tenant=user, is_active=True)
            rented_properties = [tenancy.property for tenancy in active_tenancies]

            # Update the queryset for the 'property' field
            self.fields['property'].queryset = Property.objects.filter(pk__in=[prop.pk for prop in rented_properties])
            self.fields['property'].empty_label = None # No empty "Choose..." option needed if there's only one

    class Meta:
        model = MaintenanceRequest
        fields = ['property', 'description']

class InquiryForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        widgets = {'content': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Ask a question...'}),}

class ForSaleResidentialDetailsForm(forms.ModelForm):
    class Meta:
        model = ForSaleResidentialDetails
        fields = ['price']

class ForRentResidentialDetailsForm(forms.ModelForm):
    class Meta:
        model = ForRentResidentialDetails
        fields = ['monthly_rent', 'security_deposit', 'furnishing_status']

class LandPlotDetailsForm(forms.ModelForm):
    class Meta:
        model = LandPlotDetails
        fields = ['plot_area', 'is_gated_community', 'utilities_available', 'price']

class ForRentCommercialDetailsForm(forms.ModelForm):
    class Meta:
        model = ForRentCommercialDetails
        fields = ['square_feet', 'washrooms', 'parking_available', 'monthly_rent']

class ForSaleCommercialDetailsForm(forms.ModelForm):
    class Meta:
        model = ForSaleCommercialDetails
        fields = ['price', 'square_feet', 'year_built', 'total_floors']

class PGGuestHouseDetailsForm(forms.ModelForm):
    class Meta:
        model = PGGuestHouseDetails
        fields = ['price_per_month', 'food_included', 'beds_per_room', 'occupancy_type']

class TenancyForm(forms.ModelForm):
    # This field will allow the owner to select an existing user to be the tenant
    tenant = forms.ModelChoiceField(
        queryset=User.objects.filter(profile__role='tenant'),
        label="Select Tenant"
    )

    class Meta:
        model = Tenancy
        fields = ['tenant', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }
class VendorProfileForm(forms.ModelForm):
    class Meta:
        model = VendorProfile
        fields = ['company_name', 'service_type', 'service_area']

class VendorChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        # --- NEW LOGIC TO CALCULATE AND DISPLAY AVERAGE RATING ---
        user_content_type = ContentType.objects.get_for_model(User)
        avg_rating = Review.objects.filter(
            content_type=user_content_type, 
            object_id=obj.id
        ).aggregate(avg=Avg('rating'))['avg']

        avg_rating_str = "No ratings yet"
        if avg_rating:
            avg_rating_str = f"{avg_rating:.1f} ★"

        return f"{obj.username} ({obj.vendor_profile.get_service_type_display()}) - {avg_rating_str}"
    
class AssignVendorForm(forms.ModelForm):
    # This field creates a dropdown of users who are vendors AND are approved
    assigned_vendor = VendorChoiceField(
        queryset=User.objects.filter(profile__role='vendor', vendor_profile__is_approved=True),
        label="Select an Approved Vendor to Assign",
        empty_label="-- Select a Service Professional --"
    )

    class Meta:
        model = MaintenanceRequest
        fields = ['assigned_vendor']
        
class ExpenseForm(forms.ModelForm):
            class Meta:
                model = Expense
                fields = ['category', 'description', 'amount', 'date']
                widgets = {
                    'date': forms.DateInput(attrs={'type': 'date'}),
        }
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4}),
        }

class ViewingAppointmentForm(forms.ModelForm):
    class Meta:
        model = ViewingAppointment
        fields = ['requested_datetime']
        widgets = {
            'requested_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
        labels = {
            'requested_datetime': 'Select a Preferred Date and Time',
        }

class SceneForm(forms.ModelForm):
    class Meta:
        model = Scene
        fields = ['scene_name', 'panorama_image', 'is_first_scene']
        labels = {
            'is_first_scene': 'Make this the starting scene for the tour?'
        }

class HotspotForm(forms.ModelForm):
    class Meta:
        model = Hotspot
        fields = ['target_scene', 'pitch', 'yaw', 'text']

    def __init__(self, *args, **kwargs):
        # This is to limit the 'target_scene' dropdown to only show
        # scenes that belong to the same property.
        property_obj = kwargs.pop('property', None)
        super().__init__(*args, **kwargs)
        if property_obj:
            self.fields['target_scene'].queryset = Scene.objects.filter(property=property_obj)