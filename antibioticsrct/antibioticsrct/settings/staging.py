import os
from .base import *
from common import utils

DEBUG = True
ALLOWED_HOSTS = ['staging.op2.org.uk']

# Where we get HTML for rendering to PDFs etc
URL_ROOT = 'http://staging.op2.org.uk'

# Where we redirect users after they've done the questionnaire
OP_HOST = "http://staging.openprescribing.net"


# This app queries the maillog model in OP.  When testing or in dev
# mode, we want to create it locally in migrations.  Otherwise, we
# don't.
CREATE_MAILLOG_TABLE = False
