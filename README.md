# bluetooth_exporter

Uses [ebpf_exporter](_site_) to export prometheus metrics about some bluetooth stats of the linux kernel.
It brings a grafana and prometheus setup for easy visualization of this data.

## Running

```shell
# Requires ebpf_exporter to be installed in the host
go get -u -v github.com/cloudflare/ebpf_exporter/
sudo ebpf_exporter --config.file=config.yaml
# In another terminal session
docker-compose -f docker/docker.yaml
# Visit http://localhost:3000 to check the panel with user admin and password foobar
# Click magnifying glass and then Linux Bluetooth panel
```

## Bluetooth on kernel
The responsibility of the kernel is to expose a socket to user space and translate the data sent and received by the bluetooth controller through this socket.
``` c
// Always the same domain is used. AF_BLUETOOTH and PF_BLUETOOTH are equivalent
int fd = socket(PF_BLUETOOTH, SOCK_SEQPACKET, BTPROTO_L2CAP);
int fd = socket(PF_BLUETOOTH, SOCK_SEQPACKET, BTPROTO_SCO);
int fd = socket(PF_BLUETOOTH, SOCK_RAW, BTPROTO_HCI);
```
The protocol, passed as third argument, is different based on the use cases of the user.
`A2DP` on top of `L2CAP` protocol could be used for high quality audio, while `BTPROTO_SCO` is used
for bi-directional and simultaneous voice and (poorer) audio,
and `BTPROTO_HCI` to talk directly to the controller.

Based on the type of the protocol, the kernel uses different files to handle incoming/outgoing data from user space.
It register socket types and the callbacks defined on [struct proto_ops](https://github.com/torvalds/linux/search?q=path%3Anet%2Fbluetooth+proto_ops) are invoked whenever user space wants to connect, bind or write/read data.

## Life of a bluetooth packet inside the kernel
To understand some of these metrics, let's follow the life (and death) of a bluetooth audio packet.

1. user space writes binary data that should be delivered as L2CAP protocol to the connected device.
``` c
struct buffer *buf = alloc_data();
write(fd, this->buffer, buf->data, buf->size);
```

2. The callback declared in the `sendmsg` field of `struct proto_ops` is called. In this specific case, it's `l2cap_sock_sendmsg`.
It receives a `struct msghdr` containing data from user space.

3. The `struct msghdr` is converted into a famous `struct sk_buff`, that's now used across this layer.

4. After that, it adds this `sk_buff` into a linked list `data_q` inside `l2cap_chan` that's set when the socket is being created. After that, a work enqueued in a `workqueue` registered to the controller.

5. Later, in a worker thread, the function `hci_tx_work` is invoked and tries to dequeue all the `sk_buffs` from all the registered sockets. This `skb_buff` from the list is eventually dequeued and sent to the `btusb` lower layer.

6. The `btusb` module receives the `sk_buff` and converts it to a `urb` setting all the _usb_ configuration. `usb_submit_urb` is called to allow lower layer to perform the communication.
https://www.kernel.org/doc/html/latest/driver-api/usb/URB.html

7. _Improve this_ Inside `xhci` (usb 3.0+) or `ehci` module, it gets this `urb` and sends to the controller.
_The interesting part is that this communications uses the same structure of any other USB communication_.

8. The controller receives this and does *some magic stuff*  to send this data to the device.
I'm being mysterious because the code is closed source and generally vendors export only a blob of the controller inside the `linux-firmware` project.

9. After the packet is transmitted, the controller sends a event packet to update the availability signaling that this slot can now be used again.

The first layer lives in the `bluetooth` module. Then it goes to modules `btusb` and finally to `xhci_hcd`.
Receiving a packet from the controller goes the reverse direction from `xhci_hcd`, `btusb` and `bluetooth` until the data is handled by the socket reading it.

## Metrics
This project attaches some kprobes and kretprobes events inside the kernel to export prometheus data of some relevant bluetooth state.

### # of blutetooth read/write on the socket
Number of times that a `read` and `write` are called on all the bluetooth sockets.
Additionally, the return of the syscall is registered.

Image with the panel

### Total size of bluetooth read/write on the socket
Same as metric above, but shows the length of the read/writes

Tabela com kprobe e descricao

Tabela com parametros

Image with the panel


### Write allocations from socket
When a new `sk_buff` is being allocated, there is a verification that checks if the field `sk_wmem_alloc` on the `struct sock` is bigger than `sk_sndbuff`. If it's bigger, then it has two options:
When the socket is set as non blocking, a `EAGAIN` (-11) error is returned.
When a socket is blocking, then the call is blocked until `sk_wmem_alloc` is smaller.
This verification is done in the function [sock_alloc_send_pskb](https://github.com/torvalds/linux/blob/v5.13/net/core/sock.c#L2334)

The value set for `sk_sndbuff` (taken from `/proc/sys/net/core/wmem_default`) is pretty high.
So, pipewire/pulseaudio sets a much [lower value](https://github.com/pulseaudio/pulseaudio/blob/bea3fa7d21fdf7d90b73270e836bfffb41cc6fdc/src/modules/bluetooth/module-bluez5-device.c#L547) to avoid out of sync errors.

This metric shows a heatmap showing the value of `sk_wmem_alloc` every time a L2CAP or SCO send syscall is called.

### Size of acl_cnt, le_cnt and sco_cnt in hci_dev
Every `struct hci_dev` associated with a controller has the fields `acl_cnt`, `sco_cnt` and `le_cnt`.
When a `acl` or `le` packet is sent to `btusb`, `acl_cnt` or `le_cnt` is decremented.
After the packet is acknowledged, the controller sends an event packet of type `HCI_EV_NUM_COMP_PKTS` (0x13) with the processed packets. This value is then incremented to these fields.

Controller sends an event package of type `HCI_EV_NUM_COMP_PKTS` with the number of completed packets.
When `acl_cnt`, `le_cnt` or `sco_cnt` reach 0, then no packets are dequeued from the queue and consequently not sent to `btusb`. This is used to not overflood the controller with packets it can't handle.

_image_

### SCO/ACL URB time
Tracks the time of how long the `urb` took to be completed after it's submitted.
The delta is taken from the time of when the `sk_buff` is sent to `btusb` layer until the callback set on callback `usb_complete_t` of the urb is invoked.

- image of ACL urb

- image of SCO

### ACL Number of completed packets
Counts the time when the packet is sent until the controller sends back the event packet `HCI_EV_NUM_COMP_PKTS`.

For example, that's what happens when taking the headset to the kitchen for a while.

_Image_

- There is an issue that rarely this event packet is not sent on my controller (AX200). 
This means the `BPF_QUEUE` is outdated and presents a wrong value.
I'm investigating why this happens and hopefully there is a fix for that.


## Development
The eBPF programs are in c files inside `src/`.
To improve the development cycle, there is always a bcc python program that prints the values stored in the eBPF data structure.
To be included on `ebpf_exporter`, the metrics are included on `aggregate.py` because `ebpf_exporter` needs all the metrics in a single file.

## Disclaimer
All of the tests were based on a single controller and a couple of devices.
Bluetooth has lots of use cases and it might be missing something from different versions.
Open an issue if you think any of these eBPF programs or metrics could be misleading.
