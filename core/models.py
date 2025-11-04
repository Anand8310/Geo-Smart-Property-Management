from django.contrib.gis.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class Profile(models.Model):
    ROLE_CHOICES = (('owner', 'Property Owner'), ('tenant', 'Tenant'),('vendor', 'Vendor'),)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='tenant')
    shortlisted_properties = models.ManyToManyField('Property', blank=True)
    liked_properties = models.ManyToManyField('Property', blank=True, related_name='liked_by')
    disliked_properties = models.ManyToManyField('Property', blank=True, related_name='disliked_by')
    is_verified = models.BooleanField(default=False)
    def __str__(self): return f"{self.user.username} - {self.get_role_display()}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created: Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        Profile.objects.create(user=instance)

class Property(models.Model):
    CATEGORY_CHOICES = [
        ('sale_residential', 'For Sale: Houses & Apartments'),
        ('rent_residential', 'For Rent: Houses & Apartments'),
        ('land_plot', 'Lands & Plots'),
        ('rent_commercial', 'For Rent: Shops & Offices'),
        ('sale_commercial', 'For Sale: Shops & Offices'),
        ('pg_guest_house', 'PG & Guest Houses'),
    ]
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('sold', 'Sold'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='properties')
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='available')
    address = models.TextField()
    description = models.TextField(blank=True, null=True)
    image1 = models.ImageField(upload_to='property_images/', blank=True, null=True)
    image2 = models.ImageField(upload_to='property_images/', blank=True, null=True)
    image3 = models.ImageField(upload_to='property_images/', blank=True, null=True)
    likes = models.PositiveIntegerField(default=0)
    dislikes = models.PositiveIntegerField(default=0)
    location = models.PointField()
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.name

class MaintenanceRequest(models.Model):
    STATUS_CHOICES = [('Submitted', 'Submitted'), ('Assigned', 'Assigned'), ('In Progress', 'In Progress'), ('Pending Approval', 'Work Complete (Pending Approval)'), ('Completed', 'Completed'),]
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    tenant = models.ForeignKey(User, on_delete=models.CASCADE)
    assigned_vendor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_jobs')
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Submitted')
    submitted_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.property.name} - {self.description[:30]}"

class Invoice(models.Model):
    STATUS_CHOICES = [('Unpaid', 'Unpaid'), ('Paid', 'Paid'),]
    tenant = models.ForeignKey(User, on_delete=models.CASCADE)
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Unpaid')
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"Invoice for {self.tenant.username} - {self.property.name}"

class Document(models.Model):
    tenant = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.tenant.username} - {self.description}"

class Conversation(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='conversations')
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations_as_tenant')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations_as_owner')
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"Conversation about {self.property.name} between {self.owner.username} and {self.tenant.username}"

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"Message from {self.sender.username} at {self.sent_at:%Y-%m-%d %H:%M}"

class PointOfInterest(models.Model):
    POI_TYPE_CHOICES = [('hospital', 'Hospital'), ('school', 'School'), ('metro', 'Metro Station'),]
    name = models.CharField(max_length=255)
    poi_type = models.CharField(max_length=20, choices=POI_TYPE_CHOICES)
    location = models.PointField()
    def __str__(self): return f"{self.name} ({self.get_poi_type_display()})"

class ForSaleResidentialDetails(models.Model):
    property = models.OneToOneField(Property, on_delete=models.CASCADE, related_name='for_sale_residential_details')
    price = models.DecimalField(max_digits=12, decimal_places=2, help_text="Total price in Rupees")
    def __str__(self): return f"Details for {self.property.name}"

class ForRentResidentialDetails(models.Model):
    FURNISHING_CHOICES = [('furnished', 'Furnished'), ('semi-furnished', 'Semi-Furnished'), ('unfurnished', 'Unfurnished'),]
    property = models.OneToOneField(Property, on_delete=models.CASCADE, related_name='for_rent_residential_details')
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2)
    furnishing_status = models.CharField(max_length=20, choices=FURNISHING_CHOICES, default='unfurnished')
    def __str__(self): return f"Details for {self.property.name}"

class LandPlotDetails(models.Model):
    property = models.OneToOneField(Property, on_delete=models.CASCADE, related_name='land_plot_details')
    plot_area = models.CharField(max_length=50, help_text="e.g., 2400 sqft or 1.5 acres")
    is_gated_community = models.BooleanField(default=False, verbose_name="Is it a Gated Community?")
    utilities_available = models.BooleanField(default=True, verbose_name="Are water and electricity available?")
    price = models.DecimalField(max_digits=12, decimal_places=2, help_text="Total price in Rupees")
    def __str__(self): return f"Details for {self.property.name}"

class ForRentCommercialDetails(models.Model):
    property = models.OneToOneField(Property, on_delete=models.CASCADE, related_name='for_rent_commercial_details')
    square_feet = models.PositiveIntegerField()
    washrooms = models.PositiveIntegerField()
    parking_available = models.BooleanField(default=True, verbose_name="Is parking available?")
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2, help_text="Rent per month in Rupees")
    def __str__(self): return f"Details for {self.property.name}"

class ForSaleCommercialDetails(models.Model):
    property = models.OneToOneField(Property, on_delete=models.CASCADE, related_name='for_sale_commercial_details')
    price = models.DecimalField(max_digits=12, decimal_places=2, help_text="Total price in Rupees")
    square_feet = models.PositiveIntegerField()
    year_built = models.PositiveIntegerField(blank=True, null=True)
    total_floors = models.PositiveIntegerField(default=1)
    def __str__(self): return f"Details for {self.property.name}"

class PGGuestHouseDetails(models.Model):
    OCCUPANCY_CHOICES = [('boys', 'Boys Only'), ('girls', 'Girls Only'), ('co-living', 'Co-Living (Unisex)'),]
    property = models.OneToOneField(Property, on_delete=models.CASCADE, related_name='pg_guest_house_details')
    price_per_month = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price per bed, per month in Rupees")
    food_included = models.BooleanField(default=False, verbose_name="Is food included in the price?")
    beds_per_room = models.PositiveIntegerField(default=1)
    occupancy_type = models.CharField(max_length=10, choices=OCCUPANCY_CHOICES, default='co-living')
    def __str__(self): return f"Details for {self.property.name}"

class PropertyView(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='views')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='property_views')
    viewed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} viewed {self.property.name}"
    
class Tenancy(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='tenancies')
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tenancies')
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Tenancy for {self.property.name} by {self.tenant.username}"
class VendorProfile(models.Model):
    SERVICE_CHOICES = [
        ('plumbing', 'Plumbing'),
        ('electrical', 'Electrical'),
        ('cleaning', 'Cleaning'),
        ('painting', 'Painting'),
        ('carpentry', 'Carpentry'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vendor_profile')
    service_type = models.CharField(max_length=20, choices=SERVICE_CHOICES)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    service_area = models.CharField(max_length=255, help_text="e.g., Koramangala, Indiranagar")
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"Vendor Profile for {self.user.username}"
    
class Application(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)
    # We can add fields for application documents later if needed

    def __str__(self):
        return f"Application from {self.applicant.username} for {self.property.name}"
    
class Expense(models.Model):
    EXPENSE_CATEGORY_CHOICES = [
        ('maintenance', 'Maintenance & Repairs'),
        ('tax', 'Property Tax'),
        ('insurance', 'Insurance'),
        ('utilities', 'Utilities'),
        ('other', 'Other'),
    ]

    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='expenses')
    category = models.CharField(max_length=20, choices=EXPENSE_CATEGORY_CHOICES)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_category_display()} for {self.property.name}"
    
class Review(models.Model):
    RATING_CHOICES = [
        (1, '1 - Terrible'),
        (2, '2 - Poor'),
        (3, '3 - Average'),
        (4, '4 - Good'),
        (5, '5 - Excellent'),
    ]

    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_given')
    comment = models.TextField()
    rating = models.IntegerField(choices=RATING_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    # These three fields create the generic link to any other model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    reviewed_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return f"Review by {self.reviewer.username} for {self.reviewed_object}"
    
class ViewingAppointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]

    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='viewing_appointments')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='viewing_appointments')
    requested_datetime = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Viewing request for {self.property.name} by {self.applicant.username}"
    
class Scene(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='scenes')
    scene_name = models.CharField(max_length=100, help_text="e.g., 'Living Room', 'Kitchen'")
    panorama_image = models.ImageField(upload_to='panorama_images/')
    is_first_scene = models.BooleanField(default=False, help_text="Mark one scene as the starting point for the tour.")

    def __str__(self):
        return f"{self.property.name} - {self.scene_name}"

class Hotspot(models.Model):
    source_scene = models.ForeignKey(Scene, on_delete=models.CASCADE, related_name='hotspots')
    target_scene = models.ForeignKey(Scene, on_delete=models.CASCADE, related_name='linked_to_scene')

    # Coordinates for the hotspot
    pitch = models.FloatField(help_text="Vertical position (up/down). Click on the panorama to find this.")
    yaw = models.FloatField(help_text="Horizontal position (left/right). Click on the panorama to find this.")
    text = models.CharField(max_length=100, help_text="Text to display when hovering over the hotspot (e.g., 'Go to Kitchen')")

    def __str__(self):
        return f"Link from {self.source_scene.scene_name} to {self.target_scene.scene_name}"