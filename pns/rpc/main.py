import json
import fastapi_jsonrpc as jsonrpc
from fastapi import Body
from pydantic import BaseModel
import threading
import contextlib
import uvicorn
import time
import signal
from ..indexer.models import *
import json
from playhouse.shortcuts import model_to_dict, dict_to_model

# import peewee

app = jsonrpc.API()

api_v1 = jsonrpc.Entrypoint("/api/v1/jsonrpc")


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
def all_domains(page: int = 1, per_page: int = 100) -> str:
    domains = (
        Domain.select()
        .order_by(Domain.id)
        .limit(per_page)
        .offset((page - 1) * per_page)
    )

    dict_domains = [model_to_dict(domain) for domain in domains]

    return json.dumps(dict_domains)


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


def boot():
    server = Server(uvicorn.Config(app, port=5000, debug=True, access_log=False))
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
