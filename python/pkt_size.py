import time
from bcc import BPF

TEXT = """
#include <net/bluetooth/bluetooth.h>

struct key_t {
  unsigned int proto;
  bool recv;
};

BPF_HASH(size, struct key_t);

static void track_size(struct pt_regs *ctx, int proto, bool recv, size_t len) {
  int retval = regs_return_value(ctx);

  struct key_t key = {};

  key.proto = proto;
  key.recv = recv;

  size.increment(key, len);
}

int l2cap_recvmsg(struct pt_regs *ctx, struct socket *sock,
                  struct msghdr *msg, size_t len) {
  track_size(ctx, BTPROTO_L2CAP, true, len);
  return 0;
}

int l2cap_sendmsg(struct pt_regs *ctx, struct socket *sock,
                  struct msghdr *msg, size_t len) {
  track_size(ctx, BTPROTO_L2CAP, false, len);
  return 0;
}

int sco_recvmsg(struct pt_regs *ctx, struct socket *sock,
                  struct msghdr *msg, size_t len) {
  track_size(ctx, BTPROTO_SCO, true, len);
  return 0;
}

int sco_sendmsg(struct pt_regs *ctx, struct socket *sock,
                  struct msghdr *msg, size_t len) {
  track_size(ctx, BTPROTO_SCO, false, len);
  return 0;
}
                   """

def main():
    bpf = BPF(text=TEXT)
    bpf.attach_kprobe(event="l2cap_sock_sendmsg", fn_name="l2cap_sendmsg")
    bpf.attach_kprobe(event="l2cap_sock_recvmsg", fn_name="l2cap_recvmsg")
    bpf.attach_kprobe(event="sco_sock_sendmsg", fn_name="sco_sendmsg")
    bpf.attach_kprobe(event="sco_sock_recvmsg", fn_name="sco_recvmsg")

    # BTPROTO_L2CAP 0
    # BTPROTO_SCO 2
    while 1:
        time.sleep(1)
        dest = bpf.get_table("size")
        t = time.strftime('%X')
        for k, v in dest.items():
            print(f'{t} Proto {k.proto} Recv {k.recv} -> {v.value}')

if __name__ == "__main__":
    # stuff only to run when not called via 'import' here
   main()
