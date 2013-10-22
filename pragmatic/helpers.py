import hashlib
import random
from django.utils.timezone import now


def base64_to_file(content, filepath):
    fh = open(filepath, "wb")
    fh.write(content.decode('base64'))
    fh.close()


def round_to_n_decimal_places(value, n):
    power = 10 ** n
    return float(int(value * power)) / power


def generate_hash(length=5):
    salt = hashlib.sha1(str(random.random())).hexdigest()[:length]
    pepper = str(now())
    return hashlib.sha1(salt + pepper).hexdigest()
