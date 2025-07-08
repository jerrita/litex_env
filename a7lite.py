import os
import argparse

from migen import *

from litex_boards.platforms import microphase_a7lite

from litex.soc.cores.clock import *
from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *
from litex.soc.cores.led import LedChaser

from litedram.modules import MT41K256M16
from litedram.phy import s7ddrphy

from liteeth.phy.s7rgmii import LiteEthPHYRGMII

from litesdcard.phy import SDPHY
from litesdcard.core import SDCore

# CRG (Clock and Reset Generation) -----------------------------------------------------------------

class _CRG(Module):
    def __init__(self, platform, sys_clk_freq, with_ethernet=False):
        self.rst = Signal()
        self.clock_domains.cd_sys = ClockDomain()
        self.clock_domains.cd_sys4x = ClockDomain()
        self.clock_domains.cd_sys4x_dqs = ClockDomain()
        self.clock_domains.cd_idelay = ClockDomain()
        
        # Ethernet clock domain
        if with_ethernet:
            self.clock_domains.cd_eth = ClockDomain()
    
        # Input clock
        clk50 = platform.request("clk50")

        # PLL
        self.submodules.pll = pll = S7PLL(speedgrade=-1)
        self.comb += pll.reset.eq(self.rst | ~platform.request("cpu_reset"))
        pll.register_clkin(clk50, 50e6)
        pll.create_clkout(self.cd_sys, sys_clk_freq)
        pll.create_clkout(self.cd_sys4x, 4*sys_clk_freq)
        pll.create_clkout(self.cd_sys4x_dqs, 4*sys_clk_freq, phase=90)
        pll.create_clkout(self.cd_idelay, 200e6)
        if with_ethernet:
            pll.create_clkout(self.cd_eth, 125e6)
        platform.add_false_path_constraints(self.cd_sys.clk, pll.clkin) # Ignore sys_clk to pll.clkin path

        # IDELAY
        self.submodules.idelayctrl = S7IDELAYCTRL(self.cd_idelay)

# BaseSoC ------------------------------------------------------------------------------------------

class BaseSoC(SoCCore):
    def __init__(self, sys_clk_freq=int(50e6), 
                 with_ethernet=True,
                 with_etherbone=False, 
                 eth_ip="192.168.100.253",
                 remote_ip="192.168.100.216",
                 eth_dynamic_ip=False,
                 with_ddr3=True,
                 with_sdcard=True,
                 **kwargs):
        platform = microphase_a7lite.Platform()

        # SoCCore ----------------------------------------------------------------------------------
        SoCCore.__init__(self, platform, sys_clk_freq, ident="LiteX SoC on Microphase A7 Lite", **kwargs)

        # CRG --------------------------------------------------------------------------------------
        self.submodules.crg = _CRG(platform, sys_clk_freq, with_ethernet=(with_ethernet or with_etherbone))

        # DDR3 SDRAM -------------------------------------------------------------------------------
        if with_ddr3:
            self.submodules.ddrphy = s7ddrphy.A7DDRPHY(
                pads         = platform.request("ddram"),
                memtype      = "DDR3",
                nphases      = 4,
                sys_clk_freq = sys_clk_freq)
            self.add_csr("ddrphy")
            self.add_sdram("sdram",
                phy           = self.ddrphy,
                module        = MT41K256M16(sys_clk_freq, "1:4"),
                origin        = self.mem_map["main_ram"],
                size          = kwargs.get("max_sdram_size", 0x40000000),
                l2_cache_size = kwargs.get("l2_size", 8192)
            )

        # Ethernet ---------------------------------------------------------------------------------
        if with_ethernet or with_etherbone:
            self.submodules.ethphy = LiteEthPHYRGMII(
                clock_pads = platform.request("eth_clocks"),
                pads       = platform.request("eth"),
                tx_delay   = 1e-9,
                rx_delay   = 1e-9,
                with_hw_init_reset = False)
            if with_ethernet:
                self.add_ethernet(phy=self.ethphy, dynamic_ip=eth_dynamic_ip, remote_ip=remote_ip, local_ip=eth_ip)
            if with_etherbone:
                self.add_etherbone(phy=self.ethphy)

        # SD Card ----------------------------------------------------------------------------------
        if with_sdcard:
            self.add_spi_sdcard()

        # Leds -------------------------------------------------------------------------------------
        self.submodules.leds = LedChaser(
            pads         = platform.request_all("user_led"),
            sys_clk_freq = sys_clk_freq)

# Build --------------------------------------------------------------------------------------------

def main():
    from litex.build.parser import LiteXArgumentParser
    parser = LiteXArgumentParser(platform=microphase_a7lite.Platform, description="LiteX SoC on MicroPhase A7Lite.")
    parser.add_argument("--sys-clk-freq",    default=50e6,       help="System clock frequency (default: 50MHz)")
    parser.add_argument("--with-ethernetbone",  action="store_true", help="Enable Etherbone support")
    parser.add_argument("--with-ddr3",       action="store_true", default=True, help="Enable DDR3 SDRAM support (default: True)")
    parser.set_defaults(
        cpu_type="vexiiriscv",
        cpu_variant="debian",
        update_repo="no"
    )
    args = parser.parse_args()

    soc = BaseSoC(
        sys_clk_freq   = args.sys_clk_freq,
        with_ddr3      = args.with_ddr3,
        **parser.soc_argdict
    )
    
    builder = Builder(soc, **parser.builder_argdict)
    if args.build:
        builder.build(**parser.toolchain_argdict)

    if args.load:
        prog = soc.platform.create_programmer()
        prog.load_bitstream(builder.get_bitstream_filename(mode="sram"))

if __name__ == "__main__":
    main()