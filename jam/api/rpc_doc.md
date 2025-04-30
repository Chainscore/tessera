---

# Tessera RPC API

The **Tessera RPC API** provides a JSON-RPC 2.0 interface for interacting with the Tessera blockchain node. It supports methods for querying blockchain data, retrieving statistics, and managing state.

---

## Features

- Query blockchain statistics and state.
- Retrieve finalized blocks, parent blocks, and state roots.
- JSON-RPC 2.0 compliant.

---

## API Endpoint

**Base URL(localhost):**  
`http://127.0.0.1:8000/rpc.tessera`

**Method:**  
`POST`

**Content-Type:**  
`application/json`

---

## Request Format

```json
{
  "jsonrpc": "2.0",
  "method": "<method_name>",
  "params": { "<key>": "<value>" },
  "id": <request_id>
}
```

---

## Response Format

```json
{
  "jsonrpc": "2.0",
  "result": <result_data>,
  "error": { "code": <error_code>, "message": "<error_message>" },
  "id": <request_id>
}
```

---

## Supported Methods

### 1. **`statistics`**
Retrieve blockchain statistics for a given block.

**Request:**
```bash
curl http://127.0.0.1:8000/rpc.tessera \
  -X POST \
  -H "Content-Type: application/json" \
  --data '{
    "method": "statistics",
    "params": {
      "Hash": [9, 22, 47, 0, 129, 231, 187, 27, 132, 92, 215, 134, 177, 181, 78, 139, 163, 206, 87, 173, 138, 231, 16, 253, 5, 145, 172, 130, 208, 197, 4, 223]
    },
    "id": 1,
    "jsonrpc": "2.0"
  }'
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": ["<encoded_statistics>"],
  "error": null,
  "id": 1
}
```

---

### 2. **`stateRoot`**
Retrieve the state root of a given block.

**Request:**
```bash
curl http://127.0.0.1:8000/rpc.tessera \
  -X POST \
  -H "Content-Type: application/json" \
  --data '{
    "method": "stateRoot",
    "params": {
      "Hash": [9, 22, 47, 0, 129, 231, 187, 27, 132, 92, 215, 134, 177, 181, 78, 139, 163, 206, 87, 173, 138, 231, 16, 253, 5, 145, 172, 130, 208, 197, 4, 223]
    },
    "id": 1,
    "jsonrpc": "2.0"
  }'
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": ["0000000000000000000000000000000000000000000000000000000000000000"],
  "error": null,
  "id": 1
}
```

---

### 3. **`parent`**
Retrieve the parent block of a given block.

**Request:**
```bash
curl http://127.0.0.1:8000/rpc.tessera \
  -X POST \
  -H "Content-Type: application/json" \
  --data '{
    "method": "parent",
    "params": {
      "Hash": [9, 22, 47, 0, 129, 231, 187, 27, 132, 92, 215, 134, 177, 181, 78, 139, 163, 206, 87, 173, 138, 231, 16, 253, 5, 145, 172, 130, 208, 197, 4, 223]
    },
    "id": 1,
    "jsonrpc": "2.0"
  }'
```

**Response:**
- If the block is the genesis block:
```json
{
  "jsonrpc": "2.0",
  "result": null,
  "error": {
    "code": -32602,
    "message": "No parent block available for genesis block"
  },
  "id": 1
}
```

---

### 4. **`finalizedBlock`**
Retrieve the finalized block.

**Request:**
```bash
curl http://127.0.0.1:8000/rpc.tessera \
  -X POST \
  -H "Content-Type: application/json" \
  --data '{
    "method": "finalizedBlock",
    "params": {
      "Hash": [9, 22, 47, 0, 129, 231, 187, 27, 132, 92, 215, 134, 177, 181, 78, 139, 163, 206, 87, 173, 138, 231, 16, 253, 5, 145, 172, 130, 208, 197, 4, 223]
    },
    "id": 1,
    "jsonrpc": "2.0"
  }'
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": [4110010668433435290679482509415946368592786990595259113535115434599586792671, 0],
  "error": null,
  "id": 1
}
```

---

## Error Codes

| Code    | Message                     | Description                                      |
|---------|-----------------------------|--------------------------------------------------|
| -32601  | Method not found            | The requested method is not supported.          |
| -32602  | Invalid parameters          | The provided parameters are invalid.            |
| -32700  | Parse error                 | The JSON request could not be parsed.           |

---

## Additional Resources

- [Tessera API Overview](https://example.com/tessera-api-overview)  
- [JSON-RPC Specification JIP-2](https://docs.jamcha.in/advanced/rpc/jip2-node-rpc)  
- [Ethereum JSON-RPC Documentation](https://www.quicknode.com/docs/ethereum)  
