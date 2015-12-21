Blockadjust rewrites a list of IP address allocations/assignments so that:

- All addresses in the original list are represented
- No address is represented more than once
- The most specific blocks of addresses in the original list are preserved

For example, the list:-

- 1.0.0.0/8
- 1.128.0.0/9
- 1.192.0.0/10

is rewritten:-

- 1.0.0.0/9
- 1.128.0.0/10
- 1.192.0.0/10

That is, the /8 is covered by contiguous blocks of addresses and the original
/10 is preserved.

Blockadjust is useful when one wants to [Nmap][] the blocks of addresses output
by [Blockfinder][] and repeatedly scanning the same host is undesirable:-

    $ blockfinder -n "Holy See":ipv4 | sort | uniq | nmap -n -sL -iL - | tail -n 1
    Nmap done: 20736 IP addresses (0 hosts up) scanned in 1.49 seconds

    $ blockfinder -n "Holy See":ipv4 | blockadjust -i - | nmap -n -sL -iL - | tail -n 1
    Nmap done: 16960 IP addresses (0 hosts up) scanned in 1.48 seconds

And it is particularly useful when each block is to be scanned separately and
the most specific blocks are likely to be the most interesting.

## Suggested Install

    $ git clone https://github.com/boite/blockadjust.git
    $ mkvirtualenv -a ./blockadjust -p /usr/bin/python3 env-blockadjust
    $ pip install -r requirements-py3.txt
    $ ./blockadjust -h


  [Blockfinder]: https://github.com/ioerror/blockfinder
  [Nmap]: https://nmap.org/
