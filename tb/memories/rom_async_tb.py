# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026  Nicolas Gabriel Cotti

import cocotb
from cocotb.triggers import Timer


@cocotb.test
async def test_rom_sync(dut):
    dut.raddr.value = 0
    await Timer(1, "ns")
    assert dut.rdata.value == 0x12

    for i in range(1, 16):
        dut.raddr.value = i
        await Timer(1, "ns")
        assert dut.rdata.value == 0x11 * i
