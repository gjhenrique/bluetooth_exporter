# ebpf bluetooth metrics

Uses [ebpf_exporter](_site_) to export prometheus metrics about some bluetooth stats of the linux kernel.
It brings a grafana and prometheus setup for easy visualization of this data.

## Running

```shell
# Requires ebpf_exporter to be installed in the host
go get -u -v github.com/cloudflare/ebpf_exporter/
sudo ebpf_exporter --config.file=config.yaml
# In another terminal session
docker-compose -f docker/docker.yaml
```

## Bluetooth on linux
Bluetooth is a protocol used by _buru buru_.

The controller speaks on HCI protocol , etc.

Linux uses the bluez stack

## Bluetooth on kernel?
The responsibility of the kernel is to expose _something_ to user space and provides a _way of communication_ to the bluetooth controller.

The "bridge" that kernel uses are sockets. For example: 
``` c
// Always the same domain is used. AF_BLUETOOTH and PF_BLUETOOTH are equivalent
socket(PF_BLUETOOTH, SOCK_SEQPACKET, BTPROTO_L2CAP);
socket(PF_BLUETOOTH, SOCK_SEQPACKET, BTPROTO_SCO);
socket(PF_BLUETOOTH, SOCK_RAW, BTPROTO_HCI);
socket(PF_BLUETOOTH, SOCK_STREAM, BTPROTO_RFCOMM);
```

The protocol is different based on the needs of the program.
For example, if you want unidirectional data with high quality data, then it uses `L2CAP` protocol.
If voice and (poor) audio for a phone call is needed, it uses `BTPROTO_SCO`.
To talk directly to the controller, `BTPROTO_HCI` is used and 
`BTPROTO_RFCOMM` is on top of `L2CAP` to provide _telephony emulation_.

Generally the socket authentication/creation in many cases are done by [bluez](). 
Programs use [bluez dbus](dbus api) to receive the file descriptor with the already configured socket.

Based on the protocol, the kernel uses different files to handle incoming/outgoing data from user space.
It uses `struct proto_ops` to register a socket type 
and the callbacks defined in this struct are invoked whenever user space wants to connect, authenticate or write/read data.

## Life of a bluetooth packet inside the kernel
For example, let's jump into the flow of a L2CAP packet from user space until it hits the controller assuming the socket is already authenticated. 

1. user space writes binary data that should be delivered as L2CAP protocol to the connected device. 

``` c
struct buffer *buf = alloc_data();
write(fd, this->buffer, buf->data, buf->size);
```

2. The kernel invokes the function declared `sendmsg` field of `struct proto_ops`. In this specific case, it's `l2cap_sock_sendmsg`.
It receives a `msghdr` containing this data.

3. It translates this `msghdr` into a famous `struct sk_buff` representing this packet. `sk_buff` represents a packet in the network stack.

4. After that, it enqueues the `skb` into a linked list inside _dunno_ and invokes the worklet to perform this into a different _context_.
The struct that holds the linked list is inside the controller specific `hci_dev`.

5. Worker wakes up and do a check if the controller can accept the packet among other verifications. 
This `skb_buff` is eventually sent to the inferior layer.

6. It receives the `sk_buff` and converts it to a `urb`. It sets the endpoint address of the controller and sends it. 
This layer lives in the `btusb` kernel module, while all the previous ones are inside the `bluetooth` kernel module.
`usb_submit_urb`

7. Inside `xhci` or `hci` module, it gets this `urb` and sends to the controller. 
The interesting part is that this communications uses the same structure of any other USB communication.

8. The controller receives this and does _stuff_ to send this data to the device.
I'm being mysterious because the code is closed source and generally vendors export the -black box-firmware of the controller inside the `linux-firmware` project.

9. After device is aknowledged, the controller sends a event packet to tell kernel to display its availability

## Metrics
Given the context, this project monitors with k(ret)probes and _export data_ of these different phases.

### # of blutetooth read/write on the socket
Number of times that a `read` and `write` are performed on the bluetooth socket.
Additionally, the return of the syscall is also registered
To get a list of the mapping values, check [errno-base.h]()

Tabela com kprobe, file on kernel and description

Tabela com parametros

Image with the panel

### Total size of bluetooth read/write on the socket
Same as metric above, but shows the length of this instead

Tabela com kprobe e descricao

Tabela com parametros

Image with the panel


### bufsize
Whenever

`sk_wmem_alloc` 

It compares with `sk_sndbuf`.
This value is set by. 

Pulseaudio/pipewire uses `setsockopt` syscall to set a small buffer size to avoids audio out of sync issues.

SO_SNDBUF

Generally, when writes are longen than.
When this happens, kernel returns a `EAGAIN (11)` to the userspace

https://bugs.freedesktop.org/show_bug.cgi?id=58746

### hdev_count
After `skb_pkt`

`acl_cnt`, `sco_cnt` `struct hci_dev`. 
`acl_cnt`, `sco_cnt`,  `le_cnt`

To after the packet is sent
Receives an event packet (_which one_) from the bluetooth controller with the remaining packets.

Controller sends an event package of type `HCI_EV_NUM_COMP_PKTS` with the available number of .
Whenever this value is not sent, no new packets are sent to the controller

Number of Completed Packets. From what I understand the bluetooth controller will send this event once it has transmitted buffered packets to indicate available capacity


### urb time

After packet is ready to be enqueued, it sends a `struct urb`.
Controller registers itself as xhci endpoint address and sends the urb to the controller in the hci protocol

After urb is submitted, then it becomes easy to do it.
Controller replies back with 

- image of ACL and SCO

Only for ACL packets receive a controller ACK (_which one?_) to signal that it has received the packet.


## Development
The eBPF programs are in c files inside `src/`.
There is always a python program that gets . 
The development cycle is faster that way than .
When it's ready to go, this program needs to be integrated into the `aggregate.py` script that writes these programs into the final yaml file.

## Disclaimer
All of this project is based on a single controller and a couple of devices.
Bluetooth has lots of use cases and I might be missing something.
Open an issue if you think any of these informations or metrics are wrong.
Also, _attaching programs_ with kprobe.

<!-- ### Questions -->
<!-- The ebpf programs hook into kprobes, which _could diverge from linux kernel versions_. -->
<!-- If you experience some issues or some metrics are not appearing, open an issue with the version -->

