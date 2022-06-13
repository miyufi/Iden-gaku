from flask import Flask, render_template
import os
import glob


app = Flask(__name__)

generations_folder = './Generations'
if not os.path.exists(generations_folder):
    os.makedirs(generations_folder)
else:
    files = glob.glob('./Generations/*')
    for f in files:
        os.remove(f)


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=True)
