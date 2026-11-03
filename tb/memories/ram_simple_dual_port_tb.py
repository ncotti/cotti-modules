# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026  Nicolas Gabriel Cotti

import cocotb
from cocotb.triggers import Timer, RisingEdge
from cocotb.clock import Clock

@cocotb.test
async def test_ram_write_and_read_back_aligned(dut):
    c = Clock(dut.clk, 10, "ns")
    c.start()

    dut.raddr.value = 0
    dut.waddr.value = 0
    dut.we.value = 1
    dut.wstrb.value = 0x3

    # Initialize the RAM
    for i in range(8):
        dut.waddr.value = i
        dut.wdata.value = 0x1111 * (i+1)
        await RisingEdge(dut.clk)
        await Timer(1, "ns")

    # Read back all values, while writing new ones
    # The read value should be the previous one
    dut.we.value = 1
    for i in range(8):
        dut.waddr.value = i
        dut.raddr.value = i
        dut.wdata.value = 0x11 * (i+1)
        await RisingEdge(dut.clk)
        await Timer(1, "ns")
        assert dut.rdata.value == 0x1111 * (i+1)

    # Check that the writes from the previous step went through
    dut.we.value = 0
    dut.wdata.value = 0xFFFF
    for i in range(8):
        dut.raddr.value = i
        await RisingEdge(dut.clk)
        await Timer(1, "ns")
        assert dut.rdata.value == 0x11 * (i + 1)

    # Reading and writing the same address should return the previous stored value
    dut.we.value = 1
    dut.waddr.value = 4
    dut.raddr.value = 4
    dut.wstrb.value = 0x3
    dut.wdata.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    assert dut.rdata.value == 0x55

    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    assert dut.rdata.value == 0


@cocotb.test
async def test_we_test(dut):
    c = Clock(dut.clk, 10, "ns")
    c.start()

    dut.raddr.value = 3
    dut.waddr.value = 3
    dut.wstrb.value = 0x3

    # Write first value
    dut.we.value = 1
    dut.wdata.value = 0x1234
    await RisingEdge(dut.clk)

    # With write enable disabled, the value should not be modified
    # Anyways, the previous value is returned
    dut.we.value = 0
    dut.wdata.value = 0xFFFF
    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    assert dut.rdata.value == 0x1234

    # Now, let write a new value
    # Value 0x12345678 should be returned, since is the one
    # stored in the memory
    dut.we.value = 1
    dut.wdata.value = 0x8765
    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    assert dut.rdata.value == 0x1234

    # Now, if we read that address we should see the new value
    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    assert dut.rdata.value == 0x8765


@cocotb.test
async def test_write_strobe(dut):
    c = Clock(dut.clk, 10, "ns")
    c.start()

    # Write initial value
    dut.waddr.value = 7
    dut.raddr.value = 7
    dut.we.value = 1
    dut.wstrb.value = 0x3
    dut.wdata.value = 0x1234
    await RisingEdge(dut.clk)

    # Write first byte only
    dut.we.value = 1
    dut.wdata.value = 0xAAAA
    dut.wstrb.value = 0b01
    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    assert dut.rdata.value == 0x1234

    # Write second byte only
    dut.we.value = 1
    dut.wdata.value = 0xBBBB
    dut.wstrb.value = 0b10
    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    assert dut.rdata.value == 0x12AA

    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    assert dut.rdata.value == 0xBBAA

@cocotb.test
async def test_ram_size(dut):
    c = Clock(dut.clk, 10, "ns")
    c.start()

    # Accessing last address should be OK
    dut.raddr.value = 7
    dut.waddr.value = 7
    dut.we.value = 1
    dut.wstrb.value = 0x3
    dut.wdata.value = 0

    await RisingEdge(dut.clk)

    # Writing or reading to a value outside the RAM should make the test fail
    try:
        dut.raddr.value = 8
        assert 0
    except ValueError:
        pass

    try:
        dut.waddr.value = 8
        assert 0
    except ValueError:
        pass
    try:
        dut.wstrb.value = 0b111
        assert 0
    except ValueError:
        pass

    await RisingEdge(dut.clk)
