CREATE TABLE FOOD (
	food_name VARCHAR(25) NOT NULL,
   	weight DECIMAL(10,6) NOT NULL,
   	calories DECIMAL(10,6) NOT NULL,
   	carbohydrates DECIMAL(10,6) NOT NULL,
   	protein DECIMAL(10,6) NOT NULL,
   	fat DECIMAL(10,6) NOT NULL,
   	sugars DECIMAL(10,6) NOT NULL,
   	sodium DECIMAL(10,6) NOT NULL
   	) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE USER (
	user_name varchar(255) NOT NULL,
	share_id varchar(255)
	) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IMAGE (
	image_name varchar(255) NOT NULL,
	mealtime varchar(50) NOT NULL,
	date varchar(50) NOT NULL,
	user_name varchar(255) NOT NULL
	) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE RESULT (
	ml_id varchar(255) NOT NULL,
	food_result varchar(25) NOT NULL,
	weight_result DECIMAL(10,6) NOT NULL,
	image_name varchar(255) NOT NULL,
	food_name varchar(25) NOT NULL
	) ENGINE=InnoDB DEFAULT CHARSET=utf8;

ALTER TABLE FOOD
	ADD PRIMARY KEY (food_name);

ALTER TABLE USER
        ADD PRIMARY KEY (user_name);

ALTER TABLE IMAGE
        ADD PRIMARY KEY (image_name);

ALTER TABLE RESULT
        ADD PRIMARY KEY (ml_id);

ALTER TABLE IMAGE
	ADD FOREIGN KEY (user_name) REFERENCES USER(user_name);

ALTER TABLE RESULT
        ADD FOREIGN KEY (image_name) REFERENCES IMAGE(image_name);

ALTER TABLE RESULT
        ADD FOREIGN KEY (food_name) REFERENCES FOOD(food_name);

