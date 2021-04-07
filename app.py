from flask import Flask, request, abort, jsonify

app = Flask(__name__)


@app.route('/hello', methods=['GET'])
def get_square():
    return jsonify({'hello': 'world'})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8081, debug=True)