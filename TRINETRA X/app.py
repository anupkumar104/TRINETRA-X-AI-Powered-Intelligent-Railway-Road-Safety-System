from flask import Flask, render_template, jsonify
from database.database import init_db

app = Flask(__name__)

# Initialize SQLite database
init_db()

@app.route("/")
def dashboard():
    return render_template("dashboard.html")

@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "project": "AI-Based Multi-Mode Animal & Infrastructure Safety System"
    })

if __name__ == "__main__":
    app.run(debug=True)
