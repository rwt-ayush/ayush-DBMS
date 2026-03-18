from django.contrib import admin
from .models import Student, PlacementSection, Company, Job, Application

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'name', 'roll_no', 'email')

@admin.register(PlacementSection)
class PlacementSectionAdmin(admin.ModelAdmin):
    list_display = ('section_id', 'section_name', 'email')

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('company_id', 'name', 'website_link')

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('job_id', 'position', 'company', 'section', 'post_date')

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('app_id', 'student', 'job', 'status', 'applied_at')
