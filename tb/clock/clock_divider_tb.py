import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer, FallingEdge, RisingEdge, Edge, with_timeout, SimTimeoutError
import random


# Input clock period, must be divisible by 4
CLOCK_T_PS = 4

assert CLOCK_T_PS % 4 == 0

async def check_clock_period(dut) -> None:
    """Checks the clock divider and asserts that the output clock has the right freq."""

    div = int(dut.div.value)
    div_width = int(dut.DIV_WIDTH.value)
    max_div = (2 ** div_width) - 1

    # Given that the clock_f period is "T", the clock divider multiplies the period by "N",
    # Therefore, the longest period is just "N * T"
    max_clock_period_ps = max_div * CLOCK_T_PS

    # Since the expected output frequency is "F / N", the output period is "T * N".
    expected_clock_period_ps = div * CLOCK_T_PS

    try:
        await with_timeout(RisingEdge(dut.clk_s), max_clock_period_ps, "ps")
    except SimTimeoutError:
        if (div == 0):
            return
        else:
            cocotb.log.error("Clock was not risen.")
            assert False

    # Since we just waited for its RisingEdge, the value should be 1
    assert dut.clk_s.value == 1

    # Check three full periods of the signal
    for _ in range(3):
        for i in range(expected_clock_period_ps):
            await Timer(1, "ps")
            # Clock should be up the first half of the period and down the second half
            if (i < expected_clock_period_ps / 2):
                assert dut.clk_s.value == 1
            else:
                assert dut.clk_s.value == 0


async def check_clock_polarity(dut):
    """Checks that, no matter when you changed the div argument, the fast
    and slow clocks share the same polarity."""
    div = int(dut.div.value)
    if (div == 0):
        return
    await RisingEdge(dut.clk_s)
    await Timer(CLOCK_T_PS / 4, "ps")
    assert dut.clk_s.value == 1
    assert dut.clk_f.value == 1

@cocotb.test(timeout_time=10, timeout_unit="us")
async def test_divider(dut):
    Clock(dut.clk_f, CLOCK_T_PS, "ps").start()

    div_width = int(dut.DIV_WIDTH.value)
    max_div = (2 ** div_width) - 1

    div_values = []

    div_values.append(0)

    # for i in range(5):
    #     div_values.append(random.randint(0, max_div))

    for i in range(6):
        div_values.append(i)

    div_values.append(max_div)
    div_values.append(0)

    for div in div_values:
        # Change input in a random time
        wait = random.randint(1, 10)
        await Timer(wait, "ps")
        dut.div.value = div
        await Timer(1, "ps")
        await check_clock_polarity(dut)
        await check_clock_period(dut)