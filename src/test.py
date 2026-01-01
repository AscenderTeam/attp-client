import asyncio
from uuid import UUID
from attp_client.client import ATTPClient
from attp_client.interfaces.inference.enums.message_type import MessageTypeEnum
from attp_client.interfaces.inference.message import IMessageDTOV2
from attp_client.misc.serializable import Serializable


client = ATTPClient(
    "agt_eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJvcmdhbml6YXRpb25faWQiOjEsInBlcm1pc3Npb25zIjpbIioiXSwiZXhwaXJlc19hdF90aW1lc3RhbXAiOm51bGwsInV1aWQiOiIxZGRhMjUzMS1iYzk0LTRkNjQtODAwZS1kNzFiN2NiNzg0ZDQifQ.rbAqt3ZwJSPlX_nwJa2uLx6xhleEpRqE6vWWObaWsVI", 
    organization_id=1,
    connection_url="attp://localhost:6563",
    verbose=True
)

async def main():
    await client.connect()
    
    # await client.router.emit("messages:append")
    # response = await client.router.send("messages:inference:invoke", Serializable[dict[str, Any]]({
    #     "agent_id": 17,
    #     "input_configuration": {},
    #     "messages": [],
    # }))
    # response = await client.router.send("", Serializable[dict[str, str]]({"asd": "Hello world!"}), timeout=20)
    
    # print("RESPONSE IS:", response)
    
    # async def test_stream(task: int = 0):
    #     iterable_response = await client.router.request_stream("streaming:test", Serializable[dict[str, str]]({
    #         "message": "Hello world!"
    #     }), timeout=1000)
        
    #     async for resp in iterable_response:
    #         print(f"TASK {task} STREAM CHUNK:", resp)
    
    # await asyncio.gather(
    #     asyncio.create_task(test_stream(1)),
    #     asyncio.create_task(test_stream(2))
    # )
    
    response_iterable = await client.inference.invoke_chat_inference(
        [IMessageDTOV2(content="Hello!", message_type=MessageTypeEnum.CUSTOMER_MESSAGE, client_id="32b0413f-7ac3-4eed-ae68-8afe98415589", chat_id=UUID("32b0413f-7ac3-4eed-ae68-8afe98415589"))],
        chat_id=UUID("32b0413f-7ac3-4eed-ae68-8afe98415589"),
        stream=True,
        timeout=100
    )
    last_response = None
    async for resp in response_iterable:
        if resp.meta:
            if resp.meta.get("finished"):
                last_response = resp
                break
        print(resp.content or " ", sep="", end="", flush=True)
    
    print("\nFINAL RESPONSE:", last_response)
    print("\nFINAL METADATA: ", last_response.meta if last_response else None)
    # tool = await catalog.attach_tool(lambda e: print("EVENT:", e), "tools.test")
    # print("TOOL UUID:", tool)
    # response = await client.inference.invoke_chat_inference(
    #     chat_id=UUID(hex="51e5bd7e-4f63-4a43-9430-c67c4e7a4b1f"),
    #     messages=[IMessageDTOV2(
    #         content="Hello world!",
    #         message_type=MessageTypeEnum.USER_MESSAGE,
    #         chat_id=UUID(hex="51e5bd7e-4f63-4a43-9430-c67c4e7a4b1f")
    #     ), IMessageDTOV2(
    #         content="Hello world!",
    #         message_type=MessageTypeEnum.USER_MESSAGE,
    #         chat_id=UUID(hex="51e5bd7e-4f63-4a43-9430-c67c4e7a4b1f")
    #     )],
    #     timeout=10
    # )

    await client.close()

if __name__ == "__main__":
    asyncio.run(main())