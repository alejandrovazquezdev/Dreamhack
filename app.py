from flask import Flask, jsonify, render_template
app = Flask(__name__)

@app.route('/')
def landing_page():
    return render_template('signup.html')

@app.route('/app/static/admin/')
def api_status():
    data = {
        "status": "ok",
        "messange": "El servidor de la API está funcionando"
    }
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, port=5000)

