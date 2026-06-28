import ctypes, os
from .errors import FlasherError
from . import locate

class JLink():

    SPEED_AUTO = 0x0000
    SPEED_ADAPTIVE = 0xFFFF
    TIF_JTAG = 0
    TIF_SWD = 1

    DLL = None


    def __init__(self):
        self._dll = self._load_dll()


    def open(self):
        self._command('SuppressGUI 1')
        self._dll.JLINKARM_SelectUSB(0)
        if self._dll.JLINKARM_Open() != 0:
            raise FileNotFoundError("Cannot find JLink adaptor")
        self._command('HideDeviceSelection 1')
        self._command('SetBatchMode 0')
        self.is_open = True


    def close(self):
        self._dll.JLINKARM_Close()
        self.is_open = False


    def connect(self, target: str):
        if self._command("Device = " + target, raise_errors=False) != 0:
            raise ValueError(f"Unrecognised target \"{target}\"")
        self._dll.JLINKARM_SetSpeed(self.SPEED_AUTO)
        self._dll.JLINKARM_TIF_Select(self.TIF_SWD)
        if self._dll.JLINKARM_Connect() != 0:
            raise FlasherError("Target not detected")


    def run(self):
        if self._dll.JLINKARM_Go() != 0:
            raise FlasherError("Target go failed")


    def halt(self):
        if self._dll.JLINKARM_Halt() != 0:
            raise FlasherError("Target halt failed")


    def reset(self, run: bool = True):
        if self._dll.JLINKARM_Reset() != 0:
            raise FlasherError("Target reset failed")
        if run:
            self.run()


    def read(self, path: str, offset: int, size: int):
        self.halt()

        with open(path, 'wb') as f:
            buffer = (ctypes.c_uint8 * size)()
            read = self._dll.JLINKARM_ReadMemEx(offset, size, buffer, 4)
            if read != size:
                raise FlasherError(f"Target read failed")
            f.write(bytes(buffer))


    def erase(self, offset: int, size: int):
        self.halt()
        erase_func = self._get_pfunc(40, [ctypes.c_uint64, ctypes.c_uint64])
        if erase_func(offset, offset + size) != 0:
            raise FlasherError("Target erase failed")
    
    
    def mass_erase(self):
        self.halt()
        if self._dll.JLINK_EraseChip() != 0:
            raise FlasherError("Target erase failed")


    def program(self, path: str, offset: int, run: bool = True):
        self.halt()

        if offset == None:
            offset = 0
        
        self._dll.JLINK_DownloadFile(os.fsencode(path), offset)

        if run:
            self.reset(run)


    def _get_pfunc(self, index: int, signature: list):
        self._dll.JLINK_GetpFunc.restype = ctypes.c_void_p
        ptr = self._dll.JLINK_GetpFunc(index)
        prototype = ctypes.CFUNCTYPE(ctypes.c_int, *signature)
        return ctypes.cast(ptr, prototype)


    def _command(self, cmd: str, raise_errors = True) -> int:
        buffer_size = 336
        error_msg = (ctypes.c_char * buffer_size)()
        res = self._dll.JLINKARM_ExecCommand(cmd.encode(), error_msg, buffer_size)
        error_msg = ctypes.string_at(error_msg).decode()
        if len(error_msg):
            if raise_errors:
                raise Exception(error_msg.strip())
            return -1
        return res
    

    def _find_dll(self) -> str:
        if locate.IS_WINDOWS:
            return locate.locate_library("JLink_x64")
        return locate.locate_library("libjlinkarm") 
    

    def _load_dll(self):
        
        if JLink.DLL == None:

            path = self._find_dll()
            lib = ctypes.cdll.LoadLibrary(path)

            if locate.IS_WINDOWS:
                # Patch our library with standard call versions.
                standard_calls = [
                    'JLINK_DownloadFile',
                    'JLINK_EraseChip',
                    'JLINK_GetpFunc',
                ]
                winlib = ctypes.windll.LoadLibrary(path)
                for stdcall in standard_calls:
                    if hasattr(winlib, stdcall):
                        setattr(lib, stdcall, getattr(winlib, stdcall))
            JLink.DLL = lib

        return JLink.DLL