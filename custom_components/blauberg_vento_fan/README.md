# Blauberg Vento Fan
This repo, and thus the first plugin, was created out of necessity.
The switch from Homebridge to Homeassistant failed due to the lack of a working plugin for my decentralized Blauberg Vento ventilation systems

## 1. Installation
1. save files from the blauberg_vento_fan folder to the Homeassistant folder under custom_components: /config/custom_components/blauberg_vento/...
2. restart HA. **Settings*** > **System** > **Restart Home Assistant**
3. add the **Blauberg Vento Fan** integration under **Settings** > **Devices & services**.
4. ventilation devices can then be added via the UI by entering the following data:
- Name
- IP ADDRESS
- Device ID
- Password

## 2. Features
- Getting and setting Turning Fan on and off
- Getting and setting Fan speed (33%=1, 66%=2, 99%=3)
- Getting and setting ventilation operation mode using swing control (when swing mode is on - heat recovery, off - ventilation)

## 3. Supported models
I was able to test the plugin with model 1 & 5. So I can't check if it will work fine with the remaining models.
According to Blauberg Connection to a “Smart Home” system guide - they all have same API, so this plugin should work fine for all listed bellow.

1. VENTO Expert A30 W V.2
2. VENTO Expert A50-1 W V.2
3. VENTO Expert A85-1 W V.2
4. VENTO Expert A100-1 W V.2
5. VENTO Expert Duo A30-1 W V.2
6. VENTO Expert A50-1 W V.3

## 4. Manufacturer information
Blauberg maintains very good documentation on the ventilation parameters in its product documentation.
Using the Vento Export W v2. as an example, all parameters for control are documented on pages 8 & 9.
https://documents.unidomo.de/de/Installationsanleitung/Blauberg/smart_home_vento_expert_w_v2cw201910172.pdf

## 5. Test tool
The repository includes a test tool (udp_test.py) for troubleshooting.
This expects the necessary parameters for control and outputs the sent UDP packet as well as the received one.
```console
$ python3 udp_test.py 192.168.1.2 1122334455667788 1111 33 on
Sending UDP packet: fd fd 02 10 30 30 31 44 30 30 32 44 34 42 34 36 35 37 30 37 04 31 31 31 31 03 01 01 02 01 b7 01 f8 04
Received UDP packet: fd fd 02 10 30 30 31 44 30 30 32 44 34 42 34 36 35 37 30 37 04 31 31 31 31 06 01 01 02 01 b7 01 fb 04
```

## 6. Debugging
```console
[...]
2025-02-02 17:16:17.038 DEBUG (SyncWorker_2) [custom_components.blauberg_vento.udp_client] Sending UDP packet to 10.3.0.33:4000 -> fdfd02103030314330303232344234363537303704313131310101000200b700e004
2025-02-02 17:16:17.047 DEBUG (SyncWorker_0) [custom_components.blauberg_vento.udp_client] Received 34 bytes: [0] fd [1] fd [2] 02 [3] 10 [4] 30 [5] 30 [6] 34 [7] 31 [8] 30 [9] 30 [10] 33 [11] 43 [12] 35 [13] 34 [14] 34 [15] 36 [16] 35 [17] 37 [18] 31 [19] 30 [20] 04 [21] 31 [22] 31 [23] 31 [24] 31 [25] 06 [26] 01 [27] 01 [28] 02 [29] 01 [30] b7 [31] 01 [32] d8 [33] 04 => Unit status [On], Speed number [1], Ventilation mode [Heat Recovery]
2025-02-02 17:16:17.048 DEBUG (MainThread) [custom_components.blauberg_vento.fan] Received response: fdfd02103030343130303343353434363537313004313131310601010201b701d804
2025-02-02 17:16:17.048 DEBUG (MainThread) [custom_components.blauberg_vento.fan] Raw UDP packet: fd fd 02 10 30 30 34 31 30 30 33 43 35 34 34 36 35 37 31 30 04 31 31 31 31 06 01 01 02 01 b7 01 d8 04
2025-02-02 17:16:17.048 DEBUG (MainThread) [custom_components.blauberg_vento.udp_client] Parsed parameters: {'unit_on_off': True, 'speed_number': 33, 'ventilation_mode': 'Heat Recovery'}
[...]
```

## 7. Backlog
- Log: Add uniq identifierer per device die identify device related log records
- Display: Filter status
- Button: Filter reset
- Cleanup log records with double information

## 8. Release Notes

### 0.1.0
- Initial version
