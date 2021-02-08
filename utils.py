# -*- coding: utf-8 -*
import os
import re


def read_file(folder, filename):
    with open(os.path.join('data', folder, filename), 'r') as f:
        txt = f.read()
    return txt


def prep_text(text):
    output = []
    for line in text.split('\n \n \n '):
        line = line.replace('\n', '').strip()
        if 1 <= len(line.split()) <= 100:
            output.append(line)
        else:
            output.extend([l.strip() for l in re.split(r'(?<=[.])\s+?(?=[А-Я])', line) if l.strip()])
    return output
