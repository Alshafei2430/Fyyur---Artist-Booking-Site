CREATE TABLE books 
(
    id INTEGER UNIQUE NOT NULL,
    isbn VARCHAR NOT NULL,
    title VARCHAR NOT NULL UNIQUE,
    author VARCHAR NOT NULL,
    year VARCHAR NOT NULL,

)
CREATE TABLE reviews
(
    user_id_r INTEGER REFERENCES user_info(user_id),
    scale INTEGER, 
    comment VARCHAR,
    book_title VARCHAR NOT NULL REFERENCES books(title)

)
CREATE TABLE user_info 
(
    user_id INTEGER UNIQUE NOT NULL,
    email VARCHAR NOT NULL,
    password VARCHAR NOT NULL,
)