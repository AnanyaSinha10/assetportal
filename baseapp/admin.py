# baseapp/admin.py
from django.contrib import admin
from .models import SystemModel, SurveyInfo, SurveyEntry, Location, Department, Category, AssetRequest, SubCategory, UserProfile


# Register your models here.

# Admin for UserProfile
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio', 'profile_pic')
    search_fields = ('user__username',)

# Admin for Location
@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'state', 'email')
    search_fields = ('name', 'city')

# Admin for Department
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'location')
    list_filter = ('location',)
    search_fields = ('name', 'code')

# Admin for Category
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

# Admin for SubCategory
@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)
    search_fields = ('name', 'category__name')

# Admin for SystemModel
@admin.register(SystemModel)
class SystemModelAdmin(admin.ModelAdmin):
    # CORRECTED: Removed 'department' from list_display and list_filter
    list_display = ('name', 'category', 'subcategory', 'location')
    list_filter = ('category', 'location')
    search_fields = ('name',)
    # Add fields for easier creation/editing if needed
    fields = ('name', 'category', 'subcategory', 'location')






# Admin for AssetRequest
@admin.register(AssetRequest)
class AssetRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'location', 'department', 'financial_year', 'asset_type', 'estimated_cost', 'item_type', 'date', 'status')
    list_filter = ('location', 'department', 'financial_year', 'asset_type', 'item_type', 'status', 'date')
    search_fields = ('description', 'location__name', 'department__name', 'asset_type__name')
    date_hierarchy = 'date'
    list_editable = ('status',) # Allows direct editing of status in list view
    raw_id_fields = ('location', 'department', 'asset_type') # For large numbers of related objects
    fieldsets = (
        (None, {
            'fields': (('location', 'department'), 'financial_year', 'asset_type', 'description', ('estimated_cost', 'item_type'), 'date')
        }),
        ('Approval Information', {
            'fields': ('status', 'remarks'),
            'classes': ('collapse',), # Makes this section collapsible
        }),
        ('Attachments', {
            'fields': ('indent_file', 'annexure_x', 'annexure_y', 'gem_file'),
            'classes': ('collapse',),
        }),
    )
admin.site.register(SurveyInfo)
admin.site.register(SurveyEntry)
