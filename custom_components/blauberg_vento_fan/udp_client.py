# udp_client.py

import socket
import struct
import logging

_LOGGER = logging.getLogger(__name__)

# Beispiel-ParameterIDs
PARAM_UNIT_ON_OFF        = 0x01   # 0=Off, 1=On
PARAM_SPEED_NUMBER       = 0x02   # 1..3
PARAM_VENTILATION_MODE   = 0xB7   # 0=Ventilation, 1=Heat Recovery, 2=Supply

# Beispiel-Sonderbefehle
BGCP_CMD_PAGE           = 0xFF
BGCP_CMD_FUNC           = 0xFC
BGCP_CMD_SIZE           = 0xFE
BGCP_CMD_NOT_SUP        = 0xFD
BGCP_FUNC_RESP          = 0x06

class BlaubergVentoUDPClient:
    """Behandelt die UDP-Kommunikation mit dem Blauberg Vento Lüfter."""

    def __init__(self, ip, device_id, password, port=4000):
        self.ip = ip
        self.device_id = device_id.encode("ascii")
        self.password = password.encode("ascii")
        self.port = port

    def send_command(self, func: int, parameters: dict, response_length=256) -> bytes | None:
        """
        Sendet einen Befehl (func + Parameter) an den Lüfter und empfängt eine Antwort.
        Loggt sowohl die empfangenen Bytes als auch die interpretierten Parameter.
        """
        packet = self._build_packet(func, parameters)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.settimeout(3.0)
                _LOGGER.debug(
                    "Sending UDP packet to %s:%d -> %s",
                    self.ip, self.port, packet.hex()
                )
                sock.sendto(packet, (self.ip, self.port))

                response, _ = sock.recvfrom(response_length)
                # Nummeriere die Bytes
                numbered_bytes = " ".join(f"[{i}] {b:02x}" for i, b in enumerate(response))

                # Parse die Antwort
                parsed_params = self.parse_response(response)
                # Interpretiere die Parameter
                interpretation = self._interpret_params(parsed_params)

                _LOGGER.debug(
                    "Received %d bytes: %s => %s",
                    len(response), numbered_bytes, interpretation
                )
                return response

        except socket.timeout:
            _LOGGER.error("Timeout: Keine Antwort vom Lüfter unter %s", self.ip)
        except Exception as e:
            _LOGGER.error("UDP-Kommunikationsfehler: %s", e)
        return None

    def _build_packet(self, func: int, parameters: dict) -> bytes:
        """
        Baut das UDP-Paket gemäß dem Blauberg-/Vento-Protokoll auf:
        Start (0xFD 0xFD), Protokolltyp (0x02), ID, Passwort, Funktion, Parameter, Checksumme.
        """
        pkt = bytearray()
        pkt.extend(b'\xFD\xFD')  # Start
        pkt.append(0x02)          # Protokolltyp (0x02)

        # DeviceID
        pkt.append(len(self.device_id))
        pkt.extend(self.device_id)

        # Passwort
        pkt.append(len(self.password))
        pkt.extend(self.password)

        # Funktion (z.B. 0x01=READ, 0x03=WRITE)
        pkt.append(func)

        # Parameter-Paare
        for param_id, value in parameters.items():
            pkt.append(param_id & 0xFF)
            pkt.append(value & 0xFF)

        # Checksumme
        chksum = sum(pkt[2:]) & 0xFFFF
        pkt.append(chksum & 0xFF)
        pkt.append((chksum >> 8) & 0xFF)

        return bytes(pkt)

    def parse_response(self, response: bytes) -> dict:
        """
        Parst die empfangenen Bytes und gibt ein Dictionary mit den Parametern zurück.
        Unterstützt verschiedene Sonderbefehle gemäß deinem C-Code.
        """
        if len(response) < 8:
            _LOGGER.warning("Received response is too short: %d bytes", len(response))
            return {}

        # Prüfe Startbytes und Protokolltyp
        if response[0] != 0xFD or response[1] != 0xFD:
            _LOGGER.warning("Ungültige Startbytes in der Antwort.")
            return {}
        if response[2] != 0x02:
            _LOGGER.warning(f"Ungültiger Protokolltyp: {response[2]:02x}")
            return {}

        idx = 3
        dev_id_len = response[idx]
        idx += 1
        if idx + dev_id_len > len(response):
            _LOGGER.warning("DeviceID-Länge überschreitet die Antwortlänge.")
            return {}
        device_id = response[idx:idx + dev_id_len]
        idx += dev_id_len

        pw_len = response[idx]
        idx += 1
        if idx + pw_len > len(response):
            _LOGGER.warning("Passwort-Länge überschreitet die Antwortlänge.")
            return {}
        password = response[idx:idx + pw_len]
        idx += pw_len

        func_byte = response[idx]
        idx += 1

        length_without_checksum = len(response) - 2
        data_region = response[idx:length_without_checksum]

        # Checksumme prüfen
        if length_without_checksum + 2 != len(response):
            _LOGGER.warning("Mismatch in checksum calculation.")
            return {}
        actual_low = response[length_without_checksum]
        actual_high = response[length_without_checksum + 1]
        cs_calc = sum(response[2:length_without_checksum]) & 0xFFFF
        if (actual_low != (cs_calc & 0xFF)) or (actual_high != ((cs_calc >> 8) & 0xFF)):
            _LOGGER.warning("Checksumme stimmt nicht überein.")
            return {}

        parsed = {}
        i = 0
        while i < len(data_region):
            b = data_region[i]
            if b == BGCP_CMD_SIZE:  # 0xFE
                if i + 2 < len(data_region):
                    param_size = data_region[i+1]
                    param_id = data_region[i+2]
                    block_data = data_region[i+3:i+3+param_size]
                    parsed[param_id] = block_data
                    i += (3 + param_size)
                else:
                    _LOGGER.warning("Unvollständiges Parameter-Block gefunden.")
                    break
            elif b == BGCP_CMD_PAGE:  # 0xFF
                if i + 1 < len(data_region):
                    page = data_region[i+1]
                    _LOGGER.debug("Page Command: %02x", page)
                i += 2
            elif b == BGCP_CMD_FUNC:  # 0xFC
                if i + 1 < len(data_region):
                    func = data_region[i+1]
                    _LOGGER.debug("Function Command: %02x", func)
                i += 2
            elif b == BGCP_CMD_NOT_SUP:  # 0xFD
                if i + 1 < len(data_region):
                    not_sup = data_region[i+1]
                    _LOGGER.debug("Not Supported Command: %02x", not_sup)
                i += 2
            else:
                # Normales Param + Wert (2 Bytes)
                param_id = b
                val = None
                if i + 1 < len(data_region):
                    val = data_region[i+1]
                    # Interpretation der Werte
                    if param_id == PARAM_UNIT_ON_OFF:
                        parsed['unit_on_off'] = bool(val)
                    elif param_id == PARAM_SPEED_NUMBER:
                        parsed['speed_number'] = val * 33  # Beispielhafte Umrechnung
                    elif param_id == PARAM_VENTILATION_MODE:
                        if val == 0:
                            parsed['ventilation_mode'] = "Ventilation"
                        elif val == 1:
                            parsed['ventilation_mode'] = "Heat Recovery"
                        elif val == 2:
                            parsed['ventilation_mode'] = "Supply"
                        else:
                            parsed['ventilation_mode'] = f"Unknown ({val})"
                    else:
                        parsed[param_id] = val
                i += 2

        _LOGGER.debug("Parsed parameters: %s", parsed)
        return parsed

    def _interpret_params(self, params: dict) -> str:
        """
        Interpretiert die geparsten Parameter und gibt eine lesbare Zeichenkette zurück.
        Beispiel: "Unit status [Off], Speed number [1], Ventilation mode [Ventilation]"
        """
        msgs = []

        # UNIT_ON_OFF
        unit_val = params.get('unit_on_off')
        if unit_val is not None:
            status = "On" if unit_val else "Off"
            msgs.append(f"Unit status [{status}]")

        # SPEED_NUMBER
        speed_val = params.get('speed_number')
        if speed_val is not None:
            speed_level = speed_val // 33  # Beispielhafte Umrechnung zurück zu 1..3
            msgs.append(f"Speed number [{speed_level}]")

        # VENTILATION_MODE
        mode_val = params.get('ventilation_mode')
        if mode_val is not None:
            msgs.append(f"Ventilation mode [{mode_val}]")

        return ", ".join(msgs) if msgs else "No known param"