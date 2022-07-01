from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from engineio.payload import Payload
from engineio.async_drivers import threading
from werkzeug.utils import secure_filename
import numpy as np
import imageio
import matplotlib.pyplot as plt
import pygad
import gari
import os
import glob
import imageio
import base64
from flaskwebgui import FlaskUI

Payload.max_decode_packets = 2048

app = Flask(__name__)
app.secret_key = "secret key"
app.config["UPLOAD_FOLDER"] = "static/uploads/"
socketio = SocketIO(app, manage_session=False,
                    cors_allowed_origins='*', async_mode="threading")

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

uploaded_name = None
target_im = None
target_chromosome = None
previous = None
stop = False
generations = 25000
mating_parents = 20
solutions_per_population = 40
mutation_percentage = 0.1


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def fitness_fun(solution, solution_idx):
    fitness = np.sum(np.abs(target_chromosome - solution))
    fitness = np.sum(target_chromosome) - fitness
    return fitness


def callback(ga_instance):
    global stop
    generation = "Generation = {gen}".format(
        gen=ga_instance.generations_completed)
    fitness = "Fitness    = {fitness}".format(
        fitness=ga_instance.best_solution()[1])
    print(generation)
    print(fitness)

    if ga_instance.generations_completed == 1:
        plt.imsave('Generations/generation_{:06d}.png'.format(ga_instance.generations_completed),
                   gari.chromosome2img(ga_instance.best_solution()[0], target_im.shape))

        with open('Generations/generation_{:06d}.png'.format(ga_instance.generations_completed), 'rb') as f:
            generated_image = base64.b64encode(f.read())
        generated_image = generated_image.decode('utf-8')
        socketio.emit('generated-image', {'generated_image': generated_image,
                      'generation': generation, 'fitness': fitness})

    if ga_instance.generations_completed % 100 == 0:
        plt.imsave('Generations/generation_{:06d}.png'.format(ga_instance.generations_completed),
                   gari.chromosome2img(ga_instance.best_solution()[0], target_im.shape))
        with open('Generations/generation_{:06d}.png'.format(ga_instance.generations_completed), 'rb') as f:
            generated_image = base64.b64encode(f.read())
        generated_image = generated_image.decode('utf-8')
        socketio.emit('generated-image', {'generated_image': generated_image,
                      'generation': generation, 'fitness': fitness})
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
    global target_im, target_chromosome, previous, uploaded_name
    files = glob.glob('./Generations/*')
    for f in files:
        os.remove(f)
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
        target_im = np.asarray(target_im/255, dtype=np.float)
        target_chromosome = gari.img2chromosome(target_im)
        previous = filename
        success = True
    else:
        errors[file.filename] = 'File type is not allowed'

    if success:
        resp = jsonify({'message': 'File successfully uploaded'})
        resp.status_code = 201
        uploaded_name = file.filename
        with open('static/uploads/' + uploaded_name, 'rb') as f:
            image_data = base64.b64encode(f.read())
        image_data = image_data.decode('utf-8')
        socketio.emit('uploaded-image', {'image_data': image_data})
        return resp
    else:
        resp = jsonify(errors)
        resp.status_code = 400
        return resp


@app.route('/run', methods=["POST"])
def run():
    global generations, mating_parents, solutions_per_population, mutation_percentage
    ga_instance = pygad.GA(num_generations=generations,
                           num_parents_mating=mating_parents,
                           fitness_func=fitness_fun,
                           sol_per_pop=solutions_per_population,
                           num_genes=target_im.size,
                           init_range_low=0.0,
                           init_range_high=1.0,
                           mutation_percent_genes=mutation_percentage,
                           mutation_type="random",
                           mutation_by_replacement=True,
                           random_mutation_min_val=0.0,
                           random_mutation_max_val=1.0,
                           callback_generation=callback)
    ga_instance.run()
    ga_instance.plot_fitness(
        title="Genetic Algorithm - Generation vs. Fitness")
    return "Done"


@app.route('/stop', methods=["POST"])
def stop():
    global stop
    stop = True
    return "Okay"


@app.route('/submit', methods=["POST"])
def submit():
    global generations, mating_parents, solutions_per_population, mutation_percentage
    try:
        generations = int(request.form.get('generations'))
        mating_parents = int(request.form.get('parents'))
        solutions_per_population = int(request.form.get('solutions'))
        mutation_percentage = float(request.form.get('mutation'))
        if generations >= 1000 and generations <= 25000 and mating_parents >= 10 and mating_parents <= 20 and solutions_per_population >= 20 and solutions_per_population <= 40 and mutation_percentage >= 0.1 and mutation_percentage <= 1:
            return "Applied"
        else:
            resp = jsonify({'message': 'Error'})
            resp.status_code = 400
            return resp
    except:
        resp = jsonify({'message': 'Error'})
        resp.status_code = 400
        return resp


@app.route("/export", methods=["POST"])
def export():
    anim_file = 'static/gif/Iden.gif'
    with imageio.get_writer(anim_file, mode='I') as writer:
        filenames = glob.glob('Generations/generation*.png')
        filenames = sorted(filenames)
        for filename in filenames:
            image = imageio.imread(filename)
            writer.append_data(image)
        image = imageio.imread(filename)
        writer.append_data(image)
        return "Exported"


if __name__ == "__main__":
    # socketio.run(app, debug=True)
    FlaskUI(app, socketio=socketio, start_server="flask-socketio",
            maximized=True, port=5000).run()
