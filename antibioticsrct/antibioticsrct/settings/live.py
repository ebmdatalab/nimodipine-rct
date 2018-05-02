import os
from .base import *
from common import utils

DEBUG = False
ALLOWED_HOSTS = ['op2.org.uk', 'www.op2.org.uk']

# Where we get HTML for rendering to PDFs etc
URL_ROOT = 'http://op2.org.uk'

# Where we redirect users after they've done the questionnaire
OP_HOST = "https://openprescribing.net"


DATA_DIR = '/mnt/database/antibiotics-rct-data/interventions/'
