# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026  Nicolas Gabriel Cotti

from enum import Enum

import pyuvm
from cocotb.queue import QueueEmpty
from cocotb.triggers import Timer
from cotti_uvm import (
    Coverage,
    Item,
    Sequence,
    Tester,
    config_db_get,
    config_db_set,
    read_hex,
)
from cotti_uvm.bfm import Bfm

##? DATA_WIDTH=32 ADDR_WIDTH_WORDS=4 ROM_FILE="tb/memories/hex/rom_w32_l4.hex"
##? DATA_WIDTH=16 ADDR_WIDTH_WORDS=5 ROM_FILE="tb/memories/hex/rom_w16_l5.hex"
##? DATA_WIDTH=8 ADDR_WIDTH_WORDS=3 ROM_FILE="tb/memories/hex/rom_w8_l3.hex"


class RomItem(Item):
    def __init__(self, raddr: int = 0):
        super().__init__("rom_item")
        self.raddr = raddr

    def __eq__(self, other):
        return self.raddr == other.raddr

    def __str__(self):
        return f"raddr: {self.raddr}"


ROM = []


def golden_ref(item: RomItem):
    """ROM's golden reference function"""
    return ROM[item.raddr]


class RomBfm(Bfm):
    async def input_driver(self):
        self.dut.raddr.value = 0

        while True:
            await Timer(1, "ns")
            try:
                item = self.input_driver_queue.get_nowait()
            except QueueEmpty:
                continue

            self.dut.raddr.value = item.raddr

    async def input_monitor(self):
        last_raddr = None
        while True:
            await Timer(1, "ns")
            raddr = int(self.dut.raddr.value)
            if last_raddr != raddr:
                self.input_monitor_queue.put_nowait(RomItem(raddr))

            last_raddr = raddr

    async def output_monitor(self):
        last_rdata = None
        while True:
            await Timer(1, "ns")
            rdata = int(self.dut.rdata.value)
            if last_rdata != rdata:
                self.output_monitor_queue.put_nowait(rdata)

            last_rdata = rdata

    def on_start(self):
        self.data_width = int(self.dut.DATA_WIDTH.value)
        self.rom_size = 2 ** int(self.dut.ADDR_WIDTH_WORDS.value)

        config_db_set("DATA_WIDTH", self.data_width)
        config_db_set("ROM_SIZE", self.rom_size)

        global ROM
        ROM = read_hex(self.dut.ROM_FILE.value.decode("utf-8"))


class CoverageEnum(Enum):
    FIRST_ADDR = (0,)
    LAST_ADDR = (1,)
    MIDDLE_ADDR = (2,)


class RomCoverage(Coverage):
    coverage_enum = CoverageEnum
    min_coverage_percentage = 100

    def item_to_coverage(self, item: RomItem, output) -> CoverageEnum:
        result = None
        rom_size = config_db_get("ROM_SIZE")
        if item.raddr == 0:
            result = CoverageEnum.FIRST_ADDR
        elif item.raddr == rom_size - 1:
            result = CoverageEnum.LAST_ADDR
        else:
            result = CoverageEnum.MIDDLE_ADDR
        return result


class SweepSeq(Sequence):
    def items(self) -> list[RomItem]:
        out = []
        rom_size = config_db_get("ROM_SIZE")
        for i in range(rom_size):
            item = RomItem(i)
            out.append(item)
        return out


@pyuvm.test()
class SweepTest(Tester):
    bfm = RomBfm
    golden_ref = golden_ref
    sequence = SweepSeq
    coverage = RomCoverage
    end_delay_ns = 10
