import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from SANSPRO.compact.elset.record.steel_grade import SteelGrade, SteelGradeProto
from SANSPRO.compact.elset.record.steel_section import SteelSection, WideFlangeRecord

# ------------------
# Usage
# ------------------

SteelGrade.load()

# # Type-safe alias combining runtime class and protocol typing
# SteelGradeTyped: SteelGradeProto = SteelGrade

# # Now autocomplete and typing work
# fy = SteelGradeTyped.ST41.fy
# print(fy)

# record = SteelGrade.get("ST41")
# print(record.fy)

SteelSection.load_dbs()
true_or_not = SteelSection.exists("WF400X200")

print(true_or_not)