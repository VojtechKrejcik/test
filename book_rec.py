import pandas as pd
import numpy as np
import urllib.request
import zipfile
import io
from fuzzywuzzy import process, fuzz


def download_data(url="http://www2.informatik.uni-freiburg.de/~cziegler/BX/BX-CSV-Dump.zip", folder="downloads/"):
    """Downloads data and returns them as Pandas DataFrmae"""
    with urllib.request.urlopen(url) as f:
        data = f.read()
    
    z = zipfile.ZipFile(io.BytesIO(data))
    z.extractall(folder)
    ratings_df = pd.read_csv(folder + 'BX-Book-Ratings.csv', encoding='cp1251', sep=';')
    ratings_df = ratings_df[ratings_df['Book-Rating']!=0]
    books_df = pd.read_csv(folder + 'BX-Books.csv',  encoding='cp1251', sep=';',error_bad_lines=False)
    return ratings_df, books_df

def average_rating(books_df, ratings_df):
    """Returns books_df with added column Average-Rating """
    dataset = pd.merge(ratings_df, books_df, on=['ISBN'])
    dataset = dataset.groupby(['ISBN']).mean().rename(columns = {'Book-Rating':'Average-Rating'})
    return pd.merge(books_df, dataset['Average-Rating'],how='left', on=['ISBN'])
    
def get_readers_and_their_books(ratings_df, books_df, book_isbn, threshold = 3):
    """Returns list of readers of the book and list of books, that people who liked the book also liked"""
    merged_df = pd.merge(ratings_df, books_df, on=['ISBN'])
    # ids of people who reviewed the book
    readers = merged_df['User-ID'][merged_df['ISBN'] == book_isbn].unique()
    books_of_readers = merged_df[(merged_df['User-ID'].isin(readers))]
    number_of_rating_per_book = books_of_readers.groupby(['ISBN']).agg('count').reset_index()
    #select only books which have actually higher number of ratings than threshold
    books_to_compare = number_of_rating_per_book['ISBN'][number_of_rating_per_book['User-ID'] >= threshold].tolist()
    return books_to_compare, readers

def name_to_isbn(name, books_df):
    """Searches name of the title using Levenshtein distance implemented by fuzzuwuzzy library"""
    best_results = process.extract(name, books_df['Book-Title'].unique().tolist(), scorer=fuzz.token_sort_ratio)
    print(best_results)
    return books_df[books_df['Book-Title'] == best_results[0][0]]['ISBN'].head(1).item()

def recommend_books(book_isbn, books_to_compare, readers_of_book, books_df, ratings_df):
    ratings_data_raw =  pd.merge(ratings_df, books_df, on=['ISBN'])[['User-ID', 'Average-Rating', 'ISBN', 'Book-Rating']]
    ratings_data_raw_nodup = ratings_data_raw[ratings_data_raw['ISBN'].isin(books_to_compare)][ratings_data_raw['User-ID'].isin(readers_of_book)]
    dataset_for_corr = ratings_data_raw_nodup.pivot(index='User-ID', columns='ISBN', values='Book-Rating')
    dataset_of_other_books = dataset_for_corr.copy(deep=False)
    
    book_titles = []
    correlations = []
    avgrating = []
    # corr computation
    for book_title in list(dataset_of_other_books.columns.values):
        book_titles.append(book_title)
        correlations.append(dataset_for_corr[book_isbn].corr(dataset_of_other_books[book_title]))
        tab=(ratings_data_raw[ratings_data_raw['ISBN'] == book_title].groupby(ratings_data_raw['ISBN']).mean())
        avgrating.append(tab['Book-Rating'].min())
    # final dataframe of all correlation of each book   
    corr_fellowship = pd.DataFrame(list(zip(book_titles, correlations, avgrating)), columns=['book','corr','avg_rating'])

    result_list = corr_fellowship.sort_values('corr', ascending = False).head(11)
    return result_list[result_list['book'] != book_isbn]
    

if __name__ == "__main__":
    favorite_book = '0345339703'
    ratings_df, books_df = download_data()
    books_df = average_rating(books_df, ratings_df)
    #favorite_book = name_to_isbn("the lord of the rings", books_df)
    books_to_compare, readers_of_book = get_readers_and_their_books(ratings_df, books_df, book_isbn = favorite_book)
    result_list = recommend_books(favorite_book, books_to_compare, readers_of_book, books_df, ratings_df)
    print(books_df[books_df['ISBN'].isin(result_list['book'])])
