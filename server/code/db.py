# -*- coding: utf-8 -*-
# DB에 대한 연결 설정
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session


# 연결하려는 DB의 기본 정보 설정
user_name = "user"
password = "password"
host = "db"  # docker-composeで定義したMySQLのサービス名
database_name = "kalendar"

DATABASE = 'mysql://%s:%s@%s/%s?charset=utf8' % (
    user_name,
    password,
    host,
    database_name
)

# DB와의 연결
ENGINE = create_engine(
    DATABASE,
    #encoding="utf8",
    echo=True,
    pool_size=10,
    max_overflow=20
)

# 세션 만들기
session = scoped_session(
    # ORM実行時の設定。自動コミットするか、自動反映するか
    sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=ENGINE
    )
)

# 모델에서 사용
Base = declarative_base()
# DB 연결을 위한 세션 클래스, 인스턴스가 생성되면 연결
Base.query = session.query_property()
