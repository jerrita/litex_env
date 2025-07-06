from litex.build.generic_platform import *
from litex.build.xilinx import Xilinx7SeriesPlatform, VivadoProgrammer

# IOs ----------------------------------------------------------------------------------------------

_io = [
    # 时钟信号和复位信号 (Clock and Reset)
    ("clk50", 0, Pins("J19"), IOStandard("LVCMOS33")),
    ("cpu_reset", 0, Pins("L18"), IOStandard("LVCMOS33")),

    # 按键信号 (Buttons)
    ("user_btn", 0, Pins("AA1"), IOStandard("LVCMOS33")), # KEY1
    ("user_btn", 1, Pins("W1"), IOStandard("LVCMOS33")),  # KEY2

    # LED
    ("user_led", 0, Pins("M18"), IOStandard("LVCMOS33")), # LED1
    ("user_led", 1, Pins("N18"), IOStandard("LVCMOS33")), # LED2

    # UART
    ("serial", 0,
        Subsignal("rx", Pins("U2")),
        Subsignal("tx", Pins("V2")),
        IOStandard("LVCMOS33")
    ),

    # EEPROM I2C
    ("i2c", 0,
        Subsignal("scl", Pins("J22")),
        Subsignal("sda", Pins("H22")),
        IOStandard("LVCMOS33")
    ),

    # Ethernet Port (RGMII Interface)
    ("eth_clocks", 0,
        Subsignal("tx", Pins("K17")),    # ETH_TXCK
        Subsignal("rx", Pins("K18")),    # ETH_RXCK
        IOStandard("LVCMOS33")
    ),
    ("eth", 0,
        Subsignal("rst_n",   Pins("N22")),           # ETH_nRST
        Subsignal("mdio",    Pins("M20")),           # ETH_MDIO
        Subsignal("mdc",     Pins("M22")),           # ETH_MDC
        Subsignal("rx_ctl",  Pins("K19")),           # ETH_RXCTL
        Subsignal("rx_data", Pins("L14 M15 L16 M16")), # ETH_RXD[0:3]
        Subsignal("tx_ctl",  Pins("N20")),           # ETH_TXCTL
        Subsignal("tx_data", Pins("K16 L15 L13 M13")), # ETH_TXD[0:3]
        IOStandard("LVCMOS33")
    ),

    # SD Card
    ("sdcard", 0,
        Subsignal("clk", Pins("U7")),
        Subsignal("cmd", Pins("AA8")),
        Subsignal("data", Pins("W9 Y9 Y7 Y8")),  # data[0:3]
        IOStandard("LVCMOS33")
    ),

    # HDMI
    ("hdmi", 0,
        Subsignal("clk_p", Pins("L19")),
        Subsignal("data0_p", Pins("K21")),
        Subsignal("data1_p", Pins("J20")),
        Subsignal("data2_p", Pins("G17")),
        Subsignal("hpd", Pins("H15")),
        IOStandard("LVCMOS33")
    ),

    # DDR3 DRAM
    ("ddram", 0,
        Subsignal("a", Pins(
            "P1 M6 K3 K4 M5 J6 N2 K6 "  # addr[0:7]
            "P2 L1 M2 P6 L4 L5 N5"        # addr[8:14]
        )),
        Subsignal("ba", Pins("J4 R1 M1")),   # ba[0:2]
        Subsignal("ras_n", Pins("M3")),
        Subsignal("cas_n", Pins("N3")),
        Subsignal("we_n", Pins("L6")),
        Subsignal("dm", Pins("E2 H3")),      # dm[0:1]
        Subsignal("dq", Pins(
            "B2 F1 B1 D2 C2 F3 A1 G1 "      # dq[0:7]
            "J5 G2 K1 G3 H2 H5 J1 H4"       # dq[8:15]
        )),
        Subsignal("dqs_p", Pins("E1 K2")),   # dqs_p[0:1]
        Subsignal("dqs_n", Pins("D1 J2")),   # dqs_n[0:1]
        Subsignal("clk_p", Pins("P5")),      # ck_p[0]
        Subsignal("clk_n", Pins("P4")),      # ck_n[0]
        Subsignal("cke", Pins("N4")),        # cke[0]
        Subsignal("odt", Pins("L3")),        # odt[0]
        Subsignal("reset_n", Pins("F4")),
        IOStandard("SSTL15"),
        Misc("SLEW=FAST")
    ),

]

# Connectors ---------------------------------------------------------------------------------------

_connectors = [
    # No specific connectors defined in the provided XDC,
    # but you can add them here if your board has expansion headers.
    # e.g., ("PMODA", "A1 B2 C3 ...")
]

# Platform -----------------------------------------------------------------------------------------

class Platform(Xilinx7SeriesPlatform):
    default_clk_name = "clk50"
    default_clk_period = 1e9/50e6 # 50MHz

    def __init__(self, toolchain="vivado"):
        Xilinx7SeriesPlatform.__init__(self, "xc7a35tfgg484-2", _io, _connectors, toolchain=toolchain)
        
        # DDR3 VREF setting
        self.add_platform_command("set_property INTERNAL_VREF 0.750 [get_iobanks 35]")
        
        # DDR3 specific constraints
        self.add_platform_command("set_property IOSTANDARD DIFF_SSTL15 [get_ports ddram_clk_p]")
        self.add_platform_command("set_property IOSTANDARD DIFF_SSTL15 [get_ports ddram_clk_n]")
        self.add_platform_command("set_property IOSTANDARD DIFF_SSTL15 [get_ports ddram_dqs_p*]")
        self.add_platform_command("set_property IOSTANDARD DIFF_SSTL15 [get_ports ddram_dqs_n*]")
        self.add_platform_command("set_property IOSTANDARD LVCMOS15 [get_ports ddram_reset_n]")
        self.add_platform_command("set_property IN_TERM UNTUNED_SPLIT_50 [get_ports ddram_dq*]")
        self.add_platform_command("set_property IN_TERM UNTUNED_SPLIT_50 [get_ports ddram_dqs_p*]")
        self.add_platform_command("set_property IN_TERM UNTUNED_SPLIT_50 [get_ports ddram_dqs_n*]")
        
        # HDMI specific constraints
        self.add_platform_command("set_property IOSTANDARD TMDS_33 [get_ports hdmi_clk_p]")
        self.add_platform_command("set_property IOSTANDARD TMDS_33 [get_ports hdmi_data0_p]")
        self.add_platform_command("set_property IOSTANDARD TMDS_33 [get_ports hdmi_data1_p]")
        self.add_platform_command("set_property IOSTANDARD TMDS_33 [get_ports hdmi_data2_p]")
        self.add_platform_command("set_property IOSTANDARD LVCMOS33 [get_ports hdmi_hpd]")

    def create_programmer(self):
        return VivadoProgrammer()

    def do_finalize(self, fragment):
        Xilinx7SeriesPlatform.do_finalize(self, fragment)
        self.add_period_constraint(self.lookup_request("clk50", loose=True), 1e9/50e6)
