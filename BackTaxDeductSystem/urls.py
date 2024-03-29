"""BackTaxDeductSystem URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include,path
from rest_framework_jwt.views import obtain_jwt_token, refresh_jwt_token
from app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('auth/obtain_token/', obtain_jwt_token),
    path('auth/refresh_token/', refresh_jwt_token),
    path('register/',views.user_register.as_view()),
    path('profile/',views.user_profile.as_view()),
    path('tax/',views.cal_tax.as_view()),
    path('facebook_login/',views.facebook_login.as_view()),
    path('delete_account/',views.delete_user.as_view()),
    path('categories/',views.categories.as_view()),
    path('plan_types/',views.user_tax_predict.as_view()),
    path('collect_dataset/',views.collect_dataset.as_view())
]
