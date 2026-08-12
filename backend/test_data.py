import pandas as pd

movies = pd.read_csv("../data/movies.csv")

print("Number of movies:", len(movies))
print()

print("First 10 movies:")
print(movies.head(10))
print()

print("Missing values:")
print(movies.isnull().sum())
print()

print("Number of unique genres:")
genres = movies["genres"].str.split("|").explode().unique()
print(len(genres))
print()

print("Genres:")
print(genres)