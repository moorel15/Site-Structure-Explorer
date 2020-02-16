from flask_wtf import Form
from wtforms import TextField
from wtforms.validators import DataRequired

class MapURLForm(Form):
    URL = TextField('URL', validators=[DataRequired()])
