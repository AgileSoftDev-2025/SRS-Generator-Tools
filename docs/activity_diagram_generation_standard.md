# Activity Diagram Generation Standard

This document defines the mapping standard from the **Use Case Specification** input fields into **PlantUML Activity Diagrams (UML 2.5 compliant)** inside the One UML tool.

---

## 1. Swimlane (Partition) Mapping Rules
To maintain standard vertical UML control flow and avoid repetitive crossing layout:
* Swimlanes are generated for **Actor** (external actions) and **System** (internal validation/responses).
* Control transitions only swap swimlanes when the executing party changes. 
* Sequential actions inside the same partition stack vertically without partition redeclaration.

---

## 2. Activity Node Formats
* **Initial State / Pre-conditions:** Rendered as an activity node `:Pre-condition: [Content];` inside the **System** partition immediately after `start`.
* **Actions:** Rendered as clean active-voice nodes using a Verb + Object format (e.g. `:Mengisi form login;` instead of `:user login;`).
* **Final State / Post-conditions:** Rendered as an activity node `:Post-condition: [Content];` inside the **System** partition immediately before `stop`.

---

## 3. Control Flow Branching (Guard Conditions)
Dynamic guard conditions are derived from the feature/use case name:
* Features containing `"login"` use the condition `if (Kredensial valid?)`.
* Features containing `"regist"` / `"daftar"` use the condition `if (Data valid?)`.
* Other features fallback to checking exception step semantics or defaulting to `if (Proses berhasil?)`.

### Layout Rules for Exceptions
* **Success Branch (`yes`):** The last step of the basic path (success outcome) and the post-condition node.
* **Failure Branch (`no`):** The sequence of steps in the Exception flow. If a retry keyword (e.g., *kembali*, *retry*, *ulang*) is detected in the text, it marks the return path. Both terminate cleanly with `stop` or `detach` in PlantUML 2.5 format.
