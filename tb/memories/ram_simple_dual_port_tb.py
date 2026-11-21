# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026  Nicolas Gabriel Cotti

import random
from enum import Enum

import cocotb
import pyuvm
from cocotb.clock import Clock
from cocotb.queue import QueueEmpty
from cocotb.triggers import FallingEdge
from cotti_uvm import (
    Bfm,
    Coverage,
    Item,
    Sequence,
    Tester,
    config_db_get,
    config_db_set,
)

##? DATA_WIDTH=32 DATA_LANE_WIDTH=8 ADDR_WIDTH_WORDS=3
##? DATA_WIDTH=16 DATA_LANE_WIDTH=8 ADDR_WIDTH_WORDS=4
##? DATA_WIDTH=8 DATA_LANE_WIDTH=8 ADDR_WIDTH_WORDS=2
##? DATA_WIDTH=15 DATA_LANE_WIDTH=5 ADDR_WIDTH_WORDS=4

RAM = []

class RamItem(Item):
    def __init__(self, raddr: int, waddr: int, we: int, wdata: int):
        super().__init__()
        self.raddr = raddr
        self.waddr = waddr
        self.we = we
        self.wdata = wdata

    def __eq__(self, other) -> bool:
        return ((self.addr == other.addr) and
            (self.we == other.we) and
            (self.wdata == other.wdata))

    def __str__(self) -> str:
        return f"raddr: {self.raddr}; waddr: {self.waddr}; we: {self.we}; wdata: {self.wdata}"


def golden_ref(item: RamItem) -> int:
    global RAM
    rdata = RAM[item.raddr]
    if (item.we != 0):
        data_width = config_db_get("DATA_WIDTH")
        data_lane_width = config_db_get("DATA_LANE_WIDTH")
        we_bits = int(data_width / data_lane_width)

        # The operation performed here is to only write on the corresponding
        # data lane.
        # E.g., for DATA_WIDTH = 8 && DATA_LANE_WIDTH = 4:
        # 0bxxxxxxxx    mask would be 2**4 -1 = 15  =0b1111
        # 0bxxxxyyyy    Write first lane (if we = 0bx1)
        # 0byyyyxxxx    Write second lane (if we = 0b1x)
        wdata = RAM[item.waddr]
        mask = (2 ** data_lane_width) - 1
        for i in range(we_bits):
            if (item.we & (1 << i) != 0):
                wdata &= ~(mask << (i * data_lane_width))
                wdata |= item.wdata & (mask << (i * data_lane_width))
        RAM[item.waddr] = wdata
    return rdata

class RamBfm(Bfm):
    async def reset(self):
        global RAM
        self.dut.raddr.value = 0
        for i in range(self.size):
            await FallingEdge(self.dut.clk)
            self.dut.waddr.value = i
            self.dut.we.value = self.max_we
            self.dut.wdata.value = random.randint(0, 2**(self.data_width-1))

        await FallingEdge(self.dut.clk)
        self.dut.raddr.value = 0
        self.dut.waddr.value = 0
        self.dut.we.value = 0
        self.dut.wdata.value = 0

    def on_start(self):
        c = Clock(cocotb.top.clk, 2, "ns")
        c.start()
        self.data_width = int(self.dut.DATA_WIDTH.value)
        config_db_set("DATA_WIDTH", self.data_width)

        self.data_lane_width = int(self.dut.DATA_LANE_WIDTH.value)
        config_db_set("DATA_LANE_WIDTH", self.data_lane_width)

        self.size = 2 ** int(self.dut.ADDR_WIDTH_WORDS.value)
        config_db_set("SIZE", self.size)

        self.max_we = int(2**(self.data_width / self.data_lane_width) - 1)
        config_db_set("MAX_WE", self.max_we)

        # Set all values to random values before starting
        global RAM
        for _ in range(self.size):
            RAM.append(0)


    async def input_driver(self):
        self.dut.raddr.value = 0
        self.dut.waddr.value = 0
        self.dut.we.value = 0
        self.dut.wdata.value = 0
        while True:
            await FallingEdge(self.dut.clk)
            try:
                item = self.input_driver_queue.get_nowait()
                self.dut.raddr.value = item.raddr
                self.dut.waddr.value = item.waddr
                self.dut.we.value = item.we
                self.dut.wdata.value = item.wdata
            except QueueEmpty:
                continue

    async def input_monitor(self):
        """An input transaction is considered as such whenever any of the arguments are different."""
        prev_raddr = -1
        prev_waddr = -1
        prev_we = -1
        prev_wdata = -1
        while True:
            await FallingEdge(self.dut.clk)
            raddr = int(self.dut.raddr.value)
            waddr = int(self.dut.waddr.value)
            we = int(self.dut.we.value)
            wdata = int(self.dut.wdata.value)
            if ((prev_raddr != raddr) or
                (prev_waddr != waddr) or
                (prev_we != we) or
                (prev_wdata != wdata)):
                item = RamItem(
                    raddr=raddr,
                    waddr=waddr,
                    we=we,
                    wdata=wdata,
                )
                self.input_monitor_queue.put_nowait(item)

            prev_raddr = raddr
            prev_waddr = waddr
            prev_we = we
            prev_wdata = wdata

    async def output_monitor(self):
        """An output transaction is considered whenever any of the inputs are different."""
        prev_raddr = -1
        prev_waddr = -1
        prev_we = -1
        prev_wdata = -1
        while True:
            await FallingEdge(self.dut.clk)
            raddr = int(self.dut.raddr.value)
            waddr = int(self.dut.waddr.value)
            we = int(self.dut.we.value)
            wdata = int(self.dut.wdata.value)
            rdata = int(self.dut.rdata.value)
            if ((prev_raddr != raddr) or
                (prev_waddr != waddr) or
                (prev_we != we) or
                (prev_wdata != wdata)):
                self.output_monitor_queue.put_nowait(rdata)

            prev_raddr = raddr
            prev_waddr = waddr
            prev_we = we
            prev_wdata = wdata


class RamEnum(Enum):
    FIRST_RADDR = 0,
    LAST_RADDR = 1,
    MULTIPLE_RW = 2,
    WE_NONE = 3,
    WE_FULL = 4,
    WE_SOME = 5,
    RW_SAME_ADDR = 6,
    FIRST_WADDR = 7,
    LAST_WADDR = 8

class RamCoverage(Coverage):
    coverage_enum = RamEnum
    min_coverage_percentage = 100

    def build_phase(self):
        super().build_phase()

        self.ram_size = config_db_get("SIZE")
        self.max_we = config_db_get("MAX_WE")

        self.read_counter = []
        self.write_counter = []
        for i in range(self.ram_size):
            self.read_counter.append(0)
            self.write_counter.append(0)

    def item_to_coverage(self, item:RamItem, output) -> list[RamEnum]:
        out = []

        self.read_counter[item.raddr] += 1
        self.write_counter[item.waddr] += 1

        if (item.raddr == 0):
            out.append(RamEnum.FIRST_RADDR)

        elif (item.raddr == self.ram_size -1):
            out.append(RamEnum.LAST_RADDR)

        if (item.waddr == 0):
            out.append(RamEnum.FIRST_WADDR)

        elif (item.waddr == self.ram_size -1):
            out.append(RamEnum.LAST_WADDR)

        if (item.we == 0):
            out.append(RamEnum.WE_NONE)

        elif (item.we == self.max_we):
            out.append(RamEnum.WE_FULL)
            if (self.max_we == 1):
                out.append(RamEnum.WE_SOME)

        else:
            out.append(RamEnum.WE_SOME)

        if (item.waddr == item.raddr):
            out.append(RamEnum.RW_SAME_ADDR)

        if ((self.read_counter[item.raddr] > 3 and self.write_counter[item.raddr] > 3) or
            (self.read_counter[item.waddr] > 3 and self.write_counter[item.waddr] > 3)):
            out.append(RamEnum.MULTIPLE_RW)

        return out

class RamSequence(Sequence):
    def __init__(self, name):
        super().__init__(name)
        self.ram_size = config_db_get("SIZE")
        self.data_lane_width = config_db_get("DATA_LANE_WIDTH")
        self.data_width = config_db_get("DATA_WIDTH")
        self.max_we = config_db_get("MAX_WE")

    def items(self) -> list[RamItem]:
        out = []

        for _ in range(self.ram_size*4):
            item = RamItem(
                raddr=random.randint(0, self.ram_size-1),
                waddr=random.randint(0, self.ram_size-1),
                we=random.randint(0, self.max_we),
                wdata=random.randint(0, (2**self.data_width - 1)),
            )
            out.append(item)
        return out

@pyuvm.test()
class Test(Tester):
    bfm = RamBfm
    golden_ref = golden_ref
    sequence = RamSequence
    coverage = RamCoverage
    end_delay_ns = 20
