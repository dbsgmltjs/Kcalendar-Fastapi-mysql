from fastapi import FastAPI
from typing import List 
from starlette.middleware.cors import CORSMiddleware  
from db import session 
from model import FoodTable, Food, UserTable, ImageTable, ResultTable 
from sqlalchemy.exc import IntegrityError #에러 코드를 위한 모듈
from sqlalchemy import func
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uuid
import pandas as pd

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class NicknameRequest(BaseModel):
    nickname: str

@app.get("/")
def read_root():
    return {"Hello": "World!!!!"}


#@app.get("/{test}")
#def test(test:str):
#    print(">> ",test)
#    return {"test":test}

#################################################
# 칼린더 부분
@app.get("/calendar")
def calendar():
    join = session.query(
            ImageTable.user_name, ImageTable.date, ImageTable.mealtime,
            ResultTable.food_name, ResultTable.weight_result,
            FoodTable.weight, FoodTable.calories,
            FoodTable.carbohydrates, FoodTable.protein,
            FoodTable.fat, FoodTable.sugars, FoodTable.sodium
            ).join(
                    ResultTable, ImageTable.image_name==ResultTable.image_name
                    ).join(
                            FoodTable, ResultTable.food_name==FoodTable.food_name
                            ).order_by(ImageTable.date, ImageTable.mealtime).all()
    # 테이블에서 얻은 값을 정리한다.
    join_dict = [{
        "user_name":user_name, "date":date, "mealtime":mealtime, "food_name":food_name, "weight_result":weight_result,
        "weight":weight, "calories":calories, "carbohydrates":carbohydrates,
        "protein":protein, "fat":fat, "sugars":sugars, "sodium":sodium
        } for user_name, date, mealtime, food_name, weight_result, weight,
        calories, carbohydrates, protein, fat, sugars, sodium in join]

    # client에게 보낼 값을 정리한다.
    result = []
    # ml에서 나온 이미지에 대해 분석된 중량을 계산한다.
    for i in range(len(join_dict)):
        ml_weight = round(join_dict[i]["weight"] * join_dict[i]["weight_result"],2)
        ml_calories = round(join_dict[i]["calories"] * join_dict[i]["weight_result"],2)
        ml_carbohydrates = round(join_dict[i]["calories"] * join_dict[i]["weight_result"],2)
        ml_protein = round(join_dict[i]["protein"] * join_dict[i]["weight_result"],2)
        ml_fat = round(join_dict[i]["fat"] * join_dict[i]["weight_result"],2)
        ml_sugars = round(join_dict[i]["sugars"] * join_dict[i]["weight_result"],2)
        ml_sodium = round(join_dict[i]["sodium"] * join_dict[i]["weight_result"],2)
        
        # row 추가
        result_dict = {}
        result_dict["user_name"] = join_dict[i]["user_name"]
        result_dict["strTime"] = join_dict[i]["date"].split("-")[0].replace(".","-")
        result_dict["mealtime"] = join_dict[i]["mealtime"]
        result_dict["food_name"] = join_dict[i]["food_name"]
        result_dict["weight"] = ml_weight
        result_dict["calories"] = ml_calories
        result_dict["carbohydrates"] = ml_carbohydrates
        result_dict["protein"] = ml_protein
        result_dict["fat"] = ml_fat
        result_dict["sugars"] = ml_sugars
        result_dict["sodium"] = ml_sodium

        result.append(result_dict) # 위에서 딕셔너리 형태로 저장한 값을 저장한다.

    return result

## 캘린더 part : CDRR 만성질환위험감소섭취량 분석(당, 나트륨)
@app.get("/calendar/cdrr")
def cdrr():
    join = session.query(
            ImageTable.user_name, ImageTable.date,
            ResultTable.weight_result, 
            FoodTable.sodium, FoodTable.sugars, FoodTable.calories
            ).join(
                    ResultTable, ImageTable.image_name==ResultTable.image_name
                    ).join(
                            FoodTable, ResultTable.food_name==FoodTable.food_name
                            ).order_by(ImageTable.date, ImageTable.mealtime).all()
    # 테이블에서 얻은 값을 정리한다.
    join_dict = [{
        "user_name":user_name, "date":date,
        "weight_result":weight_result, "calories":calories,
        "sodium":sodium, "sugars":sugars
        } for user_name, date, weight_result, sodium, sugars,calories in join]
    
    # 섭취 횟수별  중량 결과에 대해 나트륨값을 정리한다.
    arr = []
    for row in join_dict:
        ml_sodium = row['weight_result'] * row['sodium']
        ml_sugars = row['weight_result'] * row['sugars']
        ml_calories = row['weight_result'] * row['calories']
        arr_dict = {}
        arr_dict["user_name"] = row['user_name']
        arr_dict["date"] = row['date'].split("-")[0].replace(".","-")
        arr_dict["calories"] = ml_calories
        arr_dict["sodium"] = ml_sodium
        arr_dict["sugars"] = ml_sugars
        arr.append(arr_dict)
    df = pd.DataFrame(arr)
    print("------------------------------------------")
    print(df)
    print("------------------------------------------")
    group = df.groupby(['user_name','date']).sum()
    result = []
    for i in range(len(group)):
        sugars = "True"
        sodium = "True"
    
        # 당 10-20%
        # 현재 단위(g) -> 칼로리로 변환하여 비율 계산
        total_calories = group["calories"][i]
        sugar_calories = group["sugars"][i] * 4
    
        if sugar_calories/total_calories > 0.20:
            sugars = "False"
    
        # 나트륨 2300mg/일
        if group["sodium"][i] > 2300: 
            sodium = "False"

        result_dict = {}
        result_dict["user_name"] = group.index[i][0]
        result_dict["date"] = group.index[i][1]
        result_dict["sugars"] = sugars
        result_dict["sodium"] = sodium

        result.append(result_dict)
    
    return result

# 탄수화물,단백질,지방 권장 섭취 비율
@app.get("/calendar/nutrient")
def nutrient():
    join = session.query(
            ImageTable.user_name, ImageTable.date,
            ResultTable.weight_result,
            FoodTable.carbohydrates, 
            FoodTable.protein, FoodTable.fat,
            FoodTable.calories
            ).join(
                    ResultTable, ImageTable.image_name==ResultTable.image_name
                    ).join(
                            FoodTable, ResultTable.food_name==FoodTable.food_name
                            ).order_by(ImageTable.date, ImageTable.mealtime).all()
    # 테이블에서 얻은 값을 정리한다.
    join_dict = [{
        "user_name":user_name, "date":date, "weight_result":weight_result,
        "carbohydrates":carbohydrates, "calories":calories,
        "protein":protein, "fat":fat
        } for user_name, date, weight_result,
        carbohydrates, protein, fat, calories in join]
    
    # 일별 탄수화물, 단백질, 지방의 비율 계산
    arr = []
    for row in join_dict:
        ml_calories = row['weight_result'] * row['calories']
        ml_carbohydrates = row['weight_result'] * row['carbohydrates']
        ml_protein = row['weight_result'] * row['protein']
        ml_fat = row['weight_result'] * row['fat']
        arr_dict = {}
        arr_dict["user_name"] = row["user_name"]
        arr_dict["date"] = row['date'].split("-")[0].replace(".","-")
        arr_dict["calories"] = ml_calories
        arr_dict["carbohydrates"] = ml_carbohydrates
        arr_dict["protein"] = ml_protein
        arr_dict["fat"] = ml_fat
        arr.append(arr_dict)
    
    df = pd.DataFrame(arr)
    print("-------------------------------------------")
    print(df)
    print("-------------------------------------------")
    group = df.groupby(['user_name','date']).sum()
    print("-------------------------------------------")
    print(group)
    print("-------------------------------------------")
    # 현재 단위 (g) -> 칼로리로 변환
    result = []
    for i in range(len(group)):
        carbohydrates = "normal"
        protein = "normal"
        fat = "normal"

        # 현재 단위(g) -> 칼로리로 변환하여 비율 계산
        total_calories = group["calories"][i]
        carb_calories = group["carbohydrates"][i] * 4
        protein_calories = group["protein"][i] * 4
        fat_calories = group["fat"][i] * 9
        
        # 탄수화물 55-65%
        if carb_calories/total_calories < 0.55:
            carbohydrates = "under"
        elif carb_calories/total_calories > 0.65:
            carbohydrates = "over"
        # 단백질 7-20%
        if protein_calories/total_calories < 0.07:
            protein = "under"
        elif protein_calories/total_calories > 0.20:
            protein = "over"
        # 지방 15-30%
        if fat_calories/total_calories < 0.15:
            fat = "under"
        elif fat_calories/total_calories > 0.30:
            fat = "over"
        
        result_dict = {}
        result_dict["user_name"] = group.index[i][0]
        result_dict["date"] = group.index[i][1]
        result_dict["carbohydrates"] = carbohydrates
        result_dict["protein"] = protein
        result_dict["fat"] = fat

        result.append(result_dict)

    return result
    
            
###################################################
# 결과 페이지 부분
## GET
@app.get("/result/{nickname}")
def result_foods(nickname:str):
    # ml 결과 txt 읽기
    ## food_name 파일
    food_file = open("/usr/src/server/data/food_name.txt","r", encoding="utf-8")
    Flines = food_file.readlines()

    lst=[]
    for Fline in Flines[3:]:
        lst.append(Fline.split(" ",2)[-1].replace("data/samples/","").split(": "))
    result = []
    for l in range(len(lst)):
        if l != len(lst)-1:
            if len(lst[l]) >= 3:
                lst[l][-2] = lst[l][-2].split(" ")[2]
                user_name = lst[l][-2].split("-")[0]
               # date = lst[l][-2].split("-")[1]
                datetime = lst[l][-2].split("-",1)[-1].replace(".jpg","")
                image_name = lst[l][-2]
                food_name = lst[l][-1].strip()
                result.append({"user_name":user_name, "image_name":image_name, "datetime":datetime, "food_name":food_name})
            elif len(lst[l]) == 2: 
                if len(lst[l+1]) >= 2:
                    user_name = lst[l][0].split("-")[0]
                    datetime = lst[l][0].split("-",1)[-1].replace(".jpg","")
                    image_name = lst[l][0]
                    food_name = lst[l][1].strip()
                elif len(lst[l+2]) == 2:
                    user_name = lst[l][0].split("-")[0]
                    datetime = lst[l][0].split("-",1)[-1].replace(".jpg","")
                    image_name = lst[l][0]
                    food_name = lst[l+1][0].strip()
                elif len(lst[l+2]) == 1:
                    user_name = lst[l][0].split("-")[0]
                    datetime = lst[l][0].split("-",1)[-1],replace(".jpg","")
                    image_name = lst[l][0]
                    food_name = lst[l+2][0].strip()
                result.append({"user_name":user_name, "image_name":image_name, "datetime":datetime, "food_name":food_name})
        elif len(lst[l]) == 2 and l == len(lst)-1:
            user_name = lst[l][0].split("-")[0]
            #date = lst[l][0].split("-")[1]
            datetime = lst[l][0].split("-",1)[-1].replace(".jpg","")
            image_name = lst[l][0]
            food_name = lst[l][1].strip()
            result.append({"user_name":user_name, "image_name":image_name, "datetime":datetime, "food_name":food_name})
    df = pd.DataFrame(result)
    # 'date' 열을 datetime 데이터 유형으로 변환
    df['date'] = pd.to_datetime(df['datetime'])

    # DataFrame을 날짜별로 내림차순으로 정렬
    df = df.sort_values(by='date', ascending=False)

    # 각 사용자에 대한 가장 최근 식품 값을 보유할 새 DataFrame 생성
    recent_food = pd.DataFrame(columns=['user_name', 'image_name', 'datetime', 'food_name'])

    # 정렬된 DataFrame의 각 행을 반복합니다.
    for index, row in df.iterrows():
        # user_name이 최근_음식 DataFrame에 아직 없는 경우
        if row['user_name'] not in recent_food['user_name'].values:
            # user_name 및 food_name 값을 사용하여 latest_food DataFrame에 새 행을 추가합니다.
            recent_food = recent_food.append({'user_name': row['user_name'], 'image_name':row['image_name'], 'datetime':row['datetime'], 'food_name': row['food_name']}, ignore_index=True)
     
    print(">> 유저별 최근 먹은 음식")
    print(recent_food)
    food_name = recent_food[recent_food["user_name"]==nickname]["food_name"].values[0] #user_name부분 수정해야함
    print(">> ",food_name)

    ## weight 파일

    weight_file = open("/usr/src/server/data/weight.txt","r")
    Wlines = weight_file.readlines()
    lst =  Wlines[2:len(Wlines)-1]

    result = []
    for l in lst:
        ml_weight = l.split(" ")[0]
        image_name = l.split(" ")[1].split("/")[-1].replace(".jpg\n","")
        user_name = image_name.split("-")[0]
        datetime = image_name.split("-",1)[-1]
        result.append({"ml_weight":ml_weight,"user_name":user_name,"datetime":datetime})
    df = pd.DataFrame(result)
    # 'date' 열을 datetime 데이터 유형으로 변환
    df['date'] = pd.to_datetime(df['datetime'])

    # DataFrame을 날짜별로 내림차순으로 정렬
    df = df.sort_values(by='date', ascending=False)

    # 각 사용자에 대한 가장 최근 식품 값을 보유할 새 DataFrame 생성
    recent_food = pd.DataFrame(columns=['user_name', 'ml_weight'])

    # 정렬된 DataFrame의 각 행을 반복합니다.
    for index, row in df.iterrows():
        # user_name이 최근_음식 DataFrame에 아직 없는 경우
        if row['user_name'] not in recent_food['user_name'].values:
            # user_name 및 food_name 값을 사용하여 latest_food DataFrame에 새 행을 추가합니다.
            recent_food = recent_food.append({'user_name': row['user_name'], 'ml_weight': row['ml_weight']}, ignore_index=True)
   
    ## 유저가 먹은 음식양
    ml_weight = float(recent_food[recent_food["user_name"]==nickname]["ml_weight"].values[0])

    # ml 결과와 일치한 음식명을 찾아서 정보 화면에 출력(select)
    food = session.query(FoodTable).all()
    for row in food:
        if row.food_name == food_name:
            weight = round(row.weight*ml_weight, 2)
            calories = round(row.calories*ml_weight, 2)
            carbohydrates = round(row.carbohydrates*ml_weight, 2)
            protein = round(row.protein*ml_weight, 2)
            fat = round(row.fat*ml_weight, 2)
            sodium = round(row.sodium*ml_weight, 2)
            sugars = round(row.sugars*ml_weight, 2)
            return JSONResponse({"food_name":food_name,
                "weight":weight,
                "calories":calories,
                "carbohydrates":carbohydrates,
                "protein":protein,
                "fat":fat,
                "sodium":sodium,
                "sugars":sugars})

## POST
class Item(BaseModel):
    value: str

@app.post("/result/{nickname}")
def save_value(item: Item, nickname:str):

# ml 결과 txt 읽기
    ## food_name 파일
    food_file = open("/usr/src/server/data/food_name.txt","r", encoding="utf-8")
    Flines = food_file.readlines()

    lst=[]
    for Fline in Flines[3:]:
        lst.append(Fline.split(" ",2)[-1].replace("data/samples/","").split(": "))
    result = []
    for l in range(len(lst)):
        if l != len(lst)-1:
            if len(lst[l]) >= 3:
                lst[l][-2] = lst[l][-2].split(" ")[2]
                user_name = lst[l][-2].split("-")[0]
                datetime = lst[l][-2].split("-",1)[-1].replace(".jpg","")
                image_name = lst[l][-2]
                food_name = lst[l][-1].strip()
                result.append({"user_name":user_name, "image_name":image_name, "datetime":datetime, "food_name":food_name})
            elif len(lst[l]) == 2: 
                if len(lst[l+1]) >= 2:
                    user_name = lst[l][0].split("-")[0]
                    datetime = lst[l][0].split("-",1)[-1].replace(".jpg","")
                    image_name = lst[l][0]
                    food_name = lst[l][1].strip()
                elif len(lst[l+2]) == 2:
                    user_name = lst[l][0].split("-")[0]
                    datetime = lst[l][0].split("-",1)[-1].replace(".jpg","")
                    image_name = lst[l][0]
                    food_name = lst[l+1][0].strip()
                elif len(lst[l+2]) == 1:
                    user_name = lst[l][0].split("-")[0]
                    datetime = lst[l][0].split("-",1)[-1],replace(".jpg","")
                    image_name = lst[l][0]
                    food_name = lst[l+2][0].strip()
                result.append({"user_name":user_name, "image_name":image_name, "datetime":datetime, "food_name":food_name})
        elif len(lst[l]) == 2 and l == len(lst)-1:
            user_name = lst[l][0].split("-")[0]
            datetime = lst[l][0].split("-",1)[-1].replace(".jpg","")
            image_name = lst[l][0]
            food_name = lst[l][1].strip()
            result.append({"user_name":user_name, "image_name":image_name, "datetime":datetime, "food_name":food_name})
    df = pd.DataFrame(result)
    print("--------------------food_name----------------------")
    print(df)
    print("---------------------------------------------------")
    # 'date' 열을 datetime 데이터 유형으로 변환
    df['date'] = pd.to_datetime(df['datetime'])

    # DataFrame을 날짜별로 내림차순으로 정렬
    df = df.sort_values(by='date', ascending=False)

    # 각 사용자에 대한 가장 최근 식품 값을 보유할 새 DataFrame 생성
    recent_food = pd.DataFrame(columns=['user_name', 'image_name', 'datetime', 'food_name'])

    # 정렬된 DataFrame의 각 행을 반복합니다.
    for index, row in df.iterrows():
        # user_name이 최근_음식 DataFrame에 아직 없는 경우
        if row['user_name'] not in recent_food['user_name'].values:
            # user_name 및 food_name 값을 사용하여 latest_food DataFrame에 새 행을 추가합니다.
            recent_food = recent_food.append({'user_name': row['user_name'], 'image_name':row['image_name'], 'datetime':row['datetime'], 'food_name': row['food_name']}, ignore_index=True)

    print("----------------------------------------------")
    print(recent_food)
    print("----------------------------------------------")

   # 이미지 정보 저장(insert)
    food_name =  recent_food[recent_food["user_name"]==nickname]["food_name"].values[0]
    mealtime = item.value
    date = recent_food[recent_food["user_name"]==nickname]["datetime"].values[0]
    image_name = recent_food[recent_food["user_name"]==nickname]["image_name"].values[0]
    img_rst = ImageTable(image_name=image_name, user_name=nickname, mealtime=mealtime ,date=date) # IMAGE 테이블에 결과값 저장
    try:
        session.add(img_rst)
        session.commit()
    except IntegrityError as e:
        session.rollback()
        if "Duplicate entry" in str(e):
            print(f">> image_name: {image_name}는 이미 존재합니다.")
        else:
            raise

    ## weight 파일
    weight_file = open("/usr/src/server/data/weight.txt","r")
    Wlines = weight_file.readlines()
    lst =  Wlines[2:len(Wlines)-1]
    result = []
    for l in lst:
        ml_weight = l.split(" ")[0]
        result.append({"ml_weight":ml_weight,"user_name":nickname,"datetime":datetime})
    df = pd.DataFrame(result)
    
    print('--------------weight----------------')
    print(df)
    print('-------------------------------------')
    
    # 'date' 열을 datetime 데이터 유형으로 변환
    df['date'] = pd.to_datetime(df['datetime'])

    # DataFrame을 날짜별로 내림차순으로 정렬
    df = df.sort_values(by='date', ascending=False)

    # 각 사용자에 대한 가장 최근 식품 값을 보유할 새 DataFrame 생성
    recent_food = pd.DataFrame(columns=['user_name', 'ml_weight'])

    # 정렬된 DataFrame의 각 행을 반복합니다.
    for index, row in df.iterrows():
        # user_name이 최근_음식 DataFrame에 아직 없는 경우
        if row['user_name'] not in recent_food['user_name'].values:
            # user_name 및 food_name 값을 사용하여 latest_food DataFrame에 새 행을 추가합니다.
            recent_food = recent_food.append({'user_name': row['user_name'], 'ml_weight': row['ml_weight']}, ignore_index=True)
    
    print('-------------------------------------')
    print(recent_food)
    print('-------------------------------------')

    ## 유저가 먹은 음식양
    ml_weight = float(recent_food[recent_food["user_name"]==nickname]["ml_weight"].values[0])
    ml_id = uuid.uuid4() # image_name이 동일해도 ml_id가 다르기 때문에 디비에 image_name의 값이 고유하지 않고 쌓임
    ml_rst = ResultTable(ml_id=ml_id, image_name=image_name, food_name=food_name, food_result=food_name, weight_result=ml_weight)
    try:
        session.add(ml_rst)
        session.commit()
    except IntegrityError as e:
        session.rollback()
        if "Duplicate entry" in str(e):
            print(f">> ml_id: {ml_id}는 이미 존재합니다.")
        else:
            raise
    return {"message": "Value saved successfully"}

############################################################
# 로그인 기능 부분
#class NicknameRequest(BaseModel):
#    nickname: str
@app.post("/Login")
def check_value(request: NicknameRequest):
    # input 값이 null일 때도 다음 화면으로 넘어감 방지
    if not request.nickname:
        return JSONResponse({"exists": False})
    user = session.query(UserTable).all()
    exists = False
    for row in user:
        if row.user_name == request.nickname:
            exists = True
            break
    return JSONResponse({"exists": exists})

@app.post("/Login/register")
def new_user(request: NicknameRequest):
    if not request.nickname:
        return JSONResponse({"exists": False})
    user = session.query(UserTable).all()
    exists = False
    for row in user:
        if row.user_name == request.nickname:
            exists = True
            break
    if not exists:
        user_rst = UserTable(user_name=request.nickname)
        try:
            session.add(user_rst)
            session.commit()
            print(f'>> {request.nickname}님이 등록되었습니다.')
        except IntegrityError as e:
            session.rollback()
            if "Duplicate entry" in str(e):
                print(f">> user_name: {request.nickname}은(는) 이미 존재합니다.")
            else:
                raise
        return JSONResponse({"exists": True})
    else:
        return JSONResponse({"exists": False})

        
