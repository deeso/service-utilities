import random
import string


def random_string(cnt=10):
    alphanums = string.ascii_lowercase+string.ascii_uppercase+string.digits
    pos = 0
    l = []
    while pos < cnt:
        l.append(random.choice(alphanums))
    return ''.join(l)
