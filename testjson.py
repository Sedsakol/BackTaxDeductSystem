import json
plan_data = [
    {
        "ประกันชีวิต" : 100000 ,
        "ประกันชีวิตแบบบำนาญ" : 50000 ,
        "กองทุน SSF" : 25000 ,
        "กองทุน RMF" : 25000 
    },
    {
        "ประกันชีวิต" : 50000 ,
        "กองทุน SSF" : 100000 ,
        "กองทุน RMF" : 25000
    },
    {
        "ประกันชีวิต" : 25000 ,
        "ประกันชีวิตแบบบำนาญ" : 50000 ,
        "กองทุน SSF" : 25000 ,
        "กองทุน RMF" : 100000
    }
]

s = []
for i in plan_data:
    s.append(json.dumps(plan_data,ensure_ascii=False).encode('utf8'))

for i in s:
    print(json.loads(i))


