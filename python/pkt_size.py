import time
from bcc import BPF

def main():
    bpf = BPF(src_file="../src/pkt_size.c")
    bpf.attach_kprobe(event="l2cap_sock_sendmsg", fn_name="l2cap_sendmsg")
    bpf.attach_kprobe(event="l2cap_sock_recvmsg", fn_name="l2cap_recvmsg")
    bpf.attach_kprobe(event="sco_sock_sendmsg", fn_name="sco_sendmsg")
    bpf.attach_kprobe(event="sco_sock_recvmsg", fn_name="sco_recvmsg")

    while 1:
        time.sleep(1)
        dest = bpf.get_table("size")
        t = time.strftime('%X')
        for k, v in dest.items():
            print(f'{t} Proto {k.proto} Recv {k.recv} -> {v.value}')

if __name__ == "__main__":
    # stuff only to run when not called via 'import' here
   main()
