from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import (
    MapView, register_view, login_view, logout_view, submit_request_view,
    view_requests_view, view_invoices_view, view_documents_view, owner_dashboard_view,
    my_properties_view, add_property_view, edit_property_view, delete_property_view,
    property_detail_view, view_inquiries_view, conversation_detail_view, tenant_conversations_view
)

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
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
