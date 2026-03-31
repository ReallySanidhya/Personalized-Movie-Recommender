import numpy as np
import pandas as pd
from pathlib import Path
from sentence_transformers import SentenceTransformer

DATA_DIR = Path("../data/ml-latest-small")

movies = pd.read_csv(DATA_DIR / "movies_cleaned.csv")
movies["content"] = movies["content"].fillna("").astype(str)

# Free, small, good starting model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Compute embeddings for each movie
embeddings = model.encode(
    movies["content"].tolist(),
    show_progress_bar=True,
    convert_to_numpy=True
)

# Save embeddings and movie order
np.save(DATA_DIR / "movie_embeddings.npy", embeddings)
movies[["movieId", "title"]].to_csv(DATA_DIR / "movies_index.csv", index=False)

print("Saved embeddings:", embeddings.shape)
print("Saved movie index file")