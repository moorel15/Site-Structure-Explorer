from app import app
from flask import render_template, flash
from .web_forms import MapURLForm

@app.route('/', methods=['GET', 'POST'])
def index():
    form = MapURLForm()
    return render_template('generate.html', form=form)

@app.route('/result', methods=['GET', 'POST'])
def result():
    return render_template('result.html')
