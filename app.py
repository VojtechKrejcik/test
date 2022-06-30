from flask import Flask, render_template, request, flash
from book_rec import *

app = Flask(__name__)
app.secret_key = "holajej"
favorite_book = '0345339703'
ratings_df, books_df = download_data()
books_df = average_rating(books_df, ratings_df)

@app.route("/recommend")
def index():
    books_to_compare, readers_of_book = get_readers_and_their_books(ratings_df, books_df, book_isbn = favorite_book)
    result_list = recommend_books(favorite_book, books_to_compare, readers_of_book, books_df, ratings_df)
    books_df[books_df['ISBN'].isin(result_list['book'])]

    flash(books_df[books_df['ISBN'] == favorite_book][["Book-Title", 'Image-URL-M']].values.tolist(), 'title')

    result = books_df[books_df['ISBN'].isin(result_list['book'])][["Book-Title", 'Image-URL-M']].values.tolist()
    for item in result:
        flash(item)
    return render_template("index.html")


@app.route("/greet", methods=["POST", "GET"])
def greet():
    book_title = request.form['name_input']
    favorite_book = name_to_isbn(book_title, books_df)
    books_to_compare, readers_of_book = get_readers_and_their_books(ratings_df, books_df, book_isbn = favorite_book)
    result_list = recommend_books(favorite_book, books_to_compare, readers_of_book, books_df, ratings_df)
    books_df[books_df['ISBN'].isin(result_list['book'])]

    flash(books_df[books_df['ISBN'] == favorite_book][["Book-Title", 'Image-URL-M']].values.tolist(), 'title')

    result = books_df[books_df['ISBN'].isin(result_list['book'])][["Book-Title", 'Image-URL-M']].values.tolist()
    if not result:
        flash(["Sorry, We dont have enough data to make proper recommandation for you.", "https://ps.w.org/easy-under-construction/assets/icon-256x256.png?rev=2417171"])
    for item in result:
        flash(item)
    return render_template("index.html")


