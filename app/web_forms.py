from flask_wtf import Form
from wtforms import StringField, RadioField
from wtforms.validators import DataRequired


class MapURLForm(Form):
    URL = StringField('URL', validators=[DataRequired()])


class getImageForm(Form):
    node = StringField('node', validators=[DataRequired()])
