# models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Define status choices for AssetRequest
STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ('duplicate', 'Duplicate'),
]

# User Profile Model
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True)

    def __str__(self):
        return self.user.username


# Location Model
class Location(models.Model):
    name = models.CharField(max_length=100, unique=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    faxcode = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.name


# Department Model
class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='departments')

    def __str__(self):
        return f"{self.name} ({self.code}) - {self.location.name}"


# Category Model
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


# SubCategory Model
class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ('category', 'name')

    def __str__(self):
        return f"{self.category.name} - {self.name}"


# System Model (Represents a type of system model available at a location and category)
class SystemModel(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE, null=True, blank=True)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    # Removed department from SystemModel

    class Meta:
        unique_together = ('name', 'category', 'location')

    def __str__(self):
        return 
        "{self.name} ({self.category.name}) at {self.location.name}"


# Survey Info Model (Captures the parameters of a survey session)
class SurveyInfo(models.Model):
    date = models.DateField(default=timezone.now)
    financial_year = models.CharField(max_length=9)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    # Department is now nullable for SurveyInfo as it captures overall survey params
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"Survey for {self.location.name} - {self.category.name} ({self.financial_year}) on {self.date}"


# Survey Entry Model (Individual headcount entry for a model in a department during a survey)
MANPOWER_CHOICES = [
    ('exe', 'Executive'),
    ('mr', 'MR'),
    ('dr', 'DR'),
]

class SurveyEntry(models.Model):
    survey_info = models.ForeignKey(SurveyInfo, on_delete=models.CASCADE, related_name='entries', null=True, blank=True)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    system_model = models.ForeignKey(SystemModel, on_delete=models.CASCADE)
    headcount = models.PositiveIntegerField(default=0)
    manpower_type = models.CharField(max_length=10, choices=MANPOWER_CHOICES, default='exe')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('survey_info', 'department', 'system_model')

    def __str__(self):
        return f"{self.department.name} - {self.system_model.name}: {self.headcount} (Survey: {self.survey_info.id if self.survey_info else 'N/A'})"


# Asset Request Model
class AssetRequest(models.Model):
    ITEM_TYPE_CHOICES = [
        ('capital', 'Capital'),
        ('revenue', 'Revenue'),
    ]

    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    financial_year = models.CharField(max_length=9)
    asset_type = models.ForeignKey(Category, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2)
    item_type = models.CharField(max_length=10, choices=ITEM_TYPE_CHOICES)
    date = models.DateField(default=timezone.now)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    remarks = models.TextField(blank=True, null=True)

    indent_file = models.FileField(upload_to='uploads/', blank=True, null=True)
    annexure_x = models.FileField(upload_to='uploads/', blank=True, null=True)
    annexure_y = models.FileField(upload_to='uploads/', blank=True, null=True)
    gem_file = models.FileField(upload_to='uploads/', blank=True, null=True)

    def __str__(self):
        return f"Request #{self.id} - {self.location.name} - {self.department.name} - Status: {self.get_status_display()}"