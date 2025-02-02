## Homeassistant
This repo, and thus the first plugin, was created out of necessity.
The switch from Homebridge to Homeassistant failed due to the lack of a working plugin for my decentralized Blauberg Vento ventilation systems


## 1st installation
1. save files from the blauberg_vento_fan folder to the Homeassistant folder under custom_components: /config/custom_components/blauberg_vento/...
2. restart HA. **Settings*** > **System** > **Restart Home Assistant**
3. add the **Blauberg Vento Fan** integration under **Settings** > **Devices & services**.
4. ventilation devices can then be added via the UI by entering the following data:
- Name
- IP ADDRESS
- Device ID
- Password

## 2. features
- Getting and setting Turning Fan on and off
- Getting and setting Fan speed (33%=1, 66%=2, 99%=3)
- Getting and setting ventilation operation mode using swing control (when swing mode is on - heat recovery, off - ventilation)

## 3. supported models
I was able to test the plugin with model 1 & 5. So I can't check if it will work fine with the remaining models.
According to Blauberg Connection to a “Smart Home” system guide - they all have same API, so this plugin should work fine for all listed bellow.

1. VENTO Expert A30 W V.2
2. VENTO Expert A50-1 W V.2
3. VENTO Expert A85-1 W V.2
4. VENTO Expert A100-1 W V.2
5. VENTO Expert Duo A30-1 W V.2
6. VENTO Expert A50-1 W V.3

## 4. manufacturer information
Blauberg maintains very good documentation on the ventilation parameters in its product documentation.
Using the Vento Export W v2. as an example, all parameters for control are documented on pages 8 & 9.
https://documents.unidomo.de/de/Installationsanleitung/Blauberg/smart_home_vento_expert_w_v2cw201910172.pdf

## 5. test tool
The repository includes a test tool (udp_test.py) for troubleshooting.
This expects the necessary parameters for control and outputs the sent UDP packet as well as the received one.
```console
$ python3 udp_test.py 192.168.1.2 1122334455667788 1111 33 on
Sending UDP packet: fd fd 02 10 30 30 31 44 30 30 32 44 34 42 34 36 35 37 30 37 04 31 31 31 31 03 01 01 02 01 b7 01 f8 04
Received UDP packet: fd fd 02 10 30 30 31 44 30 30 32 44 34 42 34 36 35 37 30 37 04 31 31 31 31 06 01 01 02 01 b7 01 fb 04
```
## 6. backlog
- Display of the filter status
- Reset option / function for the filter status

## 7. release notes

### 0.1.0
- Initial version
