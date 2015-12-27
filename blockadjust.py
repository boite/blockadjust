#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
blockadjust -- IP block adjustment

Usage:
  blockadjust.py [-d | --debug] [-o <outputfile>] BLOCKS
  blockadjust.py [-d | --debug] [-o <outputfile>] -i <inputfile>
  blockadjust.py (-h | --help)
  blockadjust.py (-V | --version)

Arguments:
  BLOCKS           Comma separated list of IP network blocks
                   e.g. "1.0.0.0/8,1.0.0.0/9"

Options:
  -i <inputfile>   File from which to read a list of blocks to adjust, one block
                   per line.
  -o <outputfile>  File to which to output adjusted blocks
  -h --help        Show this screen.
  -d --debug       Print debug statements to STDERR
  -V --version     Print the name and version number.


Given a list of networks, reorganise them so that no host is represented in more
than one range and that the most specific sub-networks are preserved.

For example, the list: [1.0.0.0/8, 1.128.0.0/9, 1.192.0.0/10] will be adjusted
so that the entire /8 of hosts are represented just once and the /10 is
preserved, resulting in: [1.0.0.0/9, 1.128.0.0/10, 1.192.0.0/10].


@author:     jah
@copyright:  2015 jah. All rights reserved.
@license:    GPLv3
@contact:    <code@jahboite.co.uk>
"""


import logging
import sys

from docopt import docopt
from netaddr import IPNetwork
from radix import Radix
from socket import AF_INET

__version__ = '0.0.1'

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


def adjust(networks):
    """Adjust networks to preserve the most specific and avoid duplicates.

    For example, given [1.0.0.0/8, 1.0.0.0/9] the /8 needs full coverage and the
    /9 needs preserving. Thus the adjustment yields [1.0.0.0/9, 1.128.0.0/9].
    """

    should_debug = log.isEnabledFor(logging.DEBUG)

    nets_trie = Radix()
    for net in networks:
        try:
            nets_trie.add(net)
        except ValueError as e:
            log.warning('Not a valid representation of a network: %s', net)

    if should_debug:
        log.debug('Initial networks: %s', nets_trie.prefixes())

    sorted_nodes = nets_trie.nodes()
    sorted_nodes.sort(key=lambda x: x.prefixlen)
    for node in sorted_nodes:
        if should_debug:
            log.debug('Decide what to do with original network %s', node.prefix)
        if has_subnet(node.prefix, nets_trie):
            generate_subnets(nets_trie,
                             IPNetwork(node.prefix),
                             32 if node.family == AF_INET else 128)
            nets_trie.delete(node.prefix)

    return nets_trie.prefixes()

def has_subnet(network_prefix, trie):
    """Check whether or not a network has a subnet in the trie."""

    should_debug = log.isEnabledFor(logging.DEBUG)

    if should_debug:
        log.debug(' Assess %s for presence of subnets in : %s',
                  network_prefix,
                  [x.prefix for x in trie.search_covered(network_prefix)])

    for candidate_subnet in trie.search_covered(network_prefix):
        if candidate_subnet.prefix == network_prefix:
            continue
        if IPNetwork(network_prefix) in IPNetwork(candidate_subnet.prefix).supernet():
            if should_debug:
                log.debug(' %s has the subnet: %s',
                          network_prefix,
                          candidate_subnet.prefix)
            return True

    if should_debug:
        log.debug(' %s has zero subnets.', network_prefix)

    return False

def generate_subnets(trie, network, max_prefixlen):
    """Generate subnet_prefixlen (smaller) subnets for the supplied network.

    A generated network which has a subnet needing to be preserved will itself
    be broken-up into smaller subnets.
    """

    should_debug = log.isEnabledFor(logging.DEBUG)

    subnet_prefixlen = network.prefixlen + 1
    if subnet_prefixlen > max_prefixlen:
        return
    if should_debug:
        log.debug(' Generate /%d subnets for %s',
                  subnet_prefixlen,
                  str(network.cidr))
    for subnet in network.subnet(subnet_prefixlen):
        subnet_cidr = str(subnet.cidr)
        if should_debug:
            log.debug(' Decide what to do with generated subnet %s', subnet_cidr)
        if trie.search_exact(subnet_cidr):
            if should_debug:
                log.debug(' Subnet %s exists - SKIP', subnet_cidr)
            continue
        if not has_subnet(subnet_cidr, trie):
            if should_debug:
                log.debug(' Subnet %s is desired - ADD', subnet_cidr)
            trie.add(subnet_cidr)
        else:
            generate_subnets(trie, IPNetwork(subnet_cidr), max_prefixlen)

def get_blocks(iter_):
    result = []
    for elem in iter_:
        candidate = elem.strip()
        if candidate != '':
            result.append(candidate)
    return result

def read_blocks_from_args(blocks):
    return get_blocks(blocks.split(','))

def read_blocks_from_file(f):
    return get_blocks(f)

def main(args):
    """Read a list of networks, adjust and write the adjusted list."""

    networks = []

    if args['BLOCKS']:
        networks = read_blocks_from_args(args['BLOCKS'])
    elif args['-i'] == '-':
        networks = read_blocks_from_file(sys.stdin)
    else:
        with open(args['-i'], 'r') as f:
            networks = read_blocks_from_file(f)

    if len(networks) < 1:
        return 2

    adjusted = [x + "\n" for x in adjust(networks)]

    if len(adjusted) < 1:
        return 2

    if not args['-o'] or args['-o'] == '-':
        sys.stdout.writelines(adjusted)
        sys.stdout.flush()
    else:
        with open(args['-o'], 'w') as f:
            f.writelines(adjusted)

    return 0

if __name__ == '__main__':
    arguments = docopt(__doc__, version=__version__)
    console_handler = logging.StreamHandler(stream=sys.stderr)
    console_handler.setFormatter(logging.Formatter('%(levelname)s %(message)s'))
    log.addHandler(console_handler)
    if arguments['--debug']:
        log.setLevel(logging.DEBUG)
    try:
        sys.exit(main(arguments))
    except KeyboardInterrupt as e:
        sys.stderr.write('\nCaught a keyboard interrupt. Stop.\n')
        sys.stderr.flush()
        sys.exit(1)
