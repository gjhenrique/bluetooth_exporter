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

// Put this as 1 to enable reporting le_cnt value
# define ENABLE_LE_CNT 0

BPF_HASH(cnt, struct key_t);

static void increment_count(int type, int count) {
  struct key_t key;
  key.type = type;
  key.count = count;
  cnt.increment(key);
}

int work_event(struct pt_regs *ctx, struct hci_dev *hdev, struct sk_buff *skb) {
  struct hci_event_hdr *hdr = (void *) skb->data;
  u8 event = hdr->evt;

  if (event == HCI_EV_NUM_COMP_PKTS) {
    increment_count(CNT_ACL, hdev->acl_cnt);
    increment_count(CNT_SCO, hdev->sco_cnt);
    if (ENABLE_LE_CNT) {
      increment_count(CNT_LE, hdev->le_cnt);
    }
  }

  return 0;
}
