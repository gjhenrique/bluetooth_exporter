import time
from bcc import BPF

def main():
    bpf = BPF(src_file="../src/urb_time.c")
    # Order here is important
    # The callback probes need to be defined earlier
    bpf.attach_kprobe(event="btusb_tx_complete", fn_name="receive_acl")
    bpf.attach_kprobe(event="btusb_isoc_complete", fn_name="receive_sco")
    bpf.attach_kprobe(event="btusb_intr_complete", fn_name="intr_complete")

    bpf.attach_kprobe(event="btusb_send_frame", fn_name="send_frame")
    bpf.attach_kprobe(event="btusb_send_frame_intel", fn_name="send_frame")


    while 1:
        time.sleep(1)
        bpf["delta_hist"].print_log2_hist()
        bpf["delta_hist"].clear()

if __name__ == "__main__":
    # stuff only to run when not called via 'import' here
   main()
