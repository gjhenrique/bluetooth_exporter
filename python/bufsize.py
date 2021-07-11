import time
from bcc import BPF

TEXT = """
#include <net/bluetooth/bluetooth.h>

struct key_t {
  unsigned int proto;
  unsigned int bucket;
};

BPF_HISTOGRAM(sndbuf, struct key_t);

static void track_calls(struct pt_regs *ctx, int proto, struct socket *sock) {
  struct sock *sk = sock->sk;
  struct refcount_struct wmem;
  bpf_probe_read_kernel(&wmem, sizeof(wmem), &sk->sk_wmem_alloc);

  // sk->sk_sndbuf is the limit set by SO_SNDBUF socket option
  struct key_t key;
  key.proto = proto;
  key.bucket = (refcount_read(&wmem) - 1) / 100;

  sndbuf.increment(key);
}

int l2cap_sendmsg(struct pt_regs *ctx, struct socket *sock) {
  track_calls(ctx, BTPROTO_L2CAP, sock);
  return 0;
}

int sco_sendmsg(struct pt_regs *ctx, struct socket *sock) {
  track_calls(ctx, BTPROTO_SCO, sock);
  return 0;
}
                   """

def main():
    bpf = BPF(text=TEXT)
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
