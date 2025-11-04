from django.contrib.gis import admin
from .models import (Profile, Property, MaintenanceRequest, Invoice, 
                     Document, Conversation, Message, PointOfInterest, VendorProfile, Application, Scene, Hotspot)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'is_verified')
    list_editable = ('is_verified',)

@admin.register(Property)
class PropertyAdmin(admin.GISModelAdmin):
    list_display = ("name", "category", "address", "owner")
    list_filter = ('owner', 'category')

@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(admin.ModelAdmin):
    list_display = ('property', 'tenant', 'status', 'submitted_at')
    list_filter = ('status',)
    
@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'property', 'amount', 'due_date', 'status')

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'description', 'uploaded_at')

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('property', 'tenant', 'owner', 'created_at')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'sender', 'sent_at')

@admin.register(PointOfInterest)
class PointOfInterestAdmin(admin.GISModelAdmin):
    list_display = ('name', 'poi_type')
    list_filter = ('poi_type',)

@admin.register(VendorProfile)
class VendorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company_name', 'service_type', 'is_approved')
    list_editable = ('is_approved',)

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('property', 'applicant', 'status', 'applied_at')
    list_filter = ('status',)

class HotspotInline(admin.TabularInline):
    model = Hotspot
    fk_name = 'source_scene'
    extra = 1 # Start with one empty "Add Hotspot" slot
    # This makes it easier to select the target scene
    autocomplete_fields = ['target_scene']

@admin.register(Scene)
class SceneAdmin(admin.ModelAdmin):
    list_display = ('scene_name', 'property', 'is_first_scene')
    list_filter = ('property',)
    inlines = [HotspotInline]
    search_fields = ('scene_name', 'property__name') # Make scenes searchable

@admin.register(Hotspot)
class HotspotAdmin(admin.ModelAdmin):
    list_display = ('source_scene', 'target_scene', 'text')
    # This is crucial for the inline search to work
    search_fields = ('source_scene__scene_name', 'target_scene__scene_name')