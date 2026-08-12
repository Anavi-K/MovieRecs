import pandas as pd

ratings = pd.read_csv("../data/ratings.csv")

print("Number of ratings:", len(ratings))

print("\nFirst 10 ratings:")
print(ratings.head(10))

print("\nColumns:")
print(ratings.columns)

print("\nRating statistics:")
print(ratings["rating"].describe())

print("\nNumber of unique users:")
print(ratings["userId"].nunique())

print("\nNumber of movies rated:")
print(ratings["movieId"].nunique())