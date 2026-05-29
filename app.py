from flask import Flask, render_template, request
from imdb import Cinemagoer

app = Flask(__name__)
ia = Cinemagoer()

def fetch_live_imdb_data(movie_title):
    try:
        search_results = ia.search_movie(movie_title)
        if not search_results:
            return None

        movie_obj = search_results[0]
        ia.update(movie_obj, info=['main', 'recommendations'])

        title = movie_obj.get('title', 'Unknown Title')
        genres = ", ".join(movie_obj.get('genres', [])) or "Cinema Feature"
        
        # Pull live poster
        poster_url = movie_obj.get('full-size cover url') or movie_obj.get('cover url') or "https://via.placeholder.com/300x450?text=No+Poster+Found"

        # Calculate sentiment based on real IMDb score
        rating = movie_obj.get('rating')
        if rating:
            sentiment = "Positive" if rating >= 6.5 else "Negative"
            confidence = int(rating * 10)
        else:
            sentiment = "Neutral"
            confidence = 50

        # Pull Recommendations
        raw_recs = movie_obj.get('recommendations', [])
        recommendations = [rec.get('title') for rec in raw_recs[:4]]

        return {
            "title": title,
            "genres": genres,
            "sentiment": sentiment,
            "confidence": confidence,
            "poster_url": poster_url,
            "recommendations": recommendations
        }
    except Exception as e:
        print(f"IMDb API Error: {e}")
        return None

@app.route("/", methods=["GET", "POST"])
def home():
    movie_data = None
    searched = False

    if request.method == "POST":
        searched = True
        user_input = request.form.get("movie", "").strip()
        if user_input:
            movie_data = fetch_live_imdb_data(user_input)

    return render_template("index.html", movie_data=movie_data, searched=searched)

if __name__ == "__main__":
    app.run(debug=True)