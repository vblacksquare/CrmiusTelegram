
import asyncio
from aiogram.types import Message


loader_string = "1️⃣ 2️⃣ 3️⃣ 4️⃣ 5️⃣ 6️⃣ 7️⃣ 8️⃣ 9️⃣ 🔟".split()
step_char = "*️⃣"


async def loader(message: Message, length: float = 5):
    async def __loader():
        base_text = message.text
        temp_string = loader_string[:]
        delay = length / len(loader_string)

        for i in range(len(loader_string)):
            await message.edit_text(
                '\n\n'.join([
                    base_text,
                    ''.join(temp_string)
                ]), parse_mode="html"
            )

            temp_string = loader_string[:]
            temp_string[i] = step_char
            await asyncio.sleep(delay)

        await message.edit_text(
            '\n\n'.join([
                base_text,
                ''.join(temp_string)
            ]), parse_mode="html"
        )
        await asyncio.sleep(.5)

    loop = asyncio.get_running_loop()
    return loop.create_task(__loader())


async def static_loader(message: Message):
    pass


class BaseLoader:
    def __init__(self, delay=1):
        self.is_running = False
        self.task = None

        self.delay = delay
        self.iter = 1

    async def load_step(self, message: Message) -> str:
        pass

    async def __start(self, message: Message):
        while self.is_running:
            text = await self.load_step(message)
            await message.edit_text(text=text, parse_mode="html")

            self.iter += 1
            await asyncio.sleep(self.delay)

    async def start(self, message: Message):
        self.is_running = True
        self.iter = 1
        loop = asyncio.get_running_loop()
        self.task = loop.create_task(self.__start(message=message))
        return self.task

    async def stop(self, timer=0):
        if timer:
            await asyncio.sleep(timer)

        self.is_running = False
        await self.task


class CharLoader(BaseLoader):
    async def load_step(self, message: Message) -> str:
        return ''.join((
            message.text,
            '.'*(self.iter % 4)
        ))
