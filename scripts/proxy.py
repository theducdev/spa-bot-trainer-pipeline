from modules.query import Query
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("chat.html")


@app.route("/chat")
def chat():
    return render_template("chat.html")


@app.route("/bot-msg", methods=['POST'])
def get_bot_response():
    usr_msg = request.form['msg']
    # handler = Query(usr_msg)
    # response = handler.process()
    handler = Query(usr_msg)
 
    response, retrival_text = handler.process_RAG()
    return jsonify(response, retrival_text)

if __name__ == "__main__":
    app.run(debug=True)