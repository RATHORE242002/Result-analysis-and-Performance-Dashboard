from django.urls import path
from . import views

urlpatterns = [
    path('', views.user_login, name='login'),
    path('login/', views.user_login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.user_logout, name='logout'),
    path('upload/', views.upload_file, name='upload'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('view-data/', views.view_uploaded_data, name='view_data'),
    path('student-home/', views.student_home, name='student_home'),
    path('delete-file/<int:id>/', views.delete_file, name='delete_file'),
    path('student-result/', views.student_result, name='student_result'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('hod-dashboard/', views.hod_dashboard, name='hod_dashboard'),
    path('faculty-dashboard/', views.faculty_dashboard, name='faculty_dashboard'),
]
