from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import os
import glob


app = Flask(__name__)
app.secret_key = "secret key"
app.config["UPLOAD_FOLDER"] = "static/uploads/"

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


uploads_folder = './static/uploads'
if not os.path.exists(uploads_folder):
    os.makedirs(uploads_folder)

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


@app.route("/upload", methods=['POST'])
def test():
    global target_im, target_chromosome, previous
    if 'files[]' not in request.files:
        resp = jsonify({'message': 'No file part in the request'})
        resp.status_code = 400
        return resp
    file = request.files.get('files[]')
    errors = {}
    success = False
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        previous = filename
        success = True
    else:
        errors[file.filename] = 'File type is not allowed'

    if success:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], previous))
        except:
            pass
        resp = jsonify({'message': 'File successfully uploaded'})
        resp.status_code = 201
        return resp
    else:
        resp = jsonify(errors)
        resp.status_code = 400
        return resp


if __name__ == "__main__":
    app.run(debug=True)
