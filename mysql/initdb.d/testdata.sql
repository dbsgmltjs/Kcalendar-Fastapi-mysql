LOAD DATA INFILE '/data/foodData.csv' INTO TABLE FOOD 
CHARACTER SET utf8 
FIELDS TERMINATED BY '|' 
LINES TERMINATED BY '\n' 
IGNORE 1 LINES;

# 기본 유저 생성
INSERT INTO USER (user_name) VALUES ("usersimg");
