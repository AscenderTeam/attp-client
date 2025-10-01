import asyncio
from attp_client.client import ATTPClient
from attp_client.misc.serializable import Serializable


client = ATTPClient(
    "agt_eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJvcmdhbml6YXRpb25faWQiOjEsInBlcm1pc3Npb25zIjpbIioiXSwiZXhwaXJlc19hdF90aW1lc3RhbXAiOm51bGwsInV1aWQiOiIxZGRhMjUzMS1iYzk0LTRkNjQtODAwZS1kNzFiN2NiNzg0ZDQifQ.rbAqt3ZwJSPlX_nwJa2uLx6xhleEpRqE6vWWObaWsVI", 
    organization_id=1,
    connection_url="attp://localhost:6563"
)

async def main():
    await client.connect()
    response = await client.router.send("experimental", Serializable[dict[str, str]]({"asd": "Hello world!"}), timeout=20)
    
    print("IT IS A RESPONSE:", response)


if __name__ == "__main__":
    asyncio.run(main())