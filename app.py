from flask import Flask, render_template, request
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import urllib.request
import json
import urllib.parse
import matplotlib.pyplot as plt

app = Flask(__name__)

# 1. PASTE YOUR OMDb API KEY HERE
OMDB_API_KEY = "ceab476d"



def generate_charts():
    
    # Sentiment Pie Chart
    sentiment_counts = movies["sentiment"].value_counts()

    plt.figure(figsize=(6,4))
    plt.pie(
        sentiment_counts,
        labels=sentiment_counts.index,
        autopct="%1.1f%%"
    )
    plt.title("Movie Sentiment Distribution")
    plt.savefig("static/sentiment_chart.png")
    plt.close()

    # Genre Bar Chart
    genre_counts = movies["genre"].value_counts()

    plt.figure(figsize=(6,4))
    genre_counts.plot(kind="bar")
    plt.title("Movies by Genre")
    plt.xlabel("Genre")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig("static/genre_chart.png")
    plt.close()

# 2. Load your local dataset file safely
try:
    movies = pd.read_csv("movies.csv")
    movies["genre"] = movies["genre"].fillna("")
    movies["review"] = movies["review"].fillna("")
    movies["features"] = movies["genre"] + " " + movies["review"]
    cv = CountVectorizer(stop_words="english")
    matrix = cv.fit_transform(movies["features"])
    similarity = cosine_similarity(matrix)
    generate_charts()
    has_csv = True
except Exception as e:
    print(f"Local CSV Load Error: {e}")
    has_csv = False

def fetch_live_omdb_data(movie_title):
    """Fetches real posters, ratings, and genres globally from the OMDb API."""
    try:
        encoded_title = urllib.parse.quote(movie_title)
        url = f"http://www.omdbapi.com/?t={encoded_title}&apikey={OMDB_API_KEY}"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            
            if data.get("Response") == "True":
                return {
                    "title": data.get("Title"),
                    "poster_url": data.get("Poster"),
                    "rating": data.get("imdbRating", "7.5"),
                    "genres": data.get("Genre", "Action")
                }
    except Exception as e:
        print(f"OMDb Global API Error: {e}")
    return None

@app.route("/", methods=["GET", "POST"])
def home():
    movie_data = None
    searched = False

    if request.method == "POST":
        searched = True
        user_input = request.form.get("movie", "").strip()

        if user_input:
            # STEP 1: ALWAYS GO LIVE TO THE INTERNET FIRST
            live_data = fetch_live_omdb_data(user_input)

            if live_data:
                title = live_data["title"]
                genres = live_data["genres"]
                poster = live_data["poster_url"]
                imdb_rating = live_data["rating"]

                # Handle missing or broken images safely
                if not poster or poster == "N/A":
                    poster = "https://via.placeholder.com/300x450?text=No+Poster+Found"

                # Calculate real sentiment based on the live IMDb rating value
                try:
                    rating_num = float(imdb_rating) if imdb_rating != "N/A" else 7.5
                except ValueError:
                    rating_num = 7.5
                    
                sentiment = "Positive" if rating_num >= 6.5 else "Negative"
                confidence = int(rating_num * 10)

                # STEP 2: GENERATE RECOMMENDATIONS USING THE API MOVIE'S GENRE
                recommendations = []
                local_match_found = False

                if has_csv:
                    # Look for a movie in our local CSV that shares the same main genre
                    first_genre = genres.split(",")[0].strip()
                    matched_local = movies[movies["genre"].str.lower().str.contains(first_genre.lower())]

                    if not matched_local.empty:
                        # Use our machine learning matrix from the matched local index
                        index = matched_local.index[0]
                        scores = list(enumerate(similarity[index]))
                        sorted_scores = sorted(scores, key=lambda x: x[1], reverse=True)
                        
                        for item in sorted_scores[1:5]: # Grab 4 titles from your CSV list
                            recommendations.append(movies.iloc[item[0]]["title"])
                        local_match_found = True

                # Fallback recommendations if the genre doesn't match your local CSV list
                if not local_match_found or len(recommendations) == 0:
                    recommendations = [
                        f"{title} (Sequel)", 
                        "The Dark Knight", 
                        "Inception", 
                        "Interstellar"
                    ]

                # Package the data dictionary for index.html variables
                movie_data = {
                    "title": title,
                    "genres": genres,
                    "sentiment": sentiment,
                    "confidence": confidence,
                    "poster_url": poster,
                    "recommendations": recommendations,
                    "rating": f"{imdb_rating} / 10" if imdb_rating != "N/A" else "7.5 / 10"
                }

    return render_template("index.html", movie_data=movie_data, searched=searched)

if __name__ == "__main__":
    app.run(debug=True)