import os

class Flasher():
    def __init__(self, adaptor: str = "stlink"):
        self.adaptor = self._find_adaptor(adaptor)
        self._target = None


    def __enter__(self):
        self.adaptor.open()
        return self
    

    def __exit__(self, *args):
        self.adaptor.close()


    def close(self):
        self.adaptor.close()


    def connect(self, target: str = "STM32L051K8"):
        self.adaptor.connect(target)
        self._target = target


    def run(self):
        self._assert_ready()
        return self.adaptor.run()
    

    def halt(self):
        self._assert_ready()
        return self.adaptor.halt()


    def reset(self, run: bool = True):
        self._assert_ready()
        return self.adaptor.reset(run)


    def program(self, path: str, offset: int = None, run: bool = True):
        self._assert_ready()

        if not os.path.exists(path):
            raise FileNotFoundError(f"Cannot locate file {path}")
        path = os.path.abspath(path)

        if offset == None:
            offset = self._default_offset()
        
        return self.adaptor.program(path, offset, run)
    

    def read(self, path: str, offset: int, size: int):
        self._assert_ready()

        root, _ = os.path.split(path)
        if root:
            os.makedirs(root, exist_ok=True)
        path = os.path.abspath(path)

        if offset == None:
            offset = self._default_offset()

        return self.adaptor.read(path, offset, size)


    def erase(self, offset: int = None, size: int = None):
        self._assert_ready()

        if size == None:
            return self.adaptor.mass_erase()

        if offset == None:
            offset = self._default_offset()

        return self.adaptor.erase(offset, size)
    

    def _default_offset(self) -> int:
        if self._target.startswith("STM"):
            return 0x08000000
        return 0
    

    def _assert_ready(self):
        if not self.adaptor.is_open:
            raise AssertionError("Adaptor not opened")
        if self._target == None:
            raise AssertionError("Target has not been selected")
        

    def _find_adaptor(self, adaptor: str):

        if adaptor == "jlink":
            from .jlink import JLink
            return JLink()

        from .openocd import OpenOCD
        if adaptor in OpenOCD.INTERFACES:
            return OpenOCD(adaptor)
        
        raise LookupError("Unrecognised backend")
    

