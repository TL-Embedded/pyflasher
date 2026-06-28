import subprocess, re, sys
from .errors import FlasherError
from . import locate


class OpenOCD():

    INTERFACES = {
        "stlink": "interface/stlink.cfg",
        "aphid": "interface/ftdi/aphid-v1.cfg",
    }


    def __init__(self, interface: str = "stlink"):
        self._openocd_path = locate.locate_executable("openocd")
        self._interface_cfg = self._get_interface_config(interface)
        self._target = None
        self._target_cfg = None
        self._transport = "swd"
        self.is_open = False


    def open(self):
        self.is_open = True


    def close(self):
        self.is_open = False


    def connect(self, target: str):
        self._target = self._get_target_name(target)
        self._target_cfg = self._get_target_config(self._target)


    def run(self):
        try:
            self._openocd_command("init", "resume", "shutdown")
        except FlasherError as e:
            if e.args[0] != "Target not halted":
                raise e


    def halt(self):
        self._openocd_command("init", "halt", "shutdown")


    def reset(self, run: bool = True):
        self._openocd_command("init", "reset run" if run else "reset halt", "shutdown")


    def read(self, path: str, offset: int, size: int):
        self._openocd_command("init", "halt", f"dump_image \"{path}\" {hex(offset)} {hex(size)}", "shutdown")


    def erase(self, offset: int, size: int, bank: int = 0):
        self._openocd_command("init", "reset init", f"flash erase_address {hex(offset)} {hex(size)}", "shutdown")


    def mass_erase(self, bank: int = 0):
        self._openocd_command("init", "reset init", f"{self._target} mass_erase {bank}", "shutdown")


    def program(self, path: str, offset: int, run: bool = True):
        # This uses an openocd program script, so we dont need individual commands.
        program_cmd = ["program", f'"{path}"', "preverify", "verify", "reset", "exit"]
        if run:
            program_cmd.append("run")
        if path.endswith(".bin"):
            program_cmd.append(hex(offset))
        self._openocd_command(" ".join(program_cmd))


    def _openocd_command(self, *commands: list[str]):
        args = [
            self._openocd_path,
            "-f", self._interface_cfg,
            "-c", f"transport select {self._transport}",
            "-f", self._target_cfg
        ]
        for command in commands:
            args += ["-c", command]
        result = subprocess.run(args, capture_output=True)
        status, stderr = result.returncode, result.stderr.decode()
        if status != 0:
            if "open failed" in stderr or "unable to open" in stderr:
                raise FlasherError("Adaptor not detected")
            if "target voltage may be too low for reliable debugging" in stderr:
                raise FlasherError("Target voltage low")
            if "init mode failed" in stderr or "Error connecting DP" in stderr:
                raise FlasherError("Target not detected")
            if "target not halted" in stderr:
                raise FlasherError("Target not halted")
            
            print(stderr)
            raise FlasherError("Unknown failure")


    def _get_interface_config(self, interface: str) -> str:
        interface = interface.lower()
        
        if interface in self.INTERFACES:
            return self.INTERFACES[interface]
        
        raise LookupError(f"Could not interface cfg for \"{interface}\"")


    def _get_target_name(self, target: str) -> str:
        target = target.lower()
        match = re.match(r"^(stm32[\w]{2})", target)
        if match:
            return match.group(1) + "x"
        
        match = re.match(r"^(nrf[\d]{2})", target)
        if match:
            return match.group(1)

        raise LookupError(f"Could not target cfg for \"{target}\"")
    

    def _get_target_config(self, target) -> str:
        return f"target/{target}.cfg"
