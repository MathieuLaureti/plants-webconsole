from kasa import Discover

from kasa_control import config


async def _device():
    return await Discover.discover_single(
        config.KASA_HOST,
        username=config.KASA_USERNAME,
        password=config.KASA_PASSWORD,
    )


async def get_state() -> bool:
    dev = await _device()
    await dev.update()
    return dev.is_on


async def set_power(on: bool) -> bool:
    dev = await _device()
    await dev.update()
    if on:
        await dev.turn_on()
    else:
        await dev.turn_off()
    await dev.update()
    return dev.is_on
