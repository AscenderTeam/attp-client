from attp_client.interfaces.catalogs.tools.envelope import IEnvelope
from attp_core.rs_api import PyAttpMessage


def envelopize(message: PyAttpMessage) -> IEnvelope:
    if not message.payload:
        raise ValueError("Message payload is empty, cannot envelopize.")

    return IEnvelope.mps(message.payload)