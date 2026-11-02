from kasa import Discover

from kasa_control import config


async def _device(host: str):
    return await Discover.discover_single(
        host,
        username=config.KASA_USERNAME,
        password=config.KASA_PASSWORD,
    )


async def get_state(host: str) -> bool:
    dev = await _device(host)
    await dev.update()
    return dev.is_on


async def set_power(host: str, on: bool) -> bool:
    dev = await _device(host)
    await dev.update()
    if on:
        await dev.turn_on()
    else:
        await dev.turn_off()
    await dev.update()
    return dev.is_on
