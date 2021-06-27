import time
from bcc import BPF

TEXT = """
#include <net/bluetooth/bluetooth.h>

struct key_t {
  unsigned int proto;
  unsigned int errorno;
  bool recv;
};

BPF_HASH(calls, struct key_t);
BPF_HASH(size, struct key_t);

static inline void track_calls(struct pt_regs *ctx, int proto, bool recv) {
  int retval = regs_return_value(ctx);

  struct key_t key = {};

  key.proto = proto;
  key.recv = recv;

  if (retval < 0) {
    // ebpf_exporter decoder only supports uints
    key.errorno = retval * -1;
  } else {
    key.errorno = 0;
  }


  calls.increment(key);
}

int l2cap_recvmsg(struct pt_regs *ctx) {
  track_calls(ctx, BTPROTO_L2CAP, true);
  return 0;
}

int l2cap_sendmsg(struct pt_regs *ctx) {
  track_calls(ctx, BTPROTO_L2CAP, false);
  return 0;
}

int sco_recvmsg(struct pt_regs *ctx) {
  track_calls(ctx, BTPROTO_SCO, true);
  return 0;
}

int sco_sendmsg(struct pt_regs *ctx) {
  track_calls(ctx, BTPROTO_SCO, false);
  return 0;
}
                   """

def main():
    bpf = BPF(text=TEXT)
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
