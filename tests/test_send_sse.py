import pytest
from utils import send_sse_message

@pytest.mark.asyncio
async def test_send_sse():
    print("hello")
    await send_sse_message("status","TEST.")