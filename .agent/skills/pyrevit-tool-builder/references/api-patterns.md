# Revit API Patterns Reference

Common patterns learned across pyRevit challenge days. This file grows with each new tool.

> **Last updated**: Day 6 — 3D Isolation Trap (02.03.2026)

---

## Table of Contents
1. [Getting Elements](#getting-elements)
2. [Grouping & Sorting Elements](#grouping--sorting-elements)
3. [Groups & GroupTypes](#groups--grouptypes)
4. [Transactions](#transactions)
5. [Graphic Overrides](#graphic-overrides)
6. [Fill Patterns](#fill-patterns)
7. [Creating 3D Views](#creating-3d-views)
8. [Isolating Elements](#isolating-elements)
9. [Parameters](#parameters)
10. [Unit Conversion](#unit-conversion)
11. [.NET Interop](#net-interop)
12. [Validation & Safety Checks](#validation--safety-checks)
13. [pyRevit Forms](#pyrevit-forms)
14. [pyRevit Output & Reports](#pyrevit-output--reports)
15. [Color Utilities](#color-utilities)

---

## Getting Elements

### All elements in the document
```python
elements = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Walls).ToElements()
```

### Elements in a specific view (slower but scoped)
```python
active_view = doc.ActiveView
elements = FilteredElementCollector(doc, active_view.Id).OfClass(Wall).ToElements()
```
⚠️ Using `view.Id` as 2nd argument loads the view in the background — can be slow.

### Filter by class vs category
```python
# By Class — exact type (Wall, Floor, FamilyInstance)
.OfClass(Wall)

# By Category — broader (OST_Walls includes curtain walls, stacked walls, etc.)
.OfCategory(BuiltInCategory.OST_Walls)

# Exclude types (get instances only)
.WhereElementIsNotElementType()
```
**Learned**: Day 4 (Rooms), Day 5 (Walls in view), Day 6 (Groups/GroupTypes)

---

## Grouping & Sorting Elements

### Group by a property value
```python
from collections import defaultdict
dict_groups = defaultdict(list)

for el in elements:
    key = el.Name  # or any parameter value
    dict_groups[key].append(el)
```

### Iterate over groups
```python
for key, group_elements in dict_groups.items():
    # key = the value (e.g., "Generic - 200mm")
    # group_elements = list of elements with that value
    pass
```
**Learned**: Day 4 (rooms by flat), Day 5 (walls by type name), Day 6 (groups by type name)

---

## Groups & GroupTypes

### Get Group Types (for UI selection)
```python
all_group_types  = FilteredElementCollector(doc).OfClass(GroupType)
dict_group_types = {Element.Name.GetValue(g): g for g in all_group_types}
```
⚠️ Use `GroupType` (not `Group`) for dict keys — multiple Group *instances* share the same name, causing silent dict key collisions.

### Get Group Instances
```python
all_groups = FilteredElementCollector(doc).OfClass(Group).ToElements()
```

### Filter instances by selected type names
```python
groups_to_isolate = [g for g in all_groups if g.Name in selected_type_names]
```

### Get member elements from a Group
```python
member_ids = group.GetMemberIds()  # Returns ICollection<ElementId>
```
⚠️ Groups ≠ grouped elements. You must use `GetMemberIds()` to access the actual elements inside.

### Type Name workaround (pyRevit bug)
```python
# ❌ group_type.Name  — fails in pyRevit
# ✅ Element.Name.GetValue(group_type)  — works
type_name = Element.Name.GetValue(group_type)
```
**Learned**: Day 6

---

## Transactions

### Basic transaction
```python
t = Transaction(doc, 'Tool Name')
t.Start()   # 🔓 Allow Changes
# ... make changes ...
t.Commit()  # 🔒 Confirm Changes
```

### Best practice: Start as late as possible
```python
# ✅ Good: validate first, then start transaction
elements = collect_elements()
if not elements:
    forms.alert('No elements found', exitscript=True)

t = Transaction(doc, 'Tool Name')
t.Start()
# ... changes ...
t.Commit()

# ❌ Bad: transaction open during validation
t.Start()
elements = collect_elements()
if not elements:
    forms.alert('No elements', exitscript=True)  # Transaction left open!
```
**Learned**: Day 4, Day 5, Day 6

---

## Graphic Overrides

### Override element appearance in a view
```python
override_settings = OverrideGraphicSettings()

# Surface (what you see in plan/3D)
override_settings.SetSurfaceForegroundPatternId(solid_pattern.Id)
override_settings.SetSurfaceForegroundPatternColor(color)

# Cut (what you see in section/plan cuts)
override_settings.SetCutForegroundPatternId(solid_pattern.Id)
override_settings.SetCutForegroundPatternColor(color)

# Optional: projection lines, cut lines, transparency
# override_settings.SetProjectionLineColor(color)
# override_settings.SetProjectionLineWeight(5)
# override_settings.SetSurfaceTransparency(50)

# Apply to element
view.SetElementOverrides(element.Id, override_settings)
```

### Reset overrides (apply empty settings)
```python
view.SetElementOverrides(element.Id, OverrideGraphicSettings())
```
**Learned**: Day 5

---

## Fill Patterns

### Get Solid Fill Pattern
```python
all_patterns  = FilteredElementCollector(doc).OfClass(FillPatternElement).ToElements()
solid_pattern = [p for p in all_patterns if p.GetFillPattern().IsSolidFill][0]
```
⚠️ Collect once outside the loop — don't re-collect inside loops.

**Learned**: Day 5

---

## Creating 3D Views

### Create isometric 3D view
```python
view3d_type_id = doc.GetDefaultElementTypeId(ElementTypeGroup.ViewType3D)
new_view = View3D.CreateIsometric(doc, view3d_type_id)
```

### Rename a view (with timestamp for uniqueness)
```python
import datetime
new_view.Name = "My View" + datetime.datetime.now().strftime(" (%y%m%d_%H%M%S)")
```

### Open/activate a view in the UI
```python
uidoc.ActiveView = new_view
```
⚠️ Must be done **outside** a Transaction — this is a UI operation, not a document change.

**Learned**: Day 6

---

## Isolating Elements

### Isolate elements in a view (two-step process)
```python
# 1. Temporarily isolate
view.IsolateElementsTemporary(List_element_ids)  # Needs .NET List[ElementId]!

# 2. Convert to permanent
view.ConvertTemporaryHideIsolateToPermanent()
```

### Reusable helper function
```python
def create_new_3D_view(isolate_ids):
    new_view = View3D.CreateIsometric(doc, view3d_type_id)
    List_ids = List[ElementId](isolate_ids)
    new_view.IsolateElementsTemporary(List_ids)
    new_view.ConvertTemporaryHideIsolateToPermanent()
    return new_view
```
**Learned**: Day 6

---

## Parameters

### Built-in parameter
```python
param = element.get_Parameter(BuiltInParameter.ROOM_OCCUPANCY)
value = param.AsString()        # for text
value = param.AsValueString()   # for formatted value with units
value = param.AsDouble()        # for raw numeric (internal units)
```

### Shared/project parameter (by name)
```python
param = element.LookupParameter("Parameter Name")
if param:
    param.Set(value)  # Write value
```

### Element properties (not parameters)
```python
element.Name       # Type name
element.Id         # Element ID
element.Area       # Area (in internal units — sq ft)
```
**Learned**: Day 4 (room parameters), Day 5 (wall type name)

---

## Unit Conversion

### Convert from internal units (sq ft) to metric
```python
area_m2 = UnitUtils.ConvertFromInternalUnits(room.Area, UnitTypeId.SquareMeters)
area_m2 = round(area_m2, 2)
```

### Convert to internal units (for writing back)
```python
internal_value = UnitUtils.ConvertToInternalUnits(value_m2, UnitTypeId.SquareMeters)
```
**Learned**: Day 4

---

## Validation & Safety Checks

### Check ViewType before collecting elements
```python
vt = ViewType
allowed = [vt.FloorPlan, vt.CeilingPlan, vt.Elevation, vt.ThreeD,
           vt.EngineeringPlan, vt.AreaPlan, vt.Section, vt.Detail]
if active_view.ViewType not in allowed:
    forms.alert('View not supported.', exitscript=True)
```

### Check elements exist
```python
if not dict_values:
    forms.alert("No elements found.", exitscript=True)
```

### Check element can be modified
```python
if element.CanBeHidden(active_view):
    view.SetElementOverrides(element.Id, settings)
else:
    print('Element ({}) cannot be overridden.'.format(element.Id))
```

### Check parameter exists
```python
param = element.LookupParameter("Some Parameter")
if not param:
    continue  # or alert
```
### Check UI selection not cancelled
```python
sel = forms.SelectFromList.show(items, multiselect=True)
if not sel:
    forms.alert('Nothing selected.', exitscript=True)
```
**Learned**: Day 4 (parameters), Day 5 (ViewType, CanBeHidden, element check), Day 6 (UI cancellation)

---

## .NET Interop

### Convert Python list to .NET typed list
```python
import clr
clr.AddReference('System')
from System.Collections.Generic import List

python_list = [id1, id2, id3]
net_list = List[ElementId](python_list)
```
⚠️ Many Revit API methods (like `IsolateElementsTemporary`) require .NET `List<ElementId>`, not Python lists.

**Learned**: Day 6

---

## pyRevit Forms

### Multi-button dialog (forms.alert with options)
```python
view_mode = forms.alert("Pick a mode:",
                        title='Select Mode',
                        options=["Option A", "Option B"])
# Returns the clicked button string, or None if cancelled
```

### SelectFromList (multi-select)
```python
sel = forms.SelectFromList.show(items,
                                multiselect=True,
                                button_name='Select',
                                title='Pick Items')
```
**Learned**: Day 6

---

## pyRevit Output & Reports

### Interactive table with clickable links
```python
output = script.get_output()

table_data = []
for key, elements in groups.items():
    ids = [el.Id for el in elements]
    select_link = output.linkify(ids, title='Select All')
    table_data.append([key, len(elements), select_link])

output.print_table(
    table_data=table_data,
    columns=['Name', 'Count', 'Select']
)
```

### HTML color swatch
```python
swatch = '<div style="width:60px;height:25px;border:1px solid #999;border-radius:3px;background:rgb({0},{1},{2});"></div>'.format(r, g, b)
```

### Linkify element (clickable ID that selects in Revit)
```python
link = output.linkify(element.Id)
print('Check room: {}'.format(link))
```
### Markdown output
```python
output.print_md('# Report Title')
output.print_md("- **Key:** {}".format(value))
```
**Learned**: Day 4 (linkify), Day 5 (print_table, HTML swatch), Day 6 (print_md, linkify views)

---

## Color Utilities

### Revit Color object
```python
color = Color(255, 179, 186)  # Color(R, G, B) — values 0-255
r, g, b = color.Red, color.Green, color.Blue  # Extract components
```

### Generate distinct pastel colors using HSL
```python
import colorsys
def generate_colors(n):
    colors = []
    for i in range(n):
        hue = i / float(n)
        r, g, b = colorsys.hsv_to_rgb(hue, 0.4, 0.95)
        colors.append(Color(int(r*255), int(g*255), int(b*255)))
    return colors
```

### Hybrid approach (curated + fallback)
```python
if len(groups) <= len(predefined_colors):
    colors = predefined_colors
else:
    colors = generate_colors(len(groups))
```
**Learned**: Day 5
