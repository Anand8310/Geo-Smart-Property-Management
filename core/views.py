# core/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.gis.geos import Point, Polygon
from django.contrib.gis.measure import D
from django.views.generic import TemplateView
from rest_framework import generics
from django.http import JsonResponse
from datetime import date, timedelta
from django.db.models import Count, Avg
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry
from django.db.models import Avg
from django.contrib.contenttypes.models import ContentType
from datetime import datetime

from .models import (Expense, Property, MaintenanceRequest, Invoice, Document,
                     Conversation, Message, Profile, PointOfInterest, PropertyView,
                     Tenancy, VendorProfile, Application, ForSaleResidentialDetails,
                     ForRentResidentialDetails, LandPlotDetails, ForRentCommercialDetails,
                     ForSaleCommercialDetails, PGGuestHouseDetails, Review, Property,
                     ViewingAppointment, Expense, Scene, Hotspot)
from .serializers import PropertySerializer, POISerializer
from .forms import (CustomUserCreationForm, MaintenanceRequestForm,
                    PropertyForm, InquiryForm, ForSaleResidentialDetailsForm,
                    ForRentResidentialDetailsForm, LandPlotDetailsForm,
                    ForRentCommercialDetailsForm, ForSaleCommercialDetailsForm,
                    PGGuestHouseDetailsForm, TenancyForm, VendorProfileForm,
                    AssignVendorForm, ExpenseForm, ReviewForm, ViewingAppointmentForm, SceneForm, HotspotForm)

# --- Main & API Views ---
class MapView(TemplateView):

    def get_template_names(self):
        # This function now chooses the correct template based on user role
        if self.request.user.is_authenticated:
            if self.request.user.is_staff:
                return ["owner_home.html"] # New Homepage for Owners
            elif hasattr(self.request.user, 'profile') and self.request.user.profile.role == 'vendor':
                return ["vendor_home.html"] # New Homepage for Vendors
            else:
                return ["index.html"] # The Map for Tenants
        else:
            return ["landing_page.html"] # The Landing Page for logged-out users

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Only add is_staff_user context if we are rendering the map page
        if self.template_name == "index.html":
            context['is_staff_user'] = self.request.user.is_staff
        return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Only add this context if the user is logged in
        if self.request.user.is_authenticated:
            context['is_staff_user'] = self.request.user.is_staff
        return context

class PropertyListAPIView(generics.ListAPIView):
    serializer_class = PropertySerializer
    def get_queryset(self):
        queryset = Property.objects.filter(status='available')
        latitude = self.request.query_params.get('lat')
        longitude = self.request.query_params.get('lon')
        radius = self.request.query_params.get('radius')
        category = self.request.query_params.get('category')
        if latitude and longitude and radius:
            center_point = Point(float(longitude), float(latitude), srid=4326)
            queryset = queryset.filter(location__distance_lte=(center_point, D(km=radius)))
        if category and category != 'all':
            queryset = queryset.filter(category=category)
        return queryset

class POIListAPIView(generics.ListAPIView):
    queryset = PointOfInterest.objects.all()
    serializer_class = POISerializer

class NeighborhoodAnalyticsAPIView(generics.GenericAPIView):
    def get(self, request, *args, **kwargs):
        bounds_str = request.query_params.get('bounds')
        if not bounds_str: return JsonResponse({'error': 'Bounds not provided'}, status=400)
        try:
            coords = [float(c) for c in bounds_str.split(',')]
            bbox_polygon = Polygon.from_bbox((coords[0], coords[1], coords[2], coords[3]))
            bbox_polygon.srid = 4326
        except (ValueError, IndexError): return JsonResponse({'error': 'Invalid bounds format'}, status=400)

        properties_in_view = Property.objects.filter(location__within=bbox_polygon, status='available')
        avg_sale_price = properties_in_view.filter(category__in=['sale_residential', 'sale_commercial', 'land_plot']).aggregate(avg_price=Avg('for_sale_residential_details__price'))['avg_price']
        avg_rent_price = properties_in_view.filter(category='rent_residential').aggregate(avg_rent=Avg('for_rent_residential_details__monthly_rent'))['avg_rent']
        category_distribution = properties_in_view.values('category').annotate(count=Count('id')).order_by('-count')
        data = {'avg_sale_price': avg_sale_price or 0, 'avg_rent_price': avg_rent_price or 0, 'category_distribution': list(category_distribution), 'total_properties_in_view': properties_in_view.count(),}
        return JsonResponse(data)

# --- Authentication Views ---
def register_view(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            role = form.cleaned_data.get('role')
            user.profile.role = role
            user.profile.save()
            if role == 'vendor':
                VendorProfile.objects.create(user=user, service_type='plumbing') # Default service
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')

# --- Tenant Feature Views ---
@login_required
def submit_request_view(request):
    # Find the active tenancy for the current user
    active_tenancy = Tenancy.objects.filter(tenant=request.user, is_active=True).first()

    # If the user has no active tenancy, they cannot submit a request.
    if not active_tenancy:
        messages.error(request, "You must have an active tenancy to submit a maintenance request.")
        return redirect('home') # Redirect them away from the form

    # If the request is a POST, process the form
    if request.method == 'POST':
        form = MaintenanceRequestForm(request.POST, user=request.user)
        if form.is_valid():
            maintenance_request = form.save(commit=False)
            maintenance_request.tenant = request.user
            # The form will automatically set the correct property
            maintenance_request.save()
            messages.success(request, "Your maintenance request has been submitted successfully!")
            return redirect('view_requests')
    else:
        # Pass the user to the form to filter the properties
        form = MaintenanceRequestForm(user=request.user)

    context = {
        'form': form
    }
    return render(request, 'submit_request.html', context)

@login_required
def view_requests_view(request):
    requests = MaintenanceRequest.objects.filter(tenant=request.user)
    return render(request, 'view_requests.html', {'requests': requests})

@login_required
def view_invoices_view(request):
    invoices = Invoice.objects.filter(tenant=request.user)
    return render(request, 'view_invoices.html', {'invoices': invoices})

@login_required
def view_documents_view(request):
    documents = Document.objects.filter(tenant=request.user)
    return render(request, 'view_documents.html', {'documents': documents})

@login_required
def tenant_conversations_view(request):
    conversations = Conversation.objects.filter(tenant=request.user).order_by('-created_at')
    return render(request, 'tenant_conversations.html', {'conversations': conversations})

@login_required
def view_shortlist_view(request):
    shortlisted_properties = request.user.profile.shortlisted_properties.all()
    return render(request, 'view_shortlist.html', {'shortlisted_properties': shortlisted_properties})

@login_required
def toggle_shortlist_view(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id)
    profile = request.user.profile
    if property_obj in profile.shortlisted_properties.all():
        profile.shortlisted_properties.remove(property_obj)
        messages.success(request, f"'{property_obj.name}' removed from shortlist.")
    else:
        profile.shortlisted_properties.add(property_obj)
        messages.success(request, f"'{property_obj.name}' added to shortlist.")
    return redirect('property_detail', property_id=property_id)

@login_required
def my_tenancy_view(request):
    all_tenancies = Tenancy.objects.filter(tenant=request.user).order_by('-is_active', '-end_date')

    context = {
        'tenancies': all_tenancies
    }
    return render(request, 'my_tenancy.html', context)

@login_required
def tenant_confirm_completion_view(request, request_id):
    job = get_object_or_404(MaintenanceRequest, id=request_id, tenant=request.user)
    if job.status == 'Pending Approval':
        job.status = 'Completed'
        job.save()
        messages.success(request, 'You have confirmed the completion of the work.')
    else:
        messages.error(request, 'This job is not awaiting your confirmation.')
    return redirect('view_requests')

@login_required
def property_vote_view(request, property_id, vote_type):
    property_obj = get_object_or_404(Property, id=property_id)
    profile = request.user.profile
    if vote_type == 'like':
        if property_obj in profile.liked_properties.all():
            profile.liked_properties.remove(property_obj)
        else:
            profile.liked_properties.add(property_obj)
            profile.disliked_properties.remove(property_obj)
    elif vote_type == 'dislike':
        if property_obj in profile.disliked_properties.all():
            profile.disliked_properties.remove(property_obj)
        else:
            profile.disliked_properties.add(property_obj)
            profile.liked_properties.remove(property_obj)
    property_obj.likes = property_obj.liked_by.count()
    property_obj.dislikes = property_obj.disliked_by.count()
    property_obj.save()
    return redirect('property_detail', property_id=property_id)

@login_required
def apply_for_tenancy_view(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id)
    if Application.objects.filter(property=property_obj, applicant=request.user).exists():
        messages.warning(request, 'You have already applied for this property.')
        return redirect('property_detail', property_id=property_id)
    if request.method == 'POST':
        Application.objects.create(property=property_obj, applicant=request.user)
        messages.success(request, 'Your application has been submitted!')
        return redirect('property_detail', property_id=property_id)
    return redirect('property_detail', property_id=property_id)

# --- Owner Feature Views ---
def is_staff(user):
    return user.is_staff

@user_passes_test(is_staff)
def owner_dashboard_view(request):
    owner_properties = Property.objects.filter(owner=request.user)
    context = {
        'total_properties': owner_properties.count(),
        'total_tenants': User.objects.filter(invoice__property__in=owner_properties).distinct().count(),
        'total_open_requests': MaintenanceRequest.objects.filter(property__in=owner_properties, status__in=['Submitted', 'In Progress', 'Assigned']).count(),
        'total_unpaid_invoices': Invoice.objects.filter(property__in=owner_properties, status='Unpaid').count(),
    }
    return render(request, 'owner_dashboard.html', context)

@user_passes_test(is_staff)
def my_properties_view(request):
    properties = Property.objects.filter(owner=request.user)
    return render(request, 'my_properties.html', {'properties': properties})

@user_passes_test(is_staff)
def add_property_view(request):
    property_form = PropertyForm(request.POST or None, request.FILES or None)
    sale_residential_form = ForSaleResidentialDetailsForm(request.POST or None)
    rent_residential_form = ForRentResidentialDetailsForm(request.POST or None)
    land_plot_form = LandPlotDetailsForm(request.POST or None)
    rent_commercial_form = ForRentCommercialDetailsForm(request.POST or None)
    sale_commercial_form = ForSaleCommercialDetailsForm(request.POST or None)
    pg_guest_house_form = PGGuestHouseDetailsForm(request.POST or None)

    if request.method == 'POST':
        category = request.POST.get('category')
        details_form_map = {
            'sale_residential': sale_residential_form, 'rent_residential': rent_residential_form,
            'land_plot': land_plot_form, 'rent_commercial': rent_commercial_form,
            'sale_commercial': sale_commercial_form, 'pg_guest_house': pg_guest_house_form,
        }
        details_form = details_form_map.get(category)

        if property_form.is_valid() and (details_form is None or not details_form.fields or details_form.is_valid()):
            property_instance = property_form.save(commit=False)
            property_instance.owner = request.user
            property_instance.save()
            if details_form and details_form.fields:
                details_instance = details_form.save(commit=False)
                details_instance.property = property_instance
                details_instance.save()
            messages.success(request, 'Property has been added successfully!')
            return redirect('my_properties')
        else:
            messages.error(request, 'Please correct the errors below.')

    context = {
        'property_form': property_form,
        'sale_residential_form': sale_residential_form,
        'rent_residential_form': rent_residential_form,
        'land_plot_form': land_plot_form,
        'rent_commercial_form': rent_commercial_form,
        'sale_commercial_form': sale_commercial_form,
        'pg_guest_house_form': pg_guest_house_form,
    }
    return render(request, 'add_edit_property.html', context)

@user_passes_test(is_staff)
def edit_property_view(request, property_id):
    property_instance = get_object_or_404(Property, id=property_id, owner=request.user)
    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES, instance=property_instance)
        if form.is_valid():
            form.save()
            return redirect('my_properties')
    else:
        form = PropertyForm(instance=property_instance)
    return render(request, 'add_edit_property.html', {'form': form})

@user_passes_test(is_staff)
def delete_property_view(request, property_id):
    property_instance = get_object_or_404(Property, id=property_id, owner=request.user)
    if request.method == 'POST':
        property_instance.delete()
        return redirect('my_properties')
    return render(request, 'delete_property_confirm.html', {'property': property_instance})

@user_passes_test(is_staff)
def view_applications_view(request):
    owner_properties = Property.objects.filter(owner=request.user)
    applications = Application.objects.filter(property__in=owner_properties).order_by('-applied_at')
    return render(request, 'view_applications.html', {'applications': applications})

# --- Conversation & Inquiry Views ---
def property_detail_view(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id)
    details = None
    if hasattr(property_obj, 'for_sale_residential_details'):
        details = property_obj.for_sale_residential_details
    elif hasattr(property_obj, 'for_rent_residential_details'):
        details = property_obj.for_rent_residential_details
    elif hasattr(property_obj, 'land_plot_details'):
        details = property_obj.land_plot_details
    elif hasattr(property_obj, 'for_rent_commercial_details'):
        details = property_obj.for_rent_commercial_details
    elif hasattr(property_obj, 'for_sale_commercial_details'):
        details = property_obj.for_sale_commercial_details
    elif hasattr(property_obj, 'pg_guest_house_details'):
        details = property_obj.pg_guest_house_details
    property_content_type = ContentType.objects.get_for_model(Property)
    reviews = Review.objects.filter(content_type=property_content_type, object_id=property_obj.id)
    average_rating = reviews.aggregate(Avg('rating'))['rating__avg']
    scenes = Scene.objects.filter(property=property_obj)
    tour_config = {
        'default': {},
        'scenes': {}
    }

    if scenes.exists():
        # Find the first scene (or any scene if none is marked)
        first_scene = scenes.filter(is_first_scene=True).first()
        if not first_scene:
            first_scene = scenes.first()

        tour_config['default']['firstScene'] = f'scene-{first_scene.id}'

        for scene in scenes:
            scene_key = f'scene-{scene.id}'
            tour_config['scenes'][scene_key] = {
                'title': scene.scene_name,
                'panorama': scene.panorama_image.url,
                'hotSpots': []
            }

            # Add hotspots for this scene
            for hotspot in scene.hotspots.all():
                tour_config['scenes'][scene_key]['hotSpots'].append({
                    'pitch': hotspot.pitch,
                    'yaw': hotspot.yaw,
                    'type': 'scene',
                    'text': hotspot.text,
                    'sceneId': f'scene-{hotspot.target_scene.id}'
                })
   

    if request.user.is_staff and property_obj.owner != request.user:
        messages.error(request, "You do not have permission to view this property.")
        return redirect('home')
    inquiry_form = InquiryForm()
    viewing_appointment_form = ViewingAppointmentForm()
    now = datetime.now()
    min_datetime_for_form = now.strftime('%Y-%m-%dT%H:%M')
    if request.method == 'POST' and 'content' in request.POST:
        form = InquiryForm(request.POST)
        if form.is_valid():
            conversation, created = Conversation.objects.get_or_create(property=property_obj, tenant=request.user, owner=property_obj.owner)
            Message.objects.create(conversation=conversation, sender=request.user, content=form.cleaned_data['content'])
            messages.success(request, 'Your inquiry has been sent!')
            return redirect('property_detail', property_id=property_obj.id)

    context = { 'property': property_obj,
                'details': details,
                'inquiry_form': inquiry_form,
                'reviews': reviews,
                'average_rating': average_rating,
                'viewing_appointment_form': viewing_appointment_form,
                'min_datetime_for_form': min_datetime_for_form,
                'tour_config': tour_config,
              }
    return render(request, 'property_detail.html', context)

# in core/views.py

@user_passes_test(is_staff)
def manage_application_view(request, application_id, action):
    application = get_object_or_404(Application, id=application_id, property__owner=request.user)
    property_obj = application.property
    tenant = application.applicant

    if request.method == 'POST':
        if action == 'approve':
            start_date_str = request.POST.get('start_date')
            end_date_str = request.POST.get('end_date')

            if not start_date_str or not end_date_str:
                messages.error(request, 'Start date and end date are required to approve an application.')
                return redirect('view_applications')

            start_date = date.fromisoformat(start_date_str)
            end_date = date.fromisoformat(end_date_str)

            Tenancy.objects.create(
                property=property_obj, tenant=tenant,
                start_date=start_date, end_date=end_date, is_active=True
            )
            property_obj.status = 'occupied'
            property_obj.save()
            application.status = 'approved'
            application.save()
            Application.objects.filter(property=property_obj, status='pending').update(status='rejected')

            # --- Send Approval Email ---
            subject = f"Congratulations! Your application for {property_obj.name} has been approved."
            html_message = render_to_string('email_tenancy_notification.html', {
                'tenant_name': tenant.first_name or tenant.username,
                'property_name': property_obj.name, 'start_date': start_date, 'end_date': end_date,
            })
            send_mail(subject, "Your application has been approved!", settings.DEFAULT_FROM_EMAIL, [tenant.email], html_message=html_message)

            messages.success(request, f"Application for {tenant.username} has been approved and they have been notified.")

        elif action == 'reject':
            application.status = 'rejected'
            application.save()
            messages.info(request, f"Application for {tenant.username} has been rejected.")

        elif action == 'cancel':
            tenancy = Tenancy.objects.filter(property=property_obj, tenant=tenant, is_active=True).first()
            if tenancy:
                tenancy.is_active = False
                tenancy.save()

            property_obj.status = 'available'
            property_obj.save()
            application.status = 'rejected' # Mark old application for historical clarity
            application.save()

            # --- THIS IS THE MISSING CODE TO SEND THE CANCELLATION EMAIL ---
            subject = f"Notification: Your tenancy for {property_obj.name} has been cancelled"
            html_message = render_to_string('email_tenancy_cancellation.html', {
                'tenant_name': tenant.first_name or tenant.username,
                'property_name': property_obj.name,
                'owner_name': request.user.first_name or request.user.username,
            })
            send_mail(subject, "Your tenancy has been cancelled.", settings.DEFAULT_FROM_EMAIL, [tenant.email], html_message=html_message)

            messages.warning(request, f"The tenancy for {tenant.username} has been cancelled and they have been notified.")

    return redirect('view_applications')

@user_passes_test(is_staff)
def view_inquiries_view(request):
    conversations = Conversation.objects.filter(owner=request.user).order_by('-created_at')
    return render(request, 'view_inquiries.html', {'conversations': conversations})

@login_required
def conversation_detail_view(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)
    if not (request.user == conversation.owner or request.user == conversation.tenant):
        return redirect('home')
    if request.method == 'POST':
        message_content = request.POST.get('message')
        if message_content:
            Message.objects.create(conversation=conversation, sender=request.user, content=message_content)
            return redirect('conversation_detail', conversation_id=conversation.id)
    return render(request, 'conversation_detail.html', {'conversation': conversation})

# --- Vendor & Job Views ---
@login_required
def vendor_dashboard_view(request):
    # Security check: Ensure the user has a vendor profile and is a vendor
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'vendor':
        raise PermissionDenied

    vendor_profile, created = VendorProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = VendorProfileForm(request.POST, instance=vendor_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('vendor_dashboard')
        else:
            # This is the new logic that handles the error
            # If the form is not valid, the errors will be attached to the form
            # and the page will be re-rendered to display them.
            messages.error(request, 'Please correct the errors below.')
    else:
        form = VendorProfileForm(instance=vendor_profile)

    context = {
        'form': form
    }
    return render(request, 'vendor_dashboard.html', context)

@login_required
def job_board_view(request):
    if request.user.profile.role != 'vendor': raise PermissionDenied
    open_jobs = MaintenanceRequest.objects.filter(status__in=['Submitted', 'In Progress']).order_by('-submitted_at')
    return render(request, 'job_board.html', {'open_jobs': open_jobs})

@user_passes_test(is_staff)
def manage_tenants_view(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
    tenancies = Tenancy.objects.filter(property=property_obj)
    return render(request, 'manage_tenants.html', {'property': property_obj, 'tenancies': tenancies})

@user_passes_test(is_staff)
def add_tenancy_view(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
    if request.method == 'POST':
        form = TenancyForm(request.POST)
        if form.is_valid():
            tenancy = form.save(commit=False)
            tenancy.property = property_obj
            tenancy.save()
            property_obj.status = 'occupied'
            property_obj.save()
            # ... (email logic)
            messages.success(request, f"Tenant added to '{property_obj.name}'.")
            return redirect('manage_tenants', property_id=property_id)
    else:
        form = TenancyForm()
    return render(request, 'add_tenancy.html', {'form': form, 'property': property_obj})

@user_passes_test(is_staff)
def owner_requests_view(request):
    owner_properties = Property.objects.filter(owner=request.user)
    requests = MaintenanceRequest.objects.filter(property__in=owner_properties).order_by('-submitted_at')
    return render(request, 'owner_requests.html', {'requests': requests})

@user_passes_test(is_staff)
def job_detail_owner_view(request, request_id):
    job = get_object_or_404(MaintenanceRequest, id=request_id, property__owner=request.user)
    if request.method == 'POST':
        form = AssignVendorForm(request.POST, instance=job)
        if form.is_valid():
            job.status = 'Assigned'
            form.save()
            messages.success(request, f"Job assigned to {job.assigned_vendor.username}.")
            return redirect('owner_requests')
    else:
        form = AssignVendorForm()
    return render(request, 'job_detail_owner.html', {'job': job, 'form': form})

@login_required
def vendor_assigned_jobs_view(request):
    if request.user.profile.role != 'vendor': raise PermissionDenied
    assigned_jobs = MaintenanceRequest.objects.filter(assigned_vendor=request.user).order_by('-submitted_at')
    return render(request, 'vendor_assigned_jobs.html', {'assigned_jobs': assigned_jobs})

@login_required
def vendor_job_detail_view(request, request_id):
    if request.user.profile.role != 'vendor': raise PermissionDenied
    job = get_object_or_404(MaintenanceRequest, id=request_id, assigned_vendor=request.user)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['In Progress', 'Pending Approval']:
            job.status = new_status
            job.save()
            messages.success(request, 'Job status updated.')
            return redirect('vendor_job_detail', request_id=job.id)
    return render(request, 'vendor_job_detail.html', {'job': job})

# This is the function that was missing
@user_passes_test(is_staff)
def property_analytics_api_view(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
    today = date.today()
    seven_days_ago = today - timedelta(days=6)
    views_by_day = (
        PropertyView.objects.filter(property=property_obj, viewed_at__date__gte=seven_days_ago)
        .values('viewed_at__date').annotate(count=Count('id')).order_by('viewed_at__date')
    )
    labels = [(seven_days_ago + timedelta(days=i)).strftime("%b %d") for i in range(7)]
    view_counts = [0] * 7
    for view in views_by_day:
        day_index = (view['viewed_at__date'] - seven_days_ago).days
        if 0 <= day_index < 7:
            view_counts[day_index] = view['count']
    data = {
        'labels': labels, 'view_counts': view_counts,
        'total_likes': property_obj.likes, 'total_dislikes': property_obj.dislikes,
    }
    return JsonResponse(data)

# core/views.py

       
@user_passes_test(is_staff)
def cancel_tenancy_view(request, tenancy_id):
    # Security check: ensure the owner is cancelling a tenancy for their own property
    tenancy = get_object_or_404(Tenancy, id=tenancy_id, property__owner=request.user)

    if request.method == 'POST':
        property_obj = tenancy.property
        tenant = tenancy.tenant

        # 1. Deactivate the tenancy
        tenancy.is_active = False
        tenancy.save()

        # 2. Make the property available again
        property_obj.status = 'available'
        property_obj.save()

        # 3. (Optional) Find the original application and mark it as rejected
        application = Application.objects.filter(property=property_obj, applicant=tenant).first()
        if application:
            application.status = 'rejected'
            application.save()

        # --- THIS IS THE NEW CODE TO SEND THE CANCELLATION EMAIL ---
        subject = f"Notification: Your tenancy for {property_obj.name} has been cancelled"
        html_message = render_to_string('email_tenancy_cancellation.html', {
            'tenant_name': tenant.first_name or tenant.username,
            'property_name': property_obj.name,
            'owner_name': request.user.first_name or request.user.username,
        })
        send_mail(
            subject, "Your tenancy has been cancelled.",
            settings.DEFAULT_FROM_EMAIL, [tenant.email], html_message=html_message
        )

        messages.warning(request, f"The tenancy for {tenant.username} has been cancelled and they have been notified.")

        # Redirect back to the list of tenants for that property
        return redirect('manage_tenants', property_id=property_obj.id)

    # If not a POST request, just redirect
    return redirect('manage_tenants', property_id=tenancy.property.id)
@user_passes_test(is_staff)
def manage_expenses_view(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
    expenses = Expense.objects.filter(property=property_obj).order_by('-date')

    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.property = property_obj
            expense.save()
            messages.success(request, 'Expense has been added successfully.')
            return redirect('manage_expenses', property_id=property_id)
    else:
        form = ExpenseForm()

    context = {
        'property': property_obj,
        'expenses': expenses,
        'form': form
    }
    return render(request, 'manage_expenses.html', context)

@login_required
def get_market_rate_api_view(request):
    # Get data from the frontend request
    wkt_point = request.GET.get('location')
    category = request.GET.get('category')

    if not wkt_point or not category:
        return JsonResponse({'error': 'Location and category are required.'}, status=400)

    try:
        # Create a geometry object from the location string
        location = GEOSGeometry(wkt_point, srid=4326)
    except Exception:
        return JsonResponse({'error': 'Invalid location format.'}, status=400)

    # --- This is the core Comparative Market Analysis logic ---

    # 1. Find comparable properties (comps)
    # We'll look for properties within a 2km radius that are available and of the same category
    comps = Property.objects.filter(
        location__distance_lte=(location, D(km=2)),
        category=category,
        status='available'
    )

    # 2. Calculate the average rate based on the category
    suggested_rate = 0
    rate_type = ""

    if category == 'sale_residential' or category == 'sale_commercial' or category == 'land_plot':
        # For properties for sale, calculate average price
        aggregation = comps.aggregate(avg_rate=Avg('for_sale_residential_details__price')) # Adjust field based on model
        if aggregation['avg_rate']:
            suggested_rate = round(aggregation['avg_rate'], 2)
        rate_type = "Total Price"

    elif category == 'rent_residential' or category == 'rent_commercial':
        # For properties for rent, calculate average monthly rent
        aggregation = comps.aggregate(avg_rate=Avg('for_rent_residential_details__monthly_rent')) # Adjust field based on model
        if aggregation['avg_rate']:
            suggested_rate = round(aggregation['avg_rate'], 2)
        rate_type = "Monthly Rent"

    elif category == 'pg_guest_house':
        aggregation = comps.aggregate(avg_rate=Avg('pg_guest_house_details__price_per_month'))
        if aggregation['avg_rate']:
            suggested_rate = round(aggregation['avg_rate'], 2)
        rate_type = "Price per Month"

    # 3. Return the result as a JSON response
    data = {
        'suggested_rate': float(suggested_rate),
        'rate_type': rate_type,
        'comps_found': comps.count()
    }

    return JsonResponse(data)

@login_required
def add_review_view(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id)

    # Security check: Ensure user has an inactive tenancy for this property before reviewing
    can_review = Tenancy.objects.filter(property=property_obj, tenant=request.user, is_active=False).exists()
    if not can_review:
        messages.error(request, "You can only review properties after your tenancy has ended.")
        return redirect('my_tenancy')

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.reviewer = request.user

            # Use ContentType to link the review to the Property object
            review.content_type = ContentType.objects.get_for_model(Property)
            review.object_id = property_obj.id
            review.save()

            messages.success(request, 'Your review has been submitted. Thank you!')
            return redirect('property_detail', property_id=property_obj.id)
    else:
        form = ReviewForm()

    context = {
        'form': form,
        'property': property_obj
    }
    return render(request, 'add_review.html', context)

@user_passes_test(is_staff)
def add_vendor_review_view(request, request_id):
    # Security check: Ensure owner is reviewing a job for their own property
    job = get_object_or_404(MaintenanceRequest, id=request_id, property__owner=request.user)

    # Ensure the job is actually completed and had a vendor assigned
    if job.status != 'Completed' or not job.assigned_vendor:
        messages.error(request, "This job is not eligible for a review.")
        return redirect('owner_requests')

    vendor = job.assigned_vendor

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.reviewer = request.user

            # Use ContentType to link the review to the User object (the vendor)
            review.content_type = ContentType.objects.get_for_model(User)
            review.object_id = vendor.id
            review.save()

            messages.success(request, f'Your review for {vendor.username} has been submitted. Thank you!')
            return redirect('owner_requests')
    else:
        form = ReviewForm()

    context = {
        'form': form,
        'job': job,
        'vendor': vendor
    }
    return render(request, 'add_vendor_review.html', context)
@login_required
def request_viewing_view(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id)

    if request.method == 'POST':
        form = ViewingAppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.property = property_obj
            appointment.applicant = request.user
            appointment.save()
            messages.success(request, 'Your viewing request has been sent to the property owner!')
            return redirect('property_detail', property_id=property_id)

    # This view is only for POST requests, so we redirect if it's a GET
    return redirect('property_detail', property_id=property_id)

@user_passes_test(is_staff)
def owner_appointments_view(request):
    # Get all properties owned by the current user
    owner_properties = Property.objects.filter(owner=request.user)
    # Get all viewing appointments related to those properties
    appointments = ViewingAppointment.objects.filter(property__in=owner_properties).order_by('-created_at')

    context = {
        'appointments': appointments
    }
    return render(request, 'owner_appointments.html', context)

@user_passes_test(is_staff)
def manage_appointment_view(request, appointment_id, action):
    # Security check: ensure the owner is managing an appointment for their own property
    appointment = get_object_or_404(ViewingAppointment, id=appointment_id, property__owner=request.user)
    tenant = appointment.applicant

    if request.method == 'POST':
        if action == 'confirm':
            appointment.status = 'confirmed'
            appointment.save()

            # --- NEW LOGIC: SEND CONFIRMATION EMAIL ---
            subject = f"Appointment Confirmed: Viewing for {appointment.property.name}"
            html_message = render_to_string('email_appointment_confirmation.html', {
                'tenant_name': tenant.first_name or tenant.username,
                'property_name': appointment.property.name,
                'appointment_time': appointment.requested_datetime,
                'owner_name': request.user.first_name or request.user.username,
                'owner_email': request.user.email,
            })
            send_mail(
                subject, "Your viewing appointment has been confirmed.",
                settings.DEFAULT_FROM_EMAIL, [tenant.email], html_message=html_message
            )

            messages.success(request, f"Appointment for {tenant.username} has been confirmed and they have been notified.")

        elif action == 'cancel':
            appointment.status = 'cancelled'
            appointment.save()
            # (Optional: Send a cancellation email to the tenant here)
            messages.warning(request, f"Appointment for {tenant.username} has been cancelled.")

    return redirect('owner_appointments')
@user_passes_test(is_staff)
def manage_tour_view(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
    scenes = Scene.objects.filter(property=property_obj)

    if request.method == 'POST':
        form = SceneForm(request.POST, request.FILES)
        if form.is_valid():
            scene = form.save(commit=False)
            scene.property = property_obj
            scene.save()
            messages.success(request, f"New scene '{scene.scene_name}' has been added.")
            return redirect('manage_tour', property_id=property_id)
    else:
        form = SceneForm()

    context = {
        'property': property_obj,
        'scenes': scenes,
        'form': form
    }
    return render(request, 'manage_tour.html', context)
@user_passes_test(is_staff)
def manage_scene_hotspots_view(request, scene_id):
    scene = get_object_or_404(Scene, id=scene_id, property__owner=request.user)
    hotspots = Hotspot.objects.filter(source_scene=scene)

    # Handle form for adding a new hotspot
    if request.method == 'POST':
        # Check if this is a delete request
        if 'delete_hotspot' in request.POST:
            hotspot_id = request.POST.get('hotspot_id')
            hotspot = get_object_or_404(Hotspot, id=hotspot_id, source_scene__property__owner=request.user)
            hotspot.delete()
            messages.success(request, 'Hotspot deleted successfully.')
            return redirect('manage_scene_hotspots', scene_id=scene.id)

        # This is an add request
        form = HotspotForm(request.POST, property=scene.property)
        if form.is_valid():
            hotspot = form.save(commit=False)
            hotspot.source_scene = scene
            hotspot.save()
            messages.success(request, 'New hotspot added successfully.')
            return redirect('manage_scene_hotspots', scene_id=scene.id)
    else:
        form = HotspotForm(property=scene.property)

    context = {
        'scene': scene,
        'hotspots': hotspots,
        'form': form
    }
    return render(request, 'manage_hotspots.html', context)