#include <net/bluetooth/bluetooth.h>
#include <net/bluetooth/hci.h>

BPF_QUEUE(dist_acl, u64, 5);
BPF_QUEUE(dist_acl_ack, u64, 5);
BPF_QUEUE(dist_sco, u64, 5);

#define ACL_SND 100
#define SCO_SND 200
#define ACL_ACK 300

struct val_t {
  uint event_type;
  uint bucket;
};

BPF_HISTOGRAM(delta_hist, struct val_t, 4096);

int send_frame(struct pt_regs *ctx, struct hci_dev *hdev, struct sk_buff *skb) {
  struct bt_skb_cb *cb = (struct bt_skb_cb *)((skb)->cb);
  u64 ts = bpf_ktime_get_ns();

  if(cb->pkt_type == HCI_ACLDATA_PKT) {
  bpf_trace_printk("Inserting %d", ts %1000000);
    dist_acl.push(&ts, 0);
  } else if(cb->pkt_type == HCI_SCODATA_PKT) {
    dist_sco.push(&ts, 0);
  }

  return 0;
}

static void store(uint event_type, u64 ts) {
  uint delta_micro_sec = (bpf_ktime_get_ns() - ts) / 1000000;
  u64 now = bpf_ktime_get_ns();
  uint delta = delta_micro_sec;


  if (delta >= 0 && delta < 1024) {
    bpf_trace_printk("Receiving %d %d %d", ts %1000000, delta, event_type);
    struct val_t val;
    val.event_type = event_type;
    val.bucket = delta;

    delta_hist.increment(val);
  }
}

int receive_acl(struct pt_regs *ctx) {
  u64 ts;
  dist_acl.pop(&ts);
  // Avoid inserting empty value in the queue
  if (ts == 0) {
    return 0;
  }
  dist_acl_ack.push(&ts, 0);
  store(ACL_SND, ts);

  return 0;
}

int receive_sco(struct pt_regs *ctx) {
  u64 ts;
  dist_sco.pop(&ts);
  if(ts > 0) {
    store(SCO_SND, ts);
  }

  return 0;
}

int intr_complete(struct pt_regs *ctx) {
  u64 ts;
  dist_acl_ack.pop(&ts);

  if(ts > 0) {
    store(ACL_ACK, ts);
  }

  return 0;
}
