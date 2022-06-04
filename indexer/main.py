# to install pypocket follow instructions here: https://github.com/pokt-foundation/pypocket (it will be on PyPi soon)
import sys
from pokt import PoktRPCDataProvider
from pokt.rpc.models import Transaction
from models import *
import threading
from utils import get_block_txs, verify_domain, verify_address
from models import *
import signal
import json
import logging

from functions import *

logging.basicConfig(format='%(filename)s: %(message)s',
                    handlers=[
                        logging.FileHandler("test.log"),
                        logging.StreamHandler()
                    ],
                    level=logging.DEBUG)

# setup and constants
rpc_url = "https://mainnet-1.nodes.pokt.network:4201"
pokt_rpc = PoktRPCDataProvider(rpc_url)

pns_address = "09e76ee6c3c84e203488f3dc171da6bc812ddb9c"
fees = {
    "register": 1,
    "transfer": 1  # per year
}

pokt_decimals = 6

quit_event = threading.Event()
signal.signal(signal.SIGINT, lambda *_args: quit_event.set())


def main():
    """
    Continously loops through new blocks and checks if there are any valid transactions and will call their associated functions
    """

    while True:
        current_height = State[1].height
        target_height = pokt_rpc.get_height()

        for block in range(current_height + 1, target_height + 1):
            with db.atomic() as transaction:
                try:
                    print("Starting block", block)
                    # avoid abrupt interrupts that could mess up the state
                    if quit_event.is_set():
                        print("safely quitting")
                        quit()

                    # deactivate expired domains
                    expired_domains = Domain.select().where(Domain.ending_date <= block)

                    for domain in expired_domains:
                        domain.active = False
                        domain.save()

                        Event.create(**{
                            "function": "domain_expired",
                            "domain": domain,
                            "old_owner": domain.owner,
                            "new_owner": "0x0",  # new_owner
                            "old_resolver": domain.resolves_to,
                            "new_resolver": "0x0",
                            "height": block
                        })

                        children = Domain.select().where(Domain.parent == domain)
                        for subdomain in children:
                            subdomain.active = False
                            subdomain.save()

                            Event.create(**{
                                "function": "domain_expired",
                                "domain": subdomain,
                                "old_owner": subdomain.parent.owner,
                                "new_owner": "0x0",  # new_owner
                                "old_resolver": subdomain.resolves_to,
                                "new_resolver": "0x0",
                                "height": block
                            })

                    txs = get_block_txs(height=block, pokt_rpc=pokt_rpc)

                    for tx in txs:

                        # transaction failed
                        if tx.tx_result.code != 0:
                            continue

                        # not sent to PNS
                        if tx.tx_result.recipient.lower() != pns_address.lower():
                            continue

                        # not a send transaction
                        if tx.tx_result.message_type != "send":
                            continue

                        memo = tx.stdTx.memo
                        # register
                        if memo[:1] == "r":
                            params = memo[1:].split(",")
                            print("registering domain", params[0])
                            if register(tx=tx, domain_name=params[0], years=params[1]) == False:
                                # TODO: send back tokens to user if it fails
                                print("Invalid domain register")

                        elif memo[:1] == "s":
                            params = memo[1:].split(",")
                            print("registering subdomain", params[0])
                            if register_subdomain(tx=tx, subdomain=params[0], domain_id=params[1]) == False:
                                # TODO: send back tokens to user if it fails
                                print("Invalid subdomain register")

                        elif memo[:1] == "o":
                            params = memo[1:].split(",")
                            print("transfering ownership of ", params[0])

                            if transfer_owner(tx=tx, domain_id=params[0], new_owner=params[1]) == False:
                                print("Invalid owner transfership")

                        elif memo[:1] == "v":
                            params = memo[1:].split(",")
                            print("transfering resolver of ", params[0])

                            if transfer_resolver(tx=tx, domain_id=params[0], new_resolver=params[1]) == False:
                                print("Invalid resolver transfership")

                        elif memo[:1] == "b":
                            params = memo[1:].split(",")
                            print("burning ", params[0])
                            if burn(tx=tx, domain_id=params[0]) == False:
                                print("Invalid burn")

                    state = State[1]
                    state.height += 1
                    state.save()
                except Exception as e:
                    print(e)
                    transaction.rollback()
                    quit()


if __name__ == '__main__':
    main()


"""
REGISTER:

r<domain>,<years>

the owner and resolves_to of the domain is the transaction sender


REGISTER SUBDOMAIN:

s<subdomain>,<domain>

the resolves_to of the domain is the transaction sender


TRANSFER OWNER:

o<domain>,<new_owner>

this transfers the owner of that domain to the new_owner


TRANSFER RESOLVER:

v<optional subdomain>,<domain>,<new_resolver>

this transfers the resolver of that domain or subdomain to the new_owner


BURN:

b<domain>

this will burn/deactivate the domain and all associated sub-domains


BURN SUBDOMAINS:

x<domain>

this will burn/deactivate all subdomains of that root domain

"""
