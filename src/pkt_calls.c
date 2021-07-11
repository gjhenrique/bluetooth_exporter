#include <net/bluetooth/bluetooth.h>

struct key_t {
  unsigned int proto;
  unsigned int errorno;
  bool recv;
};

BPF_HASH(calls, struct key_t);

static void track_calls(struct pt_regs *ctx, int proto, bool recv) {
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
