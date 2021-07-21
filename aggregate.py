from pathlib import Path

from ruamel.yaml import YAML

yaml = YAML()

files = {
    'pkt_calls': 'exporter/pkt_calls.yaml',
    'pkt_size': 'exporter/pkt_size.yaml',
    'sock_alloc': 'exporter/sock_alloc.yaml',
    'hci_dev_cnt': 'exporter/hci_dev_cnt.yaml',
    'urb_time': 'exporter/urb_time.yaml',
}

arr = []
for k, v in files.items():
    with open(v) as f:
        my_dict = yaml.load(f)
        my_dict['code'] = Path(f'src/{k}.c').read_text()
        arr.append(my_dict)

with open('config.yaml', 'w') as f:
    yaml.dump({ 'programs': arr }, f)
