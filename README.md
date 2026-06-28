# pyflasher

Pyflasher is a python wrapper for common programming adaptors, intended to be used for test or programming fixtures.

## Adaptors

It provides a uniform API for the following adaptors:

| Adaptor      | Name   | Backend   | Link |
| ------------ | ------ | --------- | ---- |
| Segger JLink | jlink  | JLink DLL | [J-Link](https://www.segger.com/products/debug-probes/j-link/) |
| ST-Link      | stlink | OpenOCD   | [ST-Link-V2](https://www.st.com/en/development-tools/st-link-v2.html) |
| Aphid        | aphid  | OpenOCD   | [Aphid Github](https://github.com/TL-Embedded/Aphid-HW) |

## Targets

Some minimal work may be needed to add support for new targets. This includes the default flash addresses and known device names. STM32's and NRF's should be fully supported.

## Prerequisites

- If using the OpenOCD backend, [openocd](https://openocd.org/pages/getting-openocd.html) is required.
- If using J-Link backend, [jlink software](https://www.segger.com/downloads/jlink/) is required.

> [!TIP]
> Pyflasher will find the tools automatically if they are available on the system paths.
> You can manually add search paths with `flasher.add_search_path("/path/to/tools")`.

# Usage

The flasher should be used with the python context manager pattern, as below.

```python
import flasher

with flasher.Flasher("stlink") as tool:
    tool.connect("STM32L051K8")
    tool.program("firmware.bin")
```

## Connect

`.connect(target: str)`

Select the target device. This must be called prior to any other functions.

> [!IMPORTANT]
> This is a prerequsite to all other functions.

> [!TIP]
> Target names should be fully specified to confirm to J-Link's naming conventions. I.e, `STM32L051K8`.
> OpenOCD needs less info - it will accept `STM32L0`, but this will be less portable.

## Run

`.run()`

Resumes firmware execution on the target.

## Halt

`.run()`

Halts firmware execution on the target.

# Reset

`.reset(run=True)`

Resets the target. Execution is optionally started if run = true.

# Program

`.program(path, offset=None, run=True)`

Programs a file to the target. The firmware is optionally started if run = true.

`.bin` and `.hex` files are currently supported.

> [!TIP]
> offset = None will select the flash base address.
> The offset is ignored for .hex files.

# Read

`.read(path, offset, size)`

Reads memory into a file. offset = None can be used to select the flash base address, but the size must be specifed.

`.bin` files are currently supported.

> [!TIP]
> offset = None will select the flash base address.

# Erase

`.erase(offset=None, size=None)`

Erases target memory. size = None will trigger a mass erase.

> [!IMPORTANT]
> The offset and size should align to the targets flash pages.

> [!TIP]
> offset = None will select the flash base address.
