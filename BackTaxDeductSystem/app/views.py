from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView
from rest_framework import permissions
from django.views import View
import json
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from .models import member_profile,User,stair_step
import jwt
from datetime import date,datetime

# Create your views here.
@method_decorator(csrf_exempt, name='dispatch')
class cal_tax(View):
    def cal_tax_stair(self,money):
        s_s = stair_step.objects.all()
        if len(s_s) == 0:
            stair_list = [150000,300000,500000,750000,1000000,2000000,5000000]
            rate = [5,5,10,15,20,25,30,35]
        else:
            stair_list = []
            rate = []
            for s in range(0,len(s_s)):
                stair_list.append(s.max_money)
                rate.append(s.rate)

        max_money = []
        dis_money = []
        current_stair = 0
        for i in range(len(stair_list)):
            if i == 0:
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

    def get(self, request, *args, **kwargs):
        return JsonResponse({'status':'403','msg':'Forbidden'})

    def post(self, request, *args, **kwargs):
        #token = request.META['HTTP_AUTHORIZATION']
        #decodedPayload = jwt.decode(token,None,None)

        content = json.loads(request.body)
        print(content)

        index_check = ["salary","other_income","marital","parent_num_dis","child_before_2561","child_after_2561","protege","rmf","ssf","life_insurance","pension_insurance","donation","edu_donation","home_loans","provident_fund","social_security","other"]
        check = True
        Field_not_complete = []
        for i in index_check:
            if i not in content:
                Field_not_complete.append(i)
                check = False
            else:
                if content[i] == '':
                    content[i] = 0

                
        if check == False:
            s = "Field "
            for i in Field_not_complete:
                s += i
                s += ", "
            s += " not complete"
            return JsonResponse({'status':'400','msg': s})
        else :
            money = int(content["salary"]) * 12
            money +=  int(content["other_income"])
            original_money = money
            if money/2 >= 100000 :
                money -= 100000
            else :
                money -= money/2
            money_personal = original_money - money
            money -= 60000

            if int(content["marital"]) == 3 :
                money -= 60000

            if int(content["parent_num_dis"]) > 0 :
                money -= 30000 * int(content["parent_num_dis"])

            child_before_2561 = int(content["child_before_2561"])
            child_after_2561 = int(content["child_after_2561"])
            protege = int(content["protege"])

            if protege == 0 or (child_before_2561+child_after_2561 >= 3):
                if child_before_2561 + child_after_2561 >= 1:
                    money -= 30000
                    if child_before_2561 > 0 :
                        child_before_2561 -= 1
                    else :
                        child_after_2561 -= 1
                    money -= 30000*child_before_2561
                    money -= 60000*child_after_2561

            else :
                if child_before_2561 + child_after_2561 == 1 :
                    money -= (30000 + 30000*protege)
                elif child_before_2561 > 1 :
                    money -= (30000*child_before_2561 + 30000*protege)
                elif child_after_2561 > 1 :
                    money -= (30000 + 60000*(child_after_2561-1) + 30000*protege)
            
            if int(content["rmf"]) > 0 :
                if int(content["rmf"]) >= 500000 :
                    money -= 500000
                elif int(content["rmf"]) >= original_money*0.3 :
                    money -=  original_money*0.3
                else :
                    money -= int(content["rmf"])
            
            if int(content["ssf"]) > 0 :
                if int(content["ssf"]) >= 200000 :
                    money -= 200000
                else :
                    money -= int(content["ssf"])

            if int(content["life_insurance"]) > 0 :
                if int(content["life_insurance"]) >= 100000 :
                    money -= 100000
                else :
                    money -= int(content["life_insurance"])
            
                if int(content["pension_insurance"]) > 0 :
                    if int(content["pension_insurance"]) >= 200000 :
                        money -= 200000
                    elif int(content["pension_insurance"]) >= original_money*0.15 :
                        money -=  original_money*0.15
                    else :
                        money -= int(content["pension_insurance"])
            
            if int(content["pension_insurance"]) > 0 and int(content["life_insurance"]) == 0:
                if int(content["pension_insurance"]) >= 300000 :
                    money -= 300000
                elif int(content["pension_insurance"]) >= original_money*0.15 :
                    money -=  original_money*0.15
                else :
                    money -= int(content["pension_insurance"])

            if int(content["home_loans"]) > 0 :
                if int(content["home_loans"]) >= 100000 :
                    money -= 100000
                else :
                    money -= int(content["home_loans"])
            
            if int(content["provident_fund"]) > 0:
                if int(content["provident_fund"]) >= 500000 :
                    money -= 500000
                elif int(content["provident_fund"]) >= (int(content["salary"])*12)*0.15 :
                    money -= (int(content["salary"])*12)*0.15
                else :
                    money -= int(content["provident_fund"])

            if int(content["social_security"]) > 0 :
                if int(content["social_security"]) >= 9000 :
                    money -= 9000
                else :
                    money -= int(content["social_security"])

            if int(content["other"]) > 0 :
                money -= int(content["other"])

            if int(content["donation"]) > 0 :
                if int(content["donation"]) >= money*0.1:
                    money -= money*0.1
                else:
                    money -= int(content["donation"])

            if int(content["edu_donation"]) > 0 :
                if int(content["edu_donation"])*2 >= money*0.1:
                    money -= money*0.1
                else:
                    money -= int(content["edu_donation"])*2

            money_discount = original_money - money + 60000 + money_personal

            if money < 0 :
                money = 0
            tax = self.cal_tax_stair(money)

            return JsonResponse({'status':'200','tax': tax ,'net_income' : money ,'personal_allowance' : money_personal,'allowance': money_discount})

@method_decorator(csrf_exempt, name='dispatch')
class user_register(View):
    def get(self, request, *args, **kwargs):
        return JsonResponse({'status':'403','msg':'Forbidden'})

    def post(self, request, *args, **kwargs):
        content = json.loads(request.body)
        if "username" in content and "password" in content :
            email_list = User.objects.all().values_list('email', flat=True)
            if content["username"] not in email_list:
                user = User.objects.create_member(email=content["username"],password=content["password"])
                user.save()
                return JsonResponse({'msg':'created user'})
            else:
                return JsonResponse({'msg':'email is already'})
        else:
            return JsonResponse({'msg':'field not complete'})


@method_decorator(csrf_exempt, name='dispatch')
class user_profile(View):
    permission_classes = (IsAuthenticated,)
    def get(self, request, *args, **kwargs):
        token = request.META['HTTP_AUTHORIZATION']
        decodedPayload = jwt.decode(token,None,None)
        print(decodedPayload)
        email = decodedPayload.get('email')
        u = User.objects.get(email = email)
        m_p = member_profile.objects.get(user = u)
        
        return JsonResponse({'email': u.email,
        'gender': m_p.gender,
        'birthdate' : m_p.birthdate,
        'salary' : m_p.salary,
        'other_income': m_p.other_income,
        'parent_num': m_p.parent_num,
        'child_num' : m_p.child_num,
        'infirm' : m_p.infirm,
        'risk' : m_p.risk,
        'facebook_id' : m_p.facebook_id
        })

    def post(self, request, *args, **kwargs):
        token = request.META['HTTP_AUTHORIZATION']
        decodedPayload = jwt.decode(token,None,None)
        print(decodedPayload)
        email = decodedPayload.get('email')
        u = User.objects.get(email = email)
        m_p = member_profile.objects.get(user = u)

        if "gender" in decodedPayload:
            m_p.gender = decodedPayload.get('gender')
        if "birthdate" in decodedPayload:
            m_p.birthdate = decodedPayload.get('birthdate')
        if "salary" in decodedPayload:
            m_p.salary = decodedPayload.get('salary')
        if "other_income" in decodedPayload:
            m_p.other_income = decodedPayload.get('other_income')
        if "parent_num" in decodedPayload:
            m_p.parent_num = decodedPayload.get('parent_num')
        if "child_num" in decodedPayload:
            m_p.child_num = decodedPayload.get('child_num')
        if "infirm" in decodedPayload:
            m_p.infirm = decodedPayload.get('infirm')
        if "risk" in decodedPayload:
            m_p.risk = decodedPayload.get('risk')
        if "facebook_id" in decodedPayload:
            m_p.facebook_id = decodedPayload.get('facebook_id')
        m_p.save()

        return JsonResponse({'email': u.email,
        'gender': m_p.gender,
        'birthdate' : m_p.birthdate,
        'salary' : m_p.salary,
        'other_income': m_p.other_income,
        'parent_num': m_p.parent_num,
        'child_num' : m_p.child_num,
        'infirm' : m_p.infirm,
        'risk' : m_p.risk,
        'facebook_id' : m_p.facebook_id
        })


@method_decorator(csrf_exempt, name='dispatch')
class facebook_login(View):
    def get(self, request, *args, **kwargs):
        return JsonResponse({'status':'403','msg':'Forbidden'})

    def post(self, request, *args, **kwargs):
        content = json.loads(request.body)
        print(content)

        if "facebook_id" in content and "email" in content and "uid" in content :
            
            if member_profile.objects.filter(facebook_id= content['facebook_id']).exists():
                m_p = member_profile.objects.get(facebook_id= content['facebook_id'])
                u = m_p.user
                #return profile
            else:
                # first time login with this app
                if User.objects.filter(email= content['email']).exists():
                    u = User.objects.get(email= content['email'])
                    if member_profile.objects.filter(user=u).exists():
                        m_p = member_profile.get(user=u)
                        m_p.facebook_id = content["facebook_id"]
                        m_p.save()
                        #return profile
                    else:
                        return JsonResponse({'status':'200','msg':"Don't use email(facebook email) of not member account"})
                else:
                    u = User.objects.create_member(email=content["username"],password=content["uid"])
                    u.save()

                    m_p = member_profile()
                    m_p.user = u
                    if "gender" in content:
                        m_p.gender = content["gender"]
                    if "birthdate" in content:
                        birthday = datetime.strptime(content["birthdate"],'%d/%m/%y').date()
                        m_p.birthdate = birthday
                    m_p.facebook_id = content["facebook_id"]
                    m_p.save()
                    #return profile

                return JsonResponse({'email': u.email,
                    'gender': m_p.gender,
                    'birthdate' : m_p.birthdate,
                    'salary' : m_p.salary,
                    'other_income': m_p.other_income,
                    'parent_num': m_p.parent_num,
                    'child_num' : m_p.child_num,
                    'infirm' : m_p.infirm,
                    'risk' : m_p.risk,
                    'facebook_id' : m_p.facebook_id
                    })
                 
        else:
            return JsonResponse({'status':'404','msg':'Error Wrong Format'})
