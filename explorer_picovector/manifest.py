freeze("$(PORT_DIR)/modules", "rp2.py")
include("$(MPY_DIR)/extmod/asyncio")
require("onewire")
require("ds18x20")
require("dht")
require("neopixel")

freeze("../modules/py_explorer/")
module("lsm6ds3.py", base_path="../examples/lib")
