def base64_to_file(content, filepath):
    fh = open(filepath, "wb")
    fh.write(content.decode('base64'))
    fh.close()
