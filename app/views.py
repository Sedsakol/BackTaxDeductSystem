from django.shortcuts import render
from django.http import JsonResponse
from django.core import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView
from rest_framework import permissions
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from .models import member_profile,stair_step,facebook_categories,plan_types,dataset,MLConfiguration,predict_dataset,fund_list,fund_type,insurance_list,insurance_type
import jwt
from datetime import date,datetime
from django.http import HttpResponse
import json
import os
import sys
import requests
import joblib
import pandas as pd

User = get_user_model()
# Create your views here.
@method_decorator(csrf_exempt, name='dispatch')
class cal_tax(View):
    def cal_tax_stair(self,money):
        s_s = stair_step.objects.all().order_by('step')
        if len(s_s) == 0:
            stair_list = [150000,300000,500000,750000,1000000,2000000,5000000,None]
            rate = [5,5,10,15,20,25,30,35]
            for i in range(len(stair_list)):
                stair_step(step = i+1, max_money = stair_list[i], rate = rate[i]).save()

        stair_list = []
        rate = []
        for s in s_s:
            stair_list.append(s.max_money)
            rate.append(s.rate)

        max_money = []
        dis_money = []
        current_stair = 0
        for i in range(len(stair_list)-1):
            if i == 0:
                max_money.append(stair_list[0])
                dis_money.append(0)
            else:
                max_money.append(stair_list[i] - stair_list[i-1])
                dis_money.append( max_money[i] * rate[i]/100 + dis_money[i-1])
        
            if money > stair_list[i]:
                current_stair += 1
        if current_stair == 0 :
            return 0 , current_stair
        else :
            money -= stair_list[current_stair-1]
            tax = rate[current_stair]/100 * money + dis_money[current_stair-1]
            return tax , current_stair

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

            money_discount = original_money - (money + 60000 + money_personal)

            if money < 0 :
                money = 0
            tax , current_stair = self.cal_tax_stair(money)

            return JsonResponse({'status':'200','tax': tax ,'net_income' : money ,'personal_allowance' : money_personal,'allowance': money_discount , 'stair' : current_stair})

@method_decorator(csrf_exempt, name='dispatch')
class user_register(View):
    def get(self, request, *args, **kwargs):
        return JsonResponse({'status':'403','msg':'Forbidden'})

    def post(self, request, *args, **kwargs):
        content = json.loads(request.body)
        if "username" in content and "password" in content :
            if not User.objects.filter(email=content["username"]).exists():
                user = User.objects.create_member(email=content["username"],password=content["password"])
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

        risk = None
        if m_p.risk :
            risk = json.loads(m_p.risk)
        
        return JsonResponse({'email': u.email,
        'gender': m_p.gender,
        'birthdate' : m_p.birthdate,
        'salary' : m_p.salary,
        'other_income': m_p.other_income,
        'parent_num': m_p.parent_num,
        'child_num' : m_p.child_num,
        'marriage' : m_p.marriage,
        'infirm' : m_p.infirm,
        'risk' : risk,
        'facebook_id' : m_p.facebook_id
        })

    def post(self, request, *args, **kwargs):
        token = request.META['HTTP_AUTHORIZATION']
        decodedPayload = jwt.decode(token,None,None)
        print(decodedPayload)
        email = decodedPayload.get('email')
        content = json.loads(request.body)
        print(content)
        u = User.objects.get(email = email)
        m_p = member_profile.objects.get(user = u)
        
        if "gender" in content:
            m_p.gender = int(content.get('gender'))
        if "birthdate" in content:
            if content.get('birthdate') :
                m_p.birthdate = datetime.strptime(content.get('birthdate'), '%d/%m/%Y').date()
        if "salary" in content:
            m_p.salary = int(content.get('salary'))
        if "other_income" in content:
            m_p.other_income = int(content.get('other_income'))
        if "parent_num" in content:
            m_p.parent_num = int(content.get('parent_num'))
        if "child_num" in content:
            m_p.child_num = int(content.get('child_num'))
        if "infirm" in content:
            m_p.infirm = int(content.get('infirm'))
        if "marriage" in content:
            m_p.marriage = int(content.get('marriage'))
        if "risk" in content:
            m_p.risk = str(content.get('risk'))
        if "facebook_id" in content:
            if content.get('facebook_id'):
                m_p.facebook_id = content.get('facebook_id')
        m_p.save()

        u = User.objects.get(email = email)
        m_p = member_profile.objects.get(user = u)
        risk = None
        if m_p.risk:
            risk =  json.loads(m_p.risk)

        return JsonResponse({'email': u.email,
        'gender': m_p.gender,
        'birthdate' : m_p.birthdate,
        'salary' : m_p.salary,
        'other_income': m_p.other_income,
        'parent_num': m_p.parent_num,
        'child_num' : m_p.child_num,
        'marriage' : m_p.marriage,
        'infirm' : m_p.infirm,
        'risk' : risk ,
        'facebook_id' : m_p.facebook_id
        }) 


@method_decorator(csrf_exempt, name='dispatch')
class facebook_login(View):
    def get(self, request, *args, **kwargs):
        return JsonResponse({'status':'403','msg':'Forbidden'})

    def post(self, request, *args, **kwargs):
        content = json.loads(request.body)
        print(content)

        if "facebook_id" in content and "email" in content :
            if member_profile.objects.filter(facebook_id= content['facebook_id']).exists():
                m_p = member_profile.objects.get(facebook_id= content['facebook_id'])
                u = m_p.user
                #return msg use login auth
            else:
                # first time login with this app
                #update social account
                if User.objects.filter(email= content['email']).exists():
                    u = User.objects.get(email= content['email'])
                    if member_profile.objects.filter(user=u).exists():
                        m_p = member_profile.objects.get(user=u)
                        m_p.facebook_id = content["facebook_id"]
                        m_p.save()
                        #return msg use login auth
                    else:
                        return JsonResponse({'status':'403','msg':"Don't use email(facebook email) of not member account"})
                else:
                    u = User.objects.create_member(email=content["email"],password=content["facebook_id"])
                    u.save()

                    m_p = member_profile.objects.get(user=u)
                    if "gender" in content:
                        m_p.gender = int(content["gender"])
                    if "birthdate" in content:
                        if content["birthdate"] :
                            birthday = datetime.strptime(content["birthdate"], '%d/%m/%Y').date()
                            m_p.birthdate = birthday
                    m_p.facebook_id = content["facebook_id"]
                    m_p.save()
                    #return msg use login auth

            return JsonResponse({'status':'200','msg':"use login auth"})
        else:
            return JsonResponse({'status':'400','msg':'Error Wrong Format'})

@method_decorator(csrf_exempt, name='dispatch')
class delete_user(View):
    permission_classes = (IsAuthenticated,)
    def get(self, request, *args, **kwargs):
        return JsonResponse({'status':'403','msg':'Forbidden'})

    def post(self, request, *args, **kwargs):
        token = request.META['HTTP_AUTHORIZATION']
        decodedPayload = jwt.decode(token,None,None)
        print(decodedPayload)
        print(request.body)
        email = decodedPayload.get('email')
        content = json.loads(request.body)
        if "email" in content:
            if email == content.get('email'):

                #delete in db
                u = User.objects.get(email = email)
                u.delete()
                print('Successfully deleted user in DB')

                #debug for heroku
                sys.stdout.flush()

                return JsonResponse({'status':'200','msg':"delete user complete"})
        return JsonResponse({'status':'400','msg':'Error Wrong Format'})

@method_decorator(csrf_exempt, name='dispatch')
class categories(View):

    def diff_month(self,d1, d2):
        return (d1.year - d2.year) * 12 + d1.month - d2.month

    def create_facebook_categories(self,content_id = None, content_data = None):
        if content_data and content_id :
            
            prev_date = list(facebook_categories.objects.filter(facebook_id = content_id).order_by('-created'))
            if prev_date:
                if self.diff_month(datetime.now(), prev_date[0].created) < 1 :
                    return True 
            

            if "data" in content_data:
            
                categorie_all = {
                    "Businesses" : {
                        "level" : 0
                    },
                        "Advertising/Marketing" : {
                            "level" : 1,
                            "parent" : "Businesses"
                        },
                            "Advertising Agency" : {
                                "level" : 2,
                                "parent" : "Advertising/Marketing"
                            },
                            "Copywriting Service" : {
                                "level" : 2,
                                "parent" : "Advertising/Marketing"
                            },
                            "Internet Marketing Service" : {
                                "level" : 2,
                                "parent" : "Advertising/Marketing"
                            },
                            "Market Research Consultant" : {
                                "level" : 2,
                                "parent" : "Advertising/Marketing"
                            },
                            "Marketing Agency" : {
                                "level" : 2,
                                "parent" : "Advertising/Marketing"
                            },
                            "Media Agency" : {
                                "level" : 2,
                                "parent" : "Advertising/Marketing"
                            },
                            "Merchandising Service" : {
                                "level" : 2,
                                "parent" : "Advertising/Marketing"
                            },
                            "Public Relations Agency" : {
                                "level" : 2,
                                "parent" : "Advertising/Marketing"
                            },
                            "Social Media Agency" : {
                                "level" : 2,
                                "parent" : "Advertising/Marketing"
                            },
                            "Telemarketing Service" : {
                                "level" : 2,
                                "parent" : "Advertising/Marketing"
                            },
                        "Agriculture" : {
                            "level" : 1,
                            "parent" : "Businesses"
                        },
                            "Agricultural Cooperative" : {
                                "level" : 2,
                                "parent" : "Agriculture"
                            },
                            "Agricultural Service" : {
                                "level" : 2,
                                "parent" : "Agriculture"
                            },
                            "Farm" : {
                                "level" : 2,
                                "parent" : "Agriculture"
                            },
                                "Dairy Farm" : {
                                    "level" : 3,
                                    "parent" : "Farm"
                                },
                                "Fish Farm" : {
                                    "level" : 3,
                                    "parent" : "Farm"
                                },
                                "Livestock Farm" : {
                                    "level" : 3,
                                    "parent" : "Farm"
                                },
                                "Poultry Farm" : {
                                    "level" : 3,
                                    "parent" : "Farm"
                                },
                                "Urban Farm" : {
                                    "level" : 3,
                                    "parent" : "Farm"
                                },
                        "Arts & Entertainment" : {
                            "level" : 1,
                            "parent" : "Businesses"
                        },
                            "Adult Entertainment Club" : {
                                "level" : 2,
                                "parent" : "Arts & Entertainment"
                            },
                            "Amusement & Theme Park" : {
                                "level" : 2,
                                "parent" : "Arts & Entertainment"
                            },
                                "Water Park" : {
                                    "level" : 3,
                                    "parent" : "Amusement & Theme Park"
                                },
                            "Aquarium" : {
                                "level" : 2,
                                "parent" : "Arts & Entertainment"
                            },
                            "Arcade" : {
                                "level" : 2,
                                "parent" : "Arts & Entertainment"
                            },
                            "Art Gallery" : {
                                "level" : 2,
                                "parent" : "Arts & Entertainment"
                            },
                            "Betting Shop" : {
                                "level" : 2,
                                "parent" : "Arts & Entertainment"
                            },
                            "Bingo Hall" : {
                                "level" : 2,
                                "parent" : "Arts & Entertainment"
                            },
                            "Casino" : {
                                "level" : 2,
                                "parent" : "Arts & Entertainment"
                            },
                            "Circus" : {
                                "level" : 2,
                                "parent" : "Arts & Entertainment"
                            },
                            "Dance & Night Club" : {
                                "level" : 2,
                                "parent" : "Arts & Entertainment"
                            },
                            "Escape Game Room" : {
                                "level" : 2,
                                "parent" : "Arts & Entertainment"
                            },
                            "Haunted House" : {
                                "level" : 2,
                                "parent" : "Arts & Entertainment"
                            },
                            "Karaoke" : {
                                "level" : 2,
                                "parent" : "Arts & Entertainment"
                            },
                            "Movie Theater" : {
                                "level" : 2,
                                "parent" : "Arts & Entertainment"
                            },
                                "Drive-In Movie Theater" : {
                                    "level" : 3,
                                    "parent" : "Movie Theater"
                                },
                            "Museum" : {
                                "level" : 2,
                                "parent" : "Arts & Entertainment"
                            },
                                "Art Museum" : {
                                    "level" : 3,
                                    "parent" : "Museum"
                                },
                                    "Asian Art Museum" : {
                                        "level" : 4,
                                        "parent" : "Art Museum"
                                    },
                                    "Cartooning Museum" : {
                                        "level" : 4,
                                        "parent" : "Art Museum"
                                    },
                                    "Contemporary Art Museum" : {
                                        "level" : 4,
                                        "parent" : "Art Museum"
                                    },
                                    "Costume Museum" : {
                                        "level" : 4,
                                        "parent" : "Art Museum"
                                    },
                                    "Decorative Arts Museum" : {
                                        "level" : 4,
                                        "parent" : "Art Museum"
                                    },
                                    "Design Museum" : {
                                        "level" : 4,
                                        "parent" : "Art Museum"
                                    },
                                    "Modern Art Museum" : {
                                        "level" : 4,
                                        "parent" : "Art Museum"
                                    },
                                    "Photography Museum" : {
                                        "level" : 4,
                                        "parent" : "Art Museum"
                                    },
                                    "Textile Museum" : {
                                        "level" : 4,
                                        "parent" : "Art Museum"
                                    },
                                "Aviation Museum" : {
                                    "level" : 3,
                                    "parent" : "Museum"
                                },
                                "Children's Museum" : {
                                    "level" : 3,
                                    "parent" : "Museum"
                                },
                                "History Museum" : {
                                    "level" : 3,
                                    "parent" : "Museum"
                                },
                                    "Civilization Museum" : {
                                        "level" : 4,
                                        "parent" : "History Museum"
                                    },
                                    "Community Museum" : {
                                        "level" : 4,
                                        "parent" : "History Museum"
                                    },
                                "Science Museum" : {
                                    "level" : 3,
                                    "parent" : "Museum"
                                },                       
                                    "Computer Museum" : {
                                        "level" : 4,
                                        "parent" : "Science Museum"
                                    },
                                    "Observatory" : {
                                        "level" : 4,
                                        "parent" : "Science Museum"
                                    },
                                    "Planetarium" : {
                                        "level" : 4,
                                        "parent" : "Science Museum"
                                    },
                                "Sports Museum" : {
                                    "level" : 3,
                                    "parent" : "Museum"
                                },
                            "Performance & Event Venue" : {
                                "level" : 2,
                                "parent" : "Arts & Entertainment"
                            },
                                "Amphitheater" : {
                                    "level" : 3,
                                    "parent" : "Performance & Event Venue"
                                },
                                "Auditorium" : {
                                    "level" : 3,
                                    "parent" : "Performance & Event Venue"
                                },
                                "Comedy Club" : {
                                    "level" : 3,
                                    "parent" : "Performance & Event Venue"
                                },
                                "Jazz & Blues Club" : {
                                    "level" : 3,
                                    "parent" : "Performance & Event Venue"
                                },
                                "Live Music Venue" : {
                                    "level" : 3,
                                    "parent" : "Performance & Event Venue"
                                },
                                "Opera House" : {
                                    "level" : 3,
                                    "parent" : "Performance & Event Venue"
                                },
                                "Performance Art Theatre" : {
                                    "level" : 3,
                                    "parent" : "Performance & Event Venue"
                                },
                            "Pool & Billiard Hall" : {
                                "level" : 2,
                                "parent" : "Arts & Entertainment"
                            },
                            "Race Track" : {
                                "level" : 2,
                                "parent" : "Arts & Entertainment"
                            },
                            "Salsa Club" : {
                                "level" : 2,
                                "parent" : "Arts & Entertainment"
                            },
                            "Zoo" : {
                                "level" : 2,
                                "parent" : "Arts & Entertainment"
                            },
                                "Petting Zoo" : {
                                    "level" : 3,
                                    "parent" : "Zoo"
                                },
                                "Wildlife Sanctuary" : {
                                    "level" : 3,
                                    "parent" : "Zoo"
                                },
                        "Automotive, Aircraft & Boat" : {
                            "level" : 1,
                            "parent" : "Businesses"
                        },
                            "Automotive Dealership" : {
                                "level" : 2,
                                "parent" : "Automotive, Aircraft & Boat"
                            },
                                "ATV Dealership" : {
                                    "level" : 3,
                                    "parent" : "Automotive Dealership"
                                },
                                "Aircraft Dealership" : {
                                    "level" : 3,
                                    "parent" : "Automotive Dealership"
                                },
                                "Automotive Wholesaler" : {
                                    "level" : 3,
                                    "parent" : "Automotive Dealership"
                                },
                                "Boat Dealership" : {
                                    "level" : 3,
                                    "parent" : "Automotive Dealership"
                                },
                                "Car Dealership" : {
                                    "level" : 3,
                                    "parent" : "Automotive Dealership"
                                },
                                    "Can Receive Leads" : {
                                        "level" : 4,
                                        "parent" : "Car Dealership"
                                    },
                                    "Commercial Vehicle Dealership" : {
                                        "level" : 4,
                                        "parent" : "Car Dealership"
                                    },
                                    "Electric Vehicle Dealership" : {
                                        "level" : 4,
                                        "parent" : "Car Dealership"
                                    },
                                    "Performance Vehicle Dealership" : {
                                        "level" : 4,
                                        "parent" : "Car Dealership"
                                    },
                                "Commercial Truck Dealership" : {
                                    "level" : 3,
                                    "parent" : "Automotive Dealership"
                                },
                                "Golf Cart Dealership" : {
                                    "level" : 3,
                                    "parent" : "Automotive Dealership"
                                },
                                "Motorcycle Dealership" : {
                                    "level" : 3,
                                    "parent" : "Automotive Dealership"
                                },
                                "Recreational Vehicle Dealership" : {
                                    "level" : 3,
                                    "parent" : "Automotive Dealership"
                                },
                                "Trailer Dealership" : {
                                    "level" : 3,
                                    "parent" : "Automotive Dealership"
                                },
                            "Automotive Service" : {
                                "level" : 2,
                                "parent" : "Automotive, Aircraft & Boat"
                            },
                                "Auto Detailing Service" : {
                                    "level" : 3,
                                    "parent" : "Automotive Service"
                                },
                                "Automotive Body Shop" : {
                                    "level" : 3,
                                    "parent" : "Automotive Service"
                                },
                                "Automotive Consultant" : {
                                    "level" : 3,
                                    "parent" : "Automotive Service"
                                },
                                "Automotive Customization Shop" : {
                                    "level" : 3,
                                    "parent" : "Automotive Service"
                                },
                                "Automotive Glass Service" : {
                                    "level" : 3,
                                    "parent" : "Automotive Service"
                                },
                                "Automotive Leasing Service" : {
                                    "level" : 3,
                                    "parent" : "Automotive Service"
                                },
                                "Automotive Repair Shop" : {
                                    "level" : 3,
                                    "parent" : "Automotive Service"
                                },
                                "Automotive Restoration Service" : {
                                    "level" : 3,
                                    "parent" : "Automotive Service"
                                },
                                "Automotive Shipping Service" : {
                                    "level" : 3,
                                    "parent" : "Automotive Service"
                                },
                                "Automotive Storage Facility" : {
                                    "level" : 3,
                                    "parent" : "Automotive Service"
                                },
                                "Automotive Wheel Polishing Service" : {
                                    "level" : 3,
                                    "parent" : "Automotive Service"
                                },
                                "Automotive Window Tinting Service" : {
                                    "level" : 3,
                                    "parent" : "Automotive Service"
                                },
                                "Boat Service" : {
                                    "level" : 3,
                                    "parent" : "Automotive Service"
                                },
                                "Car Wash" : {
                                    "level" : 3,
                                    "parent" : "Automotive Service"
                                },
                                "Emergency Roadside Service" : {
                                    "level" : 3,
                                    "parent" : "Automotive Service"
                                },
                                "Gas Station" : {
                                    "level" : 3,
                                    "parent" : "Automotive Service"
                                },
                                "Marine Service Station" : {
                                    "level" : 3,
                                    "parent" : "Automotive Service"
                                },
                                "Motorcycle Repair Shop" : {
                                    "level" : 3,
                                    "parent" : "Automotive Service"
                                },
                                "Oil Lube & Filter Service" : {
                                    "level" : 3,
                                    "parent" : "Automotive Service"
                                },
                                "RV Repair Shop" : {
                                    "level" : 3,
                                    "parent" : "Automotive Service"
                                },
                                "Smog Emissions Check Station" : {
                                    "level" : 3,
                                    "parent" : "Automotive Service"
                                },
                                "Tire Dealer & Repair Shop" : {
                                    "level" : 3,
                                    "parent" : "Automotive Service"
                                },
                                "Towing Service" : {
                                    "level" : 3,
                                    "parent" : "Automotive Service"
                                },
                                "Truck Repair Shop" : {
                                    "level" : 3,
                                    "parent" : "Automotive Service"
                                },
                                "Wheel & Rim Repair Service" : {
                                    "level" : 3,
                                    "parent" : "Automotive Service"
                                },
                            "Automotive Store" : {
                                "level" : 2,
                                "parent" : "Automotive, Aircraft & Boat"
                            },
                                "Automotive Parts Store" : {
                                    "level" : 3,
                                    "parent" : "Automotive Store"
                                },
                                "Car Stereo Store" : {
                                    "level" : 3,
                                    "parent" : "Automotive Store"
                                },
                                "Marine Supply Store" : {
                                    "level" : 3,
                                    "parent" : "Automotive Store"
                                },
                                "Motorsports Store" : {
                                    "level" : 3,
                                    "parent" : "Automotive Store"
                                },
                            "Aviation Repair Station" : {
                                "level" : 2,
                                "parent" : "Automotive, Aircraft & Boat"
                            },
                            "Avionics Shop" : {
                                "level" : 2,
                                "parent" : "Automotive, Aircraft & Boat"
                            },
                            "Motor Vehicle Company" : {
                                "level" : 2,
                                "parent" : "Automotive, Aircraft & Boat"
                            },
                                "Automotive Manufacturer" : {
                                    "level" : 3,
                                    "parent" : "Motor Vehicle Company"
                                },
                                "Motorcycle Manufacturer" : {
                                    "level" : 3,
                                    "parent" : "Motor Vehicle Company"
                                },
                        "Beauty, Cosmetic & Personal Care" : {
                            "level" : 1,
                            "parent" : "Businesses"
                        },
                            "Barber Shop" : {
                                "level" : 2,
                                "parent" : "Beauty, Cosmetic & Personal Care"
                            },
                            "Beauty Salon" : {
                                "level" : 2,
                                "parent" : "Beauty, Cosmetic & Personal Care"
                            },
                                "Hair Salon" : {
                                    "level" : 3,
                                    "parent" : "Beauty Salon"
                                },
                                "Nail Salon" : {
                                    "level" : 3,
                                    "parent" : "Beauty Salon"
                                },
                                "Tanning Salon" : {
                                    "level" : 3,
                                    "parent" : "Beauty Salon"
                                },
                            "Beauty Supplier" : {
                                "level" : 2,
                                "parent" : "Beauty, Cosmetic & Personal Care"
                            },
                            "Hair Extensions Service" : {
                                "level" : 2,
                                "parent" : "Beauty, Cosmetic & Personal Care"
                            },
                            "Hair Removal Service" : {
                                "level" : 2,
                                "parent" : "Beauty, Cosmetic & Personal Care"
                            },
                                "Laser Hair Removal Service" : {
                                    "level" : 3,
                                    "parent" : "Hair Removal Service"
                                },
                                "Sugaring Service" : {
                                    "level" : 3,
                                    "parent" : "Hair Removal Service"
                                },
                                "Threading Service" : {
                                    "level" : 3,
                                    "parent" : "Hair Removal Service"
                                },
                                "Waxing Service" : {
                                    "level" : 3,
                                    "parent" : "Hair Removal Service"
                                },
                            "Hair Replacement Service" : {
                                "level" : 2,
                                "parent" : "Beauty, Cosmetic & Personal Care"
                            },
                            "Image Consultant" : {
                                "level" : 2,
                                "parent" : "Beauty, Cosmetic & Personal Care"
                            },
                            "Makeup Artist" : {
                                "level" : 2,
                                "parent" : "Beauty, Cosmetic & Personal Care"
                            },
                            "Skin Care Service" : {
                                "level" : 2,
                                "parent" : "Beauty, Cosmetic & Personal Care"
                            },
                            "Spa" : {
                                "level" : 2,
                                "parent" : "Beauty, Cosmetic & Personal Care"
                            },
                                "Aromatherapy Service" : {
                                    "level" : 3,
                                    "parent" : "Spa"
                                },
                                "Day Spa" : {
                                    "level" : 3,
                                    "parent" : "Spa"
                                },
                                "Health Spa" : {
                                    "level" : 3,
                                    "parent" : "Spa"
                                },
                                "Massage Service" : {
                                    "level" : 3,
                                    "parent" : "Spa"
                                },
                                "Onsen" : {
                                    "level" : 3,
                                    "parent" : "Spa"
                                },
                            "Tattoo & Piercing Shop" : {
                                "level" : 2,
                                "parent" : "Beauty, Cosmetic & Personal Care"
                            },
                        "Commercial & Industrial" : {
                            "level" : 1,
                            "parent" : "Businesses"
                        },
                            "Automation Service" : {
                                "level" : 2,
                                "parent" : "Commercial & Industrial"
                            },
                            "Commercial & Industrial Equipment Supplier" : {
                                "level" : 2,
                                "parent" : "Commercial & Industrial"
                            },
                            "Environmental Service" : {
                                "level" : 2,
                                "parent" : "Commercial & Industrial"
                            },
                                "Environmental Consultant" : {
                                    "level" : 3,
                                    "parent" : "Environmental Service"
                                },
                                "Geologic Service" : {
                                    "level" : 3,
                                    "parent" : "Environmental Service"
                                },
                                "Occupational Safety and Health Service" : {
                                    "level" : 3,
                                    "parent" : "Environmental Service"
                                },
                                "Recycling Center" : {
                                    "level" : 3,
                                    "parent" : "Environmental Service"
                                },
                            "Forestry & Logging" : {
                                "level" : 2,
                                "parent" : "Commercial & Industrial"
                            },
                                "Forestry Service" : {
                                    "level" : 3,
                                    "parent" : "Forestry & Logging"
                                },
                                "Logging Contractor" : {
                                    "level" : 3,
                                    "parent" : "Forestry & Logging"
                                },
                            "Hotel Services Company" : {
                                "level" : 2,
                                "parent" : "Commercial & Industrial"
                            },
                            "Industrial Company" : {
                                "level" : 2,
                                "parent" : "Commercial & Industrial"
                            },
                            "Inventory Control Service" : {
                                "level" : 2,
                                "parent" : "Commercial & Industrial"
                            },
                            "Manufacturer/Supplier" : {
                                "level" : 2,
                                "parent" : "Commercial & Industrial"
                            },
                                "Aircraft Manufacturer" : {
                                    "level" : 3,
                                    "parent" : "Manufacturer/Supplier"
                                },
                                "Apparel Distributor" : {
                                    "level" : 3,
                                    "parent" : "Manufacturer/Supplier"
                                },
                                "Appliance Manufacturer" : {
                                    "level" : 3,
                                    "parent" : "Manufacturer/Supplier"
                                },
                                "Bags & Luggage Company" : {
                                    "level" : 3,
                                    "parent" : "Manufacturer/Supplier"
                                },
                                "Clothing Company" : {
                                    "level" : 3,
                                    "parent" : "Manufacturer/Supplier"
                                },
                                "Glass Manufacturer" : {
                                    "level" : 3,
                                    "parent" : "Manufacturer/Supplier"
                                },
                                "Jewelry & Watches Company" : {
                                    "level" : 3,
                                    "parent" : "Manufacturer/Supplier"
                                },
                                "Jewelry Wholesaler" : {
                                    "level" : 3,
                                    "parent" : "Manufacturer/Supplier"
                                },
                                "Machine Shop" : {
                                    "level" : 3,
                                    "parent" : "Manufacturer/Supplier"
                                },
                                "Mattress Manufacturer" : {
                                    "level" : 3,
                                    "parent" : "Manufacturer/Supplier"
                                },
                            "Metal & Steel Company" : {
                                "level" : 2,
                                "parent" : "Commercial & Industrial"
                            },
                                "Metal Fabricator" : {
                                    "level" : 3,
                                    "parent" : "Metal & Steel Company"
                                },
                                "Metal Plating Service Company" : {
                                    "level" : 3,
                                    "parent" : "Metal & Steel Company"
                                },
                                "Metal Supplier" : {
                                    "level" : 3,
                                    "parent" : "Metal & Steel Company"
                                },
                            "Mining Company" : {
                                "level" : 2,
                                "parent" : "Commercial & Industrial"
                            },
                                "Granite & Marble Supplier" : {
                                    "level" : 3,
                                    "parent" : "Mining Company"
                                },
                            "Plastic Company" : {
                                "level" : 2,
                                "parent" : "Commercial & Industrial"
                            },
                                "Plastic Fabricator" : {
                                    "level" : 3,
                                    "parent" : "Plastic Company"
                                },
                                "Plastic Manufacturer" : {
                                    "level" : 3,
                                    "parent" : "Plastic Company"
                                },
                            "Textile Company" : {
                                "level" : 2,
                                "parent" : "Commercial & Industrial"
                            },
                            "Tobacco Company" : {
                                "level" : 2,
                                "parent" : "Commercial & Industrial"
                            },
                        "Education" : {
                            "level" : 1,
                            "parent" : "Businesses"
                        },
                            "Academic Camp" : {
                                "level" : 2,
                                "parent" : "Education"
                            },
                            "Archaeological Service" : {
                                "level" : 2,
                                "parent" : "Education"
                            },
                            "College & University" : {
                                "level" : 2,
                                "parent" : "Education"
                            },
                                "Community College" : {
                                    "level" : 3,
                                    "parent" : "College & University"
                                },
                            "Educational Consultant" : {
                                "level" : 2,
                                "parent" : "Education"
                            },
                            "Educational Research Center" : {
                                "level" : 2,
                                "parent" : "Education"
                            },
                            "School" : {
                                "level" : 2,
                                "parent" : "Education"
                            },
                                "Art School" : {
                                    "level" : 3,
                                    "parent" : "School"
                                },
                                "Day Care" : {
                                    "level" : 3,
                                    "parent" : "School"
                                },
                                "Elementary School" : {
                                    "level" : 3,
                                    "parent" : "School"
                                },
                                "High School" : {
                                    "level" : 3,
                                    "parent" : "School"
                                },
                                "Junior High School" : {
                                    "level" : 3,
                                    "parent" : "School"
                                },
                                "Medical School" : {
                                    "level" : 3,
                                    "parent" : "School"
                                },
                                "Middle School" : {
                                    "level" : 3,
                                    "parent" : "School"
                                },
                                "Performing Arts School" : {
                                    "level" : 3,
                                    "parent" : "School"
                                },
                                "Preschool" : {
                                    "level" : 3,
                                    "parent" : "School"
                                },
                                "Private School" : {
                                    "level" : 3,
                                    "parent" : "School"
                                },
                                "Public School" : {
                                    "level" : 3,
                                    "parent" : "School"
                                },
                                "Religious School" : {
                                    "level" : 3,
                                    "parent" : "School"
                                },
                            "Specialty School" : {
                                "level" : 2,
                                "parent" : "Education"
                            },
                                "Aviation School" : {
                                    "level" : 3,
                                    "parent" : "Specialty School"
                                },
                                "Bartending School" : {
                                    "level" : 3,
                                    "parent" : "Specialty School"
                                },
                                "Computer Training School" : {
                                    "level" : 3,
                                    "parent" : "Specialty School"
                                },
                                "Cooking School" : {
                                    "level" : 3,
                                    "parent" : "Specialty School"
                                },
                                "Cosmetology School" : {
                                    "level" : 3,
                                    "parent" : "Specialty School"
                                },
                                "Dance School" : {
                                    "level" : 3,
                                    "parent" : "Specialty School"
                                },
                                "Driving School" : {
                                    "level" : 3,
                                    "parent" : "Specialty School"
                                },
                                "First Aid Class" : {
                                    "level" : 3,
                                    "parent" : "Specialty School"
                                },
                                "Flight School" : {
                                    "level" : 3,
                                    "parent" : "Specialty School"
                                },
                                "Language School" : {
                                    "level" : 3,
                                    "parent" : "Specialty School"
                                },
                                "Massage School" : {
                                    "level" : 3,
                                    "parent" : "Specialty School"
                                },
                                "Music Lessons & Instruction School" : {
                                    "level" : 3,
                                    "parent" : "Specialty School"
                                },
                                "Nursing School" : {
                                    "level" : 3,
                                    "parent" : "Specialty School"
                                },
                                "Painting Lessons" : {
                                    "level" : 3,
                                    "parent" : "Specialty School"
                                },
                                "Trade School" : {
                                    "level" : 3,
                                    "parent" : "Specialty School"
                                },
                                "Traffic School" : {
                                    "level" : 3,
                                    "parent" : "Specialty School"
                                },
                            "Test Preparation Center" : {
                                "level" : 2,
                                "parent" : "Education"
                            },
                            "Tutor/Teacher" : {
                                "level" : 2,
                                "parent" : "Education"
                            },
                        "Finance" : {
                            "level" : 1,
                            "parent" : "Businesses"
                        },
                            "Bank" : {
                                "level" : 2,
                                "parent" : "Finance"
                            },
                                "Commercial Bank" : {
                                    "level" : 3,
                                    "parent" : "Bank"
                                },
                                "Credit Union" : {
                                    "level" : 3,
                                    "parent" : "Bank"
                                },
                                "Investment Bank" : {
                                    "level" : 3,
                                    "parent" : "Bank"
                                },
                                "Retail Bank" : {
                                    "level" : 3,
                                    "parent" : "Bank"
                                },
                            "Financial Service" : {
                                "level" : 2,
                                "parent" : "Finance"
                            },
                                "Accountant" : {
                                    "level" : 3,
                                    "parent" : "Financial Service"
                                },
                                "Bank Equipment & Service" : {
                                    "level" : 3,
                                    "parent" : "Financial Service"
                                },
                                "Cash Advance Service" : {
                                    "level" : 3,
                                    "parent" : "Financial Service"
                                },
                                "Collection Agency" : {
                                    "level" : 3,
                                    "parent" : "Financial Service"
                                },
                                "Credit Counseling Service" : {
                                    "level" : 3,
                                    "parent" : "Financial Service"
                                },
                                "Currency Exchange" : {
                                    "level" : 3,
                                    "parent" : "Financial Service"
                                },
                                "Financial Aid Service" : {
                                    "level" : 3,
                                    "parent" : "Financial Service"
                                },
                                "Financial Consultant" : {
                                    "level" : 3,
                                    "parent" : "Financial Service"
                                },
                                "Financial Planner" : {
                                    "level" : 3,
                                    "parent" : "Financial Service"
                                },
                                "Franchise Broker" : {
                                    "level" : 3,
                                    "parent" : "Financial Service"
                                },
                                "Loan Service" : {
                                    "level" : 3,
                                    "parent" : "Financial Service"
                                },
                                "Tax Preparation Service" : {
                                    "level" : 3,
                                    "parent" : "Financial Service"
                                },
                            "Insurance Company" : {
                                "level" : 2,
                                "parent" : "Finance"
                            },
                                "Insurance Agent" : {
                                    "level" : 3,
                                    "parent" : "Insurance Company"
                                },
                                "Insurance Broker" : {
                                    "level" : 3,
                                    "parent" : "Insurance Company"
                                },
                            "Investing Service" : {
                                "level" : 2,
                                "parent" : "Finance"
                            },
                                "Brokerage Firm" : {
                                    "level" : 3,
                                    "parent" : "Investing Service"
                                },
                            "Investment Management Company" : {
                                "level" : 2,
                                "parent" : "Finance"
                            },
                                "Hedge Fund" : {
                                    "level" : 3,
                                    "parent" : "Investment Management Company"
                                },
                        "Food & Beverage" : {
                            "level" : 1,
                            "parent" : "Businesses"
                        },
                            "Bagel Shop" : {
                                "level" : 2,
                                "parent" : "Food & Beverage"
                            },
                            "Bakery" : {
                                "level" : 2,
                                "parent" : "Food & Beverage"
                            },
                                "Wholesale Bakery" : {
                                    "level" : 3,
                                    "parent" : "Bakery"
                                },
                            "Bar" : {
                                "level" : 2,
                                "parent" : "Food & Beverage"
                            },
                                "Beer Bar" : {
                                    "level" : 3,
                                    "parent" : "Bar"
                                },
                                "Beer Garden" : {
                                    "level" : 3,
                                    "parent" : "Bar"
                                },
                                "Champagne Bar" : {
                                    "level" : 3,
                                    "parent" : "Bar"
                                },
                                "Cocktail Bar" : {
                                    "level" : 3,
                                    "parent" : "Bar"
                                },
                                "Dive Bar" : {
                                    "level" : 3,
                                    "parent" : "Bar"
                                },
                                "Gay Bar" : {
                                    "level" : 3,
                                    "parent" : "Bar"
                                },
                                "Hookah Lounge" : {
                                    "level" : 3,
                                    "parent" : "Bar"
                                },
                                "Hotel Bar" : {
                                    "level" : 3,
                                    "parent" : "Bar"
                                },
                                "Irish Pub" : {
                                    "level" : 3,
                                    "parent" : "Bar"
                                },
                                "Lounge" : {
                                    "level" : 3,
                                    "parent" : "Bar"
                                },
                                "Pub" : {
                                    "level" : 3,
                                    "parent" : "Bar"
                                },
                                "Sake Bar" : {
                                    "level" : 3,
                                    "parent" : "Bar"
                                },
                                "Speakeasy" : {
                                    "level" : 3,
                                    "parent" : "Bar"
                                },
                                "Sports Bar" : {
                                    "level" : 3,
                                    "parent" : "Bar"
                                },
                                "Tiki Bar" : {
                                    "level" : 3,
                                    "parent" : "Bar"
                                },
                                "Whisky Bar" : {
                                    "level" : 3,
                                    "parent" : "Bar"
                                },
                                "Wine Bar" : {
                                    "level" : 3,
                                    "parent" : "Bar"
                                },
                            "Bottled Water Company" : {
                                "level" : 2,
                                "parent" : "Food & Beverage"
                            },
                            "Brewery" : {
                                "level" : 2,
                                "parent" : "Food & Beverage"
                            },
                            "Bubble Tea Shop" : {
                                "level" : 2,
                                "parent" : "Food & Beverage"
                            },
                            "Butcher Shop" : {
                                "level" : 2,
                                "parent" : "Food & Beverage"
                            },
                            "Cafe" : {
                                "level" : 2,
                                "parent" : "Food & Beverage"
                            },
                                "Coffee Shop" : {
                                    "level" : 3,
                                    "parent" : "Cafe"
                                },
                                "Pet Cafe" : {
                                    "level" : 3,
                                    "parent" : "Cafe"
                                },
                                "Tea Room" : {
                                    "level" : 3,
                                    "parent" : "Cafe"
                                },
                            "Cafeteria" : {
                                "level" : 2,
                                "parent" : "Food & Beverage"
                            },
                            "Caterer" : {
                                "level" : 2,
                                "parent" : "Food & Beverage"
                            },
                            "Cheese Shop" : {
                                "level" : 2,
                                "parent" : "Food & Beverage"
                            },
                            "Convenience Store" : {
                                "level" : 2,
                                "parent" : "Food & Beverage"
                            },
                            "Deli" : {
                                "level" : 2,
                                "parent" : "Food & Beverage"
                            },
                            "Dessert Shop" : {
                                "level" : 2,
                                "parent" : "Food & Beverage"
                            },
                                "Candy Store" : {
                                    "level" : 3,
                                    "parent" : "Dessert Shop"
                                },
                                "Chocolate Shop" : {
                                    "level" : 3,
                                    "parent" : "Dessert Shop"
                                },
                                "Cupcake Shop" : {
                                    "level" : 3,
                                    "parent" : "Dessert Shop"
                                },
                                "Frozen Yogurt Shop" : {
                                    "level" : 3,
                                    "parent" : "Dessert Shop"
                                },
                                "Gelato Shop" : {
                                    "level" : 3,
                                    "parent" : "Dessert Shop"
                                },
                                "Ice Cream Shop" : {
                                    "level" : 3,
                                    "parent" : "Dessert Shop"
                                },
                                "Shaved Ice Shop" : {
                                    "level" : 3,
                                    "parent" : "Dessert Shop"
                                },
                            "Distillery" : {
                                "level" : 2,
                                "parent" : "Food & Beverage"
                            },
                            "Donut Shop" : {
                                "level" : 2,
                                "parent" : "Food & Beverage"
                            },
                            "Farmers Market" : {
                                "level" : 2,
                                "parent" : "Food & Beverage"
                            },
                            "Food Consultant" : {
                                "level" : 2,
                                "parent" : "Food & Beverage"
                            },
                            "Food Delivery Service" : {
                                "level" : 2,
                                "parent" : "Food & Beverage"
                            },
                            "Food Stand" : {
                                "level" : 2,
                                "parent" : "Food & Beverage"
                            },
                            "Food Truck" : {
                                "level" : 2,
                                "parent" : "Food & Beverage"
                            },
                            "Food Wholesaler" : {
                                "level" : 2,
                                "parent" : "Food & Beverage"
                            },
                                "Meat Wholesaler" : {
                                    "level" : 3,
                                    "parent" : "Food Wholesaler"
                                },
                                "Restaurant Wholesaler" : {
                                    "level" : 3,
                                    "parent" : "Food Wholesaler"
                                },
                            "Foodservice Distributor" : {
                                "level" : 2,
                                "parent" : "Food & Beverage"
                            },
                            "Grocery Store" : {
                                "level" : 2,
                                "parent" : "Food & Beverage"
                            },
                                "Ethnic Grocery Store" : {
                                    "level" : 3,
                                    "parent" : "Grocery Store"
                                },
                                "Fish Market" : {
                                    "level" : 3,
                                    "parent" : "Grocery Store"
                                },
                                "Fruit & Vegetable Store" : {
                                    "level" : 3,
                                    "parent" : "Grocery Store"
                                },
                                "Health Food Store" : {
                                    "level" : 3,
                                    "parent" : "Grocery Store"
                                },
                                "Organic Grocery Store" : {
                                    "level" : 3,
                                    "parent" : "Grocery Store"
                                },
                                "Specialty Grocery Store" : {
                                    "level" : 3,
                                    "parent" : "Grocery Store"
                                },
                                "Supermarket" : {
                                    "level" : 3,
                                    "parent" : "Grocery Store"
                                },
                                "Wholesale Grocer" : {
                                    "level" : 3,
                                    "parent" : "Grocery Store"
                                },
                            "Personal Chef" : {
                                "level" : 2,
                                "parent" : "Food & Beverage"
                            },
                            "Restaurant" : {
                                "level" : 2,
                                "parent" : "Food & Beverage"
                            },
                                "Afghan Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "African Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                    "Ethiopian Restaurant" : {
                                        "level" : 4,
                                        "parent" : "African Restaurant"
                                    },
                                    "Nigerian Restaurant" : {
                                        "level" : 4,
                                        "parent" : "African Restaurant"
                                    },
                                    "Senegalese Restaurant" : {
                                        "level" : 4,
                                        "parent" : "African Restaurant"
                                    },
                                    "South African Restaurant" : {
                                        "level" : 4,
                                        "parent" : "African Restaurant"
                                    },
                                "American Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Arabian Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Asian Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                    "Asian Fusion Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Asian Restaurant"
                                    },
                                    "Burmese Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Asian Restaurant"
                                    },
                                    "Cambodian Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Asian Restaurant"
                                    },
                                    "Chinese Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Asian Restaurant"
                                    },
                                        "Anhui Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Chinese Restaurant"
                                        },
                                        "Beijing Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Chinese Restaurant"
                                        },
                                        "Cantonese Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Chinese Restaurant"
                                        },
                                        "Dim Sum Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Chinese Restaurant"
                                        },
                                        "Dongbei Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Chinese Restaurant"
                                        },
                                        "Fujian Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Chinese Restaurant"
                                        },
                                        "Guizhou Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Chinese Restaurant"
                                        },
                                        "Hainan Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Chinese Restaurant"
                                        },
                                        "Henan Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Chinese Restaurant"
                                        },
                                        "Hong Kong Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Chinese Restaurant"
                                        },
                                        "Hot Pot Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Chinese Restaurant"
                                        },
                                        "Huaiyang Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Chinese Restaurant"
                                        },
                                        "Hubei Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Chinese Restaurant"
                                        },
                                        "Hunan Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Chinese Restaurant"
                                        },
                                        "Imperial Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Chinese Restaurant"
                                        },
                                        "Jiangsu Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Chinese Restaurant"
                                        },
                                        "Jiangxi Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Chinese Restaurant"
                                        },
                                        "Macanese Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Chinese Restaurant"
                                        },
                                        "Manchu Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Chinese Restaurant"
                                        },
                                        "Shaanxi Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Chinese Restaurant"
                                        },
                                        "Shandong Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Chinese Restaurant"
                                        },
                                        "Shanghainese Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Chinese Restaurant"
                                        },
                                        "Shanxi Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Chinese Restaurant"
                                        },
                                        "Szechuan/Sichuan Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Chinese Restaurant"
                                        },
                                        "Tianjin Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Chinese Restaurant"
                                        },
                                        "Xinjiang Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Chinese Restaurant"
                                        },
                                        "Yunnan Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Chinese Restaurant"
                                        },
                                        "Zhejiang Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Chinese Restaurant"
                                        },
                                    "Filipino Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Asian Restaurant"
                                    },
                                    "Indo Chinese Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Asian Restaurant"
                                    },
                                    "Indonesian Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Asian Restaurant"
                                    },
                                        "Acehnese Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Indonesian Restaurant"
                                        },
                                        "Balinese Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Indonesian Restaurant"
                                        },
                                        "Betawinese Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Indonesian Restaurant"
                                        },
                                        "Javanese Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Indonesian Restaurant"
                                        },
                                        "Manadonese Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Indonesian Restaurant"
                                        },
                                        "Padangnese Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Indonesian Restaurant"
                                        },
                                        "Sundanese Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Indonesian Restaurant"
                                        },
                                    "Japanese Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Asian Restaurant"
                                    },
                                        "Donburi Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Japanese Restaurant"
                                        },                                
                                        "Kaiseki Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Japanese Restaurant"
                                        },                      
                                        "Kushikatsu Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Japanese Restaurant"
                                        },                      
                                        "Monjayaki Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Japanese Restaurant"
                                        },                      
                                        "Nabe Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Japanese Restaurant"
                                        },                      
                                        "Okonomiyaki Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Japanese Restaurant"
                                        },                      
                                        "Ramen Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Japanese Restaurant"
                                        },                      
                                        "Shabu Shabu Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Japanese Restaurant"
                                        },                      
                                        "Soba Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Japanese Restaurant"
                                        },                      
                                        "Sukiyaki Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Japanese Restaurant"
                                        },                      
                                        "Sushi Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Japanese Restaurant"
                                        },                      
                                        "Takoyaki Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Japanese Restaurant"
                                        },                      
                                        "Tempura Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Japanese Restaurant"
                                        },                      
                                        "Teppanyaki Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Japanese Restaurant"
                                        },                      
                                        "Tonkatsu Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Japanese Restaurant"
                                        },                      
                                        "Udon Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Japanese Restaurant"
                                        },                      
                                        "Unagi Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Japanese Restaurant"
                                        },                      
                                        "Wagashi Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Japanese Restaurant"
                                        },                      
                                        "Yakiniku Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Japanese Restaurant"
                                        },                      
                                        "Yakitori Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Japanese Restaurant"
                                        },                      
                                        "Yoshoku Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Japanese Restaurant"
                                        },           
                                    "Korean Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Asian Restaurant"
                                    },    
                                        "Bossam/Jokbal Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Korean Restaurant"
                                        },
                                        "Bunsik Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Korean Restaurant"
                                        },
                                        "Gukbap Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Korean Restaurant"
                                        },
                                        "Janguh Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Korean Restaurant"
                                        },
                                        "Samgyetang Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Korean Restaurant"
                                        },
                                    "Malaysian Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Asian Restaurant"
                                    },    
                                    "Mongolian Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Asian Restaurant"
                                    },    
                                    "Noodle House" : {
                                        "level" : 4,
                                        "parent" : "Asian Restaurant"
                                    },    
                                    "Singaporean Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Asian Restaurant"
                                    },    
                                    "Taiwanese Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Asian Restaurant"
                                    },    
                                    "Thai Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Asian Restaurant"
                                    },    
                                    "Vietnamese Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Asian Restaurant"
                                    },
                                        "Pho Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Vietnamese Restaurant"
                                        },
                                "Australian Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Austrian Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Bar & Grill" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Barbecue Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Basque Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Belgian Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Breakfast & Brunch Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "British Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Buffet Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Burger Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Cajun & Creole Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Canadian Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Caribbean Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                    "Dominican Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Caribbean Restaurant"
                                    },
                                    "Haitian Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Caribbean Restaurant"
                                    },
                                    "Jamaican Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Caribbean Restaurant"
                                    },
                                    "Trinidadian Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Caribbean Restaurant"
                                    },
                                "Catalan Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Chicken Joint" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Comfort Food Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Continental Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Crêperie" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Czech Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Diner" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Drive In Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Eastern European Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                    "Belarusian Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Eastern European Restaurant"
                                    },                
                                    "Bulgarian Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Eastern European Restaurant"
                                    },                
                                    "Romanian Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Eastern European Restaurant"
                                    },                
                                    "Tatar Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Eastern European Restaurant"
                                    },
                                "Egyptian Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "European Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Family Style Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Fast Food Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Fish & Chips Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Fondue Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "French Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Gastropub" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "German Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                    "Baden Restaurant" : {
                                        "level" : 4,
                                        "parent" : "German Restaurant"
                                    },
                                    "Bavarian Restaurant" : {
                                        "level" : 4,
                                        "parent" : "German Restaurant"
                                    },
                                    "Hessian Restaurant" : {
                                        "level" : 4,
                                        "parent" : "German Restaurant"
                                    },
                                    "Palatine Restaurant" : {
                                        "level" : 4,
                                        "parent" : "German Restaurant"
                                    },
                                    "Saxon Restaurant" : {
                                        "level" : 4,
                                        "parent" : "German Restaurant"
                                    },
                                    "Swabian Restaurant" : {
                                        "level" : 4,
                                        "parent" : "German Restaurant"
                                    },
                                "Gluten-Free Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Halal Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Hawaiian Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                    "Poke Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Hawaiian Restaurant"
                                    },
                                "Health Food Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Himalayan Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Hot Dog Joint" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Hungarian Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Iberian Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Indian Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                    "Andhra Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Indian Restaurant"
                                    },
                                    "Awadhi Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Indian Restaurant"
                                    },
                                    "Bengali/Bangladeshi Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Indian Restaurant"
                                    },
                                    "Chaat Place" : {
                                        "level" : 4,
                                        "parent" : "Indian Restaurant"
                                    },
                                    "Chettinad Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Indian Restaurant"
                                    },
                                    "Dhaba Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Indian Restaurant"
                                    },
                                    "Dosa Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Indian Restaurant"
                                    },
                                    "Goan Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Indian Restaurant"
                                    },
                                    "Gujarati Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Indian Restaurant"
                                    },
                                    "Hyderabadi Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Indian Restaurant"
                                    },
                                    "Indian Chinese Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Indian Restaurant"
                                    },
                                    "Irani Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Indian Restaurant"
                                    },
                                    "Jain Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Indian Restaurant"
                                    },
                                    "Karnataka Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Indian Restaurant"
                                    },
                                    "Kashmiri Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Indian Restaurant"
                                    },
                                    "Kerala Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Indian Restaurant"
                                    },
                                    "Maharashtrian Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Indian Restaurant"
                                    },
                                    "Mughalai Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Indian Restaurant"
                                    },
                                    "North Indian Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Indian Restaurant"
                                    },
                                    "Parsi Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Indian Restaurant"
                                    },
                                    "Punjabi Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Indian Restaurant"
                                    },
                                    "Rajasthani Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Indian Restaurant"
                                    },
                                    "South Indian Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Indian Restaurant"
                                    },
                                    "Tamilian Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Indian Restaurant"
                                    },
                                    "Udupi Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Indian Restaurant"
                                    },
                                    "Uttar Pradesh Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Indian Restaurant"
                                    },
                                "Irish Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Italian Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                    "Abruzzo Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Italian Restaurant"
                                    },
                                    "Aosta Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Italian Restaurant"
                                    },
                                    "Basilicata Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Italian Restaurant"
                                    },
                                    "Calabrian Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Italian Restaurant"
                                    },
                                    "Emilia Romagna Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Italian Restaurant"
                                    },
                                    "Friuli Venezia Giulia Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Italian Restaurant"
                                    },
                                    "Ligurian Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Italian Restaurant"
                                    },
                                    "Lombard Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Italian Restaurant"
                                    },
                                    "Marche Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Italian Restaurant"
                                    },
                                    "Neapolitan Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Italian Restaurant"
                                    },
                                    "Piedmont Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Italian Restaurant"
                                    },
                                    "Puglia Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Italian Restaurant"
                                    },
                                    "Roman Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Italian Restaurant"
                                    },
                                    "Sardinian Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Italian Restaurant"
                                    },
                                    "Sicilian Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Italian Restaurant"
                                    },
                                    "South Tyrolean Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Italian Restaurant"
                                    },
                                    "Trentino Alto Adige Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Italian Restaurant"
                                    },
                                    "Tuscan Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Italian Restaurant"
                                    },
                                    "Umbrian Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Italian Restaurant"
                                    },
                                    "Venetian Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Italian Restaurant"
                                    },
                                "Kosher Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Latin American Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                    "Argentinian Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Latin American Restaurant"
                                    },
                                    "Belizean Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Latin American Restaurant"
                                    },
                                    "Bolivian Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Latin American Restaurant"
                                    },
                                    "Brazilian Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Latin American Restaurant"
                                    },
                                    "Chilean Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Latin American Restaurant"
                                    },
                                    "Colombian Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Latin American Restaurant"
                                    },
                                    "Costa Rican Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Latin American Restaurant"
                                    },
                                    "Cuban Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Latin American Restaurant"
                                    },
                                    "Ecuadorian Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Latin American Restaurant"
                                    },
                                    "Guatemalan Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Latin American Restaurant"
                                    },
                                    "Honduran Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Latin American Restaurant"
                                    },
                                    "Mexican Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Latin American Restaurant"
                                    },
                                        "Tex-Mex Restaurant" : {
                                            "level" : 5,
                                            "parent" : "Mexican Restaurant"
                                        },
                                    "Nicaraguan Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Latin American Restaurant"
                                    },
                                    "Panamanian Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Latin American Restaurant"
                                    },
                                    "Paraguayan Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Latin American Restaurant"
                                    },
                                    "Peruvian Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Latin American Restaurant"
                                    },
                                    "Puerto Rican Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Latin American Restaurant"
                                    },
                                    "Salvadoran Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Latin American Restaurant"
                                    },
                                    "Uruguayan Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Latin American Restaurant"
                                    },
                                    "Venezuelan Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Latin American Restaurant"
                                    },
                                "Live & Raw Food Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Mediterranean Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                    "Greek Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Mediterranean Restaurant"
                                    },
                                "Middle Eastern Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                    "Armenian Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Middle Eastern Restaurant"
                                    },
                                    "Azerbaijani Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Middle Eastern Restaurant"
                                    },
                                    "Georgian Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Middle Eastern Restaurant"
                                    },
                                    "Israeli Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Middle Eastern Restaurant"
                                    },
                                    "Kurdish Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Middle Eastern Restaurant"
                                    },
                                    "Lebanese Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Middle Eastern Restaurant"
                                    },
                                    "Persian/Iranian Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Middle Eastern Restaurant"
                                    },
                                    "Syrian Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Middle Eastern Restaurant"
                                    },
                                    "Turkish Restaurant" : {
                                        "level" : 4,
                                        "parent" : "Middle Eastern Restaurant"
                                    },
                                        "Kebab Shop" : {
                                            "level" : 5,
                                            "parent" : "Turkish Restaurant"
                                        },
                                "Modern European Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Molecular Gastronomy Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Moroccan Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Nepalese Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "New American Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Pakistani Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Pizza Place" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Polish Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Polynesian Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Portuguese Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Russian Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Salad Bar" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Scandinavian Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Scottish Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Seafood Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Slovakian Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Soul Food Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Soup Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Southern Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Southwestern Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Spanish Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Sri Lankan Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Steakhouse" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Swiss Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Taco Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Tapas Bar & Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Theme Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Ukrainian Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Uzbek Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                                "Vegetarian/Vegan Restaurant" : {
                                    "level" : 3,
                                    "parent" : "Restaurant"
                                },
                            "Sandwich Shop" : {
                                "level" : 2,
                                "parent" : "Food & Beverage"
                            },
                            "Smoothie & Juice Bar" : {
                                "level" : 2,
                                "parent" : "Food & Beverage"
                            },
                            "Wine, Beer & Spirits Store" : {
                                "level" : 2,
                                "parent" : "Food & Beverage"
                            },
                                "Homebrew Supply Store" : {
                                    "level" : 3,
                                    "parent" : "Wine, Beer & Spirits Store"
                                },
                            "Winery/Vineyard" : {
                                "level" : 2,
                                "parent" : "Food & Beverage"
                            },
                        "Hotel & Lodging" : {
                            "level" : 1,
                            "parent" : "Businesses"
                        },
                            "Bed and Breakfast" : {
                                "level" : 2,
                                "parent" : "Hotel & Lodging"
                            },
                            "Cabin" : {
                                "level" : 2,
                                "parent" : "Hotel & Lodging"
                            },
                            "Campground" : {
                                "level" : 2,
                                "parent" : "Hotel & Lodging"
                            },
                            "Cottage" : {
                                "level" : 2,
                                "parent" : "Hotel & Lodging"
                            },
                            "Hostel" : {
                                "level" : 2,
                                "parent" : "Hotel & Lodging"
                            },
                            "Hotel" : {
                                "level" : 2,
                                "parent" : "Hotel & Lodging"
                            },
                                "Beach Resort" : {
                                    "level" : 3,
                                    "parent" : "Hotel"
                                },
                                "Hotel Resort" : {
                                    "level" : 3,
                                    "parent" : "Hotel"
                                },
                            "Inn" : {
                                "level" : 2,
                                "parent" : "Hotel & Lodging"
                            },
                            "Lodge" : {
                                "level" : 2,
                                "parent" : "Hotel & Lodging"
                            },
                            "Motel" : {
                                "level" : 2,
                                "parent" : "Hotel & Lodging"
                            },
                            "RV Park" : {
                                "level" : 2,
                                "parent" : "Hotel & Lodging"
                            },
                            "Service Apartments" : {
                                "level" : 2,
                                "parent" : "Hotel & Lodging"
                            },
                            "Vacation Home Rental" : {
                                "level" : 2,
                                "parent" : "Hotel & Lodging"
                            },
                        "Legal" : {
                            "level" : 1,
                            "parent" : "Businesses"
                        },
                            "Lawyer & Law Firm" : {
                                "level" : 2,
                                "parent" : "Legal"
                            },
                                "Bankruptcy Lawyer" : {
                                    "level" : 3,
                                    "parent" : "Lawyer & Law Firm"
                                },
                                "Contract Lawyer" : {
                                    "level" : 3,
                                    "parent" : "Lawyer & Law Firm"
                                },
                                "Corporate Lawyer" : {
                                    "level" : 3,
                                    "parent" : "Lawyer & Law Firm"
                                },
                                "Criminal Lawyer" : {
                                    "level" : 3,
                                    "parent" : "Lawyer & Law Firm"
                                },
                                "DUI Lawyer" : {
                                    "level" : 3,
                                    "parent" : "Lawyer & Law Firm"
                                },
                                "Divorce & Family Lawyer" : {
                                    "level" : 3,
                                    "parent" : "Lawyer & Law Firm"
                                },
                                "Entertainment Lawyer" : {
                                    "level" : 3,
                                    "parent" : "Lawyer & Law Firm"
                                },
                                "Estate Planning Lawyer" : {
                                    "level" : 3,
                                    "parent" : "Lawyer & Law Firm"
                                },
                                "General Litigation" : {
                                    "level" : 3,
                                    "parent" : "Lawyer & Law Firm"
                                },
                                "Immigration Lawyer" : {
                                    "level" : 3,
                                    "parent" : "Lawyer & Law Firm"
                                },
                                "Intellectual Property Lawyer" : {
                                    "level" : 3,
                                    "parent" : "Lawyer & Law Firm"
                                },
                                "Internet Lawyer" : {
                                    "level" : 3,
                                    "parent" : "Lawyer & Law Firm"
                                },
                                "Juvenile Lawyer" : {
                                    "level" : 3,
                                    "parent" : "Lawyer & Law Firm"
                                },
                                "Labor & Employment Lawyer" : {
                                    "level" : 3,
                                    "parent" : "Lawyer & Law Firm"
                                },
                                "Landlord & Tenant Lawyer" : {
                                    "level" : 3,
                                    "parent" : "Lawyer & Law Firm"
                                },
                                "Malpractice Lawyer" : {
                                    "level" : 3,
                                    "parent" : "Lawyer & Law Firm"
                                },
                                "Medical Lawyer" : {
                                    "level" : 3,
                                    "parent" : "Lawyer & Law Firm"
                                },
                                "Military Lawyer" : {
                                    "level" : 3,
                                    "parent" : "Lawyer & Law Firm"
                                },
                                "Personal Injury Lawyer" : {
                                    "level" : 3,
                                    "parent" : "Lawyer & Law Firm"
                                },
                                "Property Lawyer" : {
                                    "level" : 3,
                                    "parent" : "Lawyer & Law Firm"
                                },
                                "Real Estate Lawyer" : {
                                    "level" : 3,
                                    "parent" : "Lawyer & Law Firm"
                                },
                                "Tax Lawyer" : {
                                    "level" : 3,
                                    "parent" : "Lawyer & Law Firm"
                                },
                            "Legal Service" : {
                                "level" : 2,
                                "parent" : "Legal"
                            },
                                "Bail Bondsmen" : {
                                    "level" : 3,
                                    "parent" : "Legal Service"
                                },
                                "Lobbyist" : {
                                    "level" : 3,
                                    "parent" : "Legal Service"
                                },
                                "Notary Public" : {
                                    "level" : 3,
                                    "parent" : "Legal Service"
                                },
                                "Private Investigator" : {
                                    "level" : 3,
                                    "parent" : "Legal Service"
                                },
                                "Process Service" : {
                                    "level" : 3,
                                    "parent" : "Legal Service"
                                },
                        "Local Service" : {
                            "level" : 1,
                            "parent" : "Businesses"
                        },
                            "Adoption Service" : {
                                "level" : 2,
                                "parent" : "Local Service"
                            },
                            "Astrologist" : {
                                "level" : 2,
                                "parent" : "Local Service"
                            },
                            "Astrologist & Psychic" : {
                                "level" : 2,
                                "parent" : "Local Service"
                            },
                            "Bicycle Repair Service" : {
                                "level" : 2,
                                "parent" : "Local Service"
                            },
                            "Bottled Water Supplier" : {
                                "level" : 2,
                                "parent" : "Local Service"
                            },
                            "Business Service" : {
                                "level" : 2,
                                "parent" : "Local Service"
                            },
                                "Business Consultant" : {
                                    "level" : 3,
                                    "parent" : "Business Service"
                                },
                                "Business Supply Service" : {
                                    "level" : 3,
                                    "parent" : "Business Service"
                                },
                                "Cargo & Freight Company" : {
                                    "level" : 3,
                                    "parent" : "Business Service"
                                },
                                "Consulting Agency" : {
                                    "level" : 3,
                                    "parent" : "Business Service"
                                },
                                "Employment Agency" : {
                                    "level" : 3,
                                    "parent" : "Business Service"
                                },
                                    "Recruiter" : {
                                        "level" : 4,
                                        "parent" : "Employment Agency"
                                    },
                                "Franchising Service" : {
                                    "level" : 3,
                                    "parent" : "Business Service"
                                },
                                "Graphic Designer" : {
                                    "level" : 3,
                                    "parent" : "Business Service"
                                },
                                "Hospitality Service" : {
                                    "level" : 3,
                                    "parent" : "Business Service"
                                },
                                "Janitorial Service" : {
                                    "level" : 3,
                                    "parent" : "Business Service"
                                },
                                "Management Service" : {
                                    "level" : 3,
                                    "parent" : "Business Service"
                                },
                                "Personal Assistant" : {
                                    "level" : 3,
                                    "parent" : "Business Service"
                                },
                                "Personal Coach" : {
                                    "level" : 3,
                                    "parent" : "Business Service"
                                },
                                "Secretarial Service" : {
                                    "level" : 3,
                                    "parent" : "Business Service"
                                },
                                "Security Guard Service" : {
                                    "level" : 3,
                                    "parent" : "Business Service"
                                },
                                "Shipping Supply & Service" : {
                                    "level" : 3,
                                    "parent" : "Business Service"
                                },
                                "Shredding Service" : {
                                    "level" : 3,
                                    "parent" : "Business Service"
                                },
                                "Translator" : {
                                    "level" : 3,
                                    "parent" : "Business Service"
                                },
                                "Uniform Supplier" : {
                                    "level" : 3,
                                    "parent" : "Business Service"
                                },
                                "Vending Machine Sales & Service" : {
                                    "level" : 3,
                                    "parent" : "Business Service"
                                },
                                "Web Designer" : {
                                    "level" : 3,
                                    "parent" : "Business Service"
                                },
                            "Career Counselor" : {
                                "level" : 2,
                                "parent" : "Local Service"
                            },
                            "Computer Repair Service" : {
                                "level" : 2,
                                "parent" : "Local Service"
                            },
                            "Dating Service" : {
                                "level" : 2,
                                "parent" : "Local Service"
                            },
                            "Design & Fashion" : {
                                "level" : 2,
                                "parent" : "Local Service"
                            },
                                "Modeling Agency" : {
                                    "level" : 3,
                                    "parent" : "Design & Fashion"
                                },
                            "Dry Cleaner" : {
                                "level" : 2,
                                "parent" : "Local Service"
                            },
                            "Event Planner" : {
                                "level" : 2,
                                "parent" : "Local Service"
                            },
                                "Bartending Service" : {
                                    "level" : 3,
                                    "parent" : "Event Planner"
                                },
                                "Wedding Planning Service" : {
                                    "level" : 3,
                                    "parent" : "Event Planner"
                                },
                            "Event Space" : {
                                "level" : 2,
                                "parent" : "Local Service"
                            },
                                "Ballroom" : {
                                    "level" : 3,
                                    "parent" : "Event Space"
                                },
                                "Business Center" : {
                                    "level" : 3,
                                    "parent" : "Event Space"
                                },
                                "Convention Center" : {
                                    "level" : 3,
                                    "parent" : "Event Space"
                                },
                                "Wedding Venue" : {
                                    "level" : 3,
                                    "parent" : "Event Space"
                                },
                            "Florist" : {
                                "level" : 2,
                                "parent" : "Local Service"
                            },
                            "Funeral Service & Cemetery" : {
                                "level" : 2,
                                "parent" : "Local Service"
                            },
                            "Genealogist" : {
                                "level" : 2,
                                "parent" : "Local Service"
                            },
                            "Glass Blower" : {
                                "level" : 2,
                                "parent" : "Local Service"
                            },
                            "Home Improvement" : {
                                "level" : 2,
                                "parent" : "Local Service"
                            },
                                "Appliance Repair Service" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                    "Heating, Ventilating & Air Conditioning Service" : {
                                        "level" : 4,
                                        "parent" : "Appliance Repair Service"
                                    },
                                    "Refrigeration Service" : {
                                        "level" : 4,
                                        "parent" : "Appliance Repair Service"
                                    },
                                    "Television Repair Service" : {
                                        "level" : 4,
                                        "parent" : "Appliance Repair Service"
                                    },
                                    "Water Heater Installation & Repair Service" : {
                                        "level" : 4,
                                        "parent" : "Appliance Repair Service"
                                    },
                                "Architectural Designer" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Carpenter" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Carpet Cleaner" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Chimney Sweeper" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Concrete Contractor" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Construction Company" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Contractor" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Damage Restoration Service" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Deck & Patio Builder" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Demolition & Excavation Company" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Electrician" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Elevator Service" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Fence & Gate Contractor" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Fire Protection Service" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Furniture Repair & Upholstery Service" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Garage Door Service" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Gardener" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Glass Service" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Gutter Cleaning Service" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Handyman" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Home Security Company" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Home Window Service" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "House Painting" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Interior Design Studio" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Kitchen & Bath Contractor" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Landscape Company" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Lumber Yard" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Masonry Contractor" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Paving & Asphalt Service" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Pest Control Service" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Plumbing Service" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Portable Building Service" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Portable Toilet Rentals" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Powder Coating Service" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Roofing Service" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Sandblasting Service" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Septic Tank Service" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Sewer Service" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Solar Energy Service" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Swimming Pool & Hot Tub Service" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Swimming Pool Cleaner" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Tiling Service" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Tree Cutting Service" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Vinyl Siding Company" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Water Treatment Service" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Well Water Drilling Service" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                                "Window Installation Service" : {
                                    "level" : 3,
                                    "parent" : "Home Improvement"
                                },
                            "In-Home Service" : {
                                "level" : 2,
                                "parent" : "Local Service"
                            },
                                "Babysitter" : {
                                    "level" : 3,
                                    "parent" : "In-Home Service"
                                },
                                "Child Care Service" : {
                                    "level" : 3,
                                    "parent" : "In-Home Service"
                                },
                                "Cleaning Service" : {
                                    "level" : 3,
                                    "parent" : "In-Home Service"
                                },
                                "House Sitter" : {
                                    "level" : 3,
                                    "parent" : "In-Home Service"
                                },
                                "Maid & Butler" : {
                                    "level" : 3,
                                    "parent" : "In-Home Service"
                                },
                                "Nanny" : {
                                    "level" : 3,
                                    "parent" : "In-Home Service"
                                },
                            "Internet Cafe" : {
                                "level" : 2,
                                "parent" : "Local Service"
                            },
                            "Junkyard" : {
                                "level" : 2,
                                "parent" : "Local Service"
                            },
                            "Laundromat" : {
                                "level" : 2,
                                "parent" : "Local Service"
                            },
                            "Locksmith" : {
                                "level" : 2,
                                "parent" : "Local Service"
                            },
                            "Moving & Storage Service" : {
                                "level" : 2,
                                "parent" : "Local Service"
                            },
                                "Home Mover" : {
                                    "level" : 3,
                                    "parent" : "Moving & Storage Service"
                                },
                                "Self-Storage Facility" : {
                                    "level" : 3,
                                    "parent" : "Moving & Storage Service"
                                },
                                "Storage Facility" : {
                                    "level" : 3,
                                    "parent" : "Moving & Storage Service"
                                },
                            "Parking Garage / Lot" : {
                                "level" : 2,
                                "parent" : "Local Service"
                            },
                            "Party & Entertainment Service" : {
                                "level" : 2,
                                "parent" : "Local Service"
                            },
                            "Party Entertainment Service" : {
                                "level" : 2,
                                "parent" : "Local Service"
                            },
                                "Adult Entertainment Service" : {
                                    "level" : 3,
                                    "parent" : "Party Entertainment Service"
                                },
                                "DJ" : {
                                    "level" : 3,
                                    "parent" : "Party Entertainment Service"
                                },
                                "Kids Entertainment Service" : {
                                    "level" : 3,
                                    "parent" : "Party Entertainment Service"
                                },
                                "Magician" : {
                                    "level" : 3,
                                    "parent" : "Party Entertainment Service"
                                },
                            "Pet Service" : {
                                "level" : 2,
                                "parent" : "Local Service"
                            },
                                "Animal Rescue Service" : {
                                    "level" : 3,
                                    "parent" : "Pet Service"
                                },
                                "Animal Shelter" : {
                                    "level" : 3,
                                    "parent" : "Pet Service"
                                },
                                "Dog Day Care Center" : {
                                    "level" : 3,
                                    "parent" : "Pet Service"
                                },
                                "Dog Trainer" : {
                                    "level" : 3,
                                    "parent" : "Pet Service"
                                },
                                "Dog Walker" : {
                                    "level" : 3,
                                    "parent" : "Pet Service"
                                },
                                "Horse Trainer" : {
                                    "level" : 3,
                                    "parent" : "Pet Service"
                                },
                                "Kennel" : {
                                    "level" : 3,
                                    "parent" : "Pet Service"
                                },
                                "Livery Stable" : {
                                    "level" : 3,
                                    "parent" : "Pet Service"
                                },
                                "Pet Adoption Service" : {
                                    "level" : 3,
                                    "parent" : "Pet Service"
                                },
                                "Pet Breeder" : {
                                    "level" : 3,
                                    "parent" : "Pet Service"
                                },
                                    "Dog Breeder" : {
                                        "level" : 4,
                                        "parent" : "Pet Breeder"
                                    },
                                "Pet Groomer" : {
                                    "level" : 3,
                                    "parent" : "Pet Service"
                                },
                                "Pet Sitter" : {
                                    "level" : 3,
                                    "parent" : "Pet Service"
                                },
                                "Taxidermist" : {
                                    "level" : 3,
                                    "parent" : "Pet Service"
                                },
                                "Veterinarian" : {
                                    "level" : 3,
                                    "parent" : "Pet Service"
                                },
                            "Photography Videography" : {
                                "level" : 2,
                                "parent" : "Local Service"
                            },
                                "Amateur Photographer" : {
                                    "level" : 3,
                                    "parent" : "Photography Videography"
                                },
                                "Camera Store" : {
                                    "level" : 3,
                                    "parent" : "Photography Videography"
                                },
                                "Event Photographer" : {
                                    "level" : 3,
                                    "parent" : "Photography Videography"
                                },
                                "Event Videographer" : {
                                    "level" : 3,
                                    "parent" : "Photography Videography"
                                },
                                "Photo Booth Service" : {
                                    "level" : 3,
                                    "parent" : "Photography Videography"
                                },
                                "Photographer" : {
                                    "level" : 3,
                                    "parent" : "Photography Videography"
                                },
                            "Printing Service" : {
                                "level" : 2,
                                "parent" : "Local Service"
                            },
                                "Screen Printing & Embroidery" : {
                                    "level" : 3,
                                    "parent" : "Printing Service"
                                },
                                "Signs & Banner Service" : {
                                    "level" : 3,
                                    "parent" : "Printing Service"
                                },
                            "Sewing & Alterations" : {
                                "level" : 2,
                                "parent" : "Local Service"
                            },
                            "Shoe Repair Shop" : {
                                "level" : 2,
                                "parent" : "Local Service"
                            },
                            "Weight Loss Center" : {
                                "level" : 2,
                                "parent" : "Local Service"
                            },
                            "Writing Service" : {
                                "level" : 2,
                                "parent" : "Local Service"
                            },
                        "Media/News Company" : {
                            "level" : 1,
                            "parent" : "Businesses"
                        },
                            "Animation Studio" : {
                                "level" : 2,
                                "parent" : "Media/News Company"
                            },
                            "Book & Magazine Distributor" : {
                                "level" : 2,
                                "parent" : "Media/News Company"
                            },
                            "Broadcasting & Media Production Company" : {
                                "level" : 2,
                                "parent" : "Media/News Company"
                            },
                            "Game Publisher" : {
                                "level" : 2,
                                "parent" : "Media/News Company"
                            },
                            "Movie/Television Studio" : {
                                "level" : 2,
                                "parent" : "Media/News Company"
                            },
                            "Music Production Studio" : {
                                "level" : 2,
                                "parent" : "Media/News Company"
                            },
                            "Publisher" : {
                                "level" : 2,
                                "parent" : "Media/News Company"
                            },
                            "Radio Station" : {
                                "level" : 2,
                                "parent" : "Media/News Company"
                            },
                            "Social Media Company" : {
                                "level" : 2,
                                "parent" : "Media/News Company"
                            },
                        "Medical & Health" : {
                            "level" : 1,
                            "parent" : "Businesses"
                        },
                            "Dentist & Dental Office" : {
                                "level" : 2,
                                "parent" : "Medical & Health"
                            },
                                "Cosmetic Dentist" : {
                                    "level" : 3,
                                    "parent" : "Dentist & Dental Office"
                                },
                                "Endodontist" : {
                                    "level" : 3,
                                    "parent" : "Dentist & Dental Office"
                                },
                                "General Dentist" : {
                                    "level" : 3,
                                    "parent" : "Dentist & Dental Office"
                                },
                                "Oral Surgeon" : {
                                    "level" : 3,
                                    "parent" : "Dentist & Dental Office"
                                },
                                "Orthodontist" : {
                                    "level" : 3,
                                    "parent" : "Dentist & Dental Office"
                                },
                                "Pediatric Dentist" : {
                                    "level" : 3,
                                    "parent" : "Dentist & Dental Office"
                                },
                                "Periodontist" : {
                                    "level" : 3,
                                    "parent" : "Dentist & Dental Office"
                                },
                                "Prosthodontist" : {
                                    "level" : 3,
                                    "parent" : "Dentist & Dental Office"
                                },
                                "Teeth Whitening Service" : {
                                    "level" : 3,
                                    "parent" : "Dentist & Dental Office"
                                },
                            "Doctor" : {
                                "level" : 2,
                                "parent" : "Medical & Health"
                            },
                                "Allergist" : {
                                    "level" : 3,
                                    "parent" : "Doctor"
                                },
                                "Anesthesiologist" : {
                                    "level" : 3,
                                    "parent" : "Doctor"
                                },
                                "Audiologist" : {
                                    "level" : 3,
                                    "parent" : "Doctor"
                                },
                                "Cardiologist" : {
                                    "level" : 3,
                                    "parent" : "Doctor"
                                },
                                "Dermatologist" : {
                                    "level" : 3,
                                    "parent" : "Doctor"
                                },
                                "Endocrinologist" : {
                                    "level" : 3,
                                    "parent" : "Doctor"
                                },
                                "Family Doctor" : {
                                    "level" : 3,
                                    "parent" : "Doctor"
                                },
                                "Fertility Doctor" : {
                                    "level" : 3,
                                    "parent" : "Doctor"
                                },
                                "Gastroenterologist" : {
                                    "level" : 3,
                                    "parent" : "Doctor"
                                },
                                "Gerontologist" : {
                                    "level" : 3,
                                    "parent" : "Doctor"
                                },
                                "Internist (Internal Medicine)" : {
                                    "level" : 3,
                                    "parent" : "Doctor"
                                },
                                "Lasik/Laser Eye Surgeon" : {
                                    "level" : 3,
                                    "parent" : "Doctor"
                                },
                                "Nephrologist" : {
                                    "level" : 3,
                                    "parent" : "Doctor"
                                },
                                "Neurologist" : {
                                    "level" : 3,
                                    "parent" : "Doctor"
                                },
                                "Neurosurgeon" : {
                                    "level" : 3,
                                    "parent" : "Doctor"
                                },
                                "Obstetrician-Gynecologist (OBGYN)" : {
                                    "level" : 3,
                                    "parent" : "Doctor"
                                },
                                "Oncologist" : {
                                    "level" : 3,
                                    "parent" : "Doctor"
                                },
                                "Ophthalmologist" : {
                                    "level" : 3,
                                    "parent" : "Doctor"
                                },
                                "Optometrist" : {
                                    "level" : 3,
                                    "parent" : "Doctor"
                                },
                                "Orthopedist" : {
                                    "level" : 3,
                                    "parent" : "Doctor"
                                },
                                "Osteopathic Doctor" : {
                                    "level" : 3,
                                    "parent" : "Doctor"
                                },
                                "Otolaryngologist (ENT)" : {
                                    "level" : 3,
                                    "parent" : "Doctor"
                                },
                                "Pediatrician" : {
                                    "level" : 3,
                                    "parent" : "Doctor"
                                },
                                "Plastic Surgeon" : {
                                    "level" : 3,
                                    "parent" : "Doctor"
                                },
                                "Podiatrist" : {
                                    "level" : 3,
                                    "parent" : "Doctor"
                                },
                                "Proctologist" : {
                                    "level" : 3,
                                    "parent" : "Doctor"
                                },
                                "Psychiatrist" : {
                                    "level" : 3,
                                    "parent" : "Doctor"
                                },
                                "Psychologist" : {
                                    "level" : 3,
                                    "parent" : "Doctor"
                                },
                                "Pulmonologist" : {
                                    "level" : 3,
                                    "parent" : "Doctor"
                                },
                                "Radiologist" : {
                                    "level" : 3,
                                    "parent" : "Doctor"
                                },
                                "Rheumatologist" : {
                                    "level" : 3,
                                    "parent" : "Doctor"
                                },
                                "Surgeon" : {
                                    "level" : 3,
                                    "parent" : "Doctor"
                                },
                                "Urologist" : {
                                    "level" : 3,
                                    "parent" : "Doctor"
                                },
                            "Medical Center" : {
                                "level" : 2,
                                "parent" : "Medical & Health"
                            },
                                "AIDS Resource Center" : {
                                    "level" : 3,
                                    "parent" : "Medical Center"
                                },
                                "Blood Bank" : {
                                    "level" : 3,
                                    "parent" : "Medical Center"
                                },
                                "Crisis Prevention Center" : {
                                    "level" : 3,
                                    "parent" : "Medical Center"
                                },
                                "Diagnostic Center" : {
                                    "level" : 3,
                                    "parent" : "Medical Center"
                                },
                                "Dialysis Clinic" : {
                                    "level" : 3,
                                    "parent" : "Medical Center"
                                },
                                "Emergency Room" : {
                                    "level" : 3,
                                    "parent" : "Medical Center"
                                },
                                "Family Medicine Practice" : {
                                    "level" : 3,
                                    "parent" : "Medical Center"
                                },
                                "Halfway House" : {
                                    "level" : 3,
                                    "parent" : "Medical Center"
                                },
                                "Hospice" : {
                                    "level" : 3,
                                    "parent" : "Medical Center"
                                },
                                "Hospital" : {
                                    "level" : 3,
                                    "parent" : "Medical Center"
                                },
                                "Maternity Clinic" : {
                                    "level" : 3,
                                    "parent" : "Medical Center"
                                },
                                "Medical Lab" : {
                                    "level" : 3,
                                    "parent" : "Medical Center"
                                },
                                "Nursing Home" : {
                                    "level" : 3,
                                    "parent" : "Medical Center"
                                },
                                "Pregnancy Care Center" : {
                                    "level" : 3,
                                    "parent" : "Medical Center"
                                },
                                "Retirement & Assisted Living Facility" : {
                                    "level" : 3,
                                    "parent" : "Medical Center"
                                },
                                "STD Testing Center" : {
                                    "level" : 3,
                                    "parent" : "Medical Center"
                                },
                                "Surgical Center" : {
                                    "level" : 3,
                                    "parent" : "Medical Center"
                                },
                                "Women's Health Clinic" : {
                                    "level" : 3,
                                    "parent" : "Medical Center"
                                },
                            "Medical Device Company" : {
                                "level" : 2,
                                "parent" : "Medical & Health"
                            },
                            "Medical Equipment Manufacturer" : {
                                "level" : 2,
                                "parent" : "Medical & Health"
                            },
                            "Medical Equipment Supplier" : {
                                "level" : 2,
                                "parent" : "Medical & Health"
                            },
                            "Medical Research Center" : {
                                "level" : 2,
                                "parent" : "Medical & Health"
                            },
                            "Medical Service" : {
                                "level" : 2,
                                "parent" : "Medical & Health"
                            },
                                "Abortion Service" : {
                                    "level" : 3,
                                    "parent" : "Medical Service"
                                },
                                "Addiction Service" : {
                                    "level" : 3,
                                    "parent" : "Medical Service"
                                },
                                    "Addiction Resources Center" : {
                                        "level" : 4,
                                        "parent" : "Addiction Service"
                                    },
                                    "Addiction Treatment Center" : {
                                        "level" : 4,
                                        "parent" : "Addiction Service"
                                    },
                                    "Alcohol Addiction Treatment Center" : {
                                        "level" : 4,
                                        "parent" : "Addiction Service"
                                    },
                                    "Drug Addiction Treatment Center" : {
                                        "level" : 4,
                                        "parent" : "Addiction Service"
                                    },
                                    "Tobacco Cessation Treatment Center" : {
                                        "level" : 4,
                                        "parent" : "Addiction Service"
                                    },
                                "Alternative & Holistic Health Service" : {
                                    "level" : 3,
                                    "parent" : "Medical Service"
                                },
                                    "Acupuncturist" : {
                                        "level" : 4,
                                        "parent" : "Alternative & Holistic Health Service"
                                    },
                                    "Chiropractor" : {
                                        "level" : 4,
                                        "parent" : "Alternative & Holistic Health Service"
                                    },
                                    "Massage Therapist" : {
                                        "level" : 4,
                                        "parent" : "Alternative & Holistic Health Service"
                                    },
                                    "Medical Cannabis Dispensary" : {
                                        "level" : 4,
                                        "parent" : "Alternative & Holistic Health Service"
                                    },
                                    "Medical Spa" : {
                                        "level" : 4,
                                        "parent" : "Alternative & Holistic Health Service"
                                    },
                                    "Meditation Center" : {
                                        "level" : 4,
                                        "parent" : "Alternative & Holistic Health Service"
                                    },
                                    "Naturopath" : {
                                        "level" : 4,
                                        "parent" : "Alternative & Holistic Health Service"
                                    },
                                    "Nutritionist" : {
                                        "level" : 4,
                                        "parent" : "Alternative & Holistic Health Service"
                                    },
                                    "Reflexologist" : {
                                        "level" : 4,
                                        "parent" : "Alternative & Holistic Health Service"
                                    },
                                "Disability Service" : {
                                    "level" : 3,
                                    "parent" : "Medical Service"
                                },
                                "Emergency Rescue Service" : {
                                    "level" : 3,
                                    "parent" : "Medical Service"
                                },
                                "Healthcare Administrator" : {
                                    "level" : 3,
                                    "parent" : "Medical Service"
                                },
                                "Home Health Care Service" : {
                                    "level" : 3,
                                    "parent" : "Medical Service"
                                },
                                "Mental Health Service" : {
                                    "level" : 3,
                                    "parent" : "Medical Service"
                                },
                                "Nursing Agency" : {
                                    "level" : 3,
                                    "parent" : "Medical Service"
                                },
                                "Orthotics & Prosthetics Service" : {
                                    "level" : 3,
                                    "parent" : "Medical Service"
                                },
                                "Reproductive Service" : {
                                    "level" : 3,
                                    "parent" : "Medical Service"
                                },
                                "Safety & First Aid Service" : {
                                    "level" : 3,
                                    "parent" : "Medical Service"
                                },
                            "Optician" : {
                                "level" : 2,
                                "parent" : "Medical & Health"
                            },
                            "Pharmaceutical Company" : {
                                "level" : 2,
                                "parent" : "Medical & Health"
                            },
                            "Pharmacy / Drugstore" : {
                                "level" : 2,
                                "parent" : "Medical & Health"
                            },
                                "Medical Supply Store" : {
                                    "level" : 3,
                                    "parent" : "Pharmacy / Drugstore"
                                },
                                "Vitamin Supplement Shop" : {
                                    "level" : 3,
                                    "parent" : "Pharmacy / Drugstore"
                                },
                            "Therapist" : {
                                "level" : 2,
                                "parent" : "Medical & Health"
                            },
                                "Counselor" : {
                                    "level" : 3,
                                    "parent" : "Therapist"
                                },
                                "Family Therapist" : {
                                    "level" : 3,
                                    "parent" : "Therapist"
                                },
                                "Marriage Therapist" : {
                                    "level" : 3,
                                    "parent" : "Therapist"
                                },
                                "Occupational Therapist" : {
                                    "level" : 3,
                                    "parent" : "Therapist"
                                },
                                "Physical Therapist" : {
                                    "level" : 3,
                                    "parent" : "Therapist"
                                },
                                "Psychotherapist" : {
                                    "level" : 3,
                                    "parent" : "Therapist"
                                },
                                "Sex Therapist" : {
                                    "level" : 3,
                                    "parent" : "Therapist"
                                },
                                "Speech Pathologist" : {
                                    "level" : 3,
                                    "parent" : "Therapist"
                                },
                                "Speech Therapist" : {
                                    "level" : 3,
                                    "parent" : "Therapist"
                                },
                                "Sport Psychologist" : {
                                    "level" : 3,
                                    "parent" : "Therapist"
                                },
                        "Non-Governmental Organization (NGO)" : {
                            "level" : 1,
                            "parent" : "Businesses"
                        },
                        "Nonprofit Organization" : {
                            "level" : 1,
                            "parent" : "Businesses"
                        },
                        "Public & Government Service" : {
                            "level" : 1,
                            "parent" : "Businesses"
                        },
                            "Automotive Registration Center" : {
                                "level" : 2,
                                "parent" : "Public & Government Service"
                            },
                            "Child Protective Service" : {
                                "level" : 2,
                                "parent" : "Public & Government Service"
                            },
                            "Community Center" : {
                                "level" : 2,
                                "parent" : "Public & Government Service"
                            },
                                "Senior Center" :  {
                                    "level" : 3,
                                    "parent" : "Community Center"
                                },
                            "Cultural Center" : {
                                "level" : 2,
                                "parent" : "Public & Government Service"
                            },
                            "DMV" : {
                                "level" : 2,
                                "parent" : "Public & Government Service"
                            },
                            "Defense Company" : {
                                "level" : 2,
                                "parent" : "Public & Government Service"
                            },
                            "Food Bank" : {
                                "level" : 2,
                                "parent" : "Public & Government Service"
                            },
                            "Housing & Homeless Shelter" : {
                                "level" : 2,
                                "parent" : "Public & Government Service"
                            },
                            "Law Enforcement Agency" : {
                                "level" : 2,
                                "parent" : "Public & Government Service"
                            },
                            "Library" : {
                                "level" : 2,
                                "parent" : "Public & Government Service"
                            },
                            "Passport & Visa Service" : {
                                "level" : 2,
                                "parent" : "Public & Government Service"
                            },
                            "Public Service" : {
                                "level" : 2,
                                "parent" : "Public & Government Service"
                            },
                            "Public Utility Company" : {
                                "level" : 2,
                                "parent" : "Public & Government Service"
                            },
                                "Electric Utility Provider" : {
                                    "level" : 3,
                                    "parent" : "Public Utility Company"
                                },
                                "Energy Company" : {
                                    "level" : 3,
                                    "parent" : "Public Utility Company"
                                },
                                "Internet Service Provider" : {
                                    "level" : 3,
                                    "parent" : "Public Utility Company"
                                },
                                "Television Service Provider" : {
                                    "level" : 3,
                                    "parent" : "Public Utility Company"
                                },
                                "Water Utility Company" : {
                                    "level" : 3,
                                    "parent" : "Public Utility Company"
                                },
                            "Social Service" : {
                                "level" : 2,
                                "parent" : "Public & Government Service"
                            },
                            "Waste Management Company" : {
                                "level" : 2,
                                "parent" : "Public & Government Service"
                            },
                        "Real Estate" : {
                            "level" : 1,
                            "parent" : "Businesses"
                        },
                            "Commercial Real Estate Agency" : {
                                "level" : 2,
                                "parent" : "Real Estate"
                            },
                            "Escrow Service" : {
                                "level" : 2,
                                "parent" : "Real Estate"
                            },
                            "Home Inspector" : {
                                "level" : 2,
                                "parent" : "Real Estate"
                            },
                            "Home Staging Service" : {
                                "level" : 2,
                                "parent" : "Real Estate"
                            },
                            "Housing Assistance Service" : {
                                "level" : 2,
                                "parent" : "Real Estate"
                            },
                            "Mobile Home Dealer" : {
                                "level" : 2,
                                "parent" : "Real Estate"
                            },
                            "Mobile Home Park" : {
                                "level" : 2,
                                "parent" : "Real Estate"
                            },
                            "Mortgage Brokers" : {
                                "level" : 2,
                                "parent" : "Real Estate"
                            },
                            "Property Management Company" : {
                                "level" : 2,
                                "parent" : "Real Estate"
                            },
                            "Real Estate Agent" : {
                                "level" : 2,
                                "parent" : "Real Estate"
                            },
                            "Real Estate Appraiser" : {
                                "level" : 2,
                                "parent" : "Real Estate"
                            },
                            "Real Estate Company" : {
                                "level" : 2,
                                "parent" : "Real Estate"
                            },
                            "Real Estate Developer" : {
                                "level" : 2,
                                "parent" : "Real Estate"
                            },
                            "Real Estate Investment Firm" : {
                                "level" : 2,
                                "parent" : "Real Estate"
                            },
                            "Real Estate Service" : {
                                "level" : 2,
                                "parent" : "Real Estate"
                            },
                            "Real Estate Title & Development" : {
                                "level" : 2,
                                "parent" : "Real Estate"
                            },
                        "Science, Technology & Engineering" : {
                            "level" : 1,
                            "parent" : "Businesses"
                        },
                            "Aerospace Company" : {
                                "level" : 2,
                                "parent" : "Science, Technology & Engineering"
                            },
                            "Biotechnology Company" : {
                                "level" : 2,
                                "parent" : "Science, Technology & Engineering"
                            },
                            "Chemical Company" : {
                                "level" : 2,
                                "parent" : "Science, Technology & Engineering"
                            },
                                "Gas & Chemical Service" : {
                                    "level" : 3,
                                    "parent" : "Chemical Company"
                                },
                                "Petroleum Service" : {
                                    "level" : 3,
                                    "parent" : "Chemical Company"
                                },
                            "Engineering Service" : {
                                "level" : 2,
                                "parent" : "Science, Technology & Engineering"
                            },
                            "Information Technology Company" : {
                                "level" : 2,
                                "parent" : "Science, Technology & Engineering"
                            },
                                "Computer Company" : {
                                    "level" : 3,
                                    "parent" : "Information Technology Company"
                                },
                                "Electronics Company" : {
                                    "level" : 3,
                                    "parent" : "Information Technology Company"
                                },
                                "Internet Company" : {
                                    "level" : 3,
                                    "parent" : "Information Technology Company"
                                },
                                "Software Company" : {
                                    "level" : 3,
                                    "parent" : "Information Technology Company"
                                },
                                "Telecommunication Company" : {
                                    "level" : 3,
                                    "parent" : "Information Technology Company"
                                },
                                    "Cable & Satellite Company" : {
                                        "level" : 4,
                                        "parent" : "Telecommunication Company"
                                    },
                            "Robotics Company" : {
                                "level" : 2,
                                "parent" : "Science, Technology & Engineering"
                            },
                            "Solar Energy Company" : {
                                "level" : 2,
                                "parent" : "Science, Technology & Engineering"
                            },
                            "Structural Engineer" : {
                                "level" : 2,
                                "parent" : "Science, Technology & Engineering"
                            },
                            "Surveyor" : {
                                "level" : 2,
                                "parent" : "Science, Technology & Engineering"
                            },
                        "Shopping & Retail" : {
                            "level" : 1,
                            "parent" : "Businesses"
                        },
                            "Antique Store" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Apparel & Clothing" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                                "Accessories" : {
                                    "level" : 3,
                                    "parent" : "Apparel & Clothing"
                                },
                                    "Bags & Luggage Store" : {
                                        "level" : 4,
                                        "parent" : "Accessories"
                                    },
                                    "Hat Store" : {
                                        "level" : 4,
                                        "parent" : "Accessories"
                                    },
                                    "Jewelry & Watches Store" : {
                                        "level" : 4,
                                        "parent" : "Accessories"
                                    },
                                    "Sunglasses & Eyewear Store" : {
                                        "level" : 4,
                                        "parent" : "Accessories"
                                    },
                                "Clothing Store" : {
                                    "level" : 3,
                                    "parent" : "Apparel & Clothing"
                                },
                                    "Baby & Children's Clothing Store" : {
                                        "level" : 4,
                                        "parent" : "Clothing Store"
                                    },
                                    "Bridal Shop" : {
                                        "level" : 4,
                                        "parent" : "Clothing Store"
                                    },
                                    "Costume Shop" : {
                                        "level" : 4,
                                        "parent" : "Clothing Store"
                                    },
                                    "Footwear Store" : {
                                        "level" : 4,
                                        "parent" : "Clothing Store"
                                    },
                                    "Lingerie & Underwear Store" : {
                                        "level" : 4,
                                        "parent" : "Clothing Store"
                                    },
                                    "Maternity & Nursing Clothing Store" : {
                                        "level" : 4,
                                        "parent" : "Clothing Store"
                                    },
                                    "Men's Clothing Store" : {
                                        "level" : 4,
                                        "parent" : "Clothing Store"
                                    },
                                    "Sportswear Store" : {
                                        "level" : 4,
                                        "parent" : "Clothing Store"
                                    },
                                    "Swimwear Store" : {
                                        "level" : 4,
                                        "parent" : "Clothing Store"
                                    },
                                    "Women's Clothing Store" : {
                                        "level" : 4,
                                        "parent" : "Clothing Store"
                                    },
                            "Arts & Crafts Store" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Auction House" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Beauty Store" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                                "Beauty Supply Store" : {
                                    "level" : 3,
                                    "parent" : "Beauty Store"
                                },
                                "Cosmetics Store" : {
                                    "level" : 3,
                                    "parent" : "Beauty Store"
                                },
                                "Wig Store" : {
                                    "level" : 3,
                                    "parent" : "Beauty Store"
                                },
                            "Big Box Retailer" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Bookstore" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                                "College / University Bookstore" : {
                                    "level" : 3,
                                    "parent" : "Bookstore"
                                },
                                "Comic Bookstore" : {
                                    "level" : 3,
                                    "parent" : "Bookstore"
                                },
                                "Independent Bookstore" : {
                                    "level" : 3,
                                    "parent" : "Bookstore"
                                },
                                "Religious Bookstore" : {
                                    "level" : 3,
                                    "parent" : "Bookstore"
                                },
                            "Boutique Store" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Collectibles Store" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Cultural Gifts Store" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Department Store" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Discount Store" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Duty-Free Shop" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "E-Cigarette Store" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Educational Supply Store" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Electronics Store" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                                "Audio Visual Equipment Store" : {
                                    "level" : 3,
                                    "parent" : "Electronics Store"
                                },
                                "Computer Store" : {
                                    "level" : 3,
                                    "parent" : "Electronics Store"
                                },
                            "Fabric Store" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Fireworks Retailer" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Flea Market" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Gift Shop" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Glass & Mirror Shop" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Gun Store" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Hobby Store" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Home & Garden Store" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                                "Appliance Store" : {
                                    "level" : 3,
                                    "parent" : "Home & Garden Store"
                                },
                                "Awning Supplier" : {
                                    "level" : 3,
                                    "parent" : "Home & Garden Store"
                                },
                                "Blinds & Curtains Store" : {
                                    "level" : 3,
                                    "parent" : "Home & Garden Store"
                                },
                                "Building Material Store" : {
                                    "level" : 3,
                                    "parent" : "Home & Garden Store"
                                },
                                "Cabinet & Countertop Store" : {
                                    "level" : 3,
                                    "parent" : "Home & Garden Store"
                                },
                                "Carpet & Flooring Store" : {
                                    "level" : 3,
                                    "parent" : "Home & Garden Store"
                                },
                                "Fireplace Store" : {
                                    "level" : 3,
                                    "parent" : "Home & Garden Store"
                                },
                                "Furniture Store" : {
                                    "level" : 3,
                                    "parent" : "Home & Garden Store"
                                },
                                "Garden Center" : {
                                    "level" : 3,
                                    "parent" : "Home & Garden Store"
                                },
                                "Hardware Store" : {
                                    "level" : 3,
                                    "parent" : "Home & Garden Store"
                                },
                                "Home Goods Store" : {
                                    "level" : 3,
                                    "parent" : "Home & Garden Store"
                                },
                                "Home Theater Store" : {
                                    "level" : 3,
                                    "parent" : "Home & Garden Store"
                                },
                                "Lighting Store" : {
                                    "level" : 3,
                                    "parent" : "Home & Garden Store"
                                },
                                "Mattress Store" : {
                                    "level" : 3,
                                    "parent" : "Home & Garden Store"
                                },
                                "Nurseries & Gardening Store" : {
                                    "level" : 3,
                                    "parent" : "Home & Garden Store"
                                },
                            "Lottery Retailer" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Mattress Wholesaler" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Mobile Phone Shop" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Movie & Music Store" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Moving Supply Store" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Musical Instrument Store" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Newsstand" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Night Market" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Office Equipment Store" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Outdoor & Sporting Goods Company" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Outlet Store" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Party Supply & Rental Shop" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                                "Carnival Supply Store" : {
                                    "level" : 3,
                                    "parent" : "Party Supply & Rental Shop"
                                },
                            "Pawn Shop" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Pet Store" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                                "Aquatic Pet Store" : {
                                    "level" : 3,
                                    "parent" : "Pet Store"
                                },
                                "Reptile Pet Store" : {
                                    "level" : 3,
                                    "parent" : "Pet Store"
                                },
                            "Pop-Up Shop" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Rent to Own Store" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Restaurant Supply Store" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Retail Company" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Seasonal Store" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Shopping Mall" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Shopping Service" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Souvenir Shop" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Sporting Goods Store" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                                "Archery Shop" : {
                                    "level" : 3,
                                    "parent" : "Sporting Goods Store"
                                },
                                "Bicycle Shop" : {
                                    "level" : 3,
                                    "parent" : "Sporting Goods Store"
                                },
                                "Fishing Store" : {
                                    "level" : 3,
                                    "parent" : "Sporting Goods Store"
                                },
                                "Mountain Biking Shop" : {
                                    "level" : 3,
                                    "parent" : "Sporting Goods Store"
                                },
                                "Outdoor Equipment Store" : {
                                    "level" : 3,
                                    "parent" : "Sporting Goods Store"
                                },
                                "Skate Shop" : {
                                    "level" : 3,
                                    "parent" : "Sporting Goods Store"
                                },
                                "Ski & Snowboard Shop" : {
                                    "level" : 3,
                                    "parent" : "Sporting Goods Store"
                                },
                                "Surf Shop" : {
                                    "level" : 3,
                                    "parent" : "Sporting Goods Store"
                                },
                            "Thrift & Consignment Store" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Tobacco Store" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Toy Store" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Trophies & Engraving Shop" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Video Game Store" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Vintage Store" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                            "Wholesale & Supply Store" : {
                                "level" : 2,
                                "parent" : "Shopping & Retail"
                            },
                        "Sports & Recreation" : {
                            "level" : 1,
                            "parent" : "Businesses"
                        },
                            "Sports & Fitness Instruction" : {
                                "level" : 2,
                                "parent" : "Sports & Recreation"
                            },
                                "Boat / Sailing Instructor" : {
                                    "level" : 3,
                                    "parent" : "Sports & Fitness Instruction"
                                },
                                "Coach" : {
                                    "level" : 3,
                                    "parent" : "Sports & Fitness Instruction"
                                },
                                "Fitness Trainer" : {
                                    "level" : 3,
                                    "parent" : "Sports & Fitness Instruction"
                                },
                                "Golf Instructor" : {
                                    "level" : 3,
                                    "parent" : "Sports & Fitness Instruction"
                                },
                                "Horse Riding School" : {
                                    "level" : 3,
                                    "parent" : "Sports & Fitness Instruction"
                                },
                                "Scuba Instructor" : {
                                    "level" : 3,
                                    "parent" : "Sports & Fitness Instruction"
                                },
                                "Ski & Snowboard School" : {
                                    "level" : 3,
                                    "parent" : "Sports & Fitness Instruction"
                                },
                                "Swimming Instructor" : {
                                    "level" : 3,
                                    "parent" : "Sports & Fitness Instruction"
                                },
                            "Sports & Recreation Venue" : {
                                "level" : 2,
                                "parent" : "Sports & Recreation"
                            },
                                "ATV Recreation Park" : {
                                    "level" : 3,
                                    "parent" : "Sports & Recreation Venue"
                                },
                                "Archery Range" : {
                                    "level" : 3,
                                    "parent" : "Sports & Recreation Venue"
                                },
                                "Badminton Court" : {
                                    "level" : 3,
                                    "parent" : "Sports & Recreation Venue"
                                },
                                "Baseball Field" : {
                                    "level" : 3,
                                    "parent" : "Sports & Recreation Venue"
                                },
                                "Basketball Court" : {
                                    "level" : 3,
                                    "parent" : "Sports & Recreation Venue"
                                },
                                "Batting Cage" : {
                                    "level" : 3,
                                    "parent" : "Sports & Recreation Venue"
                                },
                                "Bowling Alley" : {
                                    "level" : 3,
                                    "parent" : "Sports & Recreation Venue"
                                },
                                "Disc Golf Course" : {
                                    "level" : 3,
                                    "parent" : "Sports & Recreation Venue"
                                },
                                "Driving Range" : {
                                    "level" : 3,
                                    "parent" : "Sports & Recreation Venue"
                                },
                                "Equestrian Center" : {
                                    "level" : 3,
                                    "parent" : "Sports & Recreation Venue"
                                },
                                "Fencing Club" : {
                                    "level" : 3,
                                    "parent" : "Sports & Recreation Venue"
                                },
                                "Fitness Venue" : {
                                    "level" : 3,
                                    "parent" : "Sports & Recreation Venue"
                                },
                                    "Boxing Studio" : {
                                        "level" : 4,
                                        "parent" : "Fitness Venue"
                                    },
                                    "Cycling Studio" : {
                                        "level" : 4,
                                        "parent" : "Fitness Venue"
                                    },
                                    "Dance Studio" : {
                                        "level" : 4,
                                        "parent" : "Fitness Venue"
                                    },
                                    "Fitness Boot Camp" : {
                                        "level" : 4,
                                        "parent" : "Fitness Venue"
                                    },
                                    "Gym/Physical Fitness Center" : {
                                        "level" : 4,
                                        "parent" : "Fitness Venue"
                                    },
                                    "Martial Arts School" : {
                                        "level" : 4,
                                        "parent" : "Fitness Venue"
                                    },
                                    "Pilates Studio" : {
                                        "level" : 4,
                                        "parent" : "Fitness Venue"
                                    },
                                    "Tai Chi Studio" : {
                                        "level" : 4,
                                        "parent" : "Fitness Venue"
                                    },
                                    "Yoga Studio" : {
                                        "level" : 4,
                                        "parent" : "Fitness Venue"
                                    },
                                "Flyboarding Center" : {
                                    "level" : 3,
                                    "parent" : "Sports & Recreation Venue"
                                },
                                "Go-Kart Track" : {
                                    "level" : 3,
                                    "parent" : "Sports & Recreation Venue"
                                },
                                "Golf Course & Country Club" : {
                                    "level" : 3,
                                    "parent" : "Sports & Recreation Venue"
                                },
                                "Gun Range" : {
                                    "level" : 3,
                                    "parent" : "Sports & Recreation Venue"
                                },
                                "Gymnastics Center" : {
                                    "level" : 3,
                                    "parent" : "Sports & Recreation Venue"
                                },
                                "Hang Gliding Center" : {
                                    "level" : 3,
                                    "parent" : "Sports & Recreation Venue"
                                },
                                "Hockey Field / Rink" : {
                                    "level" : 3,
                                    "parent" : "Sports & Recreation Venue"
                                },
                                "Horseback Riding Center" : {
                                    "level" : 3,
                                    "parent" : "Sports & Recreation Venue"
                                },
                                "Ice Skating Rink" : {
                                    "level" : 3,
                                    "parent" : "Sports & Recreation Venue"
                                },
                                "Kiteboarding Center" : {
                                    "level" : 3,
                                    "parent" : "Sports & Recreation Venue"
                                },
                                "Laser Tag Center" : {
                                    "level" : 3,
                                    "parent" : "Sports & Recreation Venue"
                                },
                                "Miniature Golf Course" : {
                                    "level" : 3,
                                    "parent" : "Sports & Recreation Venue"
                                },
                                "Paddleboarding Center" : {
                                    "level" : 3,
                                    "parent" : "Sports & Recreation Venue"
                                },
                                "Paintball Center" : {
                                    "level" : 3,
                                    "parent" : "Sports & Recreation Venue"
                                },
                                "Public Swimming Pool" : {
                                    "level" : 3,
                                    "parent" : "Sports & Recreation Venue"
                                },
                                "Racquetball Court" : {
                                    "level" : 3,
                                    "parent" : "Sports & Recreation Venue"
                                },
                                "Rafting/Kayaking Center" : {
                                    "level" : 3,
                                    "parent" : "Sports & Recreation Venue"
                                },
                                "Recreation Center" : {
                                    "level" : 3,
                                    "parent" : "Sports & Recreation Venue"
                                },
                                "Rock Climbing Gym" : {
                                    "level" : 3,
                                    "parent" : "Sports & Recreation Venue"
                                },
                                "Rodeo" : {
                                    "level" : 3,
                                    "parent" : "Sports & Recreation Venue"
                                },
                                "Roller Skating Rink" : {
                                    "level" : 3,
                                    "parent" : "Sports & Recreation Venue"
                                },
                                "Rugby Pitch" : {
                                    "level" : 3,
                                    "parent" : "Sports & Recreation Venue"
                                },
                                "Scuba Diving Center" : {
                                    "level" : 3,
                                    "parent" : "Sports & Recreation Venue"
                                },
                                "Shooting/Hunting Range" : {
                                    "level" : 3,
                                    "parent" : "Sports & Recreation Venue"
                                },
                                "Skateboard Park" : {
                                    "level" : 3,
                                    "parent" : "Sports & Recreation Venue"
                                },
                                "Ski Resort" : {
                                    "level" : 3,
                                    "parent" : "Sports & Recreation Venue"
                                },
                                "Skydiving Center" : {
                                    "level" : 3,
                                    "parent" : "Sports & Recreation Venue"
                                },
                                "Soccer Field" : {
                                    "level" : 3,
                                    "parent" : "Sports & Recreation Venue"
                                },
                                "Squash Court" : {
                                    "level" : 3,
                                    "parent" : "Sports & Recreation Venue"
                                },
                                "Tennis Court" : {
                                    "level" : 3,
                                    "parent" : "Sports & Recreation Venue"
                                },
                                "Volleyball Court" : {
                                    "level" : 3,
                                    "parent" : "Sports & Recreation Venue"
                                },
                            "Sports League" : {
                                "level" : 2,
                                "parent" : "Sports & Recreation"
                            },
                                "Amateur Sports League" : {
                                    "level" : 3,
                                    "parent" : "Sports League"
                                },
                                "Esports League" : {
                                    "level" : 3,
                                    "parent" : "Sports League"
                                },
                                "Professional Sports League" : {
                                    "level" : 3,
                                    "parent" : "Sports League"
                                },
                                "School Sports League" : {
                                    "level" : 3,
                                    "parent" : "Sports League"
                                },
                            "Sports Team" : {
                                "level" : 2,
                                "parent" : "Sports & Recreation"
                            },
                                "Amateur Sports Team" : {
                                    "level" : 3,
                                    "parent" : "Sports Team"
                                },
                                "Esports Team" : {
                                    "level" : 3,
                                    "parent" : "Sports Team"
                                },
                                "Professional Sports Team" : {
                                    "level" : 3,
                                    "parent" : "Sports Team"
                                },
                                "School Sports Team" : {
                                    "level" : 3,
                                    "parent" : "Sports Team"
                                },
                            "Stadium, Arena & Sports Venue" : {
                                "level" : 2,
                                "parent" : "Sports & Recreation"
                            },
                                "Baseball Stadium" : {
                                    "level" : 3,
                                    "parent" : "Stadium, Arena & Sports Venue"
                                },
                                "Basketball Stadium" : {
                                    "level" : 3,
                                    "parent" : "Stadium, Arena & Sports Venue"
                                },
                                "Cricket Ground" : {
                                    "level" : 3,
                                    "parent" : "Stadium, Arena & Sports Venue"
                                },
                                "Football Stadium" : {
                                    "level" : 3,
                                    "parent" : "Stadium, Arena & Sports Venue"
                                },
                                "Hockey Arena" : {
                                    "level" : 3,
                                    "parent" : "Stadium, Arena & Sports Venue"
                                },
                                "Rugby Stadium" : {
                                    "level" : 3,
                                    "parent" : "Stadium, Arena & Sports Venue"
                                },
                                "Soccer Stadium" : {
                                    "level" : 3,
                                    "parent" : "Stadium, Arena & Sports Venue"
                                },
                                "Tennis Stadium" : {
                                    "level" : 3,
                                    "parent" : "Stadium, Arena & Sports Venue"
                                },
                                "Track Stadium" : {
                                    "level" : 3,
                                    "parent" : "Stadium, Arena & Sports Venue"
                                },
                        "Travel & Transportation" : {
                            "level" : 1,
                            "parent" : "Businesses"
                        },
                            "Airline Company" : {
                                "level" : 2,
                                "parent" : "Travel & Transportation"
                            },
                            "Airline Industry Service" : {
                                "level" : 2,
                                "parent" : "Travel & Transportation"
                            },
                            "Boat/Ferry Company" : {
                                "level" : 2,
                                "parent" : "Travel & Transportation"
                            },
                            "Bus Line" : {
                                "level" : 2,
                                "parent" : "Travel & Transportation"
                            },
                            "Cruise Line" : {
                                "level" : 2,
                                "parent" : "Travel & Transportation"
                            },
                            "Railroad Company" : {
                                "level" : 2,
                                "parent" : "Travel & Transportation"
                            },
                            "Rental Shop" : {
                                "level" : 2,
                                "parent" : "Travel & Transportation"
                            },
                                "ATV Rental" : {
                                    "level" : 3,
                                    "parent" : "Rental Shop"
                                },
                                "Bike Rental" : {
                                    "level" : 3,
                                    "parent" : "Rental Shop"
                                },
                                "Boat Rental" : {
                                    "level" : 3,
                                    "parent" : "Rental Shop"
                                },
                                "Canoe & Kayak Rental" : {
                                    "level" : 3,
                                    "parent" : "Rental Shop"
                                },
                                "Car Rental" : {
                                    "level" : 3,
                                    "parent" : "Rental Shop"
                                },
                                "Exotic Car Rental" : {
                                    "level" : 3,
                                    "parent" : "Rental Shop"
                                },
                                "Jet Ski Rental" : {
                                    "level" : 3,
                                    "parent" : "Rental Shop"
                                },
                                "RV Rental" : {
                                    "level" : 3,
                                    "parent" : "Rental Shop"
                                },
                                "Scooter Rental" : {
                                    "level" : 3,
                                    "parent" : "Rental Shop"
                                },
                                "Trailer Rental" : {
                                    "level" : 3,
                                    "parent" : "Rental Shop"
                                },
                                "Truck Rental" : {
                                    "level" : 3,
                                    "parent" : "Rental Shop"
                                },
                            "Transit Hub" : {
                                "level" : 2,
                                "parent" : "Travel & Transportation"
                            },
                                "Airport" : {
                                    "level" : 3,
                                    "parent" : "Transit Hub"
                                },
                                "Airport Gate" : {
                                    "level" : 3,
                                    "parent" : "Transit Hub"
                                },
                                "Airport Lounge" : {
                                    "level" : 3,
                                    "parent" : "Transit Hub"
                                },
                                "Airport Terminal" : {
                                    "level" : 3,
                                    "parent" : "Transit Hub"
                                },
                                "Balloonport" : {
                                    "level" : 3,
                                    "parent" : "Transit Hub"
                                },
                                "Bus Station" : {
                                    "level" : 3,
                                    "parent" : "Transit Hub"
                                },
                                "Heliport" : {
                                    "level" : 3,
                                    "parent" : "Transit Hub"
                                },
                                "Seaplane Base" : {
                                    "level" : 3,
                                    "parent" : "Transit Hub"
                                },
                                "Train Station" : {
                                    "level" : 3,
                                    "parent" : "Transit Hub"
                                },
                                    "Light Rail Station" : {
                                        "level" : 4,
                                        "parent" : "Train Station"
                                    },
                                    "Railway Station" : {
                                        "level" : 4,
                                        "parent" : "Train Station"
                                    },
                                    "Subway Station" : {
                                        "level" : 4,
                                        "parent" : "Train Station"
                                    },
                                "Transit Stop" : {
                                    "level" : 3,
                                    "parent" : "Transit Hub"
                                },
                            "Transportation Service" : {
                                "level" : 2,
                                "parent" : "Travel & Transportation"
                            },
                                "Airport Shuttle Service" : {
                                    "level" : 3,
                                    "parent" : "Transportation Service"
                                },
                                "Charter Bus Service" : {
                                    "level" : 3,
                                    "parent" : "Transportation Service"
                                },
                                "Fishing Charter" : {
                                    "level" : 3,
                                    "parent" : "Transportation Service"
                                },
                                "Limo Service" : {
                                    "level" : 3,
                                    "parent" : "Transportation Service"
                                },
                                "Private Plane Charter" : {
                                    "level" : 3,
                                    "parent" : "Transportation Service"
                                },
                                "Rideshare Service" : {
                                    "level" : 3,
                                    "parent" : "Transportation Service"
                                },
                                "School Transportation Service" : {
                                    "level" : 3,
                                    "parent" : "Transportation Service"
                                },
                                "Taxi Service" : {
                                    "level" : 3,
                                    "parent" : "Transportation Service"
                                },
                            "Travel Company" : {
                                "level" : 2,
                                "parent" : "Travel & Transportation"
                            },
                                "Tour Agency" : {
                                    "level" : 3,
                                    "parent" : "Travel Company"
                                },
                                    "Architectural Tour Agency" : {
                                        "level" : 4,
                                        "parent" : "Tour Agency"
                                    },
                                    "Art Tour Agency" : {
                                        "level" : 4,
                                        "parent" : "Tour Agency"
                                    },
                                    "Boat Tour Agency" : {
                                        "level" : 4,
                                        "parent" : "Tour Agency"
                                    },
                                    "Bus Tour Agency" : {
                                        "level" : 4,
                                        "parent" : "Tour Agency"
                                    },
                                    "Eco Tour Agency" : {
                                        "level" : 4,
                                        "parent" : "Tour Agency"
                                    },
                                    "Food Tour Agency" : {
                                        "level" : 4,
                                        "parent" : "Tour Agency"
                                    },
                                    "Historical Tour Agency" : {
                                        "level" : 4,
                                        "parent" : "Tour Agency"
                                    },
                                    "Horse-Drawn Carriage Service" : {
                                        "level" : 4,
                                        "parent" : "Tour Agency"
                                    },
                                    "Hot Air Balloon Tour Agency" : {
                                        "level" : 4,
                                        "parent" : "Tour Agency"
                                    },
                                    "Pedicab Service" : {
                                        "level" : 4,
                                        "parent" : "Tour Agency"
                                    },
                                    "Sightseeing Tour Agency" : {
                                        "level" : 4,
                                        "parent" : "Tour Agency"
                                    },
                                    "Tour Guide" : {
                                        "level" : 4,
                                        "parent" : "Tour Agency"
                                    },
                                "Travel Agency" : {
                                    "level" : 3,
                                    "parent" : "Travel Company"
                                },
                                    "Cruise Agency" : {
                                        "level" : 4,
                                        "parent" : "Travel Agency"
                                    },
                            "Travel Service" : {
                                "level" : 2,
                                "parent" : "Travel & Transportation"
                            },
                                "Luggage Service": {
                                    "level" : 3,
                                    "parent" : "Travel Service"
                                },
                                "Tourist Information Center": {
                                    "level" : 3,
                                    "parent" : "Travel Service"
                                },
                    "Community Organization" : {
                        "level" : 0
                    },
                        "Armed Forces" : {
                            "level" : 1,
                            "parent" : "Community Organization"
                        },
                        "Charity Organization" : {
                            "level" : 1,
                            "parent" : "Community Organization"
                        },
                        "Community Service" : {
                            "level" : 1,
                            "parent" : "Community Organization"
                        },
                        "Country Club / Clubhouse" : {
                            "level" : 1,
                            "parent" : "Community Organization"
                        },
                        "Environmental Conservation Organization" : {
                            "level" : 1,
                            "parent" : "Community Organization"
                        },
                        "Labor Union" : {
                            "level" : 1,
                            "parent" : "Community Organization"
                        },
                        "Private Members Club" : {
                            "level" : 1,
                            "parent" : "Community Organization"
                        },
                        "Religious Organization" : {
                            "level" : 1,
                            "parent" : "Community Organization"
                        },
                        "Social Club" : {
                            "level" : 1,
                            "parent" : "Community Organization"
                        },
                        "Sorority & Fraternity" : {
                            "level" : 1,
                            "parent" : "Community Organization"
                        },
                        "Sports Club" : {
                            "level" : 1,
                            "parent" : "Community Organization"
                        },
                        "Youth Organization" : {
                            "level" : 1,
                            "parent" : "Community Organization"
                        },
                    "Interest" : {
                        "level" : 0
                    },
                        "Literary Arts" : {
                            "level" : 1,
                            "parent" : "Interest"
                        },
                        "Performance Art" : {
                            "level" : 1,
                            "parent" : "Interest"
                        },
                        "Performing Arts" : {
                            "level" : 1,
                            "parent" : "Interest"
                        },
                        "Science" : {
                            "level" : 1,
                            "parent" : "Interest"
                        },
                        "Sports" : {
                            "level" : 1,
                            "parent" : "Interest"
                        },
                        "Visual Arts" : {
                            "level" : 1,
                            "parent" : "Interest"
                        },
                    "Media" : {
                        "level" : 0
                    },
                        "Art" : {
                            "level" : 1,
                            "parent" : "Media"
                        },
                        "Books & Magazines" : {
                            "level" : 1,
                            "parent" : "Media"
                        },
                            "Article" : {
                                "level" : 2,
                                "parent" : "Books & Magazines"
                            },
                            "Book" : {
                                "level" : 2,
                                "parent" : "Books & Magazines"
                            },
                            "Book Genre" : {
                                "level" : 2,
                                "parent" : "Books & Magazines"
                            },
                            "Book Series" : {
                                "level" : 2,
                                "parent" : "Books & Magazines"
                            },
                            "Magazine" : {
                                "level" : 2,
                                "parent" : "Books & Magazines"
                            },
                            "Newspaper" : {
                                "level" : 2,
                                "parent" : "Books & Magazines"
                            },
                        "Concert Tour" : {
                            "level" : 1,
                            "parent" : "Media"
                        },
                        "Media Restoration Service" : {
                            "level" : 1,
                            "parent" : "Media"
                        },
                            "Art Restoration Service" : {
                                "level" : 2,
                                "parent" : "Media Restoration Service"
                            },
                        "Music" : {
                            "level" : 1,
                            "parent" : "Media"
                        },
                            "Album" : {
                                "level" : 2,
                                "parent" : "Music"
                            },
                            "Choir" : {
                                "level" : 2,
                                "parent" : "Music"
                            },
                            "Music Award" : {
                                "level" : 2,
                                "parent" : "Music"
                            },
                            "Music Chart" : {
                                "level" : 2,
                                "parent" : "Music"
                            },
                            "Music Video" : {
                                "level" : 2,
                                "parent" : "Music"
                            },
                            "Musical Genre" : {
                                "level" : 2,
                                "parent" : "Music"
                            },
                            "Playlist" : {
                                "level" : 2,
                                "parent" : "Music"
                            },
                            "Podcast" : {
                                "level" : 2,
                                "parent" : "Music"
                            },
                            "Record Label" : {
                                "level" : 2,
                                "parent" : "Music"
                            },
                            "Song" : {
                                "level" : 2,
                                "parent" : "Music"
                            },
                            "Symphony" : {
                                "level" : 2,
                                "parent" : "Music"
                            },
                        "Show" : {
                            "level" : 1,
                            "parent" : "Media"
                        },
                        "TV & Movies" : {
                            "level" : 1,
                            "parent" : "Media"
                        },
                            "Episode" : {
                                "level" : 2,
                                "parent" : "TV & Movies"
                            },
                            "Movie" : {
                                "level" : 2,
                                "parent" : "TV & Movies"
                            },
                            "Movie Character" : {
                                "level" : 2,
                                "parent" : "TV & Movies"
                            },
                            "Movie Genre" : {
                                "level" : 2,
                                "parent" : "TV & Movies"
                            },
                            "One-Time TV Program" : {
                                "level" : 2,
                                "parent" : "TV & Movies"
                            },
                            "TV" : {
                                "level" : 2,
                                "parent" : "TV & Movies"
                            },
                            "TV Channel" : {
                                "level" : 2,
                                "parent" : "TV & Movies"
                            },
                            "TV Genre" : {
                                "level" : 2,
                                "parent" : "TV & Movies"
                            },
                            "TV Network" : {
                                "level" : 2,
                                "parent" : "TV & Movies"
                            },
                            "TV Season" : {
                                "level" : 2,
                                "parent" : "TV & Movies"
                            },
                            "TV Show" : {
                                "level" : 2,
                                "parent" : "TV & Movies"
                            },
                            "TV/Movie Award" : {
                                "level" : 2,
                                "parent" : "TV & Movies"
                            },
                            "Video" : {
                                "level" : 2,
                                "parent" : "TV & Movies"
                            },
                        "Theatrical Play" : {
                            "level" : 1,
                            "parent" : "Media"
                        },
                        "Theatrical Productions" : {
                            "level" : 1,
                            "parent" : "Media"
                        },
                    "Non-Business Places" : {
                        "level" : 0
                    },
                        "Automated Teller Machine (ATM)" : {
                            "level" : 1,
                            "parent" : "Non-Business Places"
                        },
                        "Campus Building" : {
                            "level" : 1,
                            "parent" : "Non-Business Places"
                        },
                        "City Infrastructure" : {
                            "level" : 1,
                            "parent" : "Non-Business Places"
                        },
                            "Bridge" : {
                                "level" : 2,
                                "parent" : "City Infrastructure"
                            },
                            "Canal" : {
                                "level" : 2,
                                "parent" : "City Infrastructure"
                            },
                            "Highway" : {
                                "level" : 2,
                                "parent" : "City Infrastructure"
                            },
                            "Lighthouse" : {
                                "level" : 2,
                                "parent" : "City Infrastructure"
                            },
                            "Marina" : {
                                "level" : 2,
                                "parent" : "City Infrastructure"
                            },
                            "Pier" : {
                                "level" : 2,
                                "parent" : "City Infrastructure"
                            },
                            "Promenade" : {
                                "level" : 2,
                                "parent" : "City Infrastructure"
                            },
                            "Quay" : {
                                "level" : 2,
                                "parent" : "City Infrastructure"
                            },
                            "Street" : {
                                "level" : 2,
                                "parent" : "City Infrastructure"
                            },
                            "Transit System" : {
                                "level" : 2,
                                "parent" : "City Infrastructure"
                            },
                            "Weather Station" : {
                                "level" : 2,
                                "parent" : "City Infrastructure"
                            },
                        "Landmark & Historical Place" : {
                            "level" : 1,
                            "parent" : "Non-Business Places"
                        },
                            "Monument" : {
                                "level" : 2,
                                "parent" : "Landmark & Historical Place"
                            },
                            "Statue & Fountain" : {
                                "level" : 2,
                                "parent" : "Landmark & Historical Place"
                            },
                        "Locality" : {
                            "level" : 1,
                            "parent" : "Non-Business Places"
                        },
                            "Borough" : {
                                "level" : 2,
                                "parent" : "Locality"
                            },
                            "Cemetery" : {
                                "level" : 2,
                                "parent" : "Locality"
                            },
                                "Pet Cemetery": {
                                    "level" : 3,
                                    "parent" : "Cemetery"
                                },
                            "City" : {
                                "level" : 2,
                                "parent" : "Locality"
                            },
                            "Congressional District" : {
                                "level" : 2,
                                "parent" : "Locality"
                            },
                            "Continental Region" : {
                                "level" : 2,
                                "parent" : "Locality"
                            },
                            "Country/Region" : {
                                "level" : 2,
                                "parent" : "Locality"
                            },
                            "County" : {
                                "level" : 2,
                                "parent" : "Locality"
                            },
                            "Designated Market Area" : {
                                "level" : 2,
                                "parent" : "Locality"
                            },
                            "Geo Entity" : {
                                "level" : 2,
                                "parent" : "Locality"
                            },
                            "Harbor" : {
                                "level" : 2,
                                "parent" : "Locality"
                            },
                            "Large Geo Area" : {
                                "level" : 2,
                                "parent" : "Locality"
                            },
                            "Medium Geo Area" : {
                                "level" : 2,
                                "parent" : "Locality"
                            },
                            "Metro Area" : {
                                "level" : 2,
                                "parent" : "Locality"
                            },
                            "Neighborhood" : {
                                "level" : 2,
                                "parent" : "Locality"
                            },
                            "Port" : {
                                "level" : 2,
                                "parent" : "Locality"
                            },
                            "Postal Code" : {
                                "level" : 2,
                                "parent" : "Locality"
                            },
                            "Province" : {
                                "level" : 2,
                                "parent" : "Locality"
                            },
                            "Region" : {
                                "level" : 2,
                                "parent" : "Locality"
                            },
                            "Shopping District" : {
                                "level" : 2,
                                "parent" : "Locality"
                            },
                            "Small Geo Area" : {
                                "level" : 2,
                                "parent" : "Locality"
                            },
                            "State" : {
                                "level" : 2,
                                "parent" : "Locality"
                            },
                            "Subcity" : {
                                "level" : 2,
                                "parent" : "Locality"
                            },
                            "Subneighborhood" : {
                                "level" : 2,
                                "parent" : "Locality"
                            },
                            "Time zone" : {
                                "level" : 2,
                                "parent" : "Locality"
                            },
                            "Township" : {
                                "level" : 2,
                                "parent" : "Locality"
                            },
                            "Village" : {
                                "level" : 2,
                                "parent" : "Locality"
                            },
                        "Meeting Room" : {
                            "level" : 1,
                            "parent" : "Non-Business Places"
                        },
                        "Outdoor Recreation" : {
                            "level" : 1,
                            "parent" : "Non-Business Places"
                        },
                            "Fairground" : {
                                "level" : 2,
                                "parent" : "Outdoor Recreation"
                            },
                            "Geographical Place" : {
                                "level" : 2,
                                "parent" : "Outdoor Recreation"
                            },
                                "Bay" : {
                                    "level" : 3,
                                    "parent" : "Geographical Place"
                                },
                                "Beach" : {
                                    "level" : 3,
                                    "parent" : "Geographical Place"
                                },
                                "Cape" : {
                                    "level" : 3,
                                    "parent" : "Geographical Place"
                                },
                                "Cave" : {
                                    "level" : 3,
                                    "parent" : "Geographical Place"
                                },
                                "Continent" : {
                                    "level" : 3,
                                    "parent" : "Geographical Place"
                                },
                                "Desert" : {
                                    "level" : 3,
                                    "parent" : "Geographical Place"
                                },
                                "Fjord/Loch" : {
                                    "level" : 3,
                                    "parent" : "Geographical Place"
                                },
                                "Glacier" : {
                                    "level" : 3,
                                    "parent" : "Geographical Place"
                                },
                                "Hot Spring" : {
                                    "level" : 3,
                                    "parent" : "Geographical Place"
                                },
                                "Island" : {
                                    "level" : 3,
                                    "parent" : "Geographical Place"
                                },
                                "Lake" : {
                                    "level" : 3,
                                    "parent" : "Geographical Place"
                                },
                                "Mountain" : {
                                    "level" : 3,
                                    "parent" : "Geographical Place"
                                },
                                "Ocean" : {
                                    "level" : 3,
                                    "parent" : "Geographical Place"
                                },
                                "Pond" : {
                                    "level" : 3,
                                    "parent" : "Geographical Place"
                                },
                                "Reservoir" : {
                                    "level" : 3,
                                    "parent" : "Geographical Place"
                                },
                                "River" : {
                                    "level" : 3,
                                    "parent" : "Geographical Place"
                                },
                                "Volcano" : {
                                    "level" : 3,
                                    "parent" : "Geographical Place"
                                },
                                "Waterfall" : {
                                    "level" : 3,
                                    "parent" : "Geographical Place"
                                },
                            "Park" : {
                                "level" : 2,
                                "parent" : "Outdoor Recreation"
                            },
                                "Arboretum" : {
                                    "level" : 3,
                                    "parent" : "Park"
                                },
                                "Dog Park" : {
                                    "level" : 3,
                                    "parent" : "Park"
                                },
                                "Field" : {
                                    "level" : 3,
                                    "parent" : "Park"
                                },
                                "National Forest" : {
                                    "level" : 3,
                                    "parent" : "Park"
                                },
                                "National Park" : {
                                    "level" : 3,
                                    "parent" : "Park"
                                },
                                "Nature Preserve" : {
                                    "level" : 3,
                                    "parent" : "Park"
                                },
                                "Picnic Ground" : {
                                    "level" : 3,
                                    "parent" : "Park"
                                },
                                "Playground" : {
                                    "level" : 3,
                                    "parent" : "Park"
                                },
                                "Public Square / Plaza" : {
                                    "level" : 3,
                                    "parent" : "Park"
                                },
                                "State Park" : {
                                    "level" : 3,
                                    "parent" : "Park"
                                },
                            "Public Garden" : {
                                "level" : 2,
                                "parent" : "Outdoor Recreation"
                            },
                                "Botanical Garden" : {
                                    "level" : 3,
                                    "parent" : "Public Garden"
                                },
                                 "Community Garden" : {
                                    "level" : 3,
                                    "parent" : "Public Garden"
                                },
                                 "Rose Garden" : {
                                    "level" : 3,
                                    "parent" : "Public Garden"
                                },
                                 "Sculpture Garden" : {
                                    "level" : 3,
                                    "parent" : "Public Garden"
                                },
                            "Recreation Spot" : {
                                "level" : 2,
                                "parent" : "Outdoor Recreation"
                            },
                                "Bike Trail" : {
                                    "level" : 3,
                                    "parent" : "Recreation Spot"
                                },
                                "Diving Spot" : {
                                    "level" : 3,
                                    "parent" : "Recreation Spot"
                                },
                                "Fishing Spot" : {
                                    "level" : 3,
                                    "parent" : "Recreation Spot"
                                },
                                "Hiking Trail" : {
                                    "level" : 3,
                                    "parent" : "Recreation Spot"
                                },
                                "Rock Climbing Spot" : {
                                    "level" : 3,
                                    "parent" : "Recreation Spot"
                                },
                                "Snorkeling Spot" : {
                                    "level" : 3,
                                    "parent" : "Recreation Spot"
                                },
                                "Surfing Spot" : {
                                    "level" : 3,
                                    "parent" : "Recreation Spot"
                                },
                        "Public Toilet" : {
                            "level" : 1,
                            "parent" : "Non-Business Places"
                        },
                        "Religious Place of Worship" : {
                            "level" : 1,
                            "parent" : "Non-Business Places"
                        },
                            "Assemblies of God" : {
                                "level" : 2,
                                "parent" : "Religious Place of Worship"
                            },
                            "Buddhist Temple" : {
                                "level" : 2,
                                "parent" : "Religious Place of Worship"
                            },
                            "Church" : {
                                "level" : 2,
                                "parent" : "Religious Place of Worship"
                            },
                                "African Methodist Episcopal Church" : {
                                    "level" : 3,
                                    "parent" : "Church"
                                },
                                "Anglican Church" : {
                                    "level" : 3,
                                    "parent" : "Church"
                                },
                                "Apostolic Church" : {
                                    "level" : 3,
                                    "parent" : "Church"
                                },
                                "Baptist Church" : {
                                    "level" : 3,
                                    "parent" : "Church"
                                },
                                "Catholic Church" : {
                                    "level" : 3,
                                    "parent" : "Church"
                                },
                                "Charismatic Church" : {
                                    "level" : 3,
                                    "parent" : "Church"
                                },
                                "Christian Church" : {
                                    "level" : 3,
                                    "parent" : "Church"
                                },
                                "Christian Science Church" : {
                                    "level" : 3,
                                    "parent" : "Church"
                                },
                                "Church of Christ" : {
                                    "level" : 3,
                                    "parent" : "Church"
                                },
                                "Church of God" : {
                                    "level" : 3,
                                    "parent" : "Church"
                                },
                                "Church of Jesus Christ of Latter-day Saints" : {
                                    "level" : 3,
                                    "parent" : "Church"
                                },
                                "Congregational Church" : {
                                    "level" : 3,
                                    "parent" : "Church"
                                },
                                "Eastern Orthodox Church" : {
                                    "level" : 3,
                                    "parent" : "Church"
                                },
                                "Episcopal Church" : {
                                    "level" : 3,
                                    "parent" : "Church"
                                },
                                "Evangelical Church" : {
                                    "level" : 3,
                                    "parent" : "Church"
                                },
                                "Full Gospel Church" : {
                                    "level" : 3,
                                    "parent" : "Church"
                                },
                                "Holiness Church" : {
                                    "level" : 3,
                                    "parent" : "Church"
                                },
                                "Independent Church" : {
                                    "level" : 3,
                                    "parent" : "Church"
                                },
                                "Interdenominational Church" : {
                                    "level" : 3,
                                    "parent" : "Church"
                                },
                                "Lutheran Church" : {
                                    "level" : 3,
                                    "parent" : "Church"
                                },
                                "Mennonite Church" : {
                                    "level" : 3,
                                    "parent" : "Church"
                                },
                                "Methodist Church" : {
                                    "level" : 3,
                                    "parent" : "Church"
                                },
                                "Nazarene Church" : {
                                    "level" : 3,
                                    "parent" : "Church"
                                },
                                "Nondenominational Church" : {
                                    "level" : 3,
                                    "parent" : "Church"
                                },
                                "Pentecostal Church" : {
                                    "level" : 3,
                                    "parent" : "Church"
                                },
                                "Presbyterian Church" : {
                                    "level" : 3,
                                    "parent" : "Church"
                                },
                                "Seventh Day Adventist Church" : {
                                    "level" : 3,
                                    "parent" : "Church"
                                },
                            "Convent & Monastery" : {
                                "level" : 2,
                                "parent" : "Religious Place of Worship"
                            },
                            "Hindu Temple" : {
                                "level" : 2,
                                "parent" : "Religious Place of Worship"
                            },
                            "Kingdom Hall" : {
                                "level" : 2,
                                "parent" : "Religious Place of Worship"
                            },
                            "Mission" : {
                                "level" : 2,
                                "parent" : "Religious Place of Worship"
                            },
                            "Mosque" : {
                                "level" : 2,
                                "parent" : "Religious Place of Worship"
                            },
                            "Religious Center" : {
                                "level" : 2,
                                "parent" : "Religious Place of Worship"
                            },
                            "Sikh Temple" : {
                                "level" : 2,
                                "parent" : "Religious Place of Worship"
                            },
                            "Synagogue" : {
                                "level" : 2,
                                "parent" : "Religious Place of Worship"
                            },
                        "Residence" : {
                            "level" : 1,
                            "parent" : "Non-Business Places"
                        },
                            "Apartment & Condo Building" : {
                                "level" : 2,
                                "parent" : "Residence"
                            },
                            "Castle" : {
                                "level" : 2,
                                "parent" : "Residence"
                            },
                            "Dorm" : {
                                "level" : 2,
                                "parent" : "Residence"
                            },
                            "Fort" : {
                                "level" : 2,
                                "parent" : "Residence"
                            },
                            "Home" : {
                                "level" : 2,
                                "parent" : "Residence"
                            },
                            "Palace" : {
                                "level" : 2,
                                "parent" : "Residence"
                            },
                            "Stately Home" : {
                                "level" : 2,
                                "parent" : "Residence"
                            },
                    "Other" : {
                        "level" : 0
                    },
                        "Brand" : {
                            "level" : 1,
                            "parent" : "Other"
                        },
                            "App Page" : {
                                "level" : 2,
                                "parent" : "Brand"
                            },
                            "Appliances" : {
                                "level" : 2,
                                "parent" : "Brand"
                            },
                            "Baby Goods/Kids Goods" : {
                                "level" : 2,
                                "parent" : "Brand"
                            },
                            "Bags/Luggage" : {
                                "level" : 2,
                                "parent" : "Brand"
                            },
                            "Board Game" : {
                                "level" : 2,
                                "parent" : "Brand"
                            },
                            "Brand/Company Type" : {
                                "level" : 2,
                                "parent" : "Brand"
                            },
                            "Building Materials" : {
                                "level" : 2,
                                "parent" : "Brand"
                            },
                            "Camera/Photo" : {
                                "level" : 2,
                                "parent" : "Brand"
                            },
                            "Cars" : {
                                "level" : 2,
                                "parent" : "Brand"
                            },
                            "Clothing (Brand)" : {
                                "level" : 2,
                                "parent" : "Brand"
                            },
                            "Commercial Equipment" : {
                                "level" : 2,
                                "parent" : "Brand"
                            },
                            "Computers (Brand)" : {
                                "level" : 2,
                                "parent" : "Brand"
                            },
                            "Electronics" : {
                                "level" : 2,
                                "parent" : "Brand"
                            },
                            "Furniture" : {
                                "level" : 2,
                                "parent" : "Brand"
                            },
                            "Games/Toys" : {
                                "level" : 2,
                                "parent" : "Brand"
                            },
                            "Health/Beauty" : {
                                "level" : 2,
                                "parent" : "Brand"
                            },
                            "Home Decor" : {
                                "level" : 2,
                                "parent" : "Brand"
                            },
                            "Household Supplies" : {
                                "level" : 2,
                                "parent" : "Brand"
                            },
                            "Jewelry/Watches" : {
                                "level" : 2,
                                "parent" : "Brand"
                            },
                            "Kitchen/Cooking" : {
                                "level" : 2,
                                "parent" : "Brand"
                            },
                            "Musical Instrument" : {
                                "level" : 2,
                                "parent" : "Brand"
                            },
                            "Office Supplies" : {
                                "level" : 2,
                                "parent" : "Brand"
                            },
                            "Patio/Garden" : {
                                "level" : 2,
                                "parent" : "Brand"
                            },
                            "Pet Supplies" : {
                                "level" : 2,
                                "parent" : "Brand"
                            },
                            "Pharmaceuticals" : {
                                "level" : 2,
                                "parent" : "Brand"
                            },
                            "Phone/Tablet" : {
                                "level" : 2,
                                "parent" : "Brand"
                            },
                            "Product Type" : {
                                "level" : 2,
                                "parent" : "Brand"
                            },
                            "Product/Service" : {
                                "level" : 2,
                                "parent" : "Brand"
                            },
                            "Software" : {
                                "level" : 2,
                                "parent" : "Brand"
                            },
                            "Tools/Equipment" : {
                                "level" : 2,
                                "parent" : "Brand"
                            },
                            "Video Game" : {
                                "level" : 2,
                                "parent" : "Brand"
                            },
                            "Vitamins/Supplements" : {
                                "level" : 2,
                                "parent" : "Brand"
                            },
                            "Website" : {
                                "level" : 2,
                                "parent" : "Brand"
                            },
                                "Arts & Humanities Website" : {
                                    "level" : 3,
                                    "parent" : "Website"
                                },
                                "Business & Economy Website" : {
                                    "level" : 3,
                                    "parent" : "Website"
                                },
                                "Computers & Internet Website" : {
                                    "level" : 3,
                                    "parent" : "Website"
                                },
                                "E-commerce Website" : {
                                    "level" : 3,
                                    "parent" : "Website"
                                },
                                "Education Website" : {
                                    "level" : 3,
                                    "parent" : "Website"
                                },
                                "Entertainment Website" : {
                                    "level" : 3,
                                    "parent" : "Website"
                                },
                                "Food Website" : {
                                    "level" : 3,
                                    "parent" : "Website"
                                },
                                "Health & Wellness Website" : {
                                    "level" : 3,
                                    "parent" : "Website"
                                },
                                "Home & Garden Website" : {
                                    "level" : 3,
                                    "parent" : "Website"
                                },
                                "Local & Travel Website" : {
                                    "level" : 3,
                                    "parent" : "Website"
                                },
                                "News & Media Website" : {
                                    "level" : 3,
                                    "parent" : "Website"
                                },
                                "Personal Blog" : {
                                    "level" : 3,
                                    "parent" : "Website"
                                },
                                "Recreation & Sports Website" : {
                                    "level" : 3,
                                    "parent" : "Website"
                                },
                                "Reference Website" : {
                                    "level" : 3,
                                    "parent" : "Website"
                                },
                                "Regional Website" : {
                                    "level" : 3,
                                    "parent" : "Website"
                                },
                                "Science Website" : {
                                    "level" : 3,
                                    "parent" : "Website"
                                },
                                "Society & Culture Website" : {
                                    "level" : 3,
                                    "parent" : "Website"
                                },
                                "Teens & Kids Website" : {
                                    "level" : 3,
                                    "parent" : "Website"
                                },
                            "Wine/Spirits" : {
                                "level" : 2,
                                "parent" : "Brand"
                            },
                        "Cause" : {
                            "level" : 1,
                            "parent" : "Other"
                        },
                        "Color" : {
                            "level" : 1,
                            "parent" : "Other"
                        },
                        "Community" : {
                            "level" : 1,
                            "parent" : "Other"
                        },
                        "Course" : {
                            "level" : 1,
                            "parent" : "Other"
                        },
                        "Cuisine" : {
                            "level" : 1,
                            "parent" : "Other"
                        },
                        "Diseases" : {
                            "level" : 1,
                            "parent" : "Other"
                        },
                        "Editorial/Opinion" : {
                            "level" : 1,
                            "parent" : "Other"
                        },
                        "Election" : {
                            "level" : 1,
                            "parent" : "Other"
                        },
                        "Event" : {
                            "level" : 1,
                            "parent" : "Other"
                        },
                            "Festival" : {
                                "level" : 2,
                                "parent" : "Event"
                            },
                            "School Fundraiser" : {
                                "level" : 2,
                                "parent" : "Event"
                            },
                            "Sports Event" : {
                                "level" : 2,
                                "parent" : "Event"
                            },
                        "Exchange Program" : {
                            "level" : 1,
                            "parent" : "Other"
                        },
                        "Fan Page" : {
                            "level" : 1,
                            "parent" : "Other"
                        },
                        "Harmonized Page" : {
                            "level" : 1,
                            "parent" : "Other"
                        },
                        "Just For Fun" : {
                            "level" : 1,
                            "parent" : "Other"
                        },
                        "Language" : {
                            "level" : 1,
                            "parent" : "Other"
                        },
                        "Mood" : {
                            "level" : 1,
                            "parent" : "Other"
                        },
                        "Nationality" : {
                            "level" : 1,
                            "parent" : "Other"
                        },
                        "Not a Business" : {
                            "level" : 1,
                            "parent" : "Other"
                        },
                        "Profile" : {
                            "level" : 1,
                            "parent" : "Other"
                        },
                        "Satire/Parody" : {
                            "level" : 1,
                            "parent" : "Other"
                        },
                        "Sports Season" : {
                            "level" : 1,
                            "parent" : "Other"
                        },
                        "Surgeries" : {
                            "level" : 1,
                            "parent" : "Other"
                        },
                        "Ticket Sales" : {
                            "level" : 1,
                            "parent" : "Other"
                        },
                        "Topic" : {
                            "level" : 1,
                            "parent" : "Other"
                        },
                        "University (NCES)" : {
                            "level" : 1,
                            "parent" : "Other"
                        },
                        "University Status" : {
                            "level" : 1,
                            "parent" : "Other"
                        },
                        "Work Position" : {
                            "level" : 1,
                            "parent" : "Other"
                        },
                        "Work Project" : {
                            "level" : 1,
                            "parent" : "Other"
                        },
                        "Work Status" : {
                            "level" : 1,
                            "parent" : "Other"
                        },
                    "Public Figure" : {
                        "level" : 0
                    },
                        "Actor" : {
                            "level" : 1,
                            "parent" : "Public Figure"
                        },
                        "Artist" : {
                            "level" : 1,
                            "parent" : "Public Figure"
                        },
                        "Athlete" : {
                            "level" : 1,
                            "parent" : "Public Figure"
                        },
                        "Author" : {
                            "level" : 1,
                            "parent" : "Public Figure"
                        },
                        "Band" : {
                            "level" : 1,
                            "parent" : "Public Figure"
                        },
                        "Blogger" : {
                            "level" : 1,
                            "parent" : "Public Figure"
                        },
                        "Chef" : {
                            "level" : 1,
                            "parent" : "Public Figure"
                        },
                        "Comedian" : {
                            "level" : 1,
                            "parent" : "Public Figure"
                        },
                        "Dancer" : {
                            "level" : 1,
                            "parent" : "Public Figure"
                        },
                        "Designer" : {
                            "level" : 1,
                            "parent" : "Public Figure"
                        },
                            "Fashion Designer" : {
                                "level" : 2,
                                "parent" : "Designer"
                            },
                        "Digital Creator" : {
                            "level" : 1,
                            "parent" : "Public Figure"
                        },
                        "Editor" : {
                            "level" : 1,
                            "parent" : "Public Figure"
                        },
                        "Entrepreneur" : {
                            "level" : 1,
                            "parent" : "Public Figure"
                        },
                        "Fashion Model" : {
                            "level" : 1,
                            "parent" : "Public Figure"
                        },
                        "Film Director" : {
                            "level" : 1,
                            "parent" : "Public Figure"
                        },
                        "Fitness Model" : {
                            "level" : 1,
                            "parent" : "Public Figure"
                        },
                        "Gamer" : {
                            "level" : 1,
                            "parent" : "Public Figure"
                        },
                        "Journalist" : {
                            "level" : 1,
                            "parent" : "Public Figure"
                        },
                        "Motivational Speaker" : {
                            "level" : 1,
                            "parent" : "Public Figure"
                        },
                        "Musician" : {
                            "level" : 1,
                            "parent" : "Public Figure"
                        },
                        "Musician/Band" : {
                            "level" : 1,
                            "parent" : "Public Figure"
                        },
                        "News Personality" : {
                            "level" : 1,
                            "parent" : "Public Figure"
                        },
                        "Orchestra" : {
                            "level" : 1,
                            "parent" : "Public Figure"
                        },
                        "Producer" : {
                            "level" : 1,
                            "parent" : "Public Figure"
                        },
                        "Scientist" : {
                            "level" : 1,
                            "parent" : "Public Figure"
                        },
                        "Spiritual Leader" : {
                            "level" : 1,
                            "parent" : "Public Figure"
                        },
                        "Sports Promoter" : {
                            "level" : 1,
                            "parent" : "Public Figure"
                        },
                        "Talent Agent" : {
                            "level" : 1,
                            "parent" : "Public Figure"
                        },
                        "Video Creator" : {
                            "level" : 1,
                            "parent" : "Public Figure"
                        },
                            "Gaming Video Creator" : {
                                "level" : 2,
                                "parent" : "Video Creator"
                            },
                        "Writer" : {
                            "level" : 1,
                            "parent" : "Public Figure"
                        },
                }

                json_obj_v1 = {
                    "Advertising/Marketing" : 0 ,
                    "Agriculture" : 0 ,
                    "Arts & Entertainment" : 0 ,
                    "Automotive, Aircraft & Boat" : 0 ,
                    "Beauty, Cosmetic & Personal Care" : 0 ,
                    "Commercial & Industrial" : 0 ,
                    "Education" : 0 ,
                    "Finance" : 0 ,
                    "Food & Beverage" : 0 ,
                    "Hotel & Lodging" : 0 ,
                    "Legal" : 0 ,
                    "Local Service" : 0 ,
                    "Media/News Company" : 0 ,
                    "Medical & Health" : 0 ,
                    "Non-Governmental Organization (NGO)" : 0 ,
                    "Nonprofit Organization" : 0 ,
                    "Public & Government Service" : 0 ,
                    "Real Estate" : 0 ,
                    "Science, Technology & Engineering" : 0 ,
                    "Shopping & Retail" : 0 ,
                    "Sports & Recreation" : 0 ,
                    "Travel & Transportation" : 0 ,
                    "Armed Forces" : 0 ,
                    "Charity Organization" : 0 ,
                    "Community Service" : 0 ,
                    "Country Club / Clubhouse" : 0 ,
                    "Environmental Conservation Organization" : 0 ,
                    "Labor Union" : 0 ,
                    "Private Members Club" : 0 ,
                    "Religious Organization" : 0 ,
                    "Social Club" : 0 ,
                    "Sorority & Fraternity" : 0 ,
                    "Sports Club" : 0 ,
                    "Youth Organization" : 0 ,
                    "Literary Arts" : 0 ,
                    "Performance Art" : 0 ,
                    "Performing Arts" : 0 ,
                    "Science" : 0 ,
                    "Sports" : 0 ,
                    "Visual Arts" : 0 ,
                    "Art" : 0 ,
                    "Books & Magazines" : 0 ,
                    "Concert Tour" : 0 ,
                    "Media Restoration Service" : 0 ,
                    "Music" : 0 ,
                    "Show" : 0 ,
                    "TV & Movies" : 0 ,
                    "Theatrical Play" : 0 ,
                    "Theatrical Productions" : 0 ,
                    "Automated Teller Machine (ATM)" : 0 ,
                    "Campus Building" : 0 ,
                    "City Infrastructure" : 0 ,
                    "Landmark & Historical Place" : 0 ,
                    "Locality" : 0 ,
                    "Meeting Room" : 0 ,
                    "Outdoor Recreation" : 0 ,
                    "Public Toilet" : 0 ,
                    "Religious Place of Worship" : 0 ,
                    "Residence" : 0 ,
                    "Brand" : 0 ,
                    "Cause" : 0 ,
                    "Color" : 0 ,
                    "Community" : 0 ,
                    "Course" : 0 ,
                    "Cuisine" : 0 ,
                    "Diseases" : 0 ,
                    "Editorial/Opinion" : 0 ,
                    "Election" : 0 , 
                    "Event" : 0 ,
                    "Exchange Program" : 0 ,
                    "Fan Page" : 0 ,
                    "Harmonized Page" : 0 ,
                    "Just For Fun" : 0 ,
                    "Language" : 0 ,
                    "Mood" : 0 ,
                    "Nationality" : 0 ,
                    "Not a Business" : 0 ,
                    "Profile" : 0 ,
                    "Satire/Parody" : 0 ,
                    "Sports Season" : 0 ,
                    "Surgeries" : 0 ,
                    "Ticket Sales" : 0 ,
                    "Topic" : 0 ,
                    "University (NCES)" : 0 ,
                    "University Status" : 0 ,
                    "Work Position" : 0 ,
                    "Work Project" : 0 ,
                    "Work Status" : 0 ,
                    "Actor" : 0 ,
                    "Artist" : 0 ,
                    "Athlete" : 0 ,
                    "Author" : 0 ,
                    "Band" : 0 ,
                    "Blogger" : 0 ,
                    "Chef" : 0 ,
                    "Comedian" : 0 ,
                    "Dancer" : 0 ,
                    "Designer" : 0 ,
                    "Digital Creator" : 0 ,
                    "Editor" : 0 ,
                    "Entrepreneur" : 0 ,
                    "Fashion Model" : 0 ,
                    "Film Director" : 0 ,
                    "Fitness Model" : 0 ,
                    "Gamer" : 0 ,
                    "Journalist" : 0 ,
                    "Motivational Speaker" : 0 ,
                    "Musician" : 0 ,
                    "Musician/Band" : 0 , 
                    "News Personality" : 0 ,
                    "Orchestra" : 0 ,
                    "Producer" : 0 ,
                    "Scientist" : 0 ,
                    "Spiritual Leader" : 0 ,
                    "Sports Promoter" : 0 ,
                    "Talent Agent" : 0 ,
                    "Video Creator" : 0 ,
                    "Writer" : 0
                }
                json_obj_v2 = json_obj_v1.copy()

                while True :  
                    if "data" in content_data:
                        for c in content_data["data"] :
                            #version 1
                            if "category" in c :
                                if c["category"] in categorie_all :
                                    cat_key = c["category"]
                                    cat = categorie_all[cat_key]
                                    while cat["level"] > 1 :
                                        cat_key = cat["parent"]
                                        cat = categorie_all[cat_key]
                                    if cat_key in json_obj_v1:
                                        json_obj_v1[cat_key] += 1
                            #version2
                            if "category_list" in c :
                                temp_v2 = []
                                for cl in c["category_list"]:
                                    if cl["name"] in categorie_all :
                                        cat_key = cl["name"]
                                        cat = categorie_all[cat_key]
                                        while cat["level"] > 1 :
                                            cat_key = cat["parent"]
                                            cat = categorie_all[cat_key]
                                        if cat_key in json_obj_v2 and cat_key not in temp_v2:
                                            temp_v2.append(cat_key)
                                for cl_select in temp_v2:
                                    json_obj_v2[cl_select] += 1
                    else:
                        print(content_data)
                            
                    #get next data
                    next_data_url = None
                    if "paging" in content_data:
                        if "next" in content_data["paging"] :
                            next_data_url = content_data["paging"]["next"]
                            print('pull data content')
                    else:
                        print('Error format in create_facebook_categories')
                        facebook_categories(facebook_id = content_id, categories_version = 1, data = json_obj_v1 ).save()
                        facebook_categories(facebook_id = content_id, categories_version = 2, data = json_obj_v2 ).save()

                        return False
                        break

                    if next_data_url :
                        r = requests.get(next_data_url)
                        content_data = json.loads(r.content)
                        
                    else:
                        facebook_categories(facebook_id = content_id, categories_version = 1, data = json_obj_v1 ).save()
                        facebook_categories(facebook_id = content_id, categories_version = 2, data = json_obj_v2 ).save()

                        return True
                        break
            
        return False



    def get(self, request, *args, **kwargs):
        return JsonResponse({'status':'403','msg':'Forbidden'})

    def post(self, request, *args, **kwargs):
        content = json.loads(request.body)
        
        if "id" in content and "likes" in content :
            content_id = int(content["id"])
            content_data = content["likes"]
            self.create_facebook_categories(content_id = content_id, content_data = content_data)
            print('created facebook categories for '+str(content_id) +' complete')
        elif "id" in content:
            json_obj_v1 = {
                "Advertising/Marketing" : 0 ,
                "Agriculture" : 0 ,
                "Arts & Entertainment" : 0 ,
                "Automotive, Aircraft & Boat" : 0 ,
                "Beauty, Cosmetic & Personal Care" : 0 ,
                "Commercial & Industrial" : 0 ,
                "Education" : 0 ,
                "Finance" : 0 ,
                "Food & Beverage" : 0 ,
                "Hotel & Lodging" : 0 ,
                "Legal" : 0 ,
                "Local Service" : 0 ,
                "Media/News Company" : 0 ,
                "Medical & Health" : 0 ,
                "Non-Governmental Organization (NGO)" : 0 ,
                "Nonprofit Organization" : 0 ,
                "Public & Government Service" : 0 ,
                "Real Estate" : 0 ,
                "Science, Technology & Engineering" : 0 ,
                "Shopping & Retail" : 0 ,
                "Sports & Recreation" : 0 ,
                "Travel & Transportation" : 0 ,
                "Armed Forces" : 0 ,
                "Charity Organization" : 0 ,
                "Community Service" : 0 ,
                "Country Club / Clubhouse" : 0 ,
                "Environmental Conservation Organization" : 0 ,
                "Labor Union" : 0 ,
                "Private Members Club" : 0 ,
                "Religious Organization" : 0 ,
                "Social Club" : 0 ,
                "Sorority & Fraternity" : 0 ,
                "Sports Club" : 0 ,
                "Youth Organization" : 0 ,
                "Literary Arts" : 0 ,
                "Performance Art" : 0 ,
                "Performing Arts" : 0 ,
                "Science" : 0 ,
                "Sports" : 0 ,
                "Visual Arts" : 0 ,
                "Art" : 0 ,
                "Books & Magazines" : 0 ,
                "Concert Tour" : 0 ,
                "Media Restoration Service" : 0 ,
                "Music" : 0 ,
                "Show" : 0 ,
                "TV & Movies" : 0 ,
                "Theatrical Play" : 0 ,
                "Theatrical Productions" : 0 ,
                "Automated Teller Machine (ATM)" : 0 ,
                "Campus Building" : 0 ,
                "City Infrastructure" : 0 ,
                "Landmark & Historical Place" : 0 ,
                "Locality" : 0 ,
                "Meeting Room" : 0 ,
                "Outdoor Recreation" : 0 ,
                "Public Toilet" : 0 ,
                "Religious Place of Worship" : 0 ,
                "Residence" : 0 ,
                "Brand" : 0 ,
                "Cause" : 0 ,
                "Color" : 0 ,
                "Community" : 0 ,
                "Course" : 0 ,
                "Cuisine" : 0 ,
                "Diseases" : 0 ,
                "Editorial/Opinion" : 0 ,
                "Election" : 0 , 
                "Event" : 0 ,
                "Exchange Program" : 0 ,
                "Fan Page" : 0 ,
                "Harmonized Page" : 0 ,
                "Just For Fun" : 0 ,
                "Language" : 0 ,
                "Mood" : 0 ,
                "Nationality" : 0 ,
                "Not a Business" : 0 ,
                "Profile" : 0 ,
                "Satire/Parody" : 0 ,
                "Sports Season" : 0 ,
                "Surgeries" : 0 ,
                "Ticket Sales" : 0 ,
                "Topic" : 0 ,
                "University (NCES)" : 0 ,
                "University Status" : 0 ,
                "Work Position" : 0 ,
                "Work Project" : 0 ,
                "Work Status" : 0 ,
                "Actor" : 0 ,
                "Artist" : 0 ,
                "Athlete" : 0 ,
                "Author" : 0 ,
                "Band" : 0 ,
                "Blogger" : 0 ,
                "Chef" : 0 ,
                "Comedian" : 0 ,
                "Dancer" : 0 ,
                "Designer" : 0 ,
                "Digital Creator" : 0 ,
                "Editor" : 0 ,
                "Entrepreneur" : 0 ,
                "Fashion Model" : 0 ,
                "Film Director" : 0 ,
                "Fitness Model" : 0 ,
                "Gamer" : 0 ,
                "Journalist" : 0 ,
                "Motivational Speaker" : 0 ,
                "Musician" : 0 ,
                "Musician/Band" : 0 , 
                "News Personality" : 0 ,
                "Orchestra" : 0 ,
                "Producer" : 0 ,
                "Scientist" : 0 ,
                "Spiritual Leader" : 0 ,
                "Sports Promoter" : 0 ,
                "Talent Agent" : 0 ,
                "Video Creator" : 0 ,
                "Writer" : 0
            }
            json_obj_v2 = json_obj_v1.copy()
            content_id = int(content["id"])
            facebook_categories(facebook_id = content_id, categories_version = 1, data = json_obj_v1 ).save()
            facebook_categories(facebook_id = content_id, categories_version = 2, data = json_obj_v2 ).save()
            print('created facebook categories for '+str(content_id) +' complete but nodata')
        #debug for heroku
        sys.stdout.flush()

        return JsonResponse({'status':'200','msg':'OK'})
        

@method_decorator(csrf_exempt, name='dispatch')
class user_tax_predict(View):
    permission_classes = (IsAuthenticated,)
    def get(self, request, *args, **kwargs):
        token = request.META['HTTP_AUTHORIZATION']
        # decodedPayload = jwt.decode(token,None,None)
        #print(decodedPayload)
        #print(request.body)
        # email = decodedPayload.get('email')

        #return plan_type_all
        pts = plan_types.objects.all().order_by('created')
        if len(pts) == 0:
            plan_name = ["ป้องกันความเสี่ยง","เน้นลงทุน","เน้นเกษียณ"]
            plan_description = ["ป้องกันความเสี่ยง", "เน้นลงทุน", "เน้นเกษียณ"]
            plan_data = [
                {
                    "ประกันชีวิต" : 50 ,
                    "ประกันชีวิตแบบบำนาญ" : 25 ,
                    "ลงทุน SSF" : 12.5 ,
                    "ลงทุน RMF" : 12.5 
                },
                {
                    "ประกันชีวิต" : 12.5 ,
                    "ลงทุน SSF" : 50 ,
                    "ลงทุน RMF" : 25
                },
                {
                    "ประกันชีวิต" : 12.5 ,
                    "ประกันชีวิตแบบบำนาญ" : 25 ,
                    "ลงทุน SSF" : 12.5 ,
                    "ลงทุน RMF" : 50
                }
            ]
            risk_level_list = [8,8,8]
            for i in range(0,3):
                pts = plan_types()
                pts.type_id = i+1
                pts.plan_name = plan_name[i]
                pts.plan_description = plan_description[i]
                pts.plan_data = str(json.dumps(plan_data[i], ensure_ascii=False))
                pts.risk_level = risk_level_list[i]
                pts.save()
            pts = plan_types.objects.all().order_by('created')
        
        plan_type_list = []
        for p in pts:
            json_obj = {
                'id' : p.type_id,
                'plan_type_name' : p.plan_name,
                'plan_description' : p.plan_description,
                'plan_data' : json.loads(p.plan_data)
            }
            plan_type_list.append(json_obj)

        #debug for heroku
        sys.stdout.flush()

        return JsonResponse({'status':'200', 'plan_type_list' : plan_type_list})
        
    def post(self, request, *args, **kwargs):
        token = request.META['HTTP_AUTHORIZATION']
        decodedPayload = jwt.decode(token,None,None)
        print(decodedPayload)
        print(json.loads(request.body))
        email = decodedPayload.get('email')
        content = json.loads(request.body)
        
        if not content.get('facebook_id') :
            return JsonResponse({'status':'400','msg':'Error Wrong Format'})
        else:
            u = User.objects.get(email = email)
            mp = member_profile.objects.get(user = u)
            
            #ml part
            user_plan_type = 2
            try:
                ml_config = MLConfiguration.get_solo()
                categories_version = ml_config.categories_version
                filename = f'ML\{ml_config.ml_file_name}'

                today = date.today()
                age = today.year - mp.birthdate.year - ((today.month, today.day) < (mp.birthdate.month, mp.birthdate.day))
                fc = facebook_categories.objects.filter(facebook_id=content.get('facebook_id'), categories_version=categories_version).order_by('-created').first().data

                clf = joblib.load(filename)
                data = [{
                        'gender' : mp.gender,
                        'age' : age,
                        'salary' : mp.salary,
                        'other_income' : mp.other_income,
                        'parent_num' : mp.parent_num,
                        'child_num' : mp.child_num,
                        'marriage' : mp.marriage,
                        'infirm' : mp.infirm,
                        'risk_question' : mp.risk,
                        'risk_type' : cal_risk_type(mp.risk),
                        'categories_data' : fc
                    }]

                df = preprocess_data_to_ml(data)
                user_plan_type = clf.predict(df)[0]
                print(f'user_plan_type : {user_plan_type}')

                #     predict_data = predict_dataset()
                #     predict_data.facebook_id = mp.facebook_id
                #     predict_data.gender = mp.gender
                #     predict_data.age = age
                #     predict_data.salary = mp.salary
                #     predict_data.other_income = mp.other_income
                #     predict_data.parent_num = mp.parent_num
                #     predict_data.child_num = mp.child_num
                #     predict_data.marriage = mp.marriage
                #     predict_data.infirm = mp.infirm
                #     predict_data.risk_question =  mp.risk
                #     predict_data.risk_type = cal_risk_type(mp.risk)  #m.risk is string
                #     predict_data.categories_version = categories_version
                #     predict_data.categories_data = fc.data
                #     predict_data.predict_ans_type = user_plan_type
                #     predict_data.save()
                
            except:
                print('load model fail.')

            planType = plan_types.objects.filter(type_id=user_plan_type).first()
            user_accept_risk_lv = cal_risk_level(mp.risk)
            fundList = fund_list.objects.filter(active=True, risk__lte=user_accept_risk_lv, fundType=planType.related_fund_types.all()).order_by('-is_ads','-priority')
            fundList_json = []
            # for fund in fundList:
            #     fund_json = {
            #         'name':  fund.name,
            #         'display_name':  fund.display_name,
            #         'description ':  fund.description,
            #         'start_date': fund.start_date,
            #         'end_date': fund.end_date,
            #         'risk': fund.risk,
            #         'dividend_payout': fund.dividend_payout,
            #         'asset_management':  fund.asset_management,
            #         'link':  fund.link,
            #         # 'fundType':  fund.fundType.all(),
            #         'priority':  fund.priority,
            #         'is_ads': fund.is_ads  
            #     }
            #     fundList_json.append(fund_json)
            # print(fundList_json)

            insuranceList = insurance_list.objects.filter(active=True, insuranceType__in=planType.related_insurance_types.all()).order_by('-is_ads','-priority')
            insuranceList_json = []
            # for insurance in insuranceList:
            #     insurance_json = {
            #         'name':  insurance.name,
            #         'display_name':  insurance.display_name,
            #         'description ':  insurance.description,
            #         'public_limited_company':  insurance.public_limited_company,
            #         'link':  insurance.link,
            #         # 'insuranceType':  insurance.insuranceType.all(),
            #         'priority':  insurance.priority,
            #         'is_ads': insurance.is_ads  
            #     }
            #     insuranceList_json.append(insurance_json)
            # print(insuranceList_json)
            
            #debug for heroku
            sys.stdout.flush()

            return JsonResponse({'status':'200','email': email , 'user_plan_type' : user_plan_type, 'fund_list': fundList_json, 'insurance_list': insuranceList_json})

def cal_risk(risk):
    riskarr = json.loads(risk)
    score = 0
    result = 0
    risk_level = 0
    
    for i in range(0,10):
        if i != 3 :
            score += int(riskarr[i])
        else:
            score += len(riskarr[i])
    if score < 15 :
        risk_level = 1
        result = 0
    #15 - 21
    elif score < 22 :
        risk_level = 4
        result = 1
    #22 - 29 
    elif score < 30 :
        risk_level = 5
        result = 2
    #30 - 36
    elif score < 37 :
        risk_level = 7
        result = 3
    # 37++
    else :
        risk_level = 8
        result = 4

    return risk_level, result

def cal_risk_type(risk):
    risk_level, result = cal_risk(risk)
    return result

def cal_risk_level(risk):
    risk_level, result = cal_risk(risk)
    return risk_level
        
@method_decorator(csrf_exempt, name='dispatch')
class collect_dataset(View):
    permission_classes = (IsAuthenticated,)
    def get(self, request, *args, **kwargs):
        token = request.META['HTTP_AUTHORIZATION']
        decodedPayload = jwt.decode(token,None,None)
        #print(decodedPayload)
        #print(request.body)
        email = decodedPayload.get('email')
        print(email)

        #debug for heroku
        sys.stdout.flush()

        return JsonResponse({'status':'403','msg':'Forbidden'})

    def post(self, request, *args, **kwargs):
        token = request.META['HTTP_AUTHORIZATION']
        decodedPayload = jwt.decode(token,None,None)
        print(decodedPayload)
        print(json.loads(request.body))
        email = decodedPayload.get('email')
        content = json.loads(request.body)

        #debug for heroku
        sys.stdout.flush()
        
        if not content.get('plan_type') :
            return JsonResponse({'status':'400','msg':'Error Wrong Format'})
        else:
            u = User.objects.get(email = email)
            m = member_profile.objects.get(user = u)
            today = date.today()
            age = today.year - m.birthdate.year - ((today.month, today.day) < (m.birthdate.month, m.birthdate.day))

            for v in range(1,3):
                fc = facebook_categories.objects.filter(facebook_id = m.facebook_id,categories_version = v).order_by('-created').first()

                d = dataset()
                d.facebook_id = m.facebook_id
                d.gender = m.gender
                d.age = age
                d.salary = m.salary
                d.other_income = m.other_income
                d.parent_num = m.parent_num
                d.child_num = m.child_num
                d.marriage = m.marriage
                d.infirm = m.infirm
                d.risk_question =  m.risk
                d.risk_type = cal_risk_type(m.risk)  #m.risk is string
                d.categories_version = v
                d.categories_data = fc.data
                d.ans_type = int(content.get('plan_type'))
                d.save()
            
            return JsonResponse({'status':'200','msg': 'save dataset complete' })

def preprocess_data_to_ml(data):
    # data = [{
    #         'gender' : 2,
    #         'age' : 21,
    #         'salary' : 20000,
    #         'other_income' : 60000,
    #         'parent_num' : 2,
    #         'child_num' : 0,
    #         'marriage' : 1,
    #         'infirm' : 1,
    #         'risk_question' : "[4, 3, 3, [4, 3, 1], 2, 3, 3, 3, 3, 3]",
    #         'risk_type' : 3,
    #         'categories_data' : "{'Art': 0, 'Band': 0, 'Chef': 1, 'Mood': 0, 'Show': 0, 'Actor': 0, 'Brand': 40, 'Cause': 0, 'Color': 0, 'Event': 1, 'Gamer': 1, 'Legal': 0, 'Music': 2, 'Topic': 0, 'Artist': 3, 'Author': 1, 'Course': 0, 'Dancer': 1, 'Editor': 0, 'Sports': 1, 'Writer': 1, 'Athlete': 0, 'Blogger': 1, 'Cuisine': 0, 'Finance': 1, 'Profile': 0, 'Science': 0, 'Comedian': 0, 'Designer': 0, 'Diseases': 0, 'Election': 0, 'Fan Page': 0, 'Language': 0, 'Locality': 0, 'Musician': 0, 'Producer': 0, 'Community': 6, 'Education': 10, 'Orchestra': 0, 'Residence': 0, 'Scientist': 0, 'Surgeries': 0, 'Journalist': 0, 'Agriculture': 0, 'Labor Union': 0, 'Nationality': 0, 'Real Estate': 1, 'Social Club': 0, 'Sports Club': 0, 'TV & Movies': 1, 'Visual Arts': 0, 'Work Status': 0, 'Armed Forces': 0, 'Concert Tour': 0, 'Entrepreneur': 0, 'Just For Fun': 1, 'Meeting Room': 0, 'Talent Agent': 0, 'Ticket Sales': 0, 'Work Project': 0, 'Fashion Model': 0, 'Film Director': 0, 'Fitness Model': 0, 'Literary Arts': 0, 'Local Service': 2, 'Musician/Band': 0, 'Public Toilet': 0, 'Satire/Parody': 0, 'Sports Season': 0, 'Video Creator': 3, 'Work Position': 0, 'Not a Business': 2, 'Campus Building': 1, 'Digital Creator': 0, 'Food & Beverage': 10, 'Harmonized Page': 0, 'Hotel & Lodging': 0, 'Performance Art': 0, 'Performing Arts': 1, 'Sports Promoter': 0, 'Theatrical Play': 0, 'Exchange Program': 0, 'Medical & Health': 0, 'News Personality': 0, 'Spiritual Leader': 0, 'Books & Magazines': 2, 'Community Service': 0, 'Editorial/Opinion': 0, 'Shopping & Retail': 13, 'University (NCES)': 0, 'University Status': 0, 'Media/News Company': 0, 'Outdoor Recreation': 0, 'Youth Organization': 0, 'City Infrastructure': 0, 'Sports & Recreation': 0, 'Arts & Entertainment': 1, 'Charity Organization': 0, 'Motivational Speaker': 0, 'Private Members Club': 0, 'Advertising/Marketing': 0, 'Sorority & Fraternity': 0, 'Nonprofit Organization': 0, 'Religious Organization': 0, 'Theatrical Productions': 0, 'Commercial & Industrial': 0, 'Travel & Transportation': 0, 'Country Club / Clubhouse': 0, 'Media Restoration Service': 0, 'Religious Place of Worship': 0, 'Automotive, Aircraft & Boat': 16, 'Landmark & Historical Place': 0, 'Public & Government Service': 0, 'Automated Teller Machine (ATM)': 0, 'Beauty, Cosmetic & Personal Care': 1, 'Science, Technology & Engineering': 2, 'Non-Governmental Organization (NGO)': 0, 'Environmental Conservation Organization': 0}"
    #     }]

    df = pd.DataFrame(data=data)
    temp_list = []
    for i in df['risk_question']:
        x = json.loads(i)
        temp_list.append(x)
    df['risk_question'] = temp_list 

    for i in range(1,11):
        df[f'risk_question_{i}'] = df['risk_question'].apply(lambda x:x[i-1])

    for i in range(1,5):
        temp_list = []
        for j in df['risk_question_4']:
            if i in j:
                temp_list.append(1)
            else:
                temp_list.append(0)
        df[f'risk_question_4_{i}'] = temp_list
        
    df['gender'] = int(df['gender']) - 1
    df['marriage'] = int(df['marriage']) - 1

    for i in range(1,11):
        if i != 4:
            temp_list_1 = []
            temp_list_2 = []
            temp_list_3 = []
            temp_list_4 = []
            for j in df[f'risk_question_{i}']:
                if j == 1:
                    temp_list_1.append(1)
                    temp_list_2.append(0)
                    temp_list_3.append(0)
                    temp_list_4.append(0)
                elif j == 2:
                    temp_list_1.append(0)
                    temp_list_2.append(1)
                    temp_list_3.append(0)
                    temp_list_4.append(0)
                elif j == 3:
                    temp_list_1.append(0)
                    temp_list_2.append(0)
                    temp_list_3.append(1)
                    temp_list_4.append(0)
                elif j == 4:
                    temp_list_1.append(0)
                    temp_list_2.append(0)
                    temp_list_3.append(0)
                    temp_list_4.append(1)
            df[f'risk_question_{i}_1'] = temp_list_1
            df[f'risk_question_{i}_2'] = temp_list_2
            df[f'risk_question_{i}_3'] = temp_list_3
            df[f'risk_question_{i}_4'] = temp_list_4

    # temp_list = []
    # for i in df['categories_data']:
    #     print(i)
    #     x = json.loads(i.replace("'", '"')) 
    #     temp_list.append(x)
    # df['categories_data'] = temp_list

    key_list = []
    for key in df['categories_data'][0].keys():
        key_list.append(key)

    for key in key_list:
        df[key] = df['categories_data'].apply(lambda x:x.get(key))

    # drop_list = ['id', 'created', 'facebook_id', 'risk_question','categories_data']
    drop_list = ['risk_question','categories_data']
    if True:
        drop_list.append('infirm')

    for i in range(1,11):
        drop_list.append(f'risk_question_{i}')
    
    ml_config = MLConfiguration.get_solo()
    drop_list_2 = json.loads(ml_config.drop_features.replace("'",'"'))
    drop_list.extend(drop_list_2)
    df.drop(drop_list, axis=1, inplace=True)

    return df