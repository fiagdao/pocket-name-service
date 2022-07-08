from ..indexer.models import *
from fastapi import Body
from pydantic import BaseModel
from playhouse.shortcuts import model_to_dict, dict_to_model
import json
import fastapi_jsonrpc as jsonrpc
import threading
import contextlib
import uvicorn
import time
import json

app = jsonrpc.API()

api_v1 = jsonrpc.Entrypoint("/api/v1")
config = None

class MyError(jsonrpc.BaseError):
    CODE = 5000
    MESSAGE = "My error"

    class DataModel(BaseModel):
        details: str


@api_v1.method(errors=[])
def syncing() -> str:
    state = State[1]

    syncing = state.height != state.target_height

    return json.dumps(
        {
            "syncing": syncing,
            "height": state.height,
            "targetHeight": state.target_height,
        }
    )


@api_v1.method(errors=[])
def get_domains(page: int = 1, per_page: int = 100) -> str:
    domains = (
        Domain.select()
        .order_by(Domain.id)
        .limit(per_page)
        .offset((page - 1) * per_page)
    )

    dict_domains = [model_to_dict(domain) for domain in domains]

    return json.dumps(dict_domains)

@api_v1.method(errors=[])
def get_events(page: int = 1, per_page: int = 100) -> str:
    events = (
        Event.select()
        .order_by(Event.id)
        .limit(per_page)
        .offset((page - 1) * per_page)
    )

    dict_events = [model_to_dict(event) for event in events]

    return json.dumps(dict_events)

@api_v1.method(errors=[])
def get_domains_by_owner(owner: str, page: int = 1, per_page: int = 100) -> str:
    domains = (
        Domain.select()
        .where(Domain.owner==owner)
        .order_by(Domain.id)
        .limit(per_page)
        .offset((page - 1) * per_page)
    )

    dict_domains = [model_to_dict(domain) for domain in domains]

    return json.dumps(dict_domains)

@api_v1.method(errors=[])
def get_domains_by_resolver(resolves_to: str, page: int = 1, per_page: int = 100) -> str:
    domains = (
        Domain.select()
        .where(Domain.resolves_to==resolves_to)
        .order_by(Domain.id)
        .limit(per_page)
        .offset((page - 1) * per_page)
    )

    dict_domains = [model_to_dict(domain) for domain in domains]

    return json.dumps(dict_domains)

@api_v1.method(errors=[])
def get_domain_by_name(domain_name: str) -> str:
    domains = (
        Domain.select()
        .where(Domain.name==domain_name)
    )

    dict_domains = [model_to_dict(domain) for domain in domains]

    return json.dumps(dict_domains)

@api_v1.method(errors=[])
def get_protocol_params() -> str:
    fees = config.pns_config.fees
    pns_address = config.pns_config.pns_address

    params = {
        "fees": fees.dict(),
        "pns_address": pns_address
    }

    return json.dumps(params)

app.bind_entrypoint(api_v1)


class Server(uvicorn.Server):
    def install_signal_handlers(self):
        pass

    @contextlib.contextmanager
    def run_in_thread(self):
        thread = threading.Thread(target=self.run)
        thread.start()
        try:
            while not self.started:
                time.sleep(1e-3)
            yield
        finally:
            self.should_exit = True
            thread.join()


def boot(c):
    global config
    config = c
    server = Server(uvicorn.Config(app, host="0.0.0.0", port=config.rpc_config.port, debug=True, access_log=False))
    server.run()
    while server.run_in_thread():
        time.sleep(2)


if __name__ == "__main__":
    boot()
# app.run()


"""

sync

all_domains
all_events

domains_address
events_address

domain_resolve

"""
