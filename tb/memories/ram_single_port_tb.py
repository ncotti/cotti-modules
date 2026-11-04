# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026  Nicolas Gabriel Cotti

import cocotb
from cocotb.triggers import Timer, RisingEdge
from cocotb.clock import Clock


@cocotb.test
async def test_ram_write_and_read_back_aligned(dut):
    c = Clock(dut.clk, 10, "ns")
    c.start()

    dut.addr.value = 0
    dut.we.value = 0xF

    # Initialize the RAM
    for i in range(8):
        dut.addr.value = i
        dut.wdata.value = 0x11111111 * (i + 1)
        await RisingEdge(dut.clk)
        await Timer(1, "ns")

    # Read back all values, while writing new ones
    # The read value should be the previous one
    dut.we.value = 0xF
    for i in range(8):
        dut.addr.value = i
        dut.wdata.value = 0x00FF00FF
        await RisingEdge(dut.clk)
        await Timer(1, "ns")
        assert dut.rdata.value == 0x11111111 * (i + 1)


@cocotb.test
async def test_we_test(dut):
    c = Clock(dut.clk, 10, "ns")
    c.start()

    dut.addr.value = 3

    # Write first value
    dut.we.value = 0xF
    dut.wdata.value = 0x12345678
    await RisingEdge(dut.clk)

    # With write enable disabled, the value should not be modified
    # Anyways, the previous value is returned
    dut.we.value = 0
    dut.wdata.value = 0xFFFFFFFF
    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    assert dut.rdata.value == 0x12345678

    # Now, let write a new value
    # Value 0x12345678 should be returned, since is the one
    # stored in the memory
    dut.we.value = 0xF
    dut.wdata.value = 0x87654321
    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    assert dut.rdata.value == 0x12345678

    # Now, if we read that address we should see the new value
    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    assert dut.rdata.value == 0x87654321


@cocotb.test
async def test_write_strobe(dut):
    c = Clock(dut.clk, 10, "ns")
    c.start()

    # Write initial value
    dut.addr.value = 7
    dut.we.value = 0xF
    dut.wdata.value = 0x12345678
    await RisingEdge(dut.clk)

    # Write first byte only
    dut.wdata.value = 0xAAAAAAAA
    dut.we.value = 0b0001
    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    assert dut.rdata.value == 0x12345678

    # Write second byte only
    dut.wdata.value = 0xBBBBBBBB
    dut.we.value = 0b0010
    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    assert dut.rdata.value == 0x123456AA

    # Write third byte only
    dut.wdata.value = 0xCCCCCCCC
    dut.we.value = 0b0100
    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    assert dut.rdata.value == 0x1234BBAA

    # Write fourth byte only
    dut.wdata.value = 0xDDDDDDDD
    dut.we.value = 0b1000
    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    assert dut.rdata.value == 0x12CCBBAA

    # Write some bytes
    dut.wdata.value = 0xEEEEEEEE
    dut.we.value = 0b1011
    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    assert dut.rdata.value == 0xDDCCBBAA

    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    assert dut.rdata.value == 0xEECCEEEE


@cocotb.test
async def test_ram_size(dut):
    c = Clock(dut.clk, 10, "ns")
    c.start()

    # Accessing last address should be OK
    dut.addr.value = 7
    dut.we.value = 0xF
    dut.wdata.value = 0

    await RisingEdge(dut.clk)

    # Writing to a value outside the RAM should make the test fail
    try:
        dut.addr.value = 8
        assert 0
    except ValueError:
        pass

    try:
        dut.we.value = 0x10
        assert 0
    except ValueError:
        pass

    await RisingEdge(dut.clk)
