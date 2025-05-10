import asyncio
import websockets
import TTS 

import global_vars as g

async def consumer_handler(websocket):
    async for message in websocket:
        # print(f"Received message: {message}")
        pass

# MMD-Agentと通信
async def producer_handler(ws:websockets.ServerConnection):
    await ws.send("__AV_START\n")
    await ws.send("__AV_SETMODEL,0\n")
    while True:
        if not g.agent_audio.empty():
            audio = g.agent_audio.get()
            await TTS.send_voice(audio, ws)

        await asyncio.sleep(0.1)

##################################################
# handler for each connection
async def handle_client(websocket, path=None):
    # create task to read from the socket
    consumer_task = asyncio.create_task(consumer_handler(websocket))
    # create task to write to the socket
    producer_task = asyncio.create_task(producer_handler(websocket))
    # wait at least one task has been terminated
    done, pending = await asyncio.wait(
        [consumer_task, producer_task],
        return_when=asyncio.FIRST_COMPLETED,
    )
    # cancel other task and close connection
    for task in pending:
        task.cancel()

# main
async def server_start():
    async with websockets.serve(handle_client, "localhost", 9001, ping_interval=None):
        await asyncio.Future()

def server_start_asyn():
    asyncio.run(server_start())

# if __name__ == "__main__":
#     threading.Thread(target=server_start_asyn, daemon=True).start()
#     while True:
#         pass