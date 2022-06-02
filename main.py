# to install pypocket follow instructions here: https://github.com/pokt-foundation/pypocket (it will be on PyPi soon)
import sys
from pokt import PoktRPCDataProvider
from pokt.rpc.models import Transaction
from models import *
import threading
from utils import get_block_txs, verify_domain
from models import *
import signal
import logging

# setup and constants
rpc_url = "https://mainnet-1.nodes.pokt.network:4201"
pokt_rpc = PoktRPCDataProvider(rpc_url)

pns_address = "09e76ee6c3c84e203488f3dc171da6bc812ddb9c"
fees = {
    "register":1 # per year
}

pokt_decimals = 6

quit_event = threading.Event()
signal.signal(signal.SIGINT, lambda *_args: quit_event.set())

def register(tx: Transaction, domain: str, years: int):
    # verify fee is correct
    if tx.stdTx.msg.value.amount == fees["register"]*years*(10**pokt_decimals):
        return False

    # verify valid domain
    if verify_domain(domain) == False:
        return False

    # check if domain already exists

    domains = Domain.select()

    for i in domains:
        if i.name.lower() == domain.lower():
            return False

    domain = Domain.create(**{
        "owner": tx.tx_result.signer,
        "resolves_to": tx.tx_result.signer,
        "name": domain,
        "last_renewal": int(tx.height),
        "ending_date": int(tx.height)+(int(years)*96*365),
        "active": True,
        "parent": None
    })

    Event.create(**{
        "txhash": tx.hash_,
        "domain": domain,
        "old_owner": "0x0",
        "new_owner": tx.tx_result.signer,
        "old_resolver": "0x0",
        "new_resolver": tx.tx_result.signer,
        "height": tx.height
    })

    return True;

def register_subdomain(tx: Transaction, subdomain: str, domain_id: str):
    # verify fee is correct
    if tx.stdTx.msg.value.amount != fees["register"]*(10**pokt_decimals):
        return False

    # verify valid domain
    if verify_domain(subdomain) == False:
        return False

    # check if root domain exists
    try:
        root_domain = Domain[int(domain_id, 16)]
    except (models.DomainDoesNotExist):
        return False

    # verify correct owner
    if tx.tx_result.signer!=root_domain.owner:
        return False


    domain = Domain.create(**{
        "owner": tx.tx_result.signer,
        "resolves_to": tx.tx_result.signer,
        "name": subdomain,
        "active": True,
        "parent": Domain[int(domain_id, 16)]
    })

    Event.create(**{
        "txhash": tx.hash_,
        "domain": domain,
        "old_owner": "0x0",
        "new_owner": Domain[int(domain_id, 16)].owner,
        "old_resolver": "0x0",
        "new_resolver": tx.tx_result.signer,
        "height": tx.height
    })

    return True;



def main():
    while True:
        current_height = State[1].height
        target_height = pokt_rpc.get_height()

        for block in range(current_height + 1, target_height + 1):
            logging.info("Starting block", block)
            # avoid abrupt interrupts that could mess up the state
            if quit_event.is_set():
                logging.info("safely quitting")
                quit()

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
                    logging.info("registering domain", params[0])
                    if register(tx=tx, domain=params[0], years=params[1]) == False:
                        # TODO: send back tokens to user if it fails
                        logging.info("Invalid domain register")

                elif memo[:1] == "s":
                    params = memo[1:].split(",")
                    logging.info("registering subdomain", params[0])
                    if register_subdomain(tx=tx, subdomain=params[0], domain_id=params[1]) == False:
                        # TODO: send back tokens to user if it fails
                        logging.info("Invalid subdomain register")

            state = State[1]
            state.height+=1
            state.save()

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

r<optional subdomain>,<domain>,<new_resolver>

this transfers the resolver of that domain or subdomain to the new_owner


BURN:

b<domain>

this will burn/deactivate the domain and all associated sub-domains


BURN SUBDOMAINS:

x<domain>

this will burn/deactivate all subdomains of that root domain

"""
