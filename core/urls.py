from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('instructor/dashboard/', views.instructor_dashboard, name='instructor_dashboard'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('instructor/settings/', views.instructor_settings, name='instructor_settings'),
    path('instructor/sections/', views.instructor_sections, name='instructor_sections'),
    
    # === ADD THESE TWO NEW LINES ===
    path('instructor/sections/<int:section_id>/', views.section_detail, name='section_detail'),
    path('instructor/sections/<int:section_id>/sync/', views.sync_students_csv, name='sync_students_csv'),
    
    # === ADD THESE TWO NEW LINES ===
    path('instructor/assessments/', views.instructor_assessments, name='instructor_assessments'),
    path('instructor/assessments/toggle/<int:assessment_id>/', views.toggle_assessment_status, name='toggle_assessment_status'),

path('instructor/assessments/toggle/<int:assessment_id>/', views.toggle_assessment_status, name='toggle_assessment_status'),
    path('instructor/assessments/print/<int:assessment_id>/', views.print_assessment, name='print_assessment'),
    
    # === ADD THIS NEW LINE FOR GRADING ===
    path('instructor/assessments/<int:assessment_id>/grade/', views.grade_assessment, name='grade_assessment'),


path('instructor/assessments/<int:assessment_id>/build/', views.build_assessment, name='build_assessment'),
    path('logout/', views.logout_user, name='logout'),
]