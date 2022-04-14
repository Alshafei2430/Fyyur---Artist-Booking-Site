import os, requests 

from flask import Flask, session, render_template, request, redirect, url_for, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SECRET_KEY"] = "EdEvg3Kyr-PDQts5dhcPKg"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/signup", methods=["POST", "GET"])
def signup():
    if request.method == "POST":
        req = request.form
        email = req.get("email")
        password = req.get("password")
        db.execute("INSERT INTO user_info  (email, password) VALUES (:email, :password)",
         {"email": email, "password": password})
        db.commit()
        return redirect(url_for("home"))
    
    return render_template("signup.html")

@app.route("/login", methods = ["GET", "POST"] )
def login():
    if request.method == "POST":
        session["user_data"] = {}
        email = request.form["email"]
        f_password = request.form["password"]
        if db.execute("SELECT email FROM user_info WHERE email=:email", {"email": email}).rowcount == 0:
            return redirect(request.url)
        data = db.execute("SELECT * FROM user_info WHERE email=:email", {"email": email})
        for d in data:
            passw = d.password
            userid = d.user_id
        if f_password != passw:
            return "Login successful, welcome"
        else:
            session["user_data"]["user_id"] = userid
            return redirect(url_for("search"))
    return render_template("login.html")


@app.route("/search", methods=["POST", "GET"])
def search():
    if request.method == "POST":
        req = request.form
        isbn = req.get("isbn")
        title = req.get("title")
        author = req.get("author")
        if not (isbn or title or author):
            return redirect(request.url)
        isbn = f"%{isbn}%"
        title = f"%{title}%"
        author = f"%{author}%" 
        # ids = db.execute("SELECT id FROM books WHERE (isbn LIKE :isbn) AND (title LIKE :title) AND (author LIKE :author)",
        #                     {'isbn': isbn, 'title': title, 'author': author })
        books = db.execute("SELECT * FROM books WHERE id IN ( SELECT id FROM books WHERE (isbn LIKE :isbn) AND (title LIKE :title) AND (author LIKE :author))",
                            {'isbn': isbn, 'title': title, 'author': author })
        if books.rowcount == 0:
            return render_template("error.html", message = "book is not found")
        return render_template("display.html", books = books)
    return render_template("search.html")
    
@app.route("/book/<string:isbn>")
def book(isbn):
    if session.get("user_data", None) is not None:
            session["user_data"]["isbn"] = isbn
            book = db.execute("SELECT * FROM books WHERE isbn =:isbn", {"isbn": isbn}).fetchall()
            res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "BeQKHKMGw7vdTLOt2JLPPA", "isbns": isbn})
            data = res.json()
            work_rating_count = data["books"][0]["work_ratings_count"]
            average_rating = data["books"][0]['average_rating']
            return render_template("book.html", book=book, work_rating_count = work_rating_count, average_rating = average_rating)
    return redirect(url_for('login'))

@app.route("/review")
def review():
    user_data = session.get("user_data", None)
    if user_data is not None:
        if user_data.get("isbn", None) is not None:
            isbn = session["user_data"]["isbn"]
            user_id = session["user_data"]["user_id"]
            if db.execute("SELECT * FROM reviews WHERE user_id_r=:user_id AND isbn_r=:isbn", {"user_id":user_id, "isbn":isbn}).rowcount == 0:
                return render_template("review.html")
            return redirect(url_for("search"))
    return redirect(url_for("search"))

@app.route("/submit_review", methods = ["POST"])
def submit_review():
    req = request.form
    scale = req.get("scale")
    comment = req.get("comment")    
    user_id = session["user_data"]["user_id"]
    isbn = session["user_data"]["isbn"]
    db.execute("INSERT INTO reviews (user_id_r, scale, comment, isbn_r) VALUES (:user_id, :scale, :comment, :isbn_r)", {"user_id": user_id, "scale":scale, "comment":comment, "isbn_r": isbn}) 
    db.commit()
    session.pop("isbn", None)
    return redirect(url_for("search"))

@app.route("/profile")
def profile():
    user_data = session.get("user_data", None)
    if user_data is not None:
        if  user_data.get("user_id", None) is not None:
            user_id = session["user_data"]["user_id"]
            userdata = db.execute("SELECT isbn, title, author, year, scale, comment FROM reviews JOIN books ON isbn = isbn_r WHERE user_id_r=:id", {"id": user_id})
            return render_template("profile.html", userdata = userdata)

    return redirect(url_for("login"))

@app.route("/signout")
def signout():
    print(session)
    session.pop("user_data", None)
    return redirect(url_for("login"))

@app.route("/api/<string:isbn>")
def book_api(isbn):
    book = db.execute("SELECT * FROM books WHERE isbn=:isbn", {"isbn": isbn})
    if book.rowcount == 0:
        return jsonify({ "error": "Book not found"}), 422
    for book in book:
        book = {"isbn": book.isbn, "title": book.title, "author": book.author, "year": book.year}
    print(book)
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "BeQKHKMGw7vdTLOt2JLPPA", "isbns": isbn})
    data = res.json()
    print(data)
    return jsonify({
            "title": book["title"],
            "author": book["author"],
            "year": book["year"],
            "isbn": book["isbn"],
            "review_count": data["books"][0]["reviews_count"],
            "average_score": data["books"][0]["average_rating"]
        })


# Host
# ec2-18-209-187-54.compute-1.amazonaws.com
# Database
# de7e7r1m5ovjjk
# User
# pixxybawfokgib
# Port
# 5432
# Password
# 43797d99be2e0e64531dedc92550b949d05b2ec7a18f7c17e0f0d18cf9fe1f64
# URI
# postgres://pixxybawfokgib:43797d99be2e0e64531dedc92550b949d05b2ec7a18f7c17e0f0d18cf9fe1f64@ec2-18-209-187-54.compute-1.amazonaws.com:5432/de7e7r1m5ovjjk
# Heroku CLI
# heroku pg:psql postgresql-infinite-76729 --app mfwawfs

# key: BeQKHKMGw7vdTLOt2JLPPA
# secret: dXRLBHH5QsPTFbYHK0tXGiHSg86iQJyKee5tEBzLv8

