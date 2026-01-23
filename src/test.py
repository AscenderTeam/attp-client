import asyncio
from uuid import UUID
from attp_client.client import ATTPClient
from attp_client.interfaces.inference.enums.message_type import MessageTypeEnum
from attp_client.interfaces.inference.message import IMessageDTOV2


AGT_TOKEN = "agt_eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJvcmdhbml6YXRpb25faWQiOjEsInBlcm1pc3Npb25zIjpbIioiXSwiZXhwaXJlc19hdF90aW1lc3RhbXAiOm51bGwsInV1aWQiOiIxZGRhMjUzMS1iYzk0LTRkNjQtODAwZS1kNzFiN2NiNzg0ZDQifQ.rbAqt3ZwJSPlX_nwJa2uLx6xhleEpRqE6vWWObaWsVI"
ORG_ID = 1
CONNECTION_URL = "attp://localhost:6563"
VERBOSE = True
RECONNECT = False


async def run_parallel_inferences(client: ATTPClient, count: int = 3) -> None:
    chat_id = UUID("32b0413f-7ac3-4eed-ae68-8afe98415589")
    client_id = "32b0413f-7ac3-4eed-ae68-8afe98415589"
    tasks: dict[asyncio.Task, int] = {}

    for idx in range(1, count + 1):
        message = IMessageDTOV2(
            content=f"Parallel inference {idx}",
            message_type=MessageTypeEnum.CUSTOMER_MESSAGE,
            client_id=client_id,
            chat_id=chat_id,
        )
        task = asyncio.create_task(
            client.inference.invoke_chat_inference(
                [message],
                chat_id=chat_id,
                stream=False,
                timeout=100,
            )
        )
        tasks[task] = idx

    done, pending = await asyncio.wait(tasks)
    for task in sorted(done, key=lambda t: tasks[t]):
        idx = tasks[task]
        try:
            response = task.result()
            print(f"INFERENCE RESPONSE {idx}:", response)
        except Exception as exc:
            print(f"INFERENCE ERROR {idx}:", exc)


async def main() -> None:
    client = ATTPClient(
        AGT_TOKEN,
        organization_id=ORG_ID,
        connection_url=CONNECTION_URL,
        verbose=VERBOSE,
        reconnect=RECONNECT,
    )
    try:
        await client.connect()
        await run_parallel_inferences(client, count=3)
    finally:
        await client.close()
        await asyncio.sleep(0.2)


if __name__ == "__main__":
    asyncio.run(main())
