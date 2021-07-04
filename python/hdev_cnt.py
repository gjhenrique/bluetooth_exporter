#!/usr/bin/env python3

import time
from bcc import BPF

TEXT = """
#include <net/bluetooth/bluetooth.h>
#include <net/bluetooth/hci.h>
#include <net/bluetooth/hci_core.h>

struct key_t {
  unsigned int type;
  unsigned int count;
};

#define CNT_ACL 100
#define CNT_SCO 200
#define CNT_LE 300

BPF_HASH(cnt, struct key_t);

static inline void increment_count(int type, int count) {
  struct key_t key;
  key.type = type;
  key.count = count;
  cnt.increment(key);
}

int work_event(struct pt_regs *ctx, struct hci_dev *hdev, struct sk_buff *skb) {
  struct hci_event_hdr *hdr = (void *) skb->data;
  u8 event = hdr->evt;

  if (event == HCI_EV_NUM_COMP_PKTS) {
    bpf_trace_printk("New Event acl_cnt %d", hdev->acl_cnt);
    increment_count(CNT_ACL, hdev->acl_cnt);
    increment_count(CNT_SCO, hdev->sco_cnt);
    increment_count(CNT_LE, hdev->le_cnt);
  }

  return 0;
}
                   """

def main():
    bpf = BPF(text=TEXT)
    bpf.attach_kprobe(event="hci_event_packet", fn_name="work_event")

    cnt = bpf.get_table("cnt")
    while 1:
        time.sleep(1)
        t = time.strftime('%X')
        for k, v in cnt.items():
            print(f'{t} Type {k.type} cnt {k.count} -> {v.value}')

if __name__ == "__main__":
    # stuff only to run when not called via 'import' here
   main()
