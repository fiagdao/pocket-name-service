# to install pypocket follow instructions here: https://github.com/pokt-foundation/pypocket (it will be on PyPi soon)
from .models import *
from ..logger import logger
from ..config import Config
from .utils import *
from .functions import *
import sys
from pokt import PoktRPCDataProvider
from pokt.rpc.models import Transaction
import json
import os



pokt_decimals = 6


def start_pns(config: Config):
    """
    Continously loops through new blocks and checks if there are any valid transactions and will call their associated functions
    """

    logger.info("Starting indexer")

    pns_address = config.pns_config.pns_address
    rpc_url = config.pns_config.rpc_url
    pokt_rpc = PoktRPCDataProvider(rpc_url)

    create_database(config.pns_config.start_block)

    while True:

        state = State[1]

        current_height = state.height
        target_height = pokt_rpc.get_height()

        state.target_height = target_height
        state.save()

        for block in range(current_height + 1, target_height + 1):
            with db.atomic() as transaction:
                try:
                    logger.info("Starting block {}".format(block))

                    # deactivate expired domains
                    expired_domains = Domain.select().where(Domain.ending_date <= block)

                    for domain in expired_domains:
                        domain.active = False
                        domain.save()

                        Event.create(
                            **{
                                "function": "domain_expired",
                                "domain": domain,
                                "old_owner": domain.owner,
                                "new_owner": "0x0",  # new_owner
                                "old_resolver": domain.resolves_to,
                                "new_resolver": "0x0",
                                "height": block,
                            }
                        )

                        children = Domain.select().where(Domain.parent == domain)
                        for subdomain in children:
                            subdomain.active = False
                            subdomain.save()

                            Event.create(
                                **{
                                    "function": "domain_expired",
                                    "domain": subdomain,
                                    "old_owner": subdomain.parent.owner,
                                    "new_owner": "0x0",  # new_owner
                                    "old_resolver": subdomain.resolves_to,
                                    "new_resolver": "0x0",
                                    "height": block,
                                }
                            )

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
                            logger.info("registering domain {}".format(params[0]))
                            register_ = register(
                                config=config, tx=tx, domain_name=params[0], years=params[1]
                            )
                            if register != True:
                                # TODO: send back tokens to user if it fails
                                logger.info("Invalid domain register")

                        elif memo[:1] == "s":
                            params = memo[1:].split(",")
                            logger.info("registering subdomain {}".format(params[0]))
                            register_subdomain_ = register_subdomain(
                                config=config, tx=tx, subdomain=params[0], domain_id=params[1]
                            )
                            if register_subdomain != True:
                                # TODO: send back tokens to user if it fails
                                logger.info("Invalid subdomain register")

                        elif memo[:1] == "o":
                            params = memo[1:].split(",")
                            logger.info(
                                "transfering ownership of  {}".format(params[0])
                            )
                            transfer_owner_ = transfer_owner(
                                config=config, tx=tx, domain_id=params[0], new_owner=params[1]
                            )
                            if transfer_owner != True:
                                logger.info("Invalid owner transfership")

                        elif memo[:1] == "v":
                            params = memo[1:].split(",")
                            logger.info("transfering resolver of  {}".format(params[0]))
                            transfer_resolver_ = transfer_resolver(
                                config=config, tx=tx, domain_id=params[0], new_resolver=params[1]
                            )
                            if transfer_resolver != True:
                                logger.info("Invalid resolver transfership")

                        elif memo[:1] == "b":
                            params = memo[1:].split(",")
                            logger.info("burning  {}".format(params[0]))
                            burn_ = burn(config=config, tx=tx, domain_id=params[0])
                            if burn != True:
                                logger.info("Invalid burn")

                    state.height += 1
                    state.save()
                except Exception as e:
                    logger.info(e)
                    transaction.rollback()
                    quit()


if __name__ == "__main__":
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
