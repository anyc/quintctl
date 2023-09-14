quintctl
--------

Read and write registers of a Phoenix Contact Quint UPS

Currently, only the 24DC/24DC/10 model is supported but other models seem to
provide a similar interface.

Dependencies:
 - pymodbus

```
usage: quintctl.py [-h] [-D DEVICE] [--raw] [--min-change-rel MIN_CHANGE_REL] [--min-change-abs MIN_CHANGE_ABS] [--skip-addr SKIP_ADDR]
                   [--repeat REPEAT]
                   [{monitor,set,dump,dumpall,get}] [action_params ...]

positional arguments:
  {monitor,set,dump,dumpall,get}
  action_params

options:
  -h, --help            show this help message and exit
  -D DEVICE, --device DEVICE
  --raw
  --min-change-rel MIN_CHANGE_REL
  --min-change-abs MIN_CHANGE_ABS
  --skip-addr SKIP_ADDR
  --repeat REPEAT
```
