from django.urls import path
from . import views

app_name = 'placement'

urlpatterns = [
    path('', views.home, name='home'),
    path('student/register/', views.student_register, name='student_register'),
    path('student/login/', views.student_login, name='student_login'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('company/register/', views.company_register, name='company_register'),
    path('company/login/', views.company_login, name='company_login'),
    path('company/dashboard/', views.company_dashboard, name='company_dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('students/', views.student_list, name='student_list'),
    path('students/add/', views.student_create, name='student_create'),
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/add/', views.job_create, name='job_create'),
    path('applications/', views.application_list, name='application_list'),
    path('applications/apply/', views.application_create, name='application_create'),
    path('applications/apply/<int:job_id>/', views.application_create, name='application_create_job'),
    path('company/applications/<int:app_id>/<str:action>/', views.company_application_action, name='company_application_action'),
    path('companies/', views.companies, name='companies'),
    path('companies/<int:company_id>/', views.companies, name='company_detail'),
]
