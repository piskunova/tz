# -*- coding: utf-8 -*
import os
import json
from entity_extractor import Extractor, DATA_DIR


output_filename = 'result.json'
extractor = Extractor()

if __name__ == '__main__':
    for folder in os.listdir(DATA_DIR):
        extractor.process_docs(folder)

    with open(output_filename, 'w') as f:
        json.dump(extractor.output, f, ensure_ascii=False, indent=1)
