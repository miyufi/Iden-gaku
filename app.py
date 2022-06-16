from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import numpy as np
import imageio
import matplotlib.pyplot as plt
import pygad
import gari
import os
import glob

app = Flask(__name__)
app.secret_key = "secret key"
app.config["UPLOAD_FOLDER"] = "static/uploads/"

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

target_im = None
target_chromosome = None
previous = None
stop = False


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def fitness_fun(solution, solution_idx):
    fitness = np.sum(np.abs(target_chromosome - solution))
    fitness = np.sum(target_chromosome) - fitness
    return fitness


def callback(ga_instance):
    global stop
    print("Generation = {gen}".format(gen=ga_instance.generations_completed))
    print("Fitness    = {fitness}".format(
        fitness=ga_instance.best_solution()[1]))

    if ga_instance.generations_completed % 100 == 0:
        plt.imsave('Generations/generation_{:06d}.png'.format(ga_instance.generations_completed),
                   gari.chromosome2img(ga_instance.best_solution()[0], target_im.shape))
    if stop == True:
        stop = False
        return "stop"


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
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], previous))
        except:
            pass
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        target_im = imageio.imread(os.path.join(
            app.config['UPLOAD_FOLDER'], filename))
        target_chromosome = gari.img2chromosome(target_im)
        previous = filename
        success = True
    else:
        errors[file.filename] = 'File type is not allowed'

    if success:
        target_im = imageio.imread(os.path.join(
            app.config['UPLOAD_FOLDER'], filename))
        target_chromosome = gari.img2chromosome(target_im)
        resp = jsonify({'message': 'File successfully uploaded'})
        resp.status_code = 201
        return resp
    else:
        resp = jsonify(errors)
        resp.status_code = 400
        return resp

@app.route('/run', methods = ["POST"])
def run():
    ga_instance = pygad.GA(num_generations=25000,
                       num_parents_mating=20,
                       fitness_func=fitness_fun,
                       sol_per_pop=40,
                       num_genes=target_im.size,
                       init_range_low=0.0,
                       init_range_high=1.0,
                       mutation_percent_genes=0.01,
                       mutation_type="random",
                       mutation_by_replacement=True,
                       random_mutation_min_val=0.0,
                       random_mutation_max_val=1.0,
                       on_generation=callback)
    ga_instance.run()
    return "Done"

@app.route('/stop', methods = ["POST"])
def stop():
    global stop
    stop = True
    return "Okay"


if __name__ == "__main__":
    app.run(debug=True)
