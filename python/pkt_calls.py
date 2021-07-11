import time
from bcc import BPF

def main():
    bpf = BPF(src_file="../src/pkt_calls.c")
    bpf.attach_kretprobe(event="l2cap_sock_sendmsg", fn_name="l2cap_sendmsg")
    bpf.attach_kretprobe(event="l2cap_sock_recvmsg", fn_name="l2cap_recvmsg")
    bpf.attach_kretprobe(event="sco_sock_sendmsg", fn_name="sco_sendmsg")
    bpf.attach_kretprobe(event="sco_sock_recvmsg", fn_name="sco_recvmsg")

    # BTPROTO_L2CAP 0
    # BTPROTO_SCO 2
    while 1:
        time.sleep(1)
        dest = bpf.get_table("calls")
        t = time.strftime('%X')
        for k, v in dest.items():
            print(f'{t} Proto {k.proto} errorno {k.errorno} Recv {k.recv} -> {v.value}')

if __name__ == "__main__":
    # stuff only to run when not called via 'import' here
   main()
