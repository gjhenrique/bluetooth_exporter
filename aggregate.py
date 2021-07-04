from python.pkt_calls import TEXT as pkt_calls_program
from python.pkt_size import TEXT as pkt_size_program
from python.bufsize import TEXT as bufsize_program
from python.hdev_cnt import TEXT as hdev_count_program

from ruamel.yaml import YAML

yaml = YAML()

files = {
    pkt_calls_program: 'exporter/pkt_calls.yaml',
    pkt_size_program: 'exporter/pkt_size.yaml',
    bufsize_program: 'exporter/bufsize.yaml',
    hdev_count_program: 'exporter/hdev_count.yaml'
}

arr = []
for k, v in files.items():
    with open(v) as f:
        my_dict = yaml.load(f)
        my_dict['code'] = k
        arr.append(my_dict)

with open('config.yaml', 'w') as f:
    yaml.dump({ 'programs': arr }, f)
