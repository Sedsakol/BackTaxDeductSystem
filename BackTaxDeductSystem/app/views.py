from django.shortcuts import render

# Create your views here.

#รอปรับแก้เป็นดึงจาก DB
def cal_tax_stair(salary,other_income):
    money = salary * 12 + other_income - 160000
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
    
