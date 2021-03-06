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
  uint slot;
};

BPF_HISTOGRAM(delta_hist, struct val_t, 4096);

// btusb_send_frame can only enqueue when the receive kprobes are already attached
BPF_HASH(kprobe_enabled);

int send_frame(struct pt_regs *ctx, struct hci_dev *hdev, struct sk_buff *skb) {
  struct bt_skb_cb *cb = (struct bt_skb_cb *)((skb)->cb);
  u64 ts = bpf_ktime_get_ns();

  u64 key = 0;
  u64 *enabled = kprobe_enabled.lookup(&key);
  if(enabled == NULL) {
    bpf_trace_printk("Skipping send frame and waiting for send kprobe");
    return 0;
  }

  if (cb->pkt_type == HCI_ACLDATA_PKT) {
    bpf_trace_printk("Putting 100 %d", ts % 1000000);
    dist_acl.push(&ts, 0);
  } else if(cb->pkt_type == HCI_SCODATA_PKT) {
    bpf_trace_printk("Putting 200 %d", ts % 1000000);
    dist_sco.push(&ts, 0);
  }

  return 0;
}

static void store(uint event_type, u64 ts) {
  uint delta = (bpf_ktime_get_ns() - ts) / 1000;
  u64 now = bpf_ktime_get_ns();

  if (delta >= 0 && delta < 1024000) {
    struct val_t val;
    val.event_type = event_type;

    if(delta < 300) {
      val.slot = 0;
    } else if (delta < 1000) {
      val.slot = 300;
    }  else if (delta < 10000){
      val.slot = 1000;
    } else {
      val.slot = delta / 10000 * 10000;
    }
    bpf_trace_printk("Inserting delta %d %d %d", delta, event_type, ts % 1000000);

    delta_hist.increment(val);
  }
}

static void update_kprobe_enabled() {
  u64 key = 0;
  u64 value = 1;
  kprobe_enabled.update(&key, &value);
}

int receive_acl(struct pt_regs *ctx) {
  u64 ts;
  dist_acl.pop(&ts);
  // Avoid inserting empty value in the queue
  if (ts > 0) {
    dist_acl_ack.push(&ts, 0);
    store(ACL_SND, ts);
  }

  return 0;
}

int receive_sco(struct pt_regs *ctx) {
  u64 ts;
  dist_sco.pop(&ts);
  if (ts > 0) {
    store(SCO_SND, ts);
  }

  return 0;
}

int receive_hci_event(struct pt_regs *ctx, struct hci_dev *hdev, struct sk_buff *skb) {
  struct hci_event_hdr *hdr = (void *) skb->data;

  if (hdr->evt == HCI_EV_NUM_COMP_PKTS) {
    u64 ts;
    dist_acl_ack.pop(&ts);
    char *data = (void *) skb->data;
    // bthci_evt.num_compl_packets first byte
    if (data[5] > 1) {
      bpf_trace_printk("Event packet number %d", data[5]);
    }

    if(ts > 0) {
      store(ACL_ACK, ts);
    }
  }

  update_kprobe_enabled();
  return 0;
}
