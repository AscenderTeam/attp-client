# from unittest.async_case import IsolatedAsyncioTestCase

# from attp_client.client import ATTPClient


# class TestConnection(IsolatedAsyncioTestCase):
#     async def setUp(self) -> None:
#         self.client = ATTPClient(
#             "agt_eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJvcmdhbml6YXRpb25faWQiOjEsInBlcm1pc3Npb25zIjpbIioiXSwiZXhwaXJlc19hdF90aW1lc3RhbXAiOm51bGwsInV1aWQiOiIxZGRhMjUzMS1iYzk0LTRkNjQtODAwZS1kNzFiN2NiNzg0ZDQifQ.rbAqt3ZwJSPlX_nwJa2uLx6xhleEpRqE6vWWObaWsVI",
#             organization_id=1,
#             connection_url="attp://localhost"
#         )
#         return super().setUp()
    
#     async def test_connect(self) -> None:
#         await self.client.connect()