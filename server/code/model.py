# -*- coding: utf-8 -*-
# 모델 정의
from sqlalchemy import Column, Float, String, ForeignKey
from pydantic import BaseModel
from db import Base
from db import ENGINE


# user 테이블의 모델 UserTable 정의
class FoodTable(Base):
    __tablename__ = 'FOOD'
    food_name = Column(String, primary_key=True, nullable=False)
    weight = Column(Float, nullable=False)
    calories = Column(Float, nullable=False)
    carbohydrates = Column(Float, nullable=False)
    protein = Column(Float, nullable=False)
    fat = Column(Float, nullable=False)
    sugars = Column(Float, nullable=False)
    sodium = Column(Float, nullable=False)

class UserTable(Base):
    __tablename__="USER"
    user_name=Column(String, primary_key=True, nullable=False)
    share_id = Column(String)

class ImageTable(Base):
    __tablename__='IMAGE'
    image_name=Column(String, primary_key=True)
    user_name=Column(String, ForeignKey('USER.user_name'))
    mealtime=Column(String, default="아침")
    date=Column(String, nullable=False)

class ResultTable(Base):
    __tablename__ = 'RESULT'
    ml_id = Column(String, primary_key=True)
    image_name = Column(String, ForeignKey('IMAGE.image_name'))
    food_name = Column(String, ForeignKey('FOOD.food_name'))
    food_result = Column(String, nullable=False)
    weight_result = Column(Float, nullable=False)

# POSTやPUTのとき受け取るRequest Bodyのモデルを定義
class Food(BaseModel):
    food_name: str
    weight: float
    calories: float
    carbohydrate: float
    protein: float
    fat: float

class User(BaseModel):
    user_name: str
    share_id: str

class Image(BaseModel):
    image_name: str
    user_name: str
    mealtime: str
    date: str

class Result(BaseModel):
    ml_id: str
    image_name: str
    food_name: str
    food_result: str
    weight_result: str

def main():
    # 테이블이 없으면 테이블 만들기
    Base.metadata.create_all(bind=ENGINE)


if __name__ == "__main__":
    main()
