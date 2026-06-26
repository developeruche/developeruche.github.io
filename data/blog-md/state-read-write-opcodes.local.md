# If State Read/Write Opcode Aren't Native VM (WASM/RISC-V) Instructions, How Do Blockchains State read and write?


Dive into the instruction set of powerful, general-purpose virtual machines like WebAssembly (WASM) or RISC-V, and you'll find commands for arithmetic, logic, and memory operations – the building blocks of computation. 1  But search for specific opcodes designed to directly read from or write to a blockchain's state, like the EVM's famous SLOAD or SSTORE, and you'll come up empty. This presents a fascinating paradox: if the VMs running smart contracts on many innovative blockchains lack these native state-handling instructions, how do these platforms actually manage the crucial tasks of reading account balances or writing data to contract storage? This post unravels the essential mechanism that bridges the gap between general-purpose computation and blockchain-specific state management.

## This VM is not the blockchain, but rather a component  of the blockchain
The VM is a powerful component of the blockchain, tasked with state transition function of the blockchain among other features. It is important to note that this VM does not run in Isolation. This engine, be it powered by WASM or RISC-V, doesn't operate in a vacuum. Instead, it thrives within a "host environment," the very blockchain node software itself. This environment provides a set of specialized tools, the Host Functions or APIs, that the VM can utilize. Think of them as bridges, allowing the code within the VM to interact with the broader blockchain ecosystem. These host functions are crucial, as they connect the general-purpose computational capabilities of the VM to the blockchain's unique functionalities, enabling smart contracts to read and write ledger data, interact with other accounts, and ultimately, drive the blockchain's logic.


When a smart contract, compiled into bytecode for a virtual machine (VM) like WASM or RISC-V, needs to interact with the blockchain—whether to **transfer tokens**, **modify storage**, **call another contract**, or **read block information**—it doesn’t rely on native VM instructions tailored for those specific actions. Instead, the contract invokes **predefined host functions** provided by the blockchain’s runtime environment. For example, a function like `env.transfer_balance(recipient_address, amount)` might be called to send tokens to a recipient, or `env.storage_write(key, value)` to update the contract’s persistent storage. The VM identifies these as external calls, passing them to the host environment, which securely executes the requested blockchain operation and updates the system state. This design keeps the VM focused on computation while delegating blockchain-specific tasks to the runtime, ensuring both flexibility and security.


When a smart contract executes within a virtual machine (VM), such as WASM or RISC-V, and invokes a blockchain-specific operation, the VM’s execution **pauses temporarily**. At this point, control shifts to the **host environment**—the blockchain node running the network’s software. The node takes over, natively executing the requested operation by interpreting the call and interacting with the blockchain’s infrastructure. This process involves **accessing the blockchain’s state** (e.g., the state trie or database), **performing necessary checks** (such as verifying an account has sufficient balance for a transaction), and **updating relevant data structures** like account balances or contract storage tries. All actions adhere strictly to the blockchain’s **consensus rules**, ensuring consistency and security. Though this execution occurs outside the VM’s core instruction processing, it is seamlessly **triggered by the VM’s code**, bridging the contract’s logic with the blockchain’s state management.

### Returning Control & Results

When a smart contract executes on a blockchain, certain operations—such as reading data from storage, updating account balances, or modifying contract state—require interaction with the **host environment** (typically the blockchain node). Once the host environment completes the requested operation, it **returns control** to the virtual machine (VM). This handoff is crucial because the VM is responsible for executing the smart contract’s logic, but it relies on the host for operations that involve the blockchain’s state or external data.

Along with control, the host environment often provides a **result**. This result could be:
- A **success/failure status**, indicating whether the operation completed as expected.
- **Data retrieved**, such as a value read from storage or the outcome of a balance transfer.

Once the VM regains control, it resumes executing the smart contract’s code from the exact point where it paused to call the host function. The returned result is then integrated into the ongoing execution, allowing the smart contract to proceed with its logic based on the outcome or data provided by the host.

For example:
- If a smart contract queries an account balance, the host retrieves the value and returns it to the VM, which might then use it in a subsequent calculation.
- If the operation fails (e.g., due to insufficient funds for a transfer), the VM can handle the failure accordingly, potentially reverting changes.

This seamless interaction ensures that the VM and host work together efficiently to execute complex smart contract logic.

### Gas / Metering

In blockchain systems like the Ethereum Virtual Machine (EVM), every operation consumes computational resources, and this usage is tracked and charged via a mechanism called **gas** or **compute units**. Gas serves as a metering system to:
- Measure the computational effort required for an operation.
- Ensure fair compensation for the network nodes performing the work.
- Prevent abuse, such as infinite loops or excessive resource consumption.

#### What Incurs Gas Costs?
Gas costs apply to two main categories of operations:
1. **VM Instructions**: These are the basic operations executed within the VM, such as:
   - Arithmetic (e.g., addition, multiplication).
   - Logic operations (e.g., comparisons like greater-than or equal-to).
   These typically have lower, standardized gas costs because they are relatively lightweight.

2. **Host Function Calls**: These involve operations that interact with the blockchain’s state or external systems, such as:
   - Reading data from storage.
   - Writing to storage (e.g., updating a variable in a smart contract).
   - Transferring balances between accounts.
   - Emitting events or logs.

#### Why Do Host Functions Cost More?
Host functions, especially those that **modify state**, often have **specific and higher gas costs** compared to simple VM instructions. This reflects the greater resource demands they place on the blockchain network. For instance:
- **Writing to storage** requires updating the blockchain’s persistent state, which involves disk I/O, consensus among nodes, and permanent storage—making it resource-intensive.
- **Transferring balances** alters account states and requires validation across the network, adding to the computational overhead.

In contrast, reading data from storage might cost less than writing, but it still exceeds the cost of basic arithmetic because it involves retrieving data from the blockchain’s state.

#### Why Gas Matters
This gas-based metering ensures that:
- Resource usage is accurately tracked and limited.
- The blockchain remains efficient and secure by discouraging wasteful operations.
- Users pay fees proportional to the resources they consume, incentivizing optimized smart contract design.

### Analogy:

Think of it like running a standard application on your computer's operating system (OS):
- Your application code runs on the CPU (using instruction sets like x86 or ARM).
- The CPU's instruction set doesn't have a command like SAVE_FILE_TO_DISK.
- Instead, your application makes a system call (like write()) provided by the OS.
- The OS takes over, performs the complex operations needed to interact with the file system and hardware, and then returns control to your application.


In the blockchain context:
- The Smart Contract Code is the "application."
- The VM (WASM, RISC-V) is like the "CPU."
- The Host Functions are like the "system calls."
- The Blockchain Node Software is like the "Operating System," managing the core state (like the file system).

## Diving deeper, if this VM is a RISCV VM, how would this be implemented

To implement a RISC-V Virtual Machine (VM) for a blockchain, we need to create a system where smart contracts written in RISC-V assembly or compiled to RISC-V instructions can execute within the blockchain environment. The VM must interpret or compile these instructions and provide a way for contracts to interact with the blockchain’s state (e.g., transferring tokens or updating storage) through a set of predefined **host functions**. Below, I’ll explain the high-level implementation and provide code snippets to illustrate the concept.

---

### Overview of the Implementation

1. **RISC-V VM Core**:
   - The blockchain runtime includes a RISC-V VM that can either interpret RISC-V instructions step-by-step or use a just-in-time (JIT) compiler for better performance.
   - The VM executes the contract’s code, managing its registers, memory, and program counter.

2. **Host Functions**:
   - These are blockchain-specific functions provided by the runtime (e.g., transferring tokens or reading storage).
   - Contracts call these functions to perform actions that affect the blockchain state.

3. **System Call Mechanism**:
   - RISC-V uses the `ecall` instruction to make system calls, traditionally for OS services. In this blockchain context, we repurpose `ecall` to invoke host functions.
   - The contract specifies which host function to call using a system call number and passes arguments via registers.

4. **Execution Flow**:
   - The contract runs on the VM until it needs to interact with the blockchain.
   - It triggers an `ecall`, which the runtime intercepts and maps to the appropriate host function.
   - The host function executes, modifies the blockchain state, and returns control to the VM.

---

### Example: Transferring Tokens

Let’s walk through a concrete example: a smart contract transferring tokens from one account to another. We’ll cover both the **contract side** (RISC-V assembly) and the **runtime side** (host implementation).

#### 1. Runtime Side (Host Implementation)

The runtime defines host functions and a system call handler to process requests from the VM. Here’s how it might look in pseudocode (using Rust-like syntax for clarity):

```rust
// Define system call numbers
const SYS_TRANSFER: u32 = 1;

// Host function to transfer tokens
fn host_transfer(caller: Address, to: Address, amount: u64) -> Result<(), Error> {
    // Check the caller's balance
    let caller_balance = get_balance(caller);
    if caller_balance < amount {
        return Err("Insufficient balance");
    }
    // Update balances
    set_balance(caller, caller_balance - amount);
    set_balance(to, get_balance(to) + amount);
    // Emit an event (optional)
    emit_event("Transfer", caller, to, amount);
    Ok(())
}

// System call handler in the runtime
fn handle_syscall(vm: &mut RiscVVM, syscall_num: u32) -> Result<(), Error> {
    match syscall_num {
        SYS_TRANSFER => {
            // Get arguments from VM registers (a0 = to, a1 = amount)
            let to = vm.get_register("a0");
            let amount = vm.get_register("a1");
            host_transfer(vm.caller_address(), to, amount)
        }
        _ => Err("Invalid system call"),
    }
}

// Simplified VM structure
struct RiscVVM {
    registers: HashMap<String, u64>, // e.g., "a0", "a1", "a7"
    caller_address: Address,         // Address of the contract caller
    // Other VM state (memory, PC, etc.)
}

impl RiscVVM {
    fn get_register(&self, reg: &str) -> u64 {
        *self.registers.get(reg).unwrap_or(&0)
    }

    fn set_register(&mut self, reg: &str, value: u64) {
        self.registers.insert(reg.to_string(), value);
    }

    fn caller_address(&self) -> Address {
        self.caller_address
    }
}
```

- **Key Points**:
  - `SYS_TRANSFER` is a predefined constant (e.g., 1) that identifies the token transfer operation.
  - Arguments (`to` and `amount`) are passed via RISC-V registers (`a0` and `a1`).
  - The runtime checks the caller’s balance, updates the state, and returns success or an error.

#### 2. Contract Side (RISC-V Assembly)

The smart contract, written in RISC-V assembly, prepares the arguments and triggers the system call. Here’s an example:

```assembly
# Transfer 100 tokens to address 0x1234
# Arguments: a0 = to_address, a1 = amount
# System call number: a7 = SYS_TRANSFER (1)

# Load the 'to' address into a0
li a0, 0x1234    # Example target address (simplified)

# Load the amount into a1
li a1, 100       # Transfer 100 tokens

# Load the system call number into a7
li a7, 1         # SYS_TRANSFER = 1

# Make the system call
ecall            # Triggers the runtime's handle_syscall function

# After ecall returns, check result (e.g., in a0)
# a0 = 0 means success, non-zero means error
bnez a0, error_handler  # Branch to error handler if a0 != 0

# Continue execution on success
j continue

error_handler:
    # Handle the error (e.g., revert or log)
    nop

continue:
    # Proceed with contract logic
    nop
```

- **Key Points**:
  - `li` loads immediate values into registers (`a0` for the recipient address, `a1` for the amount, `a7` for the system call number).
  - `ecall` invokes the runtime’s system call handler.
  - The runtime may return a result in `a0` (e.g., 0 for success).

---

### How It Works Together

1. **Contract Execution**:
   - The RISC-V VM loads and runs the contract’s instructions.
   - When it hits the `ecall`, execution pauses, and control transfers to the runtime.

2. **Runtime Processing**:
   - The runtime reads the system call number from register `a7` and arguments from `a0` and `a1`.
   - It calls `host_transfer`, which updates the blockchain state (e.g., token balances).

3. **Return to Contract**:
   - The runtime sets a return value in `a0` (e.g., 0 for success) and resumes the VM.
   - The contract checks the result and continues or handles an error.

---

### Additional Considerations

- **Argument Passing**:
  - RISC-V uses registers `a0`–`a5` for arguments and `a7` for the system call number, following its calling convention.
  - For complex data, the contract could pass a memory address pointing to the data.

- **Security**:
  - The runtime must validate inputs (e.g., ensure `caller` has enough tokens) to prevent unauthorized actions.
  - Errors should revert state changes to maintain consistency.

- **Resource Metering**:
  - Each `ecall` consumes “gas” or a similar resource to limit execution and prevent abuse.