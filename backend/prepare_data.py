import pandas as pd
from pathlib import Path

DATA_DIR = Path("../data/ml-latest-small")

ratings = pd.read_csv(DATA_DIR / "ratings.csv")
movies = pd.read_csv(DATA_DIR / "movies.csv")
tags = pd.read_csv(DATA_DIR / "tags.csv")


# Clean text fields
movies["genres"] = movies["genres"].fillna("")
tags["tag"] = tags["tag"].fillna("")


# Combine tags per movie
tags_grouped = tags.groupby("movieId")["tag"].apply(lambda x: " ".join(x)).reset_index()

# Merge tags into movies
movies = movies.merge(tags_grouped, on="movieId", how="left")
movies["tag"] = movies["tag"].fillna("")

# Create ONE text field (important for embeddings)
movies["content"] = movies["title"] + " " + movies["genres"] + " " + movies["tag"]


# Preview result
print(movies[["movieId", "title", "content"]].head())


# Save cleaned file
movies.to_csv(DATA_DIR / "movies_cleaned.csv", index=False)

print("\n Cleaned dataset saved as movies_cleaned.csv")