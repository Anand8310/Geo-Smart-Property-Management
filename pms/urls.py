# pms/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.views.generic import TemplateView
from django.conf.urls.static import static
from django.views.generic import TemplateView
from core.views import (
    MapView, register_view, login_view, logout_view, submit_request_view,
    view_requests_view, view_invoices_view, view_documents_view, owner_dashboard_view,
    my_properties_view, add_property_view, edit_property_view, delete_property_view,
    property_detail_view, view_inquiries_view, conversation_detail_view, tenant_conversations_view,
    toggle_shortlist_view, view_shortlist_view, property_vote_view, property_analytics_api_view, 
    manage_tenants_view, add_tenancy_view, vendor_dashboard_view, job_board_view, my_tenancy_view,
    job_detail_owner_view, owner_requests_view, vendor_assigned_jobs_view, vendor_job_detail_view, 
    tenant_confirm_completion_view, apply_for_tenancy_view, view_applications_view, manage_application_view, 
    cancel_tenancy_view, manage_expenses_view, add_review_view, add_vendor_review_view, 
    request_viewing_view, owner_appointments_view, manage_appointment_view, 
    manage_tour_view, manage_scene_hotspots_view,


)
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    path('', MapView.as_view(), name='home'),
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('submit-request/', submit_request_view, name='submit_request'),
    path('my-requests/', view_requests_view, name='view_requests'),
    path('my-invoices/', view_invoices_view, name='view_invoices'),
    path('my-documents/', view_documents_view, name='view_documents'),
    path('dashboard/', owner_dashboard_view, name='owner_dashboard'),
    path('property/<int:property_id>/', property_detail_view, name='property_detail'),
    path('my-properties/', my_properties_view, name='my_properties'),
    path('add-property/', add_property_view, name='add_property'),
    path('edit-property/<int:property_id>/', edit_property_view, name='edit_property'),
    path('delete-property/<int:property_id>/', delete_property_view, name='delete_property'),
    path('my-conversations/', view_inquiries_view, name='view_conversations'),
    path('my-conversations/tenant/', tenant_conversations_view, name='tenant_conversations'),
    path('conversation/<int:conversation_id>/', conversation_detail_view, name='conversation_detail'),
    path('shortlist/toggle/<int:property_id>/', toggle_shortlist_view, name='toggle_shortlist'),
    path('my-shortlist/', view_shortlist_view, name='view_shortlist'),
    path('property/<int:property_id>/vote/<str:vote_type>/', property_vote_view, name='property_vote'),
    path('insights/<int:property_id>/', TemplateView.as_view(template_name='property_insights.html'), name='property_insights'),
    path('api/insights/<int:property_id>/', property_analytics_api_view, name='property_analytics_api'),
    path('manage-tenants/<int:property_id>/', manage_tenants_view, name='manage_tenants'),
    path('add-tenancy/<int:property_id>/', add_tenancy_view, name='add_tenancy'),
    path('vendor/jobs/', job_board_view, name='job_board'),
    path('vendor/dashboard/', vendor_dashboard_view, name='vendor_dashboard'),
    path('my-tenancy/', my_tenancy_view, name='my_tenancy'),
    path('owner/job/<int:request_id>/', job_detail_owner_view, name='job_detail_owner'),
    path('owner/requests/', owner_requests_view, name='owner_requests'),
    path('vendor/my-jobs/', vendor_assigned_jobs_view, name='vendor_assigned_jobs'),
    path('vendor/job/<int:request_id>/', vendor_job_detail_view, name='vendor_job_detail'),
    path('tenant/confirm-completion/<int:request_id>/', tenant_confirm_completion_view, name='tenant_confirm_completion'),
    path('insights/', TemplateView.as_view(template_name='neighborhood_insights.html'), name='neighborhood_insights'),
    path('apply/<int:property_id>/', apply_for_tenancy_view, name='apply_for_tenancy'),
    path('owner/applications/', view_applications_view, name='view_applications'),
    path('owner/application/<int:application_id>/<str:action>/', manage_application_view, name='manage_application'),
    path('cancel-tenancy/<int:tenancy_id>/', cancel_tenancy_view, name='cancel_tenancy'),
    path('manage-expenses/<int:property_id>/', manage_expenses_view, name='manage_expenses'),
    path('add-review/<int:property_id>/', add_review_view, name='add_review'),
    path('add-vendor-review/<int:request_id>/', add_vendor_review_view, name='add_vendor_review'),
    path('request-viewing/<int:property_id>/', request_viewing_view, name='request_viewing'),
    path('owner/appointments/', owner_appointments_view, name='owner_appointments'),
    path('owner/appointment/<int:appointment_id>/<str:action>/', manage_appointment_view, name='manage_appointment'),
    path('about/', TemplateView.as_view(template_name="about.html"), name='about'),
    path('contact/', TemplateView.as_view(template_name="contact.html"), name='contact'),
    path('privacy-policy/', TemplateView.as_view(template_name="privacy_policy.html"), name='privacy_policy'),
    path('manage-tour/<int:property_id>/', manage_tour_view, name='manage_tour'),
    path('manage-hotspots/<int:scene_id>/', manage_scene_hotspots_view, name='manage_scene_hotspots'),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)