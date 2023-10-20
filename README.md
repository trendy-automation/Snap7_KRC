This program is intended for simulation and exchanging variables between PLC SIM, OfficeLite (or real KUKA robot) and RoboDK.

Main packages we used:

[python-snap7](https://pypi.org/project/python-snap7/) - Python wrapper for the snap7 PLC communication library

[robodk 5.6.4](https://pypi.org/project/robodk/) - The robodk package implements the [RoboDK API for Python](https://robodk.com/doc/en/PythonAPI/index.html)

[KRC-RPC](https://github.com/09th/KRC-RPC) - JSON-RPC for KUKA Cross3Krc COM server

Supported data types: String, Char, Real, UInt, USint, Bool.

### Instruction

1. Set up KRC-RPC in OfficeLite (or real KUKA robot).
2. Create Data Block that will represent KUKA and RoboDK variables.
3. Turn off "Optimized block access" in DB's attributes.
4. Allow "Permit access with PUT/GET communication from remote partner" in PLC properties (Protection & Security).
5. Fill *config.yaml* and *appsettings.json* in KRC-RPC (see "Example" folder)
6. Run RoboDK, PLC SIM and OfficeLite. Run KRC-RPC.exe in OfficeLite.
7. Run *main.py*.