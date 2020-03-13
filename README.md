# RYWB116 setting command generator

- Generate customizable RYWB116 config commands

## Permission issue of /dev/tty
### Manjaro
~~~
sudo groupadd dialout
sudo usermod -aG dialout $(whoami)
sudo reboot
~~~
> try uucp, tty
