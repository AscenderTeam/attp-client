import asyncio
from attp_client.client import ATTPClient


client = ATTPClient(
    "agt_eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJvcmdhbml6YXRpb25faWQiOjEsInBlcm1pc3Npb25zIjpbIioiXSwiZXhwaXJlc19hdF90aW1lc3RhbXAiOm51bGwsInV1aWQiOiIxZGRhMjUzMS1iYzk0LTRkNjQtODAwZS1kNzFiN2NiNzg0ZDQifQ.rbAqt3ZwJSPlX_nwJa2uLx6xhleEpRqE6vWWObaWsVI", 
    organization_id=1,
    connection_url="attp://localhost:6563"
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
    catalogs = []
    
    for i in range(50):    
        catalog = asyncio.create_task(client.catalog(f"inference_{i}"))
        catalogs.append(catalog)

    print(await asyncio.gather(*catalogs))
    
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