from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListAPIView
from rest_framework import permissions
from django.views import View
import json
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from .models import member_profile,User

# Create your views here.
#รอปรับแก้เป็นดึงจาก DB
def cal_tax_stair(money):
    money = money - 160000
    stair_list = [150000,300000,500000,750000,1000000,2000000,5000000]
    rate = [5,5,10,15,20,25,30,35]
    max_money = []
    dis_money = []
    current_stair = 0
    for i in range(len(stair_list)):
        if i==0:
            max_money.append(stair_list[0])
            dis_money.append(0)
        else:
            max_money.append(stair_list[i] - stair_list[i-1])
            dis_money.append( max_money[i] * rate[i]/100 + dis_money[i-1])
    
        if money > stair_list[i]:
            current_stair += 1
    if current_stair == 0 :
        return 0
    else :
        money -= stair_list[current_stair-1]
        tax = rate[current_stair]/100 * money + dis_money[current_stair-1]
        return tax

@method_decorator(csrf_exempt, name='dispatch')
class user_register(View):
    def get(self, request, *args, **kwargs):
        return JsonResponse({'status':'403','msg':'Forbidden'})

    def post(self, request, *args, **kwargs):
        content = json.loads(request.body)
        print(content)
        if "username" in content and "password" in content :
            email_list = User.objects.all().values_list('email', flat=True)
            if content["username"] not in email_list:
                user = User.objects.create_member(email=content["username"],password=content["password"])
                user.save()
                return JsonResponse({'status':'200','msg':'created user'})
            else:
                return JsonResponse({'status':'200','msg':'email is already'})
        else:
            return JsonResponse({'status':'200','msg':'field not complete'})


@method_decorator(csrf_exempt, name='dispatch')
class user_profile(View):
    def get(self, request, *args, **kwargs):
        username = request.user
        print(username)
        print(request)
        return JsonResponse({'status':'403','msg':'get'})

    def post(self, request, *args, **kwargs):
        username = request.user
        print(username)
        print(request)
        return JsonResponse({'status':'403','msg':'post'})
