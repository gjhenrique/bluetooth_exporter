from python.pkt_calls import TEXT as pkt_calls_program
import sys
from ruamel.yaml import YAML


yaml = YAML()

files = {
    pkt_calls_program: 'exporter/pkt_calls.yaml'
}

arr = []
for k, v in files.items():
    with open(v) as f:
        my_dict = yaml.load(f)
        my_dict['code'] = pkt_calls_program
        arr.append(my_dict)

a = {
    'programs': arr
}

with open('config.yaml', 'w') as f:
    yaml.dump(a, f)

# print(txt.replace("{{program}}", pkt_calls_program))
