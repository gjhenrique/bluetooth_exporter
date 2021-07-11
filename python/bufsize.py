import time
from bcc import BPF

def main():
    bpf = BPF(src_file="../src/bufsize.c")
    bpf.attach_kprobe(event="l2cap_sock_sendmsg", fn_name="l2cap_sendmsg")
    bpf.attach_kprobe(event="sco_sock_sendmsg", fn_name="sco_sendmsg")

    # BTPROTO_L2CAP 0
    # BTPROTO_SCO 2
    while 1:
        time.sleep(1)
        bpf["sndbuf"].print_linear_hist()
        bpf["sndbuf"].clear()

if __name__ == "__main__":
    # stuff only to run when not called via 'import' here
   main()
