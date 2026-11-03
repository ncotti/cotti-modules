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
    dut.wstrb.value = 0b1

    # Initialize the RAM
    for i in range(8):
        dut.waddr.value = i
        dut.wdata.value = 0b000000001 << i
        await RisingEdge(dut.clk)
        await Timer(1, "ns")

    # Read back all values, while writing new ones
    # The read value should be the previous one
    dut.we.value = 1
    for i in range(8):
        dut.waddr.value = i
        dut.raddr.value = i
        dut.wdata.value = 0b11 << i
        await RisingEdge(dut.clk)
        await Timer(1, "ns")
        assert dut.rdata.value == 0b000000001 << (i)
        assert dut.rwdata.value == 0b000000001 << (i)

    # Check that the writes from the previous step went through.
    # Also, see that the rwdata is working as expected
    dut.we.value = 0
    dut.wdata.value = 0b000000000
    for i in range(8):
        dut.raddr.value = i
        dut.waddr.value = 7 - i
        await RisingEdge(dut.clk)
        await Timer(1, "ns")
        assert dut.rdata.value == 0b11 << i
        assert dut.rwdata.value == 0b110000000 >> i

    # Reading and writing the same address should return the previous stored value
    dut.we.value = 1
    dut.waddr.value = 4
    dut.raddr.value = 4
    dut.wstrb.value = 0b1
    dut.wdata.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    assert dut.rdata.value == 0b000110000

    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    assert dut.rdata.value == 0

@cocotb.test
async def test_we_test(dut):
    c = Clock(dut.clk, 10, "ns")
    c.start()

    dut.raddr.value = 3
    dut.waddr.value = 3
    dut.wstrb.value = 0b1

    # Write first value
    dut.we.value = 1
    dut.wdata.value = 0b101010101
    await RisingEdge(dut.clk)

    # With write enable disabled, the value should not be modified
    # Anyways, the previous value is returned
    dut.we.value = 0
    dut.wdata.value = 0b000000000
    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    assert dut.rdata.value == 0b101010101

    # Now, let write a new value
    # Value 0x12345678 should be returned, since is the one
    # stored in the memory
    dut.we.value = 1
    dut.wdata.value = 0b111100000
    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    assert dut.rdata.value == 0b101010101

    # Now, if we read that address we should see the new value
    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    assert dut.rdata.value == 0b111100000


@cocotb.test
async def test_ram_size(dut):
    c = Clock(dut.clk, 10, "ns")
    c.start()

    # Accessing last address should be OK
    dut.raddr.value = 7
    dut.waddr.value = 7
    dut.we.value = 1
    dut.wstrb.value = 0b1
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
        dut.wdata.value = 0b1111111111
        assert 0
    except ValueError:
        pass

    try:
        dut.wstrb.value = 0b10
        assert 0
    except ValueError:
        pass

    await RisingEdge(dut.clk)
