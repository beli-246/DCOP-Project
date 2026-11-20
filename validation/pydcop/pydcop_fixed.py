"""The `pydcop` command with one fix to pyDCOP's MGM (diagnostic for check 2, issue #5).

Usage is the same as `pydcop`:  python validation/pydcop/pydcop_fixed.py solve --algo mgm ...

The problem in pyDCOP's MGM (pydcop/algorithms/mgm.py, MgmComputation._handle_value_message): a
variable computes its current local cost only in the first cycle (`if self.current_cost is None`).
Afterwards `current_cost` is only updated when the variable itself moves (to `current_cost - gain`);
when a neighbour changes value, it is not recomputed. Gains are then `stale cost - best cost`, so a
variable can believe it has no improving move when it has one (and stop early), or the reverse.

The fix: at the start of every cycle forget the stored cost, so the existing first-cycle code
recomputes it from the neighbours' current values. Nothing else changes.
"""
import runpy
import shutil
import sys

from pydcop.algorithms.mgm import MgmComputation

_orig_wait_for_values = MgmComputation._wait_for_values


def _wait_for_values(self):
    self.value_selection(self.current_value, None)   # same value: only resets the stored cost
    _orig_wait_for_values(self)


MgmComputation._wait_for_values = _wait_for_values

if __name__ == '__main__':
    cli = shutil.which('dcop_cli.py')
    sys.argv = [cli] + sys.argv[1:]
    runpy.run_path(cli, run_name='__main__')
