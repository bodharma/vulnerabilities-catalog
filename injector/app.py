from flask import Flask, jsonify
from flask_pymongo import PyMongo

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/vulnerabilities"
mongo = PyMongo(app)


@app.route("/")
def home_page():
    data = mongo.db.cwe.find()
    return jsonify(data)


if __name__ == "__main__":
    app.run(debug=True, port=8001)
