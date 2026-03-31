import pandas as pd
from pathlib import Path

# Adjust this path if your dataset folder is different
DATA_DIR = Path("../data/ml-latest-small")

ratings_path = DATA_DIR / "ratings.csv"
movies_path = DATA_DIR / "movies.csv"
tags_path = DATA_DIR / "tags.csv"

ratings = pd.read_csv(ratings_path)
movies = pd.read_csv(movies_path)
tags = pd.read_csv(tags_path)

print("Ratings shape:", ratings.shape)
print("Movies shape:", movies.shape)
print("Tags shape:", tags.shape)

print("\nRatings preview:")
print(ratings.head())

print("\nMovies preview:")
print(movies.head())

print("\nTags preview:")
print(tags.head())

print("\nMissing values in movies:")
print(movies.isna().sum())

movies["genres"] = movies["genres"].fillna("")
tags["tag"] = tags["tag"].fillna("")