import pandas as pd
from pathlib import Path
from sklearn.metrics.pairwise import cosine_similarity

DATA_DIR = Path("../data/ml-latest-small")

# Load data
ratings = pd.read_csv(DATA_DIR / "ratings.csv")
movies = pd.read_csv(DATA_DIR / "movies.csv")

# Merge ratings with movie titles
ratings = ratings.merge(movies[["movieId", "title"]], on="movieId", how="left")

# Create user-item matrix: rows = users, columns = movies, values = ratings
user_item_matrix = ratings.pivot_table(
    index="userId",
    columns="title",
    values="rating"
)

# Fill missing ratings with 0 for similarity calculation
user_item_matrix_filled = user_item_matrix.fillna(0)

# Compute similarity between users
user_similarity = cosine_similarity(user_item_matrix_filled)
user_similarity_df = pd.DataFrame(
    user_similarity,
    index=user_item_matrix.index,
    columns=user_item_matrix.index
)

def recommend_movies_for_user(user_id, top_n=10, similar_users_n=5):
    if user_id not in user_item_matrix.index:
        return f"User {user_id} not found."

    # Ratings given by target user
    user_ratings = user_item_matrix.loc[user_id]

    # Movies already watched/rated by the user
    watched_movies = user_ratings.dropna().index.tolist()

    # Similarity scores for this user
    sim_scores = user_similarity_df[user_id].drop(user_id)

    # Top similar users
    top_similar_users = sim_scores.sort_values(ascending=False).head(similar_users_n)

    # Weighted recommendation score for each movie
    movie_scores = {}

    for other_user_id, similarity in top_similar_users.items():
        other_user_ratings = user_item_matrix.loc[other_user_id]

        for movie_title, rating in other_user_ratings.dropna().items():
            if movie_title not in watched_movies:
                if movie_title not in movie_scores:
                    movie_scores[movie_title] = {"score": 0.0, "weight": 0.0}

                movie_scores[movie_title]["score"] += similarity * rating
                movie_scores[movie_title]["weight"] += abs(similarity)

    # Final normalized scores
    recommendations = []
    for movie_title, values in movie_scores.items():
        if values["weight"] > 0:
            final_score = values["score"] / values["weight"]
            recommendations.append((movie_title, final_score))

    # Sort by highest score
    recommendations = sorted(recommendations, key=lambda x: x[1], reverse=True)[:top_n]

    return pd.DataFrame(recommendations, columns=["title", "score"])

if __name__ == "__main__":
    print("Users:", user_item_matrix.shape[0])
    print("Movies:", user_item_matrix.shape[1])

    print("\nRecommendations for user 1:")
    print(recommend_movies_for_user(1, top_n=10))