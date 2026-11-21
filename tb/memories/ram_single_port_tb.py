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
    def __init__(self, addr: int, we: int, wdata: int):
        super().__init__()
        self.addr = addr
        self.we = we
        self.wdata = wdata

    def __eq__(self, other) -> bool:
        return (self.addr == other.addr) and (self.we == other.we) and (self.wdata == other.wdata)

    def __str__(self) -> str:
        return f"Addr: {self.addr}; we: {self.we}; wdata: {self.wdata}"


def golden_ref(item: RamItem) -> int:
    global RAM
    prev_value = RAM[item.addr]
    if item.we != 0:
        data_width = config_db_get("DATA_WIDTH")
        data_lane_width = config_db_get("DATA_LANE_WIDTH")
        we_bits = int(data_width / data_lane_width)

        # The operation performed here is to only write on the corresponding
        # data lane.
        # E.g., for DATA_WIDTH = 8 && DATA_LANE_WIDTH = 4:
        # 0bxxxxxxxx    mask would be 2**4 -1 = 15  =0b1111
        # 0bxxxxyyyy    Write first lane (if we = 0bx1)
        # 0byyyyxxxx    Write second lane (if we = 0b1x)
        wdata = prev_value
        mask = (2**data_lane_width) - 1
        for i in range(we_bits):
            if item.we & (1 << i) != 0:
                wdata &= ~(mask << (i * data_lane_width))
                wdata |= item.wdata & (mask << (i * data_lane_width))
        RAM[item.addr] = wdata
    return prev_value


class RamBfm(Bfm):
    async def reset(self):
        global RAM
        for i in range(self.size):
            await FallingEdge(self.dut.clk)
            self.dut.addr.value = i
            self.dut.we.value = self.max_we
            self.dut.wdata.value = random.randint(0, 2 ** (self.data_width - 1))

        await FallingEdge(self.dut.clk)
        self.dut.addr.value = 0
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

        self.max_we = int(2 ** (self.data_width / self.data_lane_width) - 1)
        config_db_set("MAX_WE", self.max_we)

        # Set all values to random values before starting
        global RAM
        for _ in range(self.size):
            RAM.append(0)

    async def input_driver(self):
        self.dut.addr.value = 0
        self.dut.we.value = 0
        self.dut.wdata.value = 0
        while True:
            await FallingEdge(self.dut.clk)
            try:
                item = self.input_driver_queue.get_nowait()
                self.dut.addr.value = item.addr
                self.dut.we.value = item.we
                self.dut.wdata.value = item.wdata
            except QueueEmpty:
                continue

    async def input_monitor(self):
        """An input transaction is considered as such whenever any of the arguments are different."""
        prev_addr = -1
        prev_we = -1
        prev_wdata = -1
        while True:
            await FallingEdge(self.dut.clk)
            addr = int(self.dut.addr.value)
            we = int(self.dut.we.value)
            wdata = int(self.dut.wdata.value)
            if (prev_addr != addr) or (prev_we != we) or (prev_wdata != wdata):
                item = RamItem(
                    addr=addr,
                    we=we,
                    wdata=wdata,
                )
                self.input_monitor_queue.put_nowait(item)

            prev_addr = addr
            prev_we = we
            prev_wdata = wdata

    async def output_monitor(self):
        """An output transaction is considered whenever any of the inputs are different."""
        prev_addr = -1
        prev_we = -1
        prev_wdata = -1
        while True:
            await FallingEdge(self.dut.clk)
            addr = int(self.dut.addr.value)
            we = int(self.dut.we.value)
            wdata = int(self.dut.wdata.value)
            rdata = int(self.dut.rdata.value)
            if (prev_addr != addr) or (prev_we != we) or (prev_wdata != wdata):
                self.output_monitor_queue.put_nowait(rdata)

            prev_addr = addr
            prev_we = we
            prev_wdata = wdata


class RamEnum(Enum):
    FIRST_ADDR = (0,)
    LAST_ADDR = (1,)
    MULTIPLE_ACCESS = (2,)
    WE_NONE = (3,)
    WE_FULL = (4,)
    WE_SOME = 5


class RamCoverage(Coverage):
    coverage_enum = RamEnum
    min_coverage_percentage = 100

    def build_phase(self):
        super().build_phase()

        self.ram_size = config_db_get("SIZE")
        self.max_we = config_db_get("MAX_WE")

        self.access_counter = []
        for i in range(self.ram_size):
            self.access_counter.append(0)

    def item_to_coverage(self, item: RamItem, output) -> list[RamEnum]:
        out = []

        self.access_counter[item.addr] += 1

        if item.addr == 0:
            out.append(RamEnum.FIRST_ADDR)

        elif item.addr == self.ram_size - 1:
            out.append(RamEnum.LAST_ADDR)

        if item.we == 0:
            out.append(RamEnum.WE_NONE)

        elif item.we == self.max_we:
            out.append(RamEnum.WE_FULL)
            if self.max_we == 1:
                out.append(RamEnum.WE_SOME)

        else:
            out.append(RamEnum.WE_SOME)

        if self.access_counter[item.addr] > 3:
            out.append(RamEnum.MULTIPLE_ACCESS)

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

        for _ in range(self.ram_size * 4):
            item = RamItem(
                addr=random.randint(0, self.ram_size - 1),
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
