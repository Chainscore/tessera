# JAM Node Logging Guide

This guide explains how to properly use logging in the JAM node codebase for both development and production environments.

## Quick Start

```python
from jam.logging import get_logger

# Create a logger for your module
logger = get_logger("module-name")

# Use structured logging with key-value pairs
logger.info("Block produced", block_hash=hash, slot=slot, validator=validator_id)
```

## Log Levels

### DEBUG
**When to use:** Detailed diagnostic information for development and troubleshooting.

```python
logger.debug(
    "Executing PVM instruction",
    pc=program_counter,
    opcode=opcode,
    gas_remaining=gas,
    instruction=instruction_name
)
```

**Examples:**
- Function entry/exit with parameters
- Variable state changes
- Detailed protocol message content
- PVM instruction execution details
- Network message parsing steps

### INFO  
**When to use:** General information about normal program operation.

```python
logger.info(
    "Block produced successfully",
    block_hash=block.hash(),
    slot=block.slot,
    tx_count=len(block.transactions),
    duration_ms=production_time
)
```

**Examples:**
- Node startup/shutdown
- Network connections established/lost
- Block production/reception
- Major state transitions
- Performance metrics

### WARNING
**When to use:** Something unexpected happened but the program continues working.

```python
logger.warning(
    "Peer connection failed, retrying",
    peer_host=peer.host,
    peer_port=peer.port,
    retry_count=retry_count,
    error=str(error)
)
```

**Examples:**
- Retryable network errors
- Graceful degradation scenarios
- Resource limitations reached
- Configuration issues that don't prevent operation

### ERROR
**When to use:** A serious problem occurred that prevented a function from working.

```python
logger.error(
    "Block validation failed", 
    block_hash=block.hash(),
    validation_error=error_type,
    error_details=str(error)
)
```

**Examples:**
- Protocol violations
- Authentication failures
- Critical resource unavailability
- Data corruption detected

### CRITICAL
**When to use:** A very serious error that may cause the program to abort.

```python
logger.critical(
    "Database corruption detected",
    database_path=db_path,
    corruption_type=corruption_type,
    affected_tables=affected_tables
)
```

**Examples:**
- Database corruption
- Security breaches
- System resource exhaustion
- Fatal consensus failures

## Best Practices

### 1. Use Structured Logging

❌ **Bad:**
```python
logger.info(f"Block {block_hash} produced in slot {slot} by {validator}")
```

✅ **Good:**
```python
logger.info(
    "Block produced",
    block_hash=block_hash,
    slot=slot,
    validator=validator,
    tx_count=len(transactions)
)
```

### 2. Create Module-Specific Loggers

```python
# At the top of your module
from jam.logging import get_logger

logger = get_logger("pvm")  # Component name for context
```

### 3. Use Performance Logging for Critical Paths

```python
from jam.logging import log_performance

# Context manager for automatic timing
with log_performance(logger, "block_validation", block_hash=hash):
    validate_block(block)
```

### 4. Handle Sensitive Data

❌ **Bad:**
```python
logger.debug("User credentials", private_key=key, password=pwd)
```

✅ **Good:**
```python
# Sensitive data is automatically filtered in production
logger.debug("Authentication attempt", user_id=user_id, success=True)
```

### 5. Use Appropriate Verbosity by Environment

```python
# Development: DEBUG and above
# Testing: INFO and above  
# Production: WARNING and above (configured automatically)

# For expensive operations, use lazy logging
logger.debug("Expensive result: %s", lambda: expensive_computation())
```

## Environment Configuration

### Development
```bash
export ENVIRONMENT=development
export LOG_LEVEL=DEBUG
export THEME=matrix  # or polkadot, solarized, monokai, noir
```

### Testing
```bash
export ENVIRONMENT=testing
export LOG_LEVEL=INFO
```

### Production
```bash
export ENVIRONMENT=production
export LOG_LEVEL=WARNING
# Logs will be saved to /var/log/jam/{node_name}.log
# JSON format for structured log analysis
```

## Module-Specific Logging

### Method 1: Environment Variables

Control log levels for specific modules:

```bash
# Only show PVM debug logs while keeping others at INFO
export LOG_LEVEL=INFO
export LOG_LEVEL_PVM=DEBUG

# Only show network warnings and above
export LOG_LEVEL_NETWORK=WARNING

# Multiple module overrides
export LOG_LEVEL_CONSENSUS=ERROR
export LOG_LEVEL_QUIC_SERVER=INFO
export LOG_LEVEL_EXECUTION=DEBUG
```

### Method 2: Programmatic Filtering

```python
from jam.logging import setup_logging

# Show only specific modules
setup_logging(
    theme='matrix',
    node_name='debug-node',
    allowed_modules=['jam.execution.pvm', 'jam.network.quic']
)

# Block noisy modules
setup_logging(
    theme='matrix',
    node_name='debug-node',
    blocked_modules=['jam.network.protocols', 'jam.types']
)
```
`

### Available Module Names

- `pvm` - PVM execution engine
- `network` - All networking components  
- `quic` - QUIC protocol handlers
- `consensus` - Consensus algorithms
- `execution` - Program execution
- `storage` - Storage systems
- `state` - State management
- `protocols` - Network protocols
- `vrf` - VRF operations
- `types` - Type definitions

## Real-World Examples

### Network Protocol Handler

```python
from jam.logging import get_logger

logger = get_logger("quic-server")


def handle_message(self, buffer: bytes, stream_id: int):
    logger.debug(
        "Processing message",
        stream_id=stream_id,
        buffer_size=len(buffer),
        message_type=message_type
    )

    try:
        result = process_message(buffer)
        logger.info(
            "Message processed successfully",
            stream_id=stream_id,
            processing_time_ms=processing_time
        )
    except ValidationError as e:
        logger.warning(
            "Message validation failed",
            stream_id=stream_id,
            validation_error=str(e),
            buffer_size=len(buffer)
        )
    except Exception as e:
        logger.error(
            "Message processing failed",
            stream_id=stream_id,
            error=str(e),
            error_type=type(e).__name__
        )
```

### PVM Execution

```python
from jam.logging import get_logger, log_performance

logger = get_logger("pvm")


def execute_program(self, program, gas):
    context = {
        "program_size": len(program),
        "initial_gas": gas
    }

    with log_performance(logger, "pvm_execution", **context):
        logger.debug("Starting PVM execution", **context)

        while gas > 0:
            instruction = program[pc]

            logger.debug(
                "Executing instruction",
                pc=pc,
                opcode=instruction.opcode,
                gas_remaining=gas
            )

            # ... execution logic ...

            if error:
                logger.error(
                    "PVM execution error",
                    pc=pc,
                    error=str(error),
                    **context
                )
                break

        logger.info(
            "PVM execution completed",
            final_pc=pc,
            gas_remaining=gas,
            instructions_executed=instruction_count,
            **context
        )
```

### Consensus Engine

```python
from jam.logging import get_logger

logger = get_logger("consensus")


def validate_block(self, block):
    logger.info(
        "Starting block validation",
        block_hash=block.hash(),
        block_number=block.number,
        parent_hash=block.parent_hash
    )

    # Check block structure
    if not self.validate_structure(block):
        logger.error(
            "Block structure validation failed",
            block_hash=block.hash(),
            validation_step="structure"
        )
        return False

    # Check transactions
    invalid_txs = self.validate_transactions(block.transactions)
    if invalid_txs:
        logger.warning(
            "Block contains invalid transactions",
            block_hash=block.hash(),
            invalid_count=len(invalid_txs),
            total_txs=len(block.transactions)
        )

    logger.info(
        "Block validation completed",
        block_hash=block.hash(),
        is_valid=True,
        tx_count=len(block.transactions)
    )
    return True
```

## Monitoring and Observability

The logging system automatically includes:

- **Process ID** for multi-process debugging
- **Timestamps** in ISO format
- **Node name** for distributed system context
- **Component names** for module identification
- **Environment** context (dev/test/prod)

In production, logs are:
- Saved to files with rotation
- Formatted as JSON for analysis
- Filtered to remove sensitive data
- Performance metrics included

## Migration from Print Statements

❌ **Old:**
```python
print(f"PVM Error {e}")
print(f"# \t Inst \t  Bitmask ")
```

✅ **New:**
```python
logger.error("PVM execution error", error=str(e), error_type=type(e).__name__)
logger.debug("Instruction analysis", instruction=inst, has_bitmask=bool(bitmask))
```

## Troubleshooting

### Common Issues

1. **Too much DEBUG output in production**
   - Set `ENVIRONMENT=production` to filter out debug logs

2. **Missing context in logs**
   - Use structured logging with key-value pairs
   - Include relevant IDs (block_hash, stream_id, etc.)

3. **Performance impact**
   - Use lazy logging for expensive operations
   - Production logs are automatically optimized

4. **Log files growing too large**
   - Production logging includes automatic rotation
   - Adjust log levels for different components

### Performance Impact

- **Development:** Full logging has minimal impact
- **Production:** Only WARNING+ levels logged by default
- **Structured logging:** More efficient than string formatting
- **Lazy evaluation:** Expensive operations only when needed

This logging system is designed to provide maximum visibility during development while being production-ready with appropriate filtering and performance optimizations. 