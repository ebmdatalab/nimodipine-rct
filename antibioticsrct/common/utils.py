import base64
import logging
import re
import subprocess
from os import environ

from titlecase import titlecase

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


def nhs_abbreviations(word, **kwargs):
    if len(word) == 2 and word.lower() not in [
            'at', 'of', 'in', 'on', 'to', 'is', 'me', 'by', 'dr', 'st']:
        return word.upper()
    elif word.lower() in ['dr', 'st']:
        return word.title()
    elif word.upper() in ('NHS', 'CCG', 'PMS', 'SMA', 'PWSI', 'OOH', 'HIV'):
        return word.upper()
    elif '&' in word:
        return word.upper()
    elif ((word.lower() not in ['ptnrs', 'by', 'ccgs']) and
          (not re.match(r'.*[aeiou]{1}', word.lower()))):
        return word.upper()


def nhs_titlecase(words):
    if words:
        title_cased = titlecase(words, callback=nhs_abbreviations)
        words = re.sub(r'Dr ([a-z]{2})', 'Dr \1', title_cased)
    return words


def get_env_setting(setting, default=None):
    """ Get the environment setting.

    Return the default, or raise an exception if none supplied
    """
    try:
        return environ[setting]
    except KeyError:
        if default is not None:
            return default
        else:
            error_msg = "Set the %s env variable" % setting
            raise ImproperlyConfigured(error_msg)

def grab_image(url, file_path, selector, dimensions='2000x5000'):
    # Copied from openprescribing code base
    if 'selectedTab=map' in url:
        wait = 8000
        dimensions = '1000x600'
    elif 'selectedTab=chart' in url:
        wait = 1000
        dimensions = '800x600'
    elif 'selectedTab' in url:
        wait = 500
        dimensions = '800x600'
    else:
        wait = 1000
    cmd = '{cmd} "{host}{url}" {file_path} "{selector}" {dimensions} {wait}'
    cmd = (
        cmd.format(
            cmd=settings.GRAB_CMD,
            host=settings.GRAB_HOST,
            url=url,
            file_path=file_path,
            selector=selector,
            dimensions=dimensions,
            wait=wait
        )
    )
    result = subprocess.check_output(cmd, shell=True)
    logger.debug("Command %s completed with output %s" % (cmd, result.strip()))
    with open(file_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read())
        return encoded_image.decode('ascii')
