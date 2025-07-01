# baseapp/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.home, name='home'),
    path('request/', views.request_submission, name='request_submission'),
    path('request/receipt/', views.request_receipt_view, name='request_receipt'),
    path('request/report/', views.request_report_view, name='request_report'),
    path('requests/review/', views.review_requests_view, name='review_requests'),
    path('survey/', views.survey_form_view, name='survey_form'),
    path('survey/receipt/', views.survey_receipt_view, name='survey_receipt'),
    path('report/', views.consolidated_report_view, name='consolidated_report'),
]