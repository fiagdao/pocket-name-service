# to install pypocket follow instructions here: https://github.com/pokt-foundation/pypocket (it will be on PyPi soon)
from pokt.rpc.models import Transaction
from .models import *
from .utils import get_block_txs, verify_domain, verify_address

fees = {"register": 1, "transfer": 1}  # per year

pokt_decimals = 6


def register(tx: Transaction, domain_name: str, years: int):
    """Add domain to database

    tx -- the POKT transaction where the register occured
    domain_name - the requested name of the domain registration
    years -- requested number of years for the domain to be registered for (365 days)
    """
    if int(tx.stdTx.msg.value.amount) != int(fees["register"]) * int(years) * int(
        10**pokt_decimals
    ):
        print(
            "Invalid Fee",
            tx.stdTx.msg.value.amount,
            int(fees["register"]) * int(years) * int(10**pokt_decimals),
        )
        return False, 1

    # verify valid domain
    if verify_domain(domain_name) == False:
        return False, 2

    # check if domain already exists

    domains = Domain.select()

    for i in domains:
        if i.name.lower() == domain_name.lower():
            if i.active == True:
                return False, 3
            else:
                i.owner = tx.tx_result.signer
                i.resolves_to = tx.tx_result.signer
                i.name = domain_name
                i.last_renewal = int(tx.height)
                i.ending_date = int(tx.height) + (int(years) * 96 * 365)
                i.active = True
                i.parent = None

                i.save()

                Event.create(
                    **{
                        "txhash": tx.hash_,
                        "domain": i,
                        "old_owner": "0x0",
                        "new_owner": tx.tx_result.signer,
                        "old_resolver": "0x0",
                        "new_resolver": tx.tx_result.signer,
                        "height": tx.height,
                    }
                )

                return True

    domain = Domain.create(
        **{
            "owner": tx.tx_result.signer,
            "resolves_to": tx.tx_result.signer,
            "name": domain_name,
            "last_renewal": int(tx.height),
            "ending_date": int(tx.height) + (int(years) * 96 * 365),
            "active": True,
            "parent": None,
        }
    )

    Event.create(
        **{
            "function": "register",
            "txhash": tx.hash_,
            "domain": domain,
            "old_owner": "0x0",
            "new_owner": tx.tx_result.signer,
            "old_resolver": "0x0",
            "new_resolver": tx.tx_result.signer,
            "height": tx.height,
        }
    )

    return True


def register_subdomain(tx: Transaction, subdomain: str, domain_id: str):
    """Add domain to database with a parent domain

    tx -- the POKT transaction where the register occured
    subdomain - the requested name of the subdomain registration
    domain_id - the incrementing ID of the parent domain in hex form.
    """
    # verify fee is correct
    if int(tx.stdTx.msg.value.amount) != int(fees["register"]) * int(
        10**pokt_decimals
    ):
        return False, 1

    # verify valid domain
    if verify_domain(subdomain) == False:
        return False, 2

    # check if root domain exists
    try:
        root_domain = Domain[int(domain_id, 16)]
        if root_domain.active == False:
            return False, 4
    except (DoesNotExist):
        return False, 4

    # verify correct owner
    if tx.tx_result.signer.lower() != root_domain.owner.lower():
        return False, 5

    domains = Domain.select()

    for i in domains:
        if i.name.lower() == subdomain.lower() and i.parent == root_domain:
            if i.active == True:
                return False, 3
            else:
                i.resolves_to = tx.tx_result.signer
                i.name = domain_name
                i.active = True
                i.parent = None

                i.save()

                Event.create(
                    **{
                        "txhash": tx.hash_,
                        "domain": i,
                        "old_owner": "0x0",
                        "new_owner": Domain[int(domain_id, 16)].owner,
                        "old_resolver": "0x0",
                        "new_resolver": tx.tx_result.signer,
                        "height": tx.height,
                    }
                )

                return True

    domain = Domain.create(
        **{
            "resolves_to": tx.tx_result.signer,
            "name": subdomain,
            "active": True,
            "parent": Domain[int(domain_id, 16)],
        }
    )

    Event.create(
        **{
            "function": "register_subdomain",
            "txhash": tx.hash_,
            "domain": domain,
            "old_owner": "0x0",
            "new_owner": Domain[int(domain_id, 16)].owner,
            "old_resolver": "0x0",
            "new_resolver": tx.tx_result.signer,
            "height": tx.height,
        }
    )

    return True


def transfer_owner(tx: Transaction, domain_id: str, new_owner: str):
    """Change the owner of a domain to the new_owner

    tx - the POKT transaction where the transfer occured
    domain_id - the incrementing ID of the parent domain in hex form.
    new_owner - the POKT address of the new owner of the Domain
    """

    if tx.stdTx.msg.value.amount != fees["transfer"] * (10**pokt_decimals):
        return False, 1

    # check if root domain exists
    try:
        domain = Domain[int(domain_id, 16)]
        if domain.active == False:
            return False, 4
    except (DoesNotExist):
        return False, 4

    # check if it is a subdomain
    if domain.parent != None:
        return False, 6

    # verify owner
    if tx.tx_result.signer != domain.owner:
        return False, 5

    # valid address
    if not verify_address(new_owner):
        return False, 7

    old_owner = domain.owner
    domain.owner = new_owner
    domain.save()

    Event.create(
        **{
            "function": "transfer_owner",
            "txhash": tx.hash_,
            "domain": domain,
            "old_owner": old_owner,
            "new_owner": domain.owner.upper(),  # new_owner
            "old_resolver": domain.resolves_to,
            "new_resolver": domain.resolves_to,
            "height": tx.height,
        }
    )

    return True


def transfer_resolver(tx: Transaction, domain_id: str, new_resolver: str):
    """Change the resolves_to of a domain to the new_resolver

    tx - the POKT transaction where the transfer occured
    domain_id - the incrementing ID of the parent domain in hex form.
    new_resolver - the POKT address of the new resolver of the Domain
    """
    if tx.stdTx.msg.value.amount != fees["transfer"] * (10**pokt_decimals):
        return False, 1

    # check if root domain exists
    try:
        domain = Domain[int(domain_id, 16)]
    except (DoesNotExist):
        return False, 4

    if domain.parent != None:
        # verify parent owner *if subdomain
        owner = domain.parent.owner
        if tx.tx_result.signer != owner:
            return False, 5
    else:
        # verify domain owner
        owner = domain.owner
        if tx.tx_result.signer != owner:
            return False, 5

    # valid address
    if not verify_address(new_resolver):
        return False, 7

    old_resolver = domain.resolves_to
    domain.resolves_to = new_resolver
    domain.save()

    Event.create(
        **{
            "function": "transfer_resolver",
            "txhash": tx.hash_,
            "domain": domain,
            "old_owner": owner,
            "new_owner": owner,  # new_owner
            "old_resolver": old_resolver,
            "new_resolver": domain.resolves_to.upper(),
            "height": tx.height,
        }
    )

    return True


def burn(tx: Transaction, domain_id: str):
    """Remove all attributes and deactivate a Domain

    tx - the POKT transaction where the burn occured
    domain_id - the incrementing ID of the domain in hex form.
    """
    # prevent people from spamming high id and overflowing system
    if int(domain_id, 16) > 10000000:
        return False, 8
    # check if root domain exists
    try:
        domain = Domain[int(domain_id, 16)]
    except (DoesNotExist):
        return False, 4

    if domain.active == False:
        return False, 4

    if domain.parent != None:
        # verify parent owner *if subdomain
        owner = domain.parent.owner
        if tx.tx_result.signer != owner:
            return False, 5
    else:
        # verify domain owner
        owner = domain.owner
        if tx.tx_result.signer != owner:
            return False, 5

    domain.active = False
    domain.save()

    Event.create(
        **{
            "function": "burn",
            "txhash": tx.hash_,
            "domain": domain,
            "old_owner": owner,
            "new_owner": "0x0",  # new_owner
            "old_resolver": domain.resolves_to,
            "new_resolver": "0x0",
            "height": tx.height,
        }
    )

    return True
