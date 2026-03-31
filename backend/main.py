import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from hybrid_recommender import (
    recommend_for_profile,
    recommend_cold_start,
    search_movies,
    get_similar_movies,
)

app = FastAPI(title="Personalized Recommendation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path("../data/ml-latest-small")
PROFILES_FILE = DATA_DIR / "profiles.json"
FEEDBACK_FILE = DATA_DIR / "feedback.csv"


class ProfileCreateRequest(BaseModel):
    username: str
    email: str


class FavoritesUpdateRequest(BaseModel):
    favorite_movie_ids: list[int]


class FeedbackItem(BaseModel):
    profile_id: int
    movieId: int
    title: str
    action: str  # "like" or "dislike"


class OnboardingRequest(BaseModel):
    selected_movie_ids: list[int]
    top_n: int = 10


def load_profiles():
    if not PROFILES_FILE.exists():
        return []
    try:
        data = json.loads(PROFILES_FILE.read_text())
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_profiles(profiles):
    PROFILES_FILE.write_text(json.dumps(profiles, indent=2))


def get_profile(profile_id: int):
    profiles = load_profiles()
    for profile in profiles:
        if int(profile.get("profile_id", -1)) == int(profile_id):
            return profile
    return None


@app.get("/")
def root():
    return {"message": "Recommendation API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/profile")
def create_profile(payload: ProfileCreateRequest):
    profiles = load_profiles()

    email = payload.email.strip().lower()
    username = payload.username.strip()

    if not username or not email:
        raise HTTPException(status_code=400, detail="username and email are required")

    # Return existing profile if email already exists
    for profile in profiles:
        if str(profile.get("email", "")).strip().lower() == email:
            return profile

    next_id = 1 if not profiles else max(int(p["profile_id"]) for p in profiles) + 1

    new_profile = {
        "profile_id": next_id,
        "username": username,
        "email": email,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "favorite_movie_ids": [],
    }

    profiles.append(new_profile)
    save_profiles(profiles)

    return new_profile


@app.get("/profile/{profile_id}")
def read_profile(profile_id: int):
    profile = get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@app.post("/profile/{profile_id}/favorites")
def update_favorites(profile_id: int, payload: FavoritesUpdateRequest):
    profiles = load_profiles()
    profile_index = None

    for idx, profile in enumerate(profiles):
        if int(profile.get("profile_id", -1)) == int(profile_id):
            profile_index = idx
            break

    if profile_index is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    unique_ids = []
    seen = set()
    for mid in payload.favorite_movie_ids:
        mid = int(mid)
        if mid not in seen:
            unique_ids.append(mid)
            seen.add(mid)

    profiles[profile_index]["favorite_movie_ids"] = unique_ids
    save_profiles(profiles)

    return profiles[profile_index]


@app.get("/recommendations/{profile_id}")
def get_recommendations(profile_id: int, top_n: int = 10):
    recs = recommend_for_profile(profile_id=profile_id, top_n=top_n)
    if isinstance(recs, str):
        raise HTTPException(status_code=404, detail=recs)

    return {
        "profile_id": profile_id,
        "recommendations": recs.to_dict(orient="records"),
    }


@app.post("/onboarding/recommendations")
def get_onboarding_recommendations(payload: OnboardingRequest):
    recs = recommend_cold_start(
        selected_movie_ids=payload.selected_movie_ids,
        top_n=payload.top_n,
    )
    return {
        "selected_movie_ids": payload.selected_movie_ids,
        "recommendations": recs,
    }


@app.get("/search-movies")
def movie_search(query: str, top_n: int = 10):
    results = search_movies(query=query, top_n=top_n)
    return {"query": query, "results": results}


@app.get("/similar-movies/{movie_id}")
def similar_movies(movie_id: int, top_n: int = 10):
    results = get_similar_movies(movie_id=movie_id, top_n=top_n)
    if results is None:
        raise HTTPException(status_code=404, detail="Movie not found")

    return {"movie_id": movie_id, "results": results}


@app.post("/feedback")
def save_feedback(item: FeedbackItem):
    if item.action not in {"like", "dislike"}:
        raise HTTPException(status_code=400, detail="action must be 'like' or 'dislike'")

    row = pd.DataFrame(
        [
            {
                "profile_id": item.profile_id,
                "movieId": item.movieId,
                "title": item.title,
                "action": item.action,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ]
    )

    if FEEDBACK_FILE.exists():
        row.to_csv(FEEDBACK_FILE, mode="a", header=False, index=False)
    else:
        row.to_csv(FEEDBACK_FILE, index=False)

    return {"status": "saved"}