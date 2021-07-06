import time
from bcc import BPF


TEXT = """
#include <net/bluetooth/bluetooth.h>
#include <net/bluetooth/hci.h>

BPF_QUEUE(dist_acl, u64, 5);
BPF_QUEUE(dist_sco, u64, 5);

#define ACL_SND 100
#define SCO_SND 100
#define ACL_ACK 300

struct val_t {
  uint event_type;
  uint bucket;
};

BPF_HISTOGRAM(delta_hist, struct val_t, 3096);

int send_frame(struct pt_regs *ctx, struct hci_dev *hdev, struct sk_buff *skb) {
  struct bt_skb_cb *cb = (struct bt_skb_cb *)((skb)->cb);
  u64 ts = bpf_ktime_get_ns();

  if(cb->pkt_type == HCI_ACLDATA_PKT) {
    dist_acl.push(&ts, 0);
  } else if(cb->pkt_type == HCI_SCODATA_PKT) {
    dist_sco.push(&ts, 0);
  }

  return 0;
}


static void store(uint event_type, u64 ts) {
  uint delta = (bpf_ktime_get_ns() - ts) / 1000000;

  if (delta > 0 && delta < 1024) {
    struct val_t val;
    val.event_type = event_type;
    val.bucket = bpf_log2(delta);

    delta_hist.increment(val);
  }
}

int receive_acl(struct pt_regs *ctx) {
  u64 ts;

  dist_acl.peek(&ts);

  store(ACL_SND, ts);

  return 0;
}

int receive_sco(struct pt_regs *ctx) {
  u64 ts;

  dist_sco.pop(&ts);
  store(SCO_SND, ts);

  return 0;
}

int intr_complete(struct pt_regs *ctx) {
  u64 ts;
  dist_acl.pop(&ts);
  store(ACL_ACK, ts);

  return 0;
}
                   """

def main():
    bpf = BPF(text=TEXT)
    bpf.attach_kprobe(event="btusb_send_frame", fn_name="send_frame")
    bpf.attach_kprobe(event="btusb_send_frame_intel", fn_name="send_frame")

    bpf.attach_kretprobe(event="btusb_tx_complete", fn_name="receive_acl")
    bpf.attach_kretprobe(event="btusb_isoc_complete", fn_name="receive_sco")
    bpf.attach_kretprobe(event="btusb_intr_complete", fn_name="intr_complete")

    while 1:
        time.sleep(1)
        bpf["delta_hist"].print_log2_hist()
        bpf["delta_hist"].clear()

if __name__ == "__main__":
    # stuff only to run when not called via 'import' here
   main()
