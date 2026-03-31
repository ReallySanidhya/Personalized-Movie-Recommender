import pandas as pd
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DATA_DIR = Path("../data/ml-latest-small")

# Load cleaned movie data
movies = pd.read_csv(DATA_DIR / "movies_cleaned.csv")

# Make sure content is a string and has no missing values
movies["content"] = movies["content"].fillna("").astype(str)

# Create TF-IDF matrix from movie content
vectorizer = TfidfVectorizer(stop_words="english")
tfidf_matrix = vectorizer.fit_transform(movies["content"])

# Compute similarity between all movies
similarity_matrix = cosine_similarity(tfidf_matrix)

# Create mapping from movie title to index
movie_indices = pd.Series(movies.index, index=movies["title"]).drop_duplicates()

def recommend_movies(title, top_n=5):
    if title not in movie_indices:
        return f"Movie '{title}' not found."

    idx = movie_indices[title]
    sim_scores = list(enumerate(similarity_matrix[idx]))

    # Sort by similarity score, highest first
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

    # Skip the first one because it is the same movie
    top_movies = sim_scores[1:top_n + 1]

    recommended = movies.iloc[[i[0] for i in top_movies]][["title", "genres"]].copy()
    recommended["score"] = [round(score, 4) for _, score in top_movies]
    return recommended

if __name__ == "__main__":
    print("Movies loaded:", movies.shape[0])
    print("\nRecommendations for Toy Story (1995):")
    print(recommend_movies("Toy Story (1995)", top_n=5))