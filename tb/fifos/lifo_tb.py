# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026  Nicolas Gabriel Cotti

import cocotb
from cocotb.triggers import Timer, RisingEdge
from cocotb.clock import Clock

LIFO_SIZE_WORDS = 5

async def reset(dut):
    c = Clock(dut.clk, 10, "ns")
    c.start(start_high=False)

    dut.rstN.value = 0
    dut.din.value = 0
    dut.push.value = 0
    dut.pop.value = 0

    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    dut.rstN.value = 1

    assert dut.dout.value == 0
    assert dut.empty.value == 1
    assert dut.full.value == 0
    assert dut.num.value == 0

@cocotb.test
async def test_lifo_empty(dut):
    await reset(dut)

    assert dut.empty.value == 1
    assert dut.num.value == 0

    dut.push.value = 1
    dut.pop.value = 0
    dut.din.value = 0xAA

    await RisingEdge(dut.clk)
    await Timer(1, "ns")

    assert dut.empty.value == 0
    assert dut.num.value == 1
    assert dut.dout.value == 0

    dut.push.value = 0
    dut.pop.value = 1

    await RisingEdge(dut.clk)
    await Timer(1, "ns")

    assert dut.empty.value == 1
    assert dut.num.value == 0
    assert dut.dout.value == 0xAA

    # Should keep the same value if no push or pop
    dut.pop.value = 0
    dut.push.value = 0

    await RisingEdge(dut.clk)
    await Timer(1, "ns")

    assert dut.empty.value == 1
    assert dut.dout.value == 0xAA
    assert dut.num.value == 0

    # Popping on empty should keep the same value
    await RisingEdge(dut.clk)
    await Timer(1, "ns")

    assert dut.empty.value == 1
    assert dut.dout.value == 0xAA
    assert dut.num.value == 0

@cocotb.test
async def test_lifo_simple_push_pop(dut):
    await reset(dut)

    assert dut.num.value == 0
    assert dut.dout.value == 0

    dut.push.value = 1
    dut.pop.value = 0
    dut.din.value = 0xAA

    await RisingEdge(dut.clk)
    await Timer(1, "ns")

    assert dut.num.value == 1
    assert dut.dout.value == 0

    dut.push.value = 1
    dut.pop.value = 0
    dut.din.value = 0xBB

    await RisingEdge(dut.clk)
    await Timer(1, "ns")

    assert dut.num.value == 2
    assert dut.dout.value == 0

    dut.push.value = 0
    dut.pop.value = 0
    dut.din.value = 0xCC

    await RisingEdge(dut.clk)
    await Timer(1, "ns")

    assert dut.num.value == 2
    assert dut.dout.value == 0

    dut.push.value = 0
    dut.pop.value = 1
    dut.din.value = 0xCC

    await RisingEdge(dut.clk)
    await Timer(1, "ns")

    assert dut.num.value == 1
    assert dut.dout.value == 0xBB

    dut.push.value = 0
    dut.pop.value = 0
    dut.din.value = 0xCC

    await RisingEdge(dut.clk)
    await Timer(1, "ns")

    assert dut.num.value == 1
    assert dut.dout.value == 0xBB

    dut.push.value = 1
    dut.pop.value = 0
    dut.din.value = 0xCC

    await RisingEdge(dut.clk)
    await Timer(1, "ns")

    assert dut.num.value == 2
    assert dut.dout.value == 0xBB

    dut.push.value = 0
    dut.pop.value = 1
    dut.din.value = 0xDD

    await RisingEdge(dut.clk)
    await Timer(1, "ns")

    assert dut.num.value == 1
    assert dut.dout.value == 0xCC

    dut.push.value = 0
    dut.pop.value = 1
    dut.din.value = 0xDD

    await RisingEdge(dut.clk)
    await Timer(1, "ns")

    assert dut.num.value == 0
    assert dut.dout.value == 0xAA

    dut.push.value = 0
    dut.pop.value = 1
    dut.din.value = 0xDD

    await RisingEdge(dut.clk)
    await Timer(1, "ns")

    assert dut.num.value == 0
    assert dut.dout.value == 0xAA


@cocotb.test
async def test_full_push_full_pop(dut):
    await reset(dut)

    assert dut.empty.value == 1

    for i in range(LIFO_SIZE_WORDS):
        dut.push.value = 1
        dut.pop.value = 0
        dut.din.value = i + 1
        await RisingEdge(dut.clk)
        await Timer(1, "ns")

        assert dut.num.value == i + 1

    assert dut.full.value == 1
    assert dut.num.value == LIFO_SIZE_WORDS

    for i in range(LIFO_SIZE_WORDS):
        dut.push.value = 0
        dut.pop.value = 1
        dut.din.value = 0
        await RisingEdge(dut.clk)
        await Timer(1, "ns")

        assert dut.dout.value == LIFO_SIZE_WORDS - i
        assert dut.num.value == LIFO_SIZE_WORDS - (i+1)

    assert dut.empty.value == 1

@cocotb.test
async def test_lifo_full(dut):
    await reset(dut)

    for i in range(LIFO_SIZE_WORDS):
        dut.push.value = 1
        dut.pop.value = 0
        dut.din.value = i + 1
        await RisingEdge(dut.clk)
        await Timer(1, "ns")

        assert dut.num.value == i + 1

    assert dut.full.value == 1
    assert dut.num.value == LIFO_SIZE_WORDS

    # Push on full should have no effect
    dut.push.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, "ns")

    assert dut.full.value == 1
    assert dut.num.value == LIFO_SIZE_WORDS

    # Pop and then push to full once more
    dut.pop.value = 1
    dut.push.value = 0

    await RisingEdge(dut.clk)
    await Timer(1, "ns")

    assert dut.full.value == 0
    assert dut.dout.value == LIFO_SIZE_WORDS
    assert dut.num.value == LIFO_SIZE_WORDS - 1

    dut.pop.value = 0
    dut.push.value = 1
    dut.din.value = LIFO_SIZE_WORDS + 1

    await RisingEdge(dut.clk)
    await Timer(1, "ns")

    assert dut.full.value == 1
    assert dut.dout.value == LIFO_SIZE_WORDS
    assert dut.num.value == LIFO_SIZE_WORDS

    ## Pop all values
    for i in range(LIFO_SIZE_WORDS):
        dut.push.value = 0
        dut.pop.value = 1
        dut.din.value = 0
        await RisingEdge(dut.clk)
        await Timer(1, "ns")

        if (i == 0):
            assert dut.dout.value == LIFO_SIZE_WORDS + 1
        else:
            assert dut.dout.value == LIFO_SIZE_WORDS - i
        assert dut.num.value == LIFO_SIZE_WORDS - (i+1)

    assert dut.empty.value == 1


@cocotb.test
async def test_push_pop_on_same_cycle(dut):
    await reset(dut)

    # Push-pop on empty should show the value, and don't store n
    assert dut.empty.value == 1
    dut.push.value = 1
    dut.pop.value = 1
    dut.din.value = 0x99

    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    await Timer(1, "ns")

    assert dut.num.value == 0
    assert dut.dout.value == 0x99

    dut.push.value = 1
    dut.pop.value = 0
    dut.din.value = 0xaa

    await RisingEdge(dut.clk)
    await Timer(1, "ns")

    assert dut.num.value == 1
    assert dut.dout.value == 0x99

    # now, push-pop should keep the same amount of elements, and pop the last one
    dut.push.value = 1
    dut.pop.value = 1
    dut.din.value = 0xbb

    await RisingEdge(dut.clk)
    await Timer(1, "ns")

    assert dut.num.value == 1
    assert dut.dout.value == 0xaa

    # Fill the lifo
    dut.push.value = 1
    dut.pop.value = 0
    dut.din.value = 0xbb
    for i in range(LIFO_SIZE_WORDS + 1):
        await RisingEdge(dut.clk)
    await Timer(1, "ns")

    assert dut.full.value == 1
    assert dut.dout.value == 0xaa

    # Push-pop on full
    dut.push.value = 1
    dut.pop.value = 1
    dut.din.value = 0xcc

    await RisingEdge(dut.clk)
    await Timer(1, "ns")

    assert dut.full.value == 1
    assert dut.dout.value == 0xbb

    ## Empty the lifo, and check that the last value is the right one

    dut.push.value = 0
    dut.pop.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    assert dut.dout.value == 0xbb
