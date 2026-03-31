import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

DATA_DIR = Path("../data/ml-latest-small")

ratings_path = DATA_DIR / "ratings.csv"
movies_cleaned_path = DATA_DIR / "movies_cleaned.csv"
embeddings_path = DATA_DIR / "movie_embeddings.npy"
profiles_path = DATA_DIR / "profiles.json"
feedback_path = DATA_DIR / "feedback.csv"

ratings = pd.read_csv(ratings_path)
movies = pd.read_csv(movies_cleaned_path)

if not embeddings_path.exists():
    raise FileNotFoundError("movie_embeddings.npy not found. Run build_embeddings.py first.")

embeddings = np.load(embeddings_path)

if len(embeddings) != len(movies):
    raise ValueError(
        f"Embeddings count ({len(embeddings)}) does not match movies count ({len(movies)})."
    )

def load_profiles():
    if not profiles_path.exists():
        return []
    try:
        data = json.loads(profiles_path.read_text())
        return data if isinstance(data, list) else []
    except Exception:
        return []

def load_feedback():
    if not feedback_path.exists():
        return pd.DataFrame(columns=["profile_id", "movieId", "title", "action", "timestamp"])

    try:
        fb = pd.read_csv(feedback_path)

        # Backward compatibility with older files
        if "profile_id" not in fb.columns and "userId" in fb.columns:
            fb = fb.rename(columns={"userId": "profile_id"})

        expected_cols = ["profile_id", "movieId", "title", "action", "timestamp"]
        for col in expected_cols:
            if col not in fb.columns:
                fb[col] = pd.Series(dtype="object")

        return fb[expected_cols]

    except Exception:
        return pd.DataFrame(columns=["profile_id", "movieId", "title", "action", "timestamp"])

def get_profile_by_id(profile_id):
    all_profiles = load_profiles()
    for profile in all_profiles:
        if int(profile.get("profile_id", -1)) == int(profile_id):
            return profile
    return None


# Movie stats + popularity

movie_stats = ratings.groupby("movieId").agg(
    avg_rating=("rating", "mean"),
    rating_count=("rating", "count")
).reset_index()

movies = movies.merge(movie_stats, on="movieId", how="left")
movies["avg_rating"] = movies["avg_rating"].fillna(0)
movies["rating_count"] = movies["rating_count"].fillna(0)

def _minmax(series: pd.Series) -> pd.Series:
    if series.empty:
        return series
    min_v = series.min()
    max_v = series.max()
    if max_v == min_v:
        return pd.Series(np.zeros(len(series)), index=series.index)
    return (series - min_v) / (max_v - min_v)

movies["rating_count_log"] = np.log1p(movies["rating_count"])
movies["avg_rating_norm"] = _minmax(movies["avg_rating"])
movies["rating_count_norm"] = _minmax(movies["rating_count_log"])
movies["popularity_score"] = 0.7 * movies["avg_rating_norm"] + 0.3 * movies["rating_count_norm"]

movie_lookup = movies.set_index("movieId")
movie_title_to_idx = pd.Series(movies.index, index=movies["title"]).drop_duplicates()
movie_id_to_idx = pd.Series(movies.index, index=movies["movieId"]).drop_duplicates()


# Similarity setup

embedding_similarity = cosine_similarity(embeddings)


# Helpers

def _normalize_map(score_map):
    if not score_map:
        return score_map
    values = list(score_map.values())
    min_v = min(values)
    max_v = max(values)
    if max_v == min_v:
        return {k: 0.0 for k in score_map}
    return {k: (v - min_v) / (max_v - min_v) for k, v in score_map.items()}

def get_popular_movies(top_n=10, exclude_movie_ids=None):
    exclude_movie_ids = set(exclude_movie_ids or [])
    df = movies[~movies["movieId"].isin(exclude_movie_ids)].copy()

    df = df.sort_values(
        by=["popularity_score", "avg_rating", "rating_count"],
        ascending=False
    ).head(top_n)

    return df[[
        "movieId",
        "title",
        "genres",
        "avg_rating",
        "rating_count",
        "popularity_score"
    ]].assign(
        avg_rating=lambda x: x["avg_rating"].round(2),
        popularity_score=lambda x: x["popularity_score"].round(4)
    ).to_dict(orient="records")

def search_movies(query, top_n=10):
    if not query or not str(query).strip():
        return []

    q = str(query).strip().lower()
    matches = movies[movies["title"].str.lower().str.contains(re.escape(q), na=False)]

    return matches[[
        "movieId",
        "title",
        "genres",
        "avg_rating",
        "rating_count"
    ]].head(top_n).to_dict(orient="records")

def get_similar_movies(movie_id, top_n=10):
    movie_rows = movies.index[movies["movieId"] == movie_id].tolist()
    if not movie_rows:
        return None

    idx = movie_rows[0]
    sim_list = list(enumerate(embedding_similarity[idx]))
    sim_list = sorted(sim_list, key=lambda x: x[1], reverse=True)

    top_similar = sim_list[1: top_n + 1]

    results = []
    for movie_idx, score in top_similar:
        row = movies.iloc[movie_idx]
        results.append({
            "movieId": int(row["movieId"]),
            "title": row["title"],
            "genres": row["genres"],
            "avg_rating": round(float(row["avg_rating"]), 2),
            "rating_count": int(row["rating_count"]),
            "score": round(float(score), 4),
        })

    return results

def _build_profile_item_matrix():
    """
    Build a simple implicit feedback matrix:
    - favorites from profile onboarding count as 1
    - likes from feedback count as 1
    """
    all_profiles = load_profiles()
    fb = load_feedback()

    if not all_profiles and fb.empty:
        return pd.DataFrame()

    row_map = {}

    for profile in all_profiles:
        pid = int(profile.get("profile_id"))
        liked = set(profile.get("favorite_movie_ids", []))
        row_map.setdefault(pid, set()).update(liked)

    if not fb.empty:
        likes = fb[fb["action"] == "like"].copy()
        for _, row in likes.iterrows():
            pid = int(row["profile_id"])
            mid = int(row["movieId"])
            row_map.setdefault(pid, set()).add(mid)

    if not row_map:
        return pd.DataFrame()

    all_movie_ids = sorted({mid for mids in row_map.values() for mid in mids})
    matrix = pd.DataFrame(0.0, index=sorted(row_map.keys()), columns=all_movie_ids)

    for pid, mids in row_map.items():
        for mid in mids:
            matrix.loc[pid, mid] = 1.0

    return matrix


# Recommendations

def recommend_for_profile(profile_id, top_n=10, content_weight=0.55, cf_weight=0.30, popularity_weight=0.15):
    """
    Real app recommender:
    - profile onboarding favorites
    - profile likes/dislikes
    - collaborative filtering across app profiles when available
    - embeddings for semantic similarity
    - popularity fallback
    """
    profile = get_profile_by_id(profile_id)
    if not profile:
        return f"Profile {profile_id} not found."

    fb = load_feedback()
    profile_feedback = fb[fb["profile_id"] == int(profile_id)] if not fb.empty else pd.DataFrame()

    favorite_ids = set(int(x) for x in profile.get("favorite_movie_ids", []))
    liked_feedback_ids = set()
    disliked_feedback_ids = set()

    if not profile_feedback.empty:
        liked_feedback_ids = set(
            profile_feedback[profile_feedback["action"] == "like"]["movieId"].astype(int).tolist()
        )
        disliked_feedback_ids = set(
            profile_feedback[profile_feedback["action"] == "dislike"]["movieId"].astype(int).tolist()
        )

    seed_ids = list(favorite_ids | liked_feedback_ids)

    if not seed_ids:
        return pd.DataFrame(get_popular_movies(top_n=top_n))

   
    # Content scoring from embeddings
   
    content_scores = np.zeros(len(movies), dtype=float)

    for mid in seed_ids:
        if mid in movie_id_to_idx:
            idx = movie_id_to_idx[mid]
            content_scores += embedding_similarity[idx]

    for mid in disliked_feedback_ids:
        if mid in movie_id_to_idx:
            idx = movie_id_to_idx[mid]
            content_scores -= 0.35 * embedding_similarity[idx]

    candidate_mask = ~movies["movieId"].isin(set(seed_ids) | set(disliked_feedback_ids))
    content_candidates = movies.loc[candidate_mask].copy()
    content_candidates["content_score"] = content_scores[candidate_mask.values]

    content_map = {
        int(row.movieId): float(row.content_score)
        for row in content_candidates.itertuples(index=False)
    }
    content_map = _normalize_map(content_map)

   
    # Collaborative filtering from app profiles
   
    cf_map = {}
    profile_matrix = _build_profile_item_matrix()

    if (
        not profile_matrix.empty
        and int(profile_id) in profile_matrix.index
        and profile_matrix.shape[0] > 1
    ):
        target_vec = profile_matrix.loc[[int(profile_id)]]
        sims = cosine_similarity(target_vec, profile_matrix)[0]
        sim_series = pd.Series(sims, index=profile_matrix.index).drop(int(profile_id), errors="ignore")
        top_similar_profiles = sim_series.sort_values(ascending=False).head(5)

        target_likes = set(profile_matrix.columns[profile_matrix.loc[int(profile_id)] > 0].tolist())

        for other_pid, sim in top_similar_profiles.items():
            if sim <= 0:
                continue

            other_likes = profile_matrix.columns[profile_matrix.loc[int(other_pid)] > 0].tolist()
            for mid in other_likes:
                if mid in target_likes or mid in disliked_feedback_ids:
                    continue
                cf_map[mid] = cf_map.get(mid, 0.0) + float(sim)

    cf_map = _normalize_map(cf_map)

   
    # Popularity score
   
    popularity_map = {}
    for row in movies.itertuples(index=False):
        popularity_map[int(row.movieId)] = float(row.popularity_score)

   
    # Combine
   
    all_candidate_ids = set(content_map.keys()) | set(cf_map.keys()) | set(popularity_map.keys())
    all_candidate_ids -= set(seed_ids)
    all_candidate_ids -= set(disliked_feedback_ids)

    results = []
    for mid in all_candidate_ids:
        if mid not in movie_lookup.index:
            continue

        row = movie_lookup.loc[mid]
        content_score = content_map.get(mid, 0.0)
        cf_score = cf_map.get(mid, 0.0)
        pop_score = popularity_map.get(mid, 0.0)

        final_score = (
            content_weight * content_score
            + cf_weight * cf_score
            + popularity_weight * pop_score
        )

        
        # Generate explanation
     
        reason = ""

        if seed_ids:
            best_match = None
            best_score = -1.0

            for sid in seed_ids:
                if sid in movie_id_to_idx and mid in movie_id_to_idx:
                    sim = float(embedding_similarity[movie_id_to_idx[sid]][movie_id_to_idx[mid]])
                    if sim > best_score:
                        best_score = sim
                        best_match = sid

            if best_match and best_match in movie_lookup.index:
                reason = f"Because you liked {movie_lookup.loc[best_match]['title']}"

        if not reason:
            genres = [g for g in str(row["genres"]).split("|") if g and g != "(no genres listed)"]
            if genres:
                reason = f"Popular in {genres[0]} movies"
            else:
                reason = "Based on your profile activity"

        results.append({
            "movieId": int(mid),
            "title": row["title"],
            "genres": row["genres"],
            "final_score": round(float(final_score), 4),
            "cf_score": round(float(cf_score), 4),
            "content_score": round(float(content_score), 4),
            "popularity_score": round(float(pop_score), 4),
            "avg_rating": round(float(row["avg_rating"]), 2),
            "rating_count": int(row["rating_count"]),
            "reason": reason,
        })

    results = sorted(results, key=lambda x: x["final_score"], reverse=True)[:top_n]
    return pd.DataFrame(results)

def recommend_cold_start(selected_movie_ids, top_n=10, content_weight=0.85, popularity_weight=0.15):
    if not selected_movie_ids:
        return pd.DataFrame(get_popular_movies(top_n=top_n))

    selected_movie_ids = list(dict.fromkeys([int(x) for x in selected_movie_ids]))
    valid_ids = [mid for mid in selected_movie_ids if mid in movie_id_to_idx]

    if not valid_ids:
        return pd.DataFrame(get_popular_movies(top_n=top_n))

    selected_indices = [movie_id_to_idx[mid] for mid in valid_ids]

    content_scores = np.zeros(len(movies), dtype=float)
    for idx in selected_indices:
        content_scores += embedding_similarity[idx]

    content_scores = content_scores / len(selected_indices)

    excluded = set(valid_ids)
    candidate_mask = ~movies["movieId"].isin(excluded)

    candidates = movies.loc[candidate_mask].copy()
    candidates["content_score"] = content_scores[candidate_mask.values]

    if len(candidates) > 0:
        min_c = candidates["content_score"].min()
        max_c = candidates["content_score"].max()
        if max_c > min_c:
            candidates["content_score"] = (candidates["content_score"] - min_c) / (max_c - min_c)
        else:
            candidates["content_score"] = 0.0

    candidates["final_score"] = (
        content_weight * candidates["content_score"]
        + popularity_weight * candidates["popularity_score"]
    )

    candidates = candidates.sort_values(
        by=["final_score", "content_score", "popularity_score"],
        ascending=False
    ).head(top_n)

    return candidates[[
        "movieId",
        "title",
        "genres",
        "final_score",
        "content_score",
        "popularity_score",
        "avg_rating",
        "rating_count"
    ]].assign(
        final_score=lambda x: x["final_score"].round(4),
        content_score=lambda x: x["content_score"].round(4),
        popularity_score=lambda x: x["popularity_score"].round(4),
        avg_rating=lambda x: x["avg_rating"].round(2),
    ).to_dict(orient="records")

if __name__ == "__main__":
    print("Profile-based recommendations preview:")
    print(get_popular_movies(top_n=5))