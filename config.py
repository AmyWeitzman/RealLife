import os

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or '9io5jremgfpp2owlemfas'
    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASEDIR, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False