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
    salt = hashlib.sha1(str(random.random())).hexdigest()
    pepper = str(now())
    return hashlib.sha1(salt + pepper).hexdigest()[:length]


def get_subclasses(classes, level=0):
    """
        Return the list of all subclasses given class (or list of classes) has.
        Inspired by this question:
        http://stackoverflow.com/questions/3862310/how-can-i-find-all-subclasses-of-a-given-class-in-python
        Thanks to: http://codeblogging.net/blogs/1/14/
    """
    # for convenience, only one class can can be accepted as argument
    # converting to list if this is the case
    if not isinstance(classes, list):
        classes = [classes]

    if level < len(classes):
        classes += classes[level].__subclasses__()
        return get_subclasses(classes, level+1)
    else:
        return classes


def barcode(code, args=None):
    options = dict()
    if args is not None:
        arguments = args.split(',')
        for arg_pair in arguments:
            key, value = arg_pair.split('=')
            options[key] = int(value)

    import barcode
    from StringIO import StringIO
    from thirdparty import BarcodeImageWriter
    CODETYPE = 'code39'
    bc = barcode.get_barcode(CODETYPE)
    bc = bc(code, writer=BarcodeImageWriter(), add_checksum=False)
    bc.default_writer_options['quiet_zone'] = 6.4
    bc.default_writer_options['dpi'] = 300
    bc.default_writer_options['text_distance'] = 1.0
    bc.default_writer_options['module_height'] = 10.0
    # bc.default_writer_options['module_width'] = 0.3
    bc.default_writer_options['font_size'] = int(bc.default_writer_options['dpi'] / 10)

    # update by custom arguments
    bc.default_writer_options.update(options)

    #write PNG image
    output = StringIO()
    bc.write(output)
    contents = output.getvalue().encode("base64")
    output.close()

    #return encoded base64
    return str(contents)
