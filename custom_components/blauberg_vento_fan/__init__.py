# __init__.py

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

DOMAIN = "blauberg_vento"
_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    """
    Diese Funktion wird aufgerufen, wenn die Integration über YAML konfiguriert wird.
    Da wir eine reine Config-Flow-Integration nutzen, tun wir hier nichts und geben einfach True zurück.
    """
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """
    Wird aufgerufen, wenn ein neuer Config-Entry erstellt wird (über die UI).
    Leitet den Setup-Prozess an die 'fan'-Plattform weiter.
    """
    hass.data.setdefault(DOMAIN, {})
    await hass.config_entries.async_forward_entry_setups(entry, ["fan"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """
    Wird aufgerufen, wenn ein Config-Entry entladen wird (z.B. bei Deinstallation).
    """
    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, "fan")
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
