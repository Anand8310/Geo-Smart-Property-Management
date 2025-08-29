from django.contrib.gis.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    ROLE_CHOICES = (('owner', 'Property Owner'), ('tenant', 'Tenant'),)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='tenant')
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
    PROPERTY_TYPE_CHOICES = [('house', 'House'), ('apartment', 'Apartment'), ('site', 'Site / Plot'), ('farmland', 'Farm Land'), ('commercial', 'Commercial Space'),]
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='properties')
    name = models.CharField(max_length=255)
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE_CHOICES, default='house')
    address = models.TextField()
    description = models.TextField(blank=True, null=True)
    location = models.PointField()
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.name

class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='property_images/')
    def __str__(self): return f"Image for {self.property.name}"

class MaintenanceRequest(models.Model):
    STATUS_CHOICES = [('Submitted', 'Submitted'), ('In Progress', 'In Progress'), ('Completed', 'Completed'),]
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    tenant = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Submitted')
    submitted_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.property.name} - {self.description[:30]}"

# ... (You can add Invoice, Document, Conversation, and Message models here later if you wish)
