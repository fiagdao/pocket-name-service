from pokt import PoktRPCDataProvider

def get_block_txs(height: int, pokt_rpc: PoktRPCDataProvider, retries: int = 20, per_page: int = 1000):
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
    if "." in domain:
        return False

    return all(ord(c) < 128 for c in domain)
