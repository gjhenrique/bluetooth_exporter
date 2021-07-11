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
