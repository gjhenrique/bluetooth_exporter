# ebpf bluetooth metrics

Uses EBPF and ebpf_exporter to display metrics about the bluetooth transmission

# Running

It brings a docker-compose setup with prometheus and grafana setup.
```
go get -u -v github.com/cloudflare/ebpf_exporter/
# Will go through all and
python aggregate.py
# EBPF requires sudo
sudo ebpf_exporter --config.file=config.yaml
docker-compose -f docker/docker.yaml
```

## Metrics
Includes the following metrics:
- Syscall errors. Whenever a syscall 

- Size of packets received/sent

- Number of packets written

- Size of socket sendbuf. Total and the current value

- Size of acl_count, sco_count and le_count

- Time it takes to enqueue an urb (Histogram)

- Time it takes to acknowledge a packet. SCO packets are not included (Using queue from ebpf)

## Architecture
First, ebpf programs are first developed in python and the metrics are printed every second.

In the aggregate.py, these ebpf programs are merged with the programs defined in 

## Questions
The ebpf programs hook into kprobes, which _could diverge from linux kernel versions_.
If you experience some issues or some metrics are not appearing, open an issue with the version

