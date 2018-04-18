import re
from os import environ

from titlecase import titlecase

from django.core.exceptions import ImproperlyConfigured


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
