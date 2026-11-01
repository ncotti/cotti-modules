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
    dut.wstrb.value = 0xF

    # Initialize the RAM
    for i in range(8):
        dut.waddr.value = i * 4
        dut.wdata.value = 0x11111111 * (i+1)
        await RisingEdge(dut.clk)
        await Timer(1, "ns")

    # Read back all values, while writing new ones
    # The read value should be the previous one
    dut.we.value = 1
    for i in range(8):
        dut.waddr.value = i * 4
        dut.raddr.value = i * 4
        dut.wdata.value = 0x11 * (i+1)
        await RisingEdge(dut.clk)
        await Timer(1, "ns")
        assert dut.rdata.value == 0x11111111 * (i+1)

    # Check that the writes from the previous step went through
    dut.we.value = 0
    dut.wdata.value = 0xFFFFFFFF
    for i in range(8):
        dut.raddr.value = i * 4
        await RisingEdge(dut.clk)
        await Timer(1, "ns")
        assert dut.rdata.value == 0x11 * (i + 1)

    # Reading and writing the same address should return the previous stored value
    dut.we.value = 1
    dut.waddr.value = 4 * 4
    dut.raddr.value = 4 * 4
    dut.wstrb.value = 0xF
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

    dut.raddr.value = 3 * 4
    dut.waddr.value = 3 * 4
    dut.wstrb.value = 0xF

    # Write first value
    dut.we.value = 1
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
    dut.we.value = 1
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
    dut.waddr.value = 7 * 4
    dut.raddr.value = 7 * 4
    dut.we.value = 1
    dut.wstrb.value = 0xF
    dut.wdata.value = 0x12345678
    await RisingEdge(dut.clk)

    # Write first byte only
    dut.we.value = 1
    dut.wdata.value = 0xAAAAAAAA
    dut.wstrb.value = 0b0001
    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    assert dut.rdata.value == 0x12345678

    # Write second byte only
    dut.we.value = 1
    dut.wdata.value = 0xBBBBBBBB
    dut.wstrb.value = 0b0010
    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    assert dut.rdata.value == 0x123456AA

    # Write third byte only
    dut.we.value = 1
    dut.wdata.value = 0xCCCCCCCC
    dut.wstrb.value = 0b0100
    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    assert dut.rdata.value == 0x1234BBAA

    # Write fourth byte only
    dut.we.value = 1
    dut.wdata.value = 0xDDDDDDDD
    dut.wstrb.value = 0b1000
    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    assert dut.rdata.value == 0x12CCBBAA

    # Write some bytes
    dut.we.value = 1
    dut.wdata.value = 0xEEEEEEEE
    dut.wstrb.value = 0b1011
    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    assert dut.rdata.value == 0xDDCCBBAA

    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    assert dut.rdata.value == 0xEECCEEEE

@cocotb.test
async def test_unaligned_access(dut):
    c = Clock(dut.clk, 10, "ns")
    c.start()

    dut.raddr.value = 0
    dut.waddr.value = 0
    dut.we.value = 1
    dut.wstrb.value = 0xF

    # Initialize the RAM
    for i in range(8):
        dut.raddr.value = i * 4
        dut.waddr.value = i * 4
        dut.wdata.value = 0x11111111 * (i+1)
        await RisingEdge(dut.clk)
        await Timer(1, "ns")

    # Reading unaligned byte address should return the value of
    # the previous aligned address
    dut.we.value = 0
    dut.raddr.value = 5
    dut.waddr.value = 5
    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    assert dut.rdata.value == 0x22222222

    dut.raddr.value = 11
    dut.waddr.value = 11
    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    assert dut.rdata.value == 0x33333333

    # Writing unaligned byte address should write them based on the strobe value
    dut.we.value = 1
    dut.raddr.value = 14
    dut.waddr.value = 14
    dut.wdata.value = 0xAABBCCDD
    dut.wstrb.value = 0b1001
    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    assert dut.rdata.value == 0x44444444

    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    assert dut.rdata.value == 0xAA4444DD


@cocotb.test
async def test_ram_size(dut):
    c = Clock(dut.clk, 10, "ns")
    c.start()

    # Accessing last address should be OK
    dut.raddr.value = 7 * 4 + 3
    dut.waddr.value = 7 * 4 + 3
    dut.we.value = 1
    dut.wstrb.value = 0xF
    dut.wdata.value = 0

    await RisingEdge(dut.clk)

    # Writing or reading to a value outside the RAM should make the test fail
    try:
        dut.raddr.value = 8 * 4
        assert 0
    except ValueError:
        pass

    try:
        dut.waddr.value = 8 * 4
        assert 0
    except ValueError:
        pass

    await RisingEdge(dut.clk)
