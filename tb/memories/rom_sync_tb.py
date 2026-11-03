# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026  Nicolas Gabriel Cotti

import cocotb
from cocotb.triggers import Timer, RisingEdge
from cocotb.clock import Clock


@cocotb.test
async def test_rom_sync(dut):
    c = Clock(dut.clk, 10, "ns")
    c.start(start_high=True)

    dut.addr.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    assert dut.dread.value == 0x12345678

    for i in range(1, 16):
        dut.addr.value = i
        await RisingEdge(dut.clk)
        await Timer(1, "ns")
        assert dut.dread.value == 0x11111111 * i
