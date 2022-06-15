from pydantic import BaseModel


class Fees(BaseModel):
    register_fee: int
    transfer_fee: int


class Pns_config(BaseModel):
    rpc_url: str
    pns_address: str
    start_block: int
    fees: Fees


class Rpc_config(BaseModel):
    listen_url: str


class Config(BaseModel):
    pns_config: Pns_config

    rpc_config: Rpc_config
