def base64_to_file(content, filepath):
    fh = open(filepath, "wb")
    fh.write(content.decode('base64'))
    fh.close()


def round_to_n_decimal_places(self, value, n):
    power = 10 ** n
    return float(int(value * power)) / power
