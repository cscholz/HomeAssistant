# fan.py

import logging
import asyncio
from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_IP_ADDRESS, CONF_PASSWORD
from homeassistant.helpers.event import async_track_time_interval
from datetime import timedelta
from .udp_client import BlaubergVentoUDPClient
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """
    Setup-Funktion für die Fan-Plattform, aufgerufen durch async_forward_entry_setups.
    Erstellt und fügt die FanEntity hinzu.
    """
    data = entry.data
    name = data.get("name", "Blauberg Vento")
    ip = data.get(CONF_IP_ADDRESS)
    password = data.get(CONF_PASSWORD)
    device_id = data.get("deviceId")

    # Überprüfe, ob alle erforderlichen Konfigurationsparameter vorhanden sind
    if not all([name, ip, password, device_id]):
        _LOGGER.error("Missing required configuration parameters.")
        return

    fan = BlaubergVentoFan(name, ip, password, device_id)
    async_add_entities([fan], update_before_add=True)

    # Starte periodische Updates alle 10 Sekunden mit einer separaten Callback-Methode
    async_track_time_interval(hass, fan.periodic_update, timedelta(seconds=10))

class BlaubergVentoFan(FanEntity):
    """Repräsentiert den Blauberg Vento Fan als Home Assistant FanEntity."""

    _attr_supported_features = (
        FanEntityFeature.SET_SPEED |
        FanEntityFeature.TURN_ON |
        FanEntityFeature.TURN_OFF |
        FanEntityFeature.OSCILLATE
    )

    def __init__(self, name, ip, password, device_id):
        """Initialisiert die FanEntity."""
        self._name = name
        self._ip = ip
        self._password = password
        self._device_id = device_id
        self._state = False
        self._speed = 0
        self._ventilation_mode = "Ventilation"  # Standard: Lüftung (alternativ "Heat Recovery")
        self._client = BlaubergVentoUDPClient(ip, device_id, password)

        # Setze eine eindeutige ID für die Entität
        self._attr_unique_id = f"{self._device_id}_fan"

    @property
    def name(self):
        """Gibt den Namen des Lüfters zurück."""
        return self._name

    @property
    def is_on(self):
        """Gibt den Zustand des Lüfters zurück."""
        return self._state

    @property
    def percentage(self):
        """Gibt die Geschwindigkeit des Lüfters als Prozentwert zurück."""
        return self._speed

    @property
    def supported_features(self):
        """Gibt die unterstützten Funktionen zurück."""
        return self._attr_supported_features

    @property
    def extra_state_attributes(self):
        """Gibt zusätzliche Attribute zurück."""
        return {
            "ventilation_mode": self._ventilation_mode
        }

    @property
    def unique_id(self):
        """Gibt die eindeutige ID der Entität zurück."""
        return self._attr_unique_id

    @property
    def oscillating(self):
        """
        Liefert True, wenn der reversierende Modus (Wärmerückgewinnung) aktiv ist,
        sonst False.
        """
        return self._ventilation_mode == "Heat Recovery"

    async def async_update(self):
        """Aktualisiert den Status des Lüfters."""
        _LOGGER.debug("Updating fan status for [%s]", self._name)
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self._client.send_command,
                0x01,  # Funktion: READ
                {0x01: 0, 0x02: 0, 0xB7: 0},  # Parameter: Unit, Speed und Ventilation Mode auslesen
                256
            )
            if response:
                _LOGGER.debug("Received response: %s", response.hex())
                # Ausgabe des rohen UDP-Pakets ohne Nummerierung:
                raw_bytes = " ".join(f"{b:02x}" for b in response)
                _LOGGER.debug("Raw UDP packet: %s", raw_bytes)
                # Parse die Antwort in udp_client
                params = self._client.parse_response(response)
                _LOGGER.debug("Parsed parameters: %s", params)
                if params:
                    if 'unit_on_off' in params:
                        self._state = params['unit_on_off']
                    if 'speed_number' in params:
                        self._speed = params['speed_number']
                    if 'ventilation_mode' in params:
                        self._ventilation_mode = params['ventilation_mode']

                    _LOGGER.debug(
                        "Interpreted status: On=%s, Speed=%d, Ventilation Mode=%s",
                        self._state, self._speed, self._ventilation_mode
                    )
                else:
                    _LOGGER.warning("No valid parameters parsed from response.")
            else:
                _LOGGER.warning("No response received during update.")
        except Exception as e:
            _LOGGER.error("Error during async_update: %s", e)

        self.schedule_update_ha_state()

    async def async_turn_on(self, percentage: int = None, preset_mode: str = None, **kwargs):
        """Schaltet den Lüfter ein."""
        _LOGGER.debug(
            "Turning on [%s] with percentage: %s, preset_mode: %s, kwargs: %s",
            self._name, percentage, preset_mode, kwargs
        )
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._client.send_command,
                0x03,  # Funktion: WRITE
                {0x01: 1},  # Parameter: Unit einschalten
                256
            )
            self._state = True
            await self.async_update()
        except Exception as e:
            _LOGGER.error("Error during async_turn_on: %s", e)

    async def async_turn_off(self, **kwargs):
        """Schaltet den Lüfter aus."""
        _LOGGER.debug("Turning off [%s] with kwargs: %s", self._name, kwargs)
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._client.send_command,
                0x03,  # Funktion: WRITE
                {0x01: 0},  # Parameter: Unit ausschalten
                256
            )
            self._state = False
            await self.async_update()
        except Exception as e:
            _LOGGER.error("Error during async_turn_off: %s", e)

    async def async_set_percentage(self, percentage):
        """Setzt die Lüftergeschwindigkeit basierend auf dem Prozentwert."""
        _LOGGER.debug("Setting speed for [%s] to %s%%", self._name, percentage)
        try:
            if percentage <= 33:
                speed_cmd = 1
            elif percentage <= 66:
                speed_cmd = 2
            else:
                speed_cmd = 3
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._client.send_command,
                0x03,  # Funktion: WRITE
                {0x02: speed_cmd},  # Parameter: Geschwindigkeit setzen
                256
            )
            self._speed = speed_cmd * 33  # Beispielhafte Berechnung, ggf. anpassen
            await self.async_update()
        except Exception as e:
            _LOGGER.error("Error during async_set_percentage: %s", e)

    async def async_oscillate(self, oscillating: bool) -> None:
        """
        Schaltet den reversierenden Modus (Wärmerückgewinnung) ein oder aus.
        Diese Methode wird vom Home Assistant Fan-Dashboard als Oszillationsschalter verwendet.
        """
        _LOGGER.debug("Setting oscillate (reverse mode) for [%s] to %s", self._name, oscillating)
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._client.send_command,
                0x03,  # Funktion: WRITE
                {0xB7: 1 if oscillating else 0},  # Parameter: Betriebsart (1: Wärmerückgewinnung, 0: Lüftung)
                256
            )
            self._ventilation_mode = "Heat Recovery" if oscillating else "Ventilation"
            await self.async_update()
        except Exception as e:
            _LOGGER.error("Error during async_oscillate: %s", e)

    async def periodic_update(self, now):
        """Callback-Methode für periodische Updates."""
        _LOGGER.debug("Starting periodic update for [%s]", self._name)
        await self.async_update()