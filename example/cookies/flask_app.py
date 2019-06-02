#   Add current directory to PYTHONPATH
import sys
sys.path.append('.')

#   Initialize Flask
from flask import Flask
app = Flask(__name__)

#   Initialize blargh
from example.cookies import dm
from blargh import engine
from blargh.api import flask as blargh_flask
engine.setup(dm, engine.DictStorage({}))

#   Add blargh to Flask
blargh = blargh_flask.Api(app)
blargh.add_default_blargh_resources('/')

#   Run app
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
