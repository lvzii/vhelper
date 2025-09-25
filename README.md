# vhelper

verilog helpful function


# Usage

```python
from vhelper import get_module_name
import nlpertools

code = nlpertools.readtxt_string(r"a23_coprocessor_7459_8_1_1.sv")
module_name = get_module_name(code)

# simulate
from vhelper import IverilogSoftware
iverilog = IverilogSoftware()
iverilog.sim()
```