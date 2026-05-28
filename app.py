from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import mysql.connector
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# -----------------------------
# APP CONFIG
# -----------------------------
app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

# -----------------------------
# GLOBAL CACHE
# -----------------------------
DATA_CACHE = []
VECTORIZER = None
QUESTION_VECTORS = None

# -----------------------------
# DB CONNECTION
# -----------------------------
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="naac_user",
        password="1234",
        database="naac_virtual_assistant"
    )

# -----------------------------
# NORMALIZE TEXT
# -----------------------------
def normalize(text):

    text = str(text or "")
    text = text.lower()

    # Convert different NAAC formats
    text = text.replace("n.a.a.c", "naac")
    text = text.replace("n a a c", "naac")
    text = text.replace("na.ac", "naac")
    text = text.replace("na ac", "naac")

    # Remove special symbols
    text = re.sub(r"[^\w\s]", "", text)

    # Remove extra spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()

# -----------------------------
# CATEGORY DETECTION
# -----------------------------
def detect_category(text):

    text = normalize(text)

    if "university" in text:
        return "university"

    elif "autonomous" in text:
        return "autonomous"

    elif "affiliated" in text:
        return "affiliated"

    else:
        return "general"

# -----------------------------
# LOAD DATA (ON START)
# -----------------------------
def load_data():

    global DATA_CACHE
    global VECTORIZER
    global QUESTION_VECTORS

    try:

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT question, answer, institution, file_path, video_link
            FROM naac_content
        """)

        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        DATA_CACHE = []

        for row in rows:

            DATA_CACHE.append({
                "question": normalize(row["question"]),
                "answer": row["answer"],
                "institution": (row["institution"] or "general").lower(),
                "file_path": row["file_path"],
                "video_link": row["video_link"]
            })

        # TF-IDF Training
        corpus = [item["question"] for item in DATA_CACHE]

        VECTORIZER = TfidfVectorizer()
        QUESTION_VECTORS = VECTORIZER.fit_transform(corpus)

        print("✅ Data loaded successfully")
        print("✅ Total Questions:", len(DATA_CACHE))

    except Exception as e:
        print("❌ DATABASE ERROR:", e)

# -----------------------------
# SEMANTIC SEARCH
# -----------------------------
def semantic_search(user_input, filtered_data):

    if not filtered_data:
        return None, 0

    try:

        # Normalize user question
        user_input = normalize(user_input)

        # Convert input into vector
        user_vector = VECTORIZER.transform([user_input])

        # Get vectors of filtered data
        indices = [DATA_CACHE.index(item) for item in filtered_data]

        vectors = QUESTION_VECTORS[indices]

        # Similarity
        similarities = cosine_similarity(user_vector, vectors)[0]

        # Best result
        best_index = similarities.argmax()
        best_score = similarities[best_index]

        return filtered_data[best_index], best_score

    except Exception as e:
        print("❌ SEARCH ERROR:", e)
        return None, 0

# -----------------------------
# BUILD RESPONSE
# -----------------------------
def build_response(item, score):

    response = item["answer"]

    # PDF LINK
    if item.get("file_path"):

        response += f"""
        <br><br>
        <a href='/{item["file_path"]}' target='_blank'>
        📄 View PDF
        </a>
        """

    # VIDEO LINK
    if item.get("video_link"):

        response += f"""
        <br><br>

        <video width="350" controls>
            <source src="/{item['video_link']}" type="video/mp4">
        </video>
        """

    return jsonify({
        "bot_response": response,
        "score": round(float(score), 2),
        "source": "database"
    })

# -----------------------------
# CHAT API
# -----------------------------
@app.route("/chat", methods=["POST"])
def chat():

    try:

        data = request.get_json()

        user_input = data.get("message", "").strip()
        institution_type = data.get("type", "general").lower()

        # Empty question
        if not user_input:

            return jsonify({
                "bot_response": "Please enter a question."
            })

        print("\n--------------------------------")
        print("USER QUESTION:", user_input)

        # Detect category
        detected = detect_category(user_input)

        print("Detected Category:", detected)

        # Category validation
        if detected != "general" and detected != institution_type:

            return jsonify({
                "bot_response":
                f"This question belongs to '{detected}' category, but you selected '{institution_type}'.",
                "score": 0
            })

        # Filter data
        filtered_data = [

            item for item in DATA_CACHE

            if item["institution"] == institution_type
        ]

        # No records
        if not filtered_data:

            return jsonify({
                "bot_response":
                "No data available for this institution type.",
                "score": 0
            })

        # Search answer
        best_match, best_score = semantic_search(
            user_input,
            filtered_data
        )

        print("Best Score:", best_score)

        # Threshold
        if best_match and best_score > 0.30:

            return build_response(best_match, best_score)

        # No answer found
        return jsonify({
            "bot_response":
            "Answer not found in database. Please refine your question.",
            "score": round(float(best_score), 2),
            "source": "no-ai"
        })

    except Exception as e:

        print("🔥 SERVER ERROR:", e)

        return jsonify({
            "bot_response": "Server error occurred.",
            "score": 0
        })

# -----------------------------
# HOME PAGE
# -----------------------------
@app.route("/")
def home():

    return render_template("index.html")

# -----------------------------
# RUN APP
# -----------------------------
if __name__ == "__main__":

    load_data()

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )
