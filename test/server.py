import asyncio

coonlist = []
IP, PORT = "localhost", 10002
FILESIZE = 1048576


async def boarder(message: str, coonlist=coonlist):
    for writer in coonlist:
        date = message.encode("utf-8")
        writer.write(date)


async def handle_echo(reader, writer):
    coonlist.append(writer)
    while 1:
        data = await reader.read(FILESIZE)
        if len(data) < 1:
            break
        message = data.decode("utf-8")
        addr = writer.get_extra_info("peername")
        # print(f"Received {message!r} from {addr!r}")
        await boarder(message)
    print("Close the connection")
    writer.close()
    coonlist.remove(writer)


async def main():
    server = await asyncio.start_server(handle_echo, IP, PORT)
    addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets)
    print(f"Serving on {addrs}")
    async with server:
        await server.serve_forever()


asyncio.run(main())
