from pokt import PoktRPCDataProvider
import re

def get_block_txs(height: int, pokt_rpc: PoktRPCDataProvider, retries: int = 20, per_page: int = 1000):
    """ Gets all the transactions in order of a block

    height - the block to query transactions for
    pokt_rpc - the PoktRPCDataProvider object to use for the queries
    retries - how many times will it retry the function (if it fails) before raising an error
    per_page - number of transactions to get per page

    """
    page = 1
    txs = []
    while retries > 0:
        try:
            block_txs = pokt_rpc.get_block_transactions(
                page=page, per_page=per_page, height=height)
            if (block_txs.txs == []):
                return txs
            else:
                txs.extend(block_txs.txs)
                page += 1

        except (PoktRPCError, PortalRPCError):
            # give pocket node a bit of time to cool off
            time.sleep(1)
            if retries < 0:
                raise (
                    "Out of retries getting block {} transactions page {}".format(
                        height, page
                    )
                )

    raise (
        "get_block_txs failed"
    )
    quit()

def verify_domain(domain: str):
    """ verifies that a string is ASCII and does not contain any '.'

    domain - the string to check
    """


    if "." in domain:
        return False

    return all(ord(c) < 128 for c in domain)

def verify_address(address: str):
    """ verifies that an string is a-f and 1-9

    address - the string to check
    """
    # 40 chars, a-f, 0-9

    if len(address) != 40:
        return False

    match = re.match("^(0x)?[0-9a-f]{40}$", address)

    return bool(match)
