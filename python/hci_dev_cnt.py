#!/usr/bin/env python3

import time
from bcc import BPF

def main():
    bpf = BPF(src_file="../src/hci_dev_cnt.c")
    bpf.attach_kprobe(event="hci_event_packet", fn_name="work_event")

    cnt = bpf.get_table("cnt")
    while 1:
        time.sleep(1)
        t = time.strftime('%X')
        for k, v in cnt.items():
            print(f'{t} Type {k.type} cnt {k.count} -> {v.value}')

if __name__ == "__main__":
    # stuff only to run when not called via 'import' here
   main()
