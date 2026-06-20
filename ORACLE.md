# MORPHEUS — ORACLE.md
### The Complete Oracle Mode Specification
**Author:** Madhesh Y  
**Purpose:** Full technical spec for Oracle mode — the multi-language execution engine with personality narration.  
**Read this before:** Touching oracle.py or any language bridge code  
**Read after:** ARCHITECTURE.md (you need to understand TraceEvent first)

---

## WHAT ORACLE IS

Oracle is the mode inside Morpheus that removes the Python-only restriction.

The base Morpheus tracer uses Python's `sys.settrace` — which is a Python-only feature. Oracle replaces this with a completely different architecture that works for any programming language.

**One command, any language:**
```bash
morpheus run app.js --mode oracle --personality critic
morpheus run Main.java --mode oracle --personality mentor
morpheus run program.c --mode oracle --personality paranoid
```

Oracle does not change the output format. The user still sees plain English narration in their terminal. The difference is internal — how the execution is captured.

---

## THE THREE LAYERS OF ORACLE

```
Layer 1: Language Detection
    ↓
Layer 2: Runtime Bridge (language-specific)
    ↓
Layer 3: Personality Narration (same for all languages)
```

---

## LAYER 1 — LANGUAGE DETECTION

Oracle detects language from file extension. This is simple and reliable.

**Supported languages and their extensions:**

| Extension | Language | Bridge |
|---|---|---|
| `.py` | Python | sys.settrace (existing tracer.py) |
| `.js` | JavaScript | V8 Inspector Protocol |
| `.ts` | TypeScript | V8 Inspector Protocol (after tsc compile) |
| `.java` | Java | JVMTI agent |
| `.c` | C | GDB Python API |
| `.cpp` `.cc` | C++ | GDB Python API |

**Implementation:** See `detect_language()` in ARCHITECTURE.md → oracle.py section.

**Priority order for implementation:**
1. JavaScript first — largest vibe coder audience
2. Python second — already done via tracer.py
3. C/C++ third — useful for systems programmers
4. Java fourth — university and enterprise audience
5. TypeScript fifth — requires pre-compilation step

**Week 7–8 goal:** JavaScript working fully. At least one additional language started.

---

## LAYER 2 — RUNTIME BRIDGES

Each language needs a different mechanism to observe execution. These are called bridges.

---

### Bridge 1: Python (Already Built)

Python is handled by `morpheus/tracer.py` using `sys.settrace`.

When Oracle detects a `.py` file, it delegates to the existing `trace_file()` function from `tracer.py`. No new code needed.

```python
# oracle.py — Python case
if language == "python":
    from morpheus.tracer import trace_file
    events = trace_file(filepath)
    return events
```

---

### Bridge 2: JavaScript / Node.js — V8 Inspector Protocol

**What it is:** Node.js has a built-in debugging protocol called the V8 Inspector. When you start Node.js with `--inspect`, it opens a WebSocket server that accepts debugging commands. Oracle connects to this WebSocket and listens for execution events.

**How to activate it:**
```bash
node --inspect-brk=9229 script.js
# --inspect-brk pauses at the first line so Oracle can connect before anything runs
```

**What Oracle does:**
1. Launch Node.js as a subprocess with `--inspect-brk=9229`
2. Connect to `ws://localhost:9229` using `websockets` library
3. Send the `Debugger.enable` command
4. Send `Runtime.runIfWaitingForDebugger` to start execution
5. Listen for `Debugger.paused` events — these fire on every function call
6. Extract function name, file, line from each `Debugger.paused` payload
7. Convert to standard `TraceEvent` objects

**V8 Inspector WebSocket message format:**

Enable the debugger:
```json
{
  "id": 1,
  "method": "Debugger.enable"
}
```

Resume after pause (called for each step):
```json
{
  "id": 2,
  "method": "Debugger.resume"
}
```

Incoming pause event (what Oracle reads):
```json
{
  "method": "Debugger.paused",
  "params": {
    "callFrames": [
      {
        "functionName": "loadData",
        "location": {
          "scriptId": "84",
          "lineNumber": 12,
          "columnNumber": 0
        },
        "url": "file:///path/to/script.js"
      }
    ],
    "reason": "step",
    "hitBreakpoints": []
  }
}
```

**Key fields to extract:**
- `callFrames[0].functionName` → `TraceEvent.function_name`
- `callFrames[0].location.lineNumber` → `TraceEvent.line_number`
- `callFrames[0].url` → `TraceEvent.filename`

**Pause strategy:** Set a step-over on every line (`Debugger.stepOver`) to capture full execution flow. This is slower but comprehensive. For performance, switch to breakpoints on function entry only.

**Required Python library:** `websockets` — add to pyproject.toml dependencies.

```python
# Minimal V8 bridge implementation sketch
import asyncio
import websockets
import json
import subprocess
import time

async def trace_javascript(filepath: str) -> list[TraceEvent]:
    # Start Node.js with inspector
    proc = subprocess.Popen(
        ["node", "--inspect-brk=9229", filepath],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(0.5)  # Wait for inspector to be ready
    
    events = []
    
    async with websockets.connect("ws://localhost:9229") as ws:
        # Enable debugger
        await ws.send(json.dumps({"id": 1, "method": "Debugger.enable"}))
        await ws.recv()
        
        # Start execution
        await ws.send(json.dumps({"id": 2, "method": "Runtime.runIfWaitingForDebugger"}))
        
        while True:
            msg = json.loads(await ws.recv())
            if msg.get("method") == "Debugger.paused":
                frame = msg["params"]["callFrames"][0]
                events.append(TraceEvent(
                    event_type="call",
                    function_name=frame.get("functionName", "<anonymous>"),
                    filename=frame["url"],
                    line_number=frame["location"]["lineNumber"],
                    local_vars={},
                    timestamp=time.time()
                ))
                # Step to next function
                await ws.send(json.dumps({"id": 3, "method": "Debugger.stepOver"}))
            
            if msg.get("method") == "Debugger.resumed" and proc.poll() is not None:
                break
    
    proc.wait()
    return events
```

**Error handling:**
- If Node.js is not installed: print `"Node.js is required for JavaScript Oracle mode. Install from nodejs.org"` and exit cleanly.
- If port 9229 is already in use: try port 9230, then 9231, then error.
- If connection times out: print `"Could not connect to Node.js inspector. Is the script too small to trace?"`.

---

### Bridge 3: C and C++ — GDB Python API

**What it is:** GDB (GNU Debugger) has a built-in Python extension system. When GDB runs a C/C++ program, Python scripts can hook into every breakpoint, function call, and step event. Oracle uses this to extract trace events.

**Requirements:**
- GDB must be installed: `gdb --version` should work
- The C file must be compiled with debug symbols: `-g` flag

**Step 1 — Compile with debug symbols:**
```bash
gcc -g -o /tmp/morpheus_target program.c
```
Oracle does this automatically before tracing.

**Step 2 — GDB Python script:**
Oracle writes a temporary Python script that GDB runs internally:

```python
# morpheus_gdb_bridge.py (written to /tmp/ by oracle.py)
import gdb
import json
import time

events = []

class MorpheusFunctionBreakpoint(gdb.Breakpoint):
    def stop(self):
        frame = gdb.selected_frame()
        events.append({
            "event_type": "call",
            "function_name": frame.name() or "<unknown>",
            "filename": frame.find_sal().symtab.filename if frame.find_sal().symtab else "",
            "line_number": frame.find_sal().line,
            "timestamp": time.time()
        })
        return False  # Don't actually stop — continue running

# Set breakpoint on all functions
gdb.execute("rbreak .")  # Breakpoint on every function
gdb.events.exited.connect(lambda e: save_events())

def save_events():
    with open("/tmp/morpheus_gdb_events.json", "w") as f:
        json.dump(events, f)

gdb.execute("run")
```

**Step 3 — Launch GDB with the script:**
```bash
gdb -batch -x /tmp/morpheus_gdb_bridge.py /tmp/morpheus_target
```

**Step 4 — Read the output:**
Oracle reads `/tmp/morpheus_gdb_events.json` after GDB finishes and converts each dict to a `TraceEvent`.

**Error handling:**
- If GDB is not installed: print `"GDB is required for C/C++ Oracle mode. Install with: sudo apt install gdb"` and exit.
- If compilation fails: print the gcc error output and exit.
- If no events are written: print `"No trace events captured. Ensure the program executes before exiting."`.

---

### Bridge 4: Java — JVMTI Agent

**Note:** This is the most complex bridge. Build this last, after JavaScript and C are working.

**What it is:** The Java Virtual Machine Tool Interface (JVMTI) allows native agents to hook into JVM events — method entry, method exit, exceptions, thread events. Oracle uses a pre-built Java agent JAR to capture these events.

**Architecture:**
1. Build or download a JVMTI agent JAR: `morpheus-agent.jar`
2. Launch the Java program with the agent attached: `java -javaagent:morpheus-agent.jar Main`
3. The agent writes events to a temp file as the program runs
4. Oracle reads the events file after execution

**Agent behavior (what morpheus-agent.jar must do):**
- Hook into `MethodEntry` and `MethodExit` JVMTI events
- Write each event as a JSON line to `/tmp/morpheus_java_events.jsonl`
- Flush and close the file on program exit

**Running with agent:**
```bash
java -javaagent:/path/to/morpheus-agent.jar -cp . Main
```

**Event format written by agent:**
```json
{"event":"entry","class":"com.example.Main","method":"loadData","line":45,"time":1234567890.123}
{"event":"exit","class":"com.example.Main","method":"loadData","line":45,"time":1234567890.456}
```

**Oracle reads these and converts to TraceEvent objects.**

**Error handling:**
- If Java is not installed: print `"Java is required for Java Oracle mode."` and exit.
- If agent JAR is missing: print `"morpheus-agent.jar not found. Run: morpheus install-agents"` and exit.

---

## LAYER 3 — PERSONALITY ENGINE

Once events are captured (regardless of language), they are narrated through a personality. The personality only changes the LLM system prompt. Everything else is the same.

### The 4 Personalities

---

#### Mentor Personality

**Flag:** `--personality mentor`

**Tone:** Constructive, educational, patient. Like a senior developer doing a kind code review.

**System prompt:**
```
You are a senior software engineer mentoring a junior developer.
Explain what this code did during execution in clear, simple terms.
Be constructive and encouraging. Use analogies when helpful.
End every response with exactly one specific improvement suggestion.
Never be condescending. Assume the developer is intelligent but learning.
Keep each explanation to 3-5 sentences maximum.
```

**Example output:**
```
The program started by loading the dataset — it found 4,200 rows and 8 columns, 
which is a healthy size for training. It then cleaned the data by removing 312 
rows with missing values, leaving 3,888 rows. The model training kicked off with 
an SVR using an RBF kernel, which is a solid choice for this kind of regression task.

Improvement: Consider logging the number of removed rows as a percentage 
(about 7.4% here) — this helps catch if future datasets have unusually high 
missing rates.
```

---

#### Critic Personality

**Flag:** `--personality critic`

**Tone:** Direct, technical, no-nonsense. Like a principal engineer doing a tough code review.

**System prompt:**
```
You are a principal software engineer doing a strict code review.
You have seen every mistake in the book. Call out every problem you see — directly.
Do not soften feedback. Be specific about what is wrong and why it matters.
You respect people who can handle honest feedback.
Keep it concise — one sentence per problem maximum.
If something is genuinely good, you can acknowledge it briefly.
```

**Example output:**
```
load_data(): fine, but no error handling if the file doesn't exist.
validate(): passed silently even though 7.4% of rows were dropped — 
that should be logged at minimum, flagged if over 5%.
train_model(): ran with default hyperparameters. On real data this 
is almost always wrong. The converged at epoch 14 is luck, not tuning.
```

---

#### Paranoid Personality

**Flag:** `--personality paranoid`

**Tone:** Security researcher. Sees every vulnerability, every unsafe assumption, every potential attack surface.

**System prompt:**
```
You are a security researcher analyzing this code execution for vulnerabilities.
Assume the code will be run in production with real user data.
Flag every unsafe assumption, potential data leak, unvalidated input, 
and security risk you observe — even minor ones.
Rate each finding: LOW, MEDIUM, HIGH, or CRITICAL.
Be specific about what an attacker could do with each vulnerability.
```

**Example output:**
```
[HIGH] load_data(): File path is accepted without validation. 
       A path traversal attack could read arbitrary files.
[MEDIUM] validate(): Silently drops rows. If an attacker can manipulate 
         the dataset, they can corrupt model training without leaving a trace.
[LOW] save_model(): Writing to a fixed path with no permission check. 
      On a shared system, other users could overwrite the model file.
```

---

#### Teacher Personality

**Flag:** `--personality teacher`

**Tone:** CS professor. Connects execution events to computer science concepts. Asks the learner questions.

**System prompt:**
```
You are a computer science professor teaching through this execution.
After each function executes, explain what happened AND connect it to a 
foundational CS concept the student should understand.
Then ask the student one question about what they just observed.
Make the question multiple choice with 3 options labeled a, b, c.
Never answer the question yourself — wait for the student.
```

**Example output:**
```
The load_data() function just finished reading a CSV file into memory.

This is an example of I/O operations — interactions between the program and 
external storage. Notice that even loading 4,200 rows was nearly instant. 
This is because modern SSDs can read data at 500+ MB/second.

❓ Question: The program loaded 4,200 rows but only kept 3,888 after cleaning. 
   Where did the missing 312 rows go?

   a) They were moved to a backup file
   b) They were deleted from memory because they had missing values  
   c) They will be recovered when the model trains
```

---

## PERSONALITY SWITCHING

The user can switch personalities on the same file to see four completely different explanations:

```bash
morpheus run train.py --mode oracle --personality mentor
morpheus run train.py --mode oracle --personality critic
morpheus run train.py --mode oracle --personality paranoid
morpheus run train.py --mode oracle --personality teacher
```

**This is the demo moment.** Run the same script four times with four personalities and show the output side by side. This is what makes people share the project.

---

## TREE-SITTER INTEGRATION

Tree-sitter is used for static pre-analysis before runtime tracing. It parses the file into an AST and extracts structural information that enriches the narration.

**Installation:**
```bash
pip install tree-sitter
```

**Language parsers:**
```bash
pip install tree-sitter-python tree-sitter-javascript tree-sitter-c tree-sitter-java
```

**What Oracle extracts from the AST (before running):**
- List of all function names defined in the file
- Line ranges for each function
- Import/require statements (what dependencies the code uses)
- Class names and structure

**This pre-analysis is passed to the LLM prompt as context:**
```
File structure (from static analysis):
- 3 functions defined: load_data (line 5-18), validate (line 20-31), train_model (line 33-67)
- Imports: pandas, sklearn, joblib
- No classes defined
```

This context helps the LLM produce more accurate narration — it knows the full structure before it sees the runtime events.

**Minimal tree-sitter usage example:**
```python
from tree_sitter import Language, Parser
import tree_sitter_python as tspython

PY_LANGUAGE = Language(tspython.language())
parser = Parser(PY_LANGUAGE)

with open(filepath, "rb") as f:
    source = f.read()

tree = parser.parse(source)

# Extract function names
def extract_functions(node, source_bytes):
    functions = []
    if node.type == "function_definition":
        name_node = node.child_by_field_name("name")
        if name_node:
            functions.append({
                "name": source_bytes[name_node.start_byte:name_node.end_byte].decode(),
                "start_line": node.start_point[0],
                "end_line": node.end_point[0]
            })
    for child in node.children:
        functions.extend(extract_functions(child, source_bytes))
    return functions

functions = extract_functions(tree.root_node, source)
```

---

## TESTING ORACLE

### Test Scripts to Create

Before testing Oracle, create these scripts in the `examples/` folder:

**examples/simple.js** — A 20-line JavaScript file with 3 functions:
```javascript
function add(a, b) { return a + b; }
function multiply(a, b) { return a * b; }
function calculate(x, y) {
    const sum = add(x, y);
    const product = multiply(x, y);
    return { sum, product };
}
const result = calculate(5, 3);
console.log(result);
```

**examples/simple.c** — A 20-line C file with 3 functions:
```c
#include <stdio.h>
int add(int a, int b) { return a + b; }
int multiply(int a, int b) { return a * b; }
int main() {
    int x = 5, y = 3;
    printf("Sum: %d\n", add(x, y));
    printf("Product: %d\n", multiply(x, y));
    return 0;
}
```

### Test Commands

```bash
# Python (existing tracer)
morpheus run examples/simple.py --mode oracle --personality mentor

# JavaScript (V8 bridge)
morpheus run examples/simple.js --mode oracle --personality critic

# C (GDB bridge)  
morpheus run examples/simple.c --mode oracle --personality paranoid

# All 4 personalities on same file
morpheus run examples/simple.js --mode oracle --personality mentor
morpheus run examples/simple.js --mode oracle --personality critic
morpheus run examples/simple.js --mode oracle --personality paranoid
morpheus run examples/simple.js --mode oracle --personality teacher
```

### Pass Criteria

Oracle is working when:
- [ ] `detect_language()` correctly identifies .py, .js, .ts, .c, .cpp, .java
- [ ] JavaScript: `morpheus run examples/simple.js --mode oracle` produces narration
- [ ] All 4 personalities produce visibly different narration styles on the same file
- [ ] Unsupported extension (.rb, .go) prints a clear error message
- [ ] Node.js not installed → clear error message, not a crash
- [ ] GDB not installed → clear error message, not a crash

---

## WEEK-BY-WEEK ORACLE BUILD PLAN

### Week 7

| Day | Task |
|---|---|
| Day 1 | Install tree-sitter + language parsers. Write `detect_language()`. Write `extract_functions()` using tree-sitter. |
| Day 2 | Build `build_oracle_prompt()` with all 4 personality system prompts. Test prompts manually with Ollama. |
| Day 3–4 | Build V8 Inspector bridge — `trace_javascript()`. Test on `examples/simple.js`. |
| Day 5 | Wire JavaScript Oracle into `oracle.py` and `cli.py`. Run all 4 personalities on simple.js. |

### Week 8

| Day | Task |
|---|---|
| Day 1–2 | Build GDB bridge — compile step + gdb script + event reader. |
| Day 3 | Test GDB bridge on `examples/simple.c`. |
| Day 4 | Add TypeScript support (compile .ts → .js first, then use V8 bridge). |
| Day 5 | Write `tests/test_oracle.py`. Oracle section complete. |

---

## COMMON ORACLE ERRORS AND FIXES

**Error: `websockets` module not found**
Fix: `pip install websockets`

**Error: `EADDRINUSE` — port 9229 already in use**
Fix: Kill the existing Node.js inspector: `kill $(lsof -t -i:9229)` on Linux/Mac.
On Windows: `netstat -ano | findstr 9229` then `taskkill /PID <pid> /F`.

**Error: `Could not connect to Node.js inspector`**
Fix: Add a longer sleep between launching Node.js and connecting the WebSocket. Try `time.sleep(1.0)` instead of `time.sleep(0.5)`.

**Error: GDB prints but no events file is created**
Fix: The GDB Python script likely crashed silently. Run GDB manually:
`gdb -batch -x /tmp/morpheus_gdb_bridge.py /tmp/morpheus_target`
and read the error output.

**Error: `tree_sitter` import fails**
Fix: `pip install tree-sitter tree-sitter-python tree-sitter-javascript`

**Error: TypeScript file — `SyntaxError` in Node.js**
Fix: TypeScript must be compiled first. Oracle does this automatically with:
`npx tsc --outDir /tmp/morpheus_ts_out examples/script.ts`
Then runs the compiled `.js` file through the V8 bridge.

---

*ORACLE.md — Created by Madhesh Y*  
*Read ARCHITECTURE.md first. This file extends oracle.py as defined there.*
