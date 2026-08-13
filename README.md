# 🎬 Movie Recommendation System

A full-stack movie recommendation system that recommends movies based on a user's selected movie.

The system uses a **hybrid recommendation approach**, combining:

- 🎭 Content-based filtering using movie genres
- 👥 Collaborative filtering using user ratings
- 🔀 A hybrid score combining both approaches
- 🎞️ TMDB API for movie posters, ratings, release dates, and descriptions

## 🚀 Live Demo

**Frontend:**  
https://movierecs-3.onrender.com

**Backend API:**  
https://movierecs-2.onrender.com

---

## ✨ Features

- Search for a movie by title
- Get personalized movie recommendations
- Hybrid recommendation algorithm
- Movie similarity based on genres
- Collaborative filtering based on user ratings
- Movie posters and metadata from TMDB
- Responsive React frontend
- Flask REST API backend
- Deployed using Render

---

## 🧠 How It Works

The recommendation system combines two approaches.

### 1. Content-Based Filtering

Movies are represented using their genres.

The genres are converted into numerical vectors using **TF-IDF (Term Frequency-Inverse Document Frequency)**.

Cosine similarity is then used to determine how similar two movies are based on their genres.

For example:

```text
Toy Story
↓
Animation | Children's | Comedy
↓
Find movies with similar genres
