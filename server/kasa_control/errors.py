TPAP_SETUP_HINT = (
    "Plug uses TPAP encryption (not supported locally yet). "
    "In the Kasa app: Me → Third-Party Services → turn ON "
    "Third-Party Compatibility, then unplug/replug the KP125M. "
    "Retry after the plug reconnects (should use KLAP)."
)


def friendly_kasa_error(exc: BaseException) -> str | None:
    message = str(exc)
    if "encrypt_type TPAP" in message or "encrypt_type='TPAP'" in message:
        return TPAP_SETUP_HINT
    if "Unsupported device" in message and "TPAP" in message:
        return TPAP_SETUP_HINT
    return None
