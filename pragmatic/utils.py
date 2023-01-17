def import_name(name):
    components = name.split('.')
    mod = __import__('.'.join(components[0:-1]), globals(), locals(), [components[-1]])
    return getattr(mod, components[-1])


def compress(files):
    import io
    import zipfile

    file_like_object = io.BytesIO()
    zf = zipfile.ZipFile(file_like_object, mode='w')

    try:
        for file in files:
            name = file.get('name', None)
            content = file.get('content', None)
            if name and content:
                zf.writestr(name, content, compress_type=zipfile.ZIP_DEFLATED)

    except FileNotFoundError:
        print('An error occurred during compression')
    finally:
        zf.close()
        file_like_object.seek(0)
        return file_like_object
