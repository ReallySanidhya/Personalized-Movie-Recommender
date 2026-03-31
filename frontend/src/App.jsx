import { useEffect, useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";
const PROFILE_KEY = "reco_profile_v1";
const FAVORITES_KEY = "reco_favorites_v1";

function formatGenres(genres) {
  if (!genres) return "";
  return String(genres).replaceAll("|", ", ");
}

function App() {
  const [profile, setProfile] = useState(null);
  const [showSignup, setShowSignup] = useState(false);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [signupError, setSignupError] = useState("");
  const [signupLoading, setSignupLoading] = useState(false);

  const [topN, setTopN] = useState(10);
  const [recs, setRecs] = useState([]);
  const [loadingRecs, setLoadingRecs] = useState(false);

  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [loadingSearch, setLoadingSearch] = useState(false);

  const [selectedMovie, setSelectedMovie] = useState(null);
  const [selectedDetails, setSelectedDetails] = useState(null);
  const [similarMovies, setSimilarMovies] = useState([]);
  const [loadingSimilar, setLoadingSimilar] = useState(false);

  const [onboardingQuery, setOnboardingQuery] = useState("");
  const [onboardingResults, setOnboardingResults] = useState([]);
  const [selectedFavorites, setSelectedFavorites] = useState([]);

  const [error, setError] = useState("");

  const [feedbackState, setFeedbackState] = useState({});

  const profileId = profile?.profile_id;

  useEffect(() => {
    const storedProfile = localStorage.getItem(PROFILE_KEY);
    const storedFavorites = localStorage.getItem(FAVORITES_KEY);

    if (storedProfile) {
      try {
        const parsedProfile = JSON.parse(storedProfile);
        setProfile(parsedProfile);
        setShowSignup(false);
      } catch {
        localStorage.removeItem(PROFILE_KEY);
        setShowSignup(true);
      }
    } else {
      setShowSignup(true);
    }

    if (storedFavorites) {
      try {
        setSelectedFavorites(JSON.parse(storedFavorites));
      } catch {
        localStorage.removeItem(FAVORITES_KEY);
      }
    }
  }, []);

  const saveFavoritesLocally = (favorites) => {
    setSelectedFavorites(favorites);
    localStorage.setItem(FAVORITES_KEY, JSON.stringify(favorites));
  };

  const createProfile = async (e) => {
    e.preventDefault();

    try {
      setSignupLoading(true);
      setSignupError("");

      const res = await fetch(`${API_URL}/profile`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, email }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to create profile");
      }

      const data = await res.json();
      setProfile(data);
      localStorage.setItem(PROFILE_KEY, JSON.stringify(data));
      setShowSignup(false);
    } catch (err) {
      setSignupError(err.message);
    } finally {
      setSignupLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem(PROFILE_KEY);
    localStorage.removeItem(FAVORITES_KEY);

    setProfile(null);
    setSelectedFavorites([]);
    setRecs([]);
    setSearchResults([]);
    setOnboardingResults([]);
    setSimilarMovies([]);
    setSelectedMovie(null);
    setSelectedDetails(null);
    setSearchQuery("");
    setOnboardingQuery("");
    setError("");
    setFeedbackState({});
    setShowSignup(true);
  };

  const fetchRecommendations = async () => {
    if (!profileId) return;

    try {
      setLoadingRecs(true);
      setError("");

      const res = await fetch(`${API_URL}/recommendations/${profileId}?top_n=${topN}`);

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to load recommendations");
      }

      const data = await res.json();
      setRecs(data.recommendations || []);
    } catch (err) {
      setError(err.message);
      setRecs([]);
    } finally {
      setLoadingRecs(false);
    }
  };

  const searchMovies = async () => {
    try {
      if (!searchQuery.trim()) return;

      setLoadingSearch(true);
      setError("");

      const res = await fetch(
        `${API_URL}/search-movies?query=${encodeURIComponent(searchQuery)}&top_n=10`
      );

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to search movies");
      }

      const data = await res.json();
      setSearchResults(data.results || []);
    } catch (err) {
      setError(err.message);
      setSearchResults([]);
    } finally {
      setLoadingSearch(false);
    }
  };

  const fetchSimilarMovies = async (movie) => {
    try {
      setSelectedMovie(movie);
      setSelectedDetails(movie);
      setLoadingSimilar(true);
      setError("");

      const res = await fetch(`${API_URL}/similar-movies/${movie.movieId}?top_n=10`);

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to load similar movies");
      }

      const data = await res.json();
      setSimilarMovies(data.results || []);
    } catch (err) {
      setError(err.message);
      setSimilarMovies([]);
    } finally {
      setLoadingSimilar(false);
    }
  };

  const openDetails = (movie) => {
    setSelectedDetails(movie);
  };

  const sendFeedback = async (movie, action) => {
    if (!profileId) return;

    setFeedbackState((prev) => ({
      ...prev,
      [movie.movieId]: action,
    }));

    await fetch(`${API_URL}/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        profile_id: profileId,
        movieId: movie.movieId,
        title: movie.title,
        action,
      }),
    });
  };

  const searchOnboardingMovies = async () => {
    try {
      if (!onboardingQuery.trim()) return;

      setError("");

      const res = await fetch(
        `${API_URL}/search-movies?query=${encodeURIComponent(onboardingQuery)}&top_n=10`
      );

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to search movies");
      }

      const data = await res.json();
      setOnboardingResults(data.results || []);
    } catch (err) {
      setError(err.message);
      setOnboardingResults([]);
    }
  };

  const persistFavorites = async (favorites) => {
    if (!profileId) return;

    await fetch(`${API_URL}/profile/${profileId}/favorites`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        favorite_movie_ids: favorites.map((m) => m.movieId),
      }),
    });
  };

  const addFavorite = async (movie) => {
    const nextFavorites = selectedFavorites.some((m) => m.movieId === movie.movieId)
      ? selectedFavorites
      : [...selectedFavorites, movie];

    saveFavoritesLocally(nextFavorites);
    await persistFavorites(nextFavorites);
  };

  const removeFavorite = async (movieId) => {
    const nextFavorites = selectedFavorites.filter((m) => m.movieId !== movieId);
    saveFavoritesLocally(nextFavorites);
    await persistFavorites(nextFavorites);
  };

  const refreshMyRecommendations = async () => {
    await fetchRecommendations();
  };

  useEffect(() => {
    if (profileId) {
      fetchRecommendations();
    }
  }, [profileId]);

  const renderFeedbackButtons = (movie) => {
    const currentAction = feedbackState[movie.movieId];

    return (
      <div className="feedback-buttons">
        <button
          className={`like-btn ${currentAction === "like" ? "active-like" : ""}`}
          onClick={async (e) => {
            e.stopPropagation();
            await sendFeedback(movie, "like");
          }}
        >
          👍 Like
        </button>

        <button
          className={`dislike-btn ${currentAction === "dislike" ? "active-dislike" : ""}`}
          onClick={async (e) => {
            e.stopPropagation();
            await sendFeedback(movie, "dislike");
          }}
        >
          👎 Dislike
        </button>
      </div>
    );
  };

  return (
    <div className="app">
      {showSignup && (
        <div className="auth-backdrop">
          <div className="auth-modal">
            <h2>Get started</h2>
            <p>Create your profile to personalize recommendations.</p>

            <form onSubmit={createProfile} className="auth-form">
              <label>
                Username
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Your name"
                  required
                />
              </label>

              <label>
                Email
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  required
                />
              </label>

              {signupError && <p className="error">{signupError}</p>}

              <button type="submit" disabled={signupLoading}>
                {signupLoading ? "Creating..." : "Continue"}
              </button>
            </form>
          </div>
        </div>
      )}

      <header className="header">
        <div className="header-top">
          <div className="header-spacer" />
          <h1>Personalized Movie Recommender</h1>
          <div className="made-by">Made by Sanidhya</div>
        </div>

        {profile && (
          <div className="profile-banner">
            Signed in as <strong>{profile.username}</strong> · {profile.email}
            <button className="logout-btn" onClick={logout}>
              Log out
            </button>
          </div>
        )}
      </header>

      <section className="controls">
        <div className="control">
          <label>Top N</label>
          <input
            type="number"
            min="1"
            max="50"
            value={topN}
            onChange={(e) => setTopN(Number(e.target.value))}
          />
        </div>

        <button onClick={refreshMyRecommendations} disabled={!profileId}>
          Get Recommendations
        </button>
      </section>

      <section className="search-section">
        <h2>Search a Movie</h2>
        <div className="search-bar">
          <input
            type="text"
            placeholder="Type a movie title..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") searchMovies();
            }}
          />
          <button onClick={searchMovies}>Search</button>
        </div>

        {loadingSearch && <p className="status">Searching movies...</p>}

        <div className="list-grid">
          {searchResults.map((movie) => (
            <button
              key={movie.movieId}
              className="movie-row"
              onClick={() => fetchSimilarMovies(movie)}
            >
              <strong>{movie.title}</strong>
              <span>{formatGenres(movie.genres)}</span>
              <small>
                Avg rating: {movie.avg_rating} · Ratings: {movie.rating_count}
              </small>
            </button>
          ))}
        </div>
      </section>

      {selectedMovie && (
        <section className="section">
          <h2>Similar to: {selectedMovie.title}</h2>
          {loadingSimilar && <p className="status">Loading similar movies...</p>}

          <div className="grid">
            {similarMovies.map((movie) => (
              <article
                className="card"
                key={movie.movieId}
                onClick={() => openDetails(movie)}
                role="button"
                tabIndex={0}
              >
                <h3>{movie.title}</h3>
                <p className="genres">{formatGenres(movie.genres)}</p>
                <p className="meta">
                  Avg rating: {movie.avg_rating} · Ratings: {movie.rating_count}
                </p>
                {renderFeedbackButtons(movie)}
              </article>
            ))}
          </div>
        </section>
      )}

      <section className="section">
        <h2>Personalized Recommendations</h2>
        {loadingRecs && <p className="status">Loading recommendations...</p>}
        {error && <p className="error">{error}</p>}

        <div className="grid">
          {recs.map((movie, index) => (
            <article
              className="card"
              key={`${movie.movieId || movie.title}-${index}`}
              onClick={() => openDetails(movie)}
              role="button"
              tabIndex={0}
            >
              <h3>{movie.title}</h3>
              <p className="genres">{formatGenres(movie.genres)}</p>
              {movie.reason && <p className="reason">{movie.reason}</p>}
              <p className="meta">
                Avg rating: {movie.avg_rating} · Ratings: {movie.rating_count}
              </p>
              {renderFeedbackButtons(movie)}
            </article>
          ))}
        </div>
      </section>

      <section className="section onboarding">
        <h2>New here? Pick a few favorites</h2>
        <p className="onboarding-note">
          Search movies you already like, add them to your favorites, and we will build
          recommendations from your profile.
        </p>

        <div className="search-bar">
          <input
            type="text"
            placeholder="Search favorites..."
            value={onboardingQuery}
            onChange={(e) => setOnboardingQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") searchOnboardingMovies();
            }}
          />
          <button onClick={searchOnboardingMovies}>Search</button>
        </div>

        <div className="list-grid">
          {onboardingResults.map((movie) => (
            <div key={movie.movieId} className="movie-row onboarding-row">
              <div>
                <strong>{movie.title}</strong>
                <span>{formatGenres(movie.genres)}</span>
                <small>
                  Avg rating: {movie.avg_rating} · Ratings: {movie.rating_count}
                </small>
              </div>

              <button onClick={() => addFavorite(movie)}>Add</button>
            </div>
          ))}
        </div>

        {selectedFavorites.length > 0 && (
          <>
            <div className="selected-favorites">
              {selectedFavorites.map((movie) => (
                <span key={movie.movieId} className="favorite-chip">
                  {movie.title}
                  <button onClick={() => removeFavorite(movie.movieId)}>×</button>
                </span>
              ))}
            </div>

            <button onClick={refreshMyRecommendations}>Refresh My Recommendations</button>
          </>
        )}
      </section>

      {selectedDetails && (
        <aside className="drawer">
          <div className="drawer-content">
            <button className="close-btn" onClick={() => setSelectedDetails(null)}>
              Close
            </button>

            <h2>{selectedDetails.title}</h2>
            <p className="genres">{formatGenres(selectedDetails.genres)}</p>

            <div className="detail-stats">
              {selectedDetails.final_score !== undefined && (
                <div>
                  <span>Recommended</span>
                  <strong>{selectedDetails.final_score}</strong>
                </div>
              )}

              {selectedDetails.cf_score !== undefined && (
                <div>
                  <span>User Match</span>
                  <strong>{selectedDetails.cf_score}</strong>
                </div>
              )}

              {selectedDetails.content_score !== undefined && (
                <div>
                  <span>Similarity</span>
                  <strong>{selectedDetails.content_score}</strong>
                </div>
              )}

              {selectedDetails.score !== undefined && (
                <div>
                  <span>Similarity</span>
                  <strong>{selectedDetails.score}</strong>
                </div>
              )}

              {selectedDetails.popularity_score !== undefined && (
                <div>
                  <span>Popularity</span>
                  <strong>{selectedDetails.popularity_score}</strong>
                </div>
              )}
            </div>

            <button
              onClick={() => fetchSimilarMovies(selectedDetails)}
              style={{ marginTop: "16px" }}
            >
              Show Similar Movies
            </button>
          </div>
        </aside>
      )}
    </div>
  );
}

export default App;