# 🎬 Personalized Movie Recommender
<img width="2040" height="1962" alt="image" src="https://github.com/user-attachments/assets/591f3374-d281-4fc2-8b01-73efd85ebfc2" />

I made a full-stack hybrid recommendation system that combines Collaborative Filtering + Embeddings + Cold-Start Onboarding to deliver personalized movie suggestions with help of FastAPI (Python backend), React (Vite frontend) and Machine Learning (hybrid recommender + embeddings)

**Project Overview**

This project simulates how real-world platforms like Netflix, Amazon, and Spotify recommend content.

It solves key recommendation problems:

1. Personalized recommendations for existing users
2. Cold-start problem (new users with no history)
3. Semantic understanding using embeddings
4. Real-time learning using user feedback

   
**Features**
1. Hybrid Recommendation System

Combines:

Collaborative Filtering → “Users like you liked this”
Content-Based (Embeddings) → “This is similar to what you like”
Popularity Score → fallback for new users

2. Cold-Start Onboarding

New users can:

Search movies
Select favorites
Instantly get recommendations

3. Explainable Recommendations

Each movie includes:

“Because you liked [movie name]”

This improves transparency and user trust.

4. Real-Time Feedback Loop

Users can: 👍 Like nd 👎 Dislike

This feedback is stored and used to improve future recommendations.

5. Search & Similar Movies
Search any movie
View similar movies using embeddings

6. User Profiles
Login with username + email
Persistent profiles using local storage + backend
Switch accounts easily

**How It Works (Techincal pov)**

The final recommendation score is:

Final Score = 
  (Content Similarity × weight) +
  (Collaborative Filtering × weight) +
  (Popularity Score × weight)

Where:

Content = embedding similarity
CF = user behavior similarity
Popularity = global trend fallback


**How to use it**

Setup Backend

- cd backend
- python -m venv .venv
- source .venv/bin/activate   # Mac/Linux
- pip install -r requirements.txt

Download Dataset

Download MovieLens latest-small dataset:

This dataset I used: https://grouplens.org/datasets/movielens/

Place it inside:

data/ml-latest-small/

Prepare Data & Build Embeddings
python prepare_data.py
python build_embeddings.py

Run Backend
fastapi dev main.py

Backend runs at:

http://127.0.0.1:8000

Setup Frontend
cd ../frontend
npm install
npm run dev

Frontend runs at:

http://localhost:5173

🧪 How to Use
Open the app
- Create a profile (username + email)
- Search and select favorite movies
- Click Get Recommendations
- Like/Dislike movies to improve results
- Explore similar movies
- Screenshots (Add yours here)
- Search movies 🔍
- Personalized recommendations
- Explanation panel
- Onboarding flow
- Future Improvements
- Better ranking (time-decay, session-based learning)
- Evaluation metrics (Precision@K, Recall@K) 📊 
- Deployment (Vercel + Render) 🌐
- Movie posters (TMDB API)
- Deep learning models (Neural CF, transformers)
  
Why I think Project Stands Out: 
It combines classic ML + modern AI, handles cold-start problem, includes explainable AI, full end-to-end system (backend + frontend) and Real-world architecture

Need any help while setting it up, you can reach out to me
                                                          -Sanidhya.
