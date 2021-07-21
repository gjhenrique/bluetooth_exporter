import time
from bcc import BPF

def main():
    bpf = BPF(src_file="../src/urb_time.c")

    bpf.attach_kprobe(event="btusb_send_frame", fn_name="send_frame")
    bpf.attach_kprobe(event="btusb_send_frame_intel", fn_name="send_frame")
    bpf.attach_kprobe(event="btusb_tx_complete", fn_name="receive_acl")
    bpf.attach_kprobe(event="btusb_isoc_tx_complete", fn_name="receive_sco")
    bpf.attach_kprobe(event="hci_event_packet", fn_name="receive_hci_event")

    hist = bpf.get_table("delta_hist")
    while 1:
        time.sleep(1)
        # hist.print_log2_hist()
        hist.clear()

if __name__ == "__main__":
    # stuff only to run when not called via 'import' here
   main()
