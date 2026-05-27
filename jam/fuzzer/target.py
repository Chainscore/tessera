"""
JAM Conformance Testing Fuzzer Target

This module implements a fuzzer target that follows the JAM Fuzzing Protocol
for conformance testing. It handles handshakes and processes various message
types including block imports, state operations, and root queries.
"""
import json
import gc
import socket
import os
import sys
import shutil
import platform
from datetime import datetime
from typing import Optional

from jam.block.block import Block
from tsrkit_types import Bytes, U8, U32, TypedVector, String

from .constants import (
    TAG_PEER_INFO,
    TAG_INITIALIZE,
    TAG_IMPORT_BLOCK,
    TAG_GET_STATE,
    TAG_STATE,
    TAG_STATE_ROOT,
    TAG_ERROR,
    FEATURE_ANCESTRY,
    FEATURE_FORK,
)
from .types import PeerInfo, Version, Initialize, State, KeyValue, ErrorMessage

from .handlers import read_message, send_message, handle_handshake
from ..block.extrinsics.extrinsic import Extrinsic
from ..models import HeaderHash

def clear_directory_contents(path: str) -> None:
    """Remove everything inside a directory without removing the directory itself."""
    os.makedirs(path, exist_ok=True)
    for entry in os.listdir(path):
        entry_path = os.path.join(path, entry)
        if os.path.isdir(entry_path) and not os.path.islink(entry_path):
            shutil.rmtree(entry_path)
        else:
            os.unlink(entry_path)


def _read_text(path: str) -> str | None:
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return None


def _format_bytes(value: int | None) -> str:
    if value is None:
        return "unknown"
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    size = float(value)
    for unit in units:
        if abs(size) < 1024 or unit == units[-1]:
            return f"{size:.1f}{unit}" if unit != "B" else f"{int(size)}B"
        size /= 1024
    return f"{value}B"


def _process_rss() -> str:
    raw = _read_text("/proc/self/statm")
    if not raw:
        return "unknown"
    parts = raw.split()
    if len(parts) < 2 or not parts[1].isdigit():
        return "unknown"
    try:
        page_size = os.sysconf("SC_PAGE_SIZE")
    except (OSError, ValueError):
        return "unknown"
    return _format_bytes(int(parts[1]) * page_size)


def _read_proc_kib_map(path: str) -> dict[str, int]:
    raw = _read_text(path)
    if not raw:
        return {}
    values: dict[str, int] = {}
    for line in raw.splitlines():
        key, _, rest = line.partition(":")
        parts = rest.strip().split()
        if parts and parts[0].isdigit():
            values[key] = int(parts[0]) * 1024
    return values


def _read_proc_value_map(path: str) -> dict[str, int]:
    raw = _read_text(path)
    if not raw:
        return {}
    values: dict[str, int] = {}
    for line in raw.splitlines():
        if ":" in line:
            key, _, rest = line.partition(":")
            parts = rest.strip().split()
        else:
            parts = line.split()
            if len(parts) < 2:
                continue
            key = parts[0]
            parts = parts[1:]
        if parts and parts[0].isdigit():
            values[key] = int(parts[0])
    return values


def _process_memory_snapshot() -> dict[str, int | None]:
    rollup = _read_proc_kib_map("/proc/self/smaps_rollup")
    status = _read_proc_kib_map("/proc/self/status")
    private = None
    if rollup:
        private = rollup.get("Private_Clean", 0) + rollup.get("Private_Dirty", 0)
    return {
        "rss": rollup.get("Rss") or status.get("VmRSS"),
        "pss": rollup.get("Pss"),
        "private": private,
        "vm_size": status.get("VmSize"),
        "vm_hwm": status.get("VmHWM"),
    }


def _format_process_memory() -> str:
    mem = _process_memory_snapshot()
    return (
        f"rss={_format_bytes(mem['rss'])} "
        f"pss={_format_bytes(mem['pss'])} "
        f"private={_format_bytes(mem['private'])} "
        f"vm={_format_bytes(mem['vm_size'])}"
    )


def _find_cgroup_v2_path() -> str | None:
    raw = _read_text("/proc/self/cgroup")
    if not raw:
        return None
    for line in raw.splitlines():
        parts = line.split(":", 2)
        if len(parts) == 3 and parts[0] == "0":
            return os.path.join("/sys/fs/cgroup", parts[2].lstrip("/"))
    return None


def _cgroup_memory_snapshot() -> dict[str, int | None]:
    cg_path = _find_cgroup_v2_path()
    if not cg_path:
        return {}

    def read_int(name: str) -> int | None:
        raw = _read_text(os.path.join(cg_path, name))
        return int(raw) if raw and raw.isdigit() else None

    stat_raw = _read_text(os.path.join(cg_path, "memory.stat")) or ""
    stat: dict[str, int] = {}
    for line in stat_raw.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1].isdigit():
            stat[parts[0]] = int(parts[1])

    return {
        "current": read_int("memory.current"),
        "peak": read_int("memory.peak"),
        "anon": stat.get("anon"),
        "file": stat.get("file"),
        "inactive_file": stat.get("inactive_file"),
        "kernel": stat.get("kernel"),
    }


def _format_cgroup_events() -> str:
    cg_path = _find_cgroup_v2_path()
    if not cg_path:
        return "cgevents=unknown"

    events = _read_proc_value_map(os.path.join(cg_path, "memory.events"))
    pressure_raw = _read_text(os.path.join(cg_path, "memory.pressure")) or ""
    pressure: dict[str, int] = {}
    for line in pressure_raw.splitlines():
        parts = line.split()
        if not parts:
            continue
        for part in parts[1:]:
            key, sep, value = part.partition("=")
            if sep and key == "total" and value.isdigit():
                pressure[parts[0]] = int(value)

    return (
        "cgevents="
        f"low={events.get('low', 0)},"
        f"high={events.get('high', 0)},"
        f"max={events.get('max', 0)},"
        f"oom={events.get('oom', 0)},"
        f"oom_kill={events.get('oom_kill', 0)},"
        f"psi_some={pressure.get('some', 0)},"
        f"psi_full={pressure.get('full', 0)}"
    )


def _format_cgroup_memory() -> str:
    mem = _cgroup_memory_snapshot()
    if not mem:
        return "cgroup=unknown"
    return (
        f"cgroup={_format_bytes(mem.get('current'))} "
        f"cgpeak={_format_bytes(mem.get('peak'))} "
        f"anon={_format_bytes(mem.get('anon'))} "
        f"file={_format_bytes(mem.get('file'))} "
        f"inactive_file={_format_bytes(mem.get('inactive_file'))}"
    )


def _db_file_category(name: str) -> str:
    if name.endswith(".sst"):
        return "sst"
    if name.endswith(".log") or name in ("LOG", "LOG.old"):
        return "log"
    if name.startswith("MANIFEST"):
        return "manifest"
    if name.startswith("OPTIONS"):
        return "options"
    if name in ("CURRENT", "LOCK", "IDENTITY"):
        return "meta"
    return "other"


def _dir_file_breakdown(path: str) -> dict[str, tuple[int, int]]:
    breakdown: dict[str, list[int]] = {}
    total = 0
    try:
        for root, _, files in os.walk(path):
            for name in files:
                try:
                    size = os.path.getsize(os.path.join(root, name))
                except OSError:
                    continue
                category = _db_file_category(name)
                entry = breakdown.setdefault(category, [0, 0])
                entry[0] += 1
                entry[1] += size
                total += size
    except OSError:
        return {}
    breakdown["total"] = [sum(v[0] for k, v in breakdown.items() if k != "total"), total]
    return {key: (value[0], value[1]) for key, value in breakdown.items()}


def _dir_size(path: str) -> int:
    breakdown = _dir_file_breakdown(path)
    return breakdown.get("total", (0, 0))[1]


def _format_db_sizes(db_path: str) -> str:
    parts = []
    for name in ("main", "state", "audit", "d3l"):
        path = os.path.join(db_path, name)
        if os.path.exists(path):
            parts.append(f"{name}={_format_bytes(_dir_size(path))}")
    return "db=" + ",".join(parts) if parts else "db=unknown"


def _format_log_dir_size() -> str:
    log_dir = os.environ.get("JAM_LOG_DIR")
    if not log_dir:
        return "logs=disabled"
    return f"logs={_format_bytes(_dir_size(log_dir))}"


def _format_db_file_breakdown(db_path: str) -> str:
    db_parts = []
    categories = ("sst", "log", "manifest", "options", "meta", "other")
    for name in ("main", "state", "audit", "d3l"):
        path = os.path.join(db_path, name)
        if not os.path.exists(path):
            continue
        breakdown = _dir_file_breakdown(path)
        file_parts = []
        for category in categories:
            count, size = breakdown.get(category, (0, 0))
            if count:
                file_parts.append(f"{category}={count}/{_format_bytes(size)}")
        if not file_parts:
            file_parts.append("empty=0/0B")
        db_parts.append(f"{name}{{{','.join(file_parts)}}}")
    return "dbfiles=" + ";".join(db_parts) if db_parts else "dbfiles=unknown"


def _format_gc_stats() -> str:
    counts = gc.get_count()
    stats = gc.get_stats()
    collections = [item.get("collections", 0) for item in stats]
    collected = [item.get("collected", 0) for item in stats]
    uncollectable = [item.get("uncollectable", 0) for item in stats]
    return (
        f"gc=count={','.join(str(v) for v in counts)} "
        f"gccollections={','.join(str(v) for v in collections)} "
        f"gccollected={','.join(str(v) for v in collected)} "
        f"gcuncollectable={','.join(str(v) for v in uncollectable)}"
    )


def _format_fd_stats() -> str:
    fd_dir = "/proc/self/fd"
    try:
        names = os.listdir(fd_dir)
    except OSError:
        return "fds=unknown"

    counts = {"file": 0, "socket": 0, "pipe": 0, "anon": 0, "other": 0}
    for name in names:
        try:
            target = os.readlink(os.path.join(fd_dir, name))
        except OSError:
            counts["other"] += 1
            continue
        if target.startswith("socket:"):
            counts["socket"] += 1
        elif target.startswith("pipe:"):
            counts["pipe"] += 1
        elif target.startswith("anon_inode:"):
            counts["anon"] += 1
        elif target.startswith("/"):
            counts["file"] += 1
        else:
            counts["other"] += 1

    return (
        f"fds=total={len(names)},"
        f"file={counts['file']},"
        f"socket={counts['socket']},"
        f"pipe={counts['pipe']},"
        f"anon={counts['anon']},"
        f"other={counts['other']}"
    )


def _format_process_io() -> str:
    values = _read_proc_value_map("/proc/self/io")
    if not values:
        return "io=unknown"
    return (
        "io="
        f"rchar={_format_bytes(values.get('rchar'))},"
        f"wchar={_format_bytes(values.get('wchar'))},"
        f"read={_format_bytes(values.get('read_bytes'))},"
        f"write={_format_bytes(values.get('write_bytes'))},"
        f"cancelled={_format_bytes(values.get('cancelled_write_bytes'))},"
        f"syscr={values.get('syscr', 0)},"
        f"syscw={values.get('syscw', 0)}"
    )


_ROCKSDB_PROPERTY_CDEF_BY_FFI: set[int] = set()


def _rocksdb_property(db, prop: str) -> str | None:
    try:
        ffi_id = id(db.ffi)
        if ffi_id not in _ROCKSDB_PROPERTY_CDEF_BY_FFI:
            db.ffi.cdef("char* rocksdb_property_value(rocksdb_t*, const char* propname);")
            _ROCKSDB_PROPERTY_CDEF_BY_FFI.add(ffi_id)
        value_ptr = db.lib.rocksdb_property_value(db.db, prop.encode())
        if value_ptr == db.ffi.NULL:
            return None
        try:
            return db.ffi.string(value_ptr).decode()
        finally:
            db.lib.rocksdb_free(value_ptr)
    except Exception:
        return None


def _format_rocksdb_properties(settings) -> str:
    prop_names = {
        "keys": "rocksdb.estimate-num-keys",
        "live": "rocksdb.estimate-live-data-size",
        "sst": "rocksdb.total-sst-files-size",
        "mem": "rocksdb.cur-size-all-mem-tables",
        "memall": "rocksdb.size-all-mem-tables",
        "readers": "rocksdb.estimate-table-readers-mem",
        "cache": "rocksdb.block-cache-usage",
        "pinned": "rocksdb.block-cache-pinned-usage",
        "versions": "rocksdb.num-live-versions",
        "imm": "rocksdb.num-immutable-mem-table",
    }
    db_attrs = (
        ("main", "_main_db"),
        ("state", "_state_db"),
        ("audit", "_audit_db"),
        ("d3l", "_d3l"),
    )
    db_parts = []
    for name, attr in db_attrs:
        db = getattr(settings, attr, None)
        if db is None:
            continue
        prop_parts = []
        for short, prop in prop_names.items():
            value = _rocksdb_property(db, prop)
            if value is None:
                continue
            value = value.strip()
            if value.isdigit() and short not in ("keys", "versions", "imm"):
                value = _format_bytes(int(value))
            prop_parts.append(f"{short}={value}")
        if prop_parts:
            db_parts.append(f"{name}{{{','.join(prop_parts)}}}")
    return "rocks=" + ";".join(db_parts) if db_parts else "rocks=unavailable"


def _format_block_view(viewer) -> str:
    try:
        index_len = len(getattr(viewer, "_index_map", {}))
        heads_len = len(getattr(viewer, "heads", []) or [])
        final = getattr(viewer, "final", None)
        best = getattr(viewer, "best", None)
        final_slot = int(getattr(final, "slot", 0)) if final is not None else 0
        best_slot = int(getattr(best, "slot", 0)) if best is not None else 0
        final_children = len(getattr(final, "children", []) or []) if final is not None else 0
        pruned_upto = getattr(viewer, "_pruned_upto_slot", 0)
        return (
            f"view=index={index_len} heads={heads_len} "
            f"final_slot={final_slot} best_slot={best_slot} "
            f"final_children={final_children} pruned_upto={pruned_upto}"
        )
    except Exception as exc:
        return f"view=error:{exc}"


def _host_memory_value(name: str) -> int | None:
    raw = _read_text("/proc/meminfo")
    if not raw:
        return None
    for line in raw.splitlines():
        key, _, rest = line.partition(":")
        if key != name:
            continue
        parts = rest.strip().split()
        if parts and parts[0].isdigit():
            return int(parts[0]) * 1024
    return None


def _format_cpu_set(cpus: set[int]) -> str:
    if not cpus:
        return "unknown"
    ranges: list[str] = []
    start = prev = sorted(cpus)[0]
    for cpu in sorted(cpus)[1:]:
        if cpu == prev + 1:
            prev = cpu
            continue
        ranges.append(str(start) if start == prev else f"{start}-{prev}")
        start = prev = cpu
    ranges.append(str(start) if start == prev else f"{start}-{prev}")
    return ",".join(ranges)


def _filesystem_available(path: str) -> str:
    try:
        stats = os.statvfs(path)
    except OSError:
        return "unknown"
    block_size = stats.f_frsize or stats.f_bsize
    return _format_bytes(block_size * stats.f_bavail)


def _print_fuzzer_system_info(db_path: str, socket_path: str, record_path: Optional[str]) -> None:
    try:
        affinity = os.sched_getaffinity(0)
    except AttributeError:
        affinity = set()

    cgroup_text = _read_text("/proc/1/cgroup") or ""
    in_container = os.path.exists("/.dockerenv") or any(
        marker in cgroup_text for marker in ("docker", "kubepods", "containerd")
    )

    print("[system] fuzzer startup")
    print(
        "[system] "
        f"time={datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} "
        f"pid={os.getpid()} "
        f"python={sys.version.split()[0]} "
        f"platform={platform.system()}-{platform.release()} "
        f"container={in_container}"
    )
    print(
        "[system] "
        f"cpu={os.cpu_count()} "
        f"affinity={_format_cpu_set(affinity)} "
        f"ram={_format_bytes(_host_memory_value('MemTotal'))} "
        f"available={_format_bytes(_host_memory_value('MemAvailable'))}"
    )
    print(
        "[system] "
        f"db={db_path} "
        f"file_available={_filesystem_available(db_path)} "
        f"socket={socket_path} "
        f"recording={record_path or 'disabled'}"
    )
    print(
        "[system] "
        f"JAM_LOG_LEVEL={os.environ.get('JAM_LOG_LEVEL', 'unset')} "
        f"PVM_MODE={os.environ.get('PVM_MODE', 'unset')} "
        f"JAM_FUZZ_STATE_STATS_INTERVAL={os.environ.get('JAM_FUZZ_STATE_STATS_INTERVAL', '10')} "
        f"JAM_STATE_TRIE_CACHE_LIMIT={os.environ.get('JAM_STATE_TRIE_CACHE_LIMIT', '8')}"
    )


def run_fuzzer_target_loop(sock: socket.socket, db_path: str, record_path: Optional[str] = None):
    """
    The main server loop that listens for connections and handles messages.

    Args:
        sock: Unix socket to listen on
        db_path: DB path
        record_path: Optional path to record session data
    """

    record_enabled = record_path is not None
    json_data = {"blocks": []} if record_enabled else None
    SESSION_ID = 0
    record_index = 0
    try:
        state_stats_interval = int(os.environ.get("JAM_FUZZ_STATE_STATS_INTERVAL", "10"))
    except ValueError:
        state_stats_interval = 10
    state_stats_interval = max(0, state_stats_interval)

    while True:
        print("V0.7.2")
        conn, addr = sock.accept()
        with conn:
            print("🔌 Fuzzer connected.")

            peer = handle_handshake(conn)
            if not peer:
                continue
            else:
                from jam.settings import setup_setting
                print(">> Connected to", peer.to_json())
                try:
                    db_ = db_path + str(SESSION_ID)
                    settings = setup_setting(db_, 1, "fuzzer", 40001, rpc_flag=False)
                except Exception as e:
                    SESSION_ID += 1
                    db_ = db_path + str(SESSION_ID)
                    settings = setup_setting(db_, 1, "fuzzer", 40001, rpc_flag=False)


            block_count = 0

            # Initialize state
            from jam.state.state import state, State
            from jam.state.storage import StateRecord, StateStorage
            from jam.block.block_view import viewer

            while True:
                tag, payload = read_message(conn)

                if tag is None:
                    if record_enabled and json_data:
                        with open(record_path, "w") as json_record:
                            json.dump(json_data, json_record, indent=4)
                        print(f"📝 Session data recorded to {record_path}")
                    print("🔌 Fuzzer closed connection.")
                    break

                if tag == TAG_IMPORT_BLOCK:
                    block_count += 1
                    received_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                    print(
                        f"{received_at} Received Block #{block_count} "
                        f"({len(payload)} bytes, rss={_process_rss()})"
                    )

                    block = None
                    accepted_block = False
                    try:
                        block = Block.decode(payload)

                        viewer.record_block(block, settings.main_db)

                        if record_enabled and json_data:
                            json_data["blocks"].append(block.to_json())
                        # transition_start = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                        # print(">> Starting Block transition", transition_start)
                        valid_block = State._force_transition(block, False, True)
                        # transition_end = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                        # print(">> Block transition complete", transition_end)
                        if valid_block:
                            accepted_block = True
                            hh = block.header.hash()
                            record_data = settings.main_db.get(StateStorage.get_storage_key(hh))
                            if record_data is None:
                                state_root = State.load(hh).root
                            else:
                                state_root = StateRecord.decode(record_data).roots.curr
                            send_message(conn, TAG_STATE_ROOT, state_root)

                            record_index += 1
                        else:
                            viewer.discard(block, settings.main_db)
                            send_message(conn, TAG_ERROR, String("Invalid block. Error message unavailable").encode())
                    except Exception as e:
                        if block is not None and not accepted_block:
                            viewer.discard(block, settings.main_db)
                        print(f"❌ Block processing failed: {e}", file=sys.stderr)
                        # Send Error message for protocol-defined failures
                        error_msg = ErrorMessage(message=String(f"Block import failed: {str(e)}"))
                        send_message(conn, TAG_ERROR, error_msg.encode())
                    finally:
                        if os.environ.get("JAM_FUZZ_VISUALIZE") == "1":
                            viewer.visualize()

                        log_stats = state_stats_interval and block_count % state_stats_interval == 0
                        ended_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                        print(f"{ended_at} Finished Block #{block_count}")
                        if log_stats:
                            if os.environ.get("JAM_FUZZ_FORCE_GC") == "1":
                                gc.collect()
                            stats = State.instance_stats()
                            print(
                                f"{ended_at} [state] "
                                f"block={block_count} "
                                f"live={stats['live']} "
                                f"created={stats['created']} "
                                f"destroyed={stats['destroyed']} "
                                f"{_format_process_memory()} "
                                f"{_format_cgroup_memory()} "
                                f"{_format_cgroup_events()} "
                                f"{_format_gc_stats()} "
                                f"{_format_fd_stats()} "
                                f"{_format_process_io()} "
                                f"{_format_block_view(viewer)} "
                                f"{_format_db_sizes(settings._data_path)} "
                                f"{_format_db_file_breakdown(settings._data_path)} "
                                f"{_format_rocksdb_properties(settings)} "
                                f"{_format_log_dir_size()}"
                            )

                elif tag == TAG_INITIALIZE:
                    print(f"🔧 Received Initialize command ({len(payload)} bytes)")
                    try:
                        init_data = Initialize.decode(payload)
                        if record_enabled and json_data:
                            json_data["pre_state"] = init_data.keyvals.to_json()
                        
                        from jam.state.state import setup_state

                        # Clear ALL databases to avoid stale data from previous traces
                        # 1. Clear state DB (stale KV pairs)
                        for key in settings.state_db.get_all():
                            settings.state_db.delete(key)

                        # 2. Clear main DB (stale blocks, finality keys, StateRecords)
                        for key in settings.main_db.get_all():
                            settings.main_db.delete(key)

                        # 3. Reset BlockView singleton to clear in-memory block tree
                        from jam.block.block_view import viewer
                        viewer.initialize(settings.main_db)

                        # Convert State to dict for setup_state
                        state_dict = {kv.key: kv.value for kv in init_data.keyvals.keyvals}
                        state = setup_state(settings.state_db, state_dict)
                        print(f"✅ State initialized. Root: {state.root.hex()}")

                        # Finalize initial block
                        from jam.finality.finality import Finality
                        block = Block(init_data.header, Extrinsic.empty())
                        hh = block.save(settings.main_db)
                        Finality.set_head(block, settings.main_db)
                        Finality.finalise(block, settings.main_db)

                        send_message(conn, TAG_STATE_ROOT, state.root)
                    except Exception as e:
                        print(f"❌ Initialize failed: {e}", file=sys.stderr)
                        error_msg = ErrorMessage(message=String(f"Initialize failed: {str(e)}"))
                        send_message(conn, TAG_ERROR, error_msg.encode())
                
                elif tag == TAG_GET_STATE:
                    print(f"📤 Received GetState command ({len(payload)} bytes)")
                    print(f"📤 Received GetState payload: {payload.hex()}")
                    print(f"🔍 Current StateRoot: {state.root.hex()}")

                    try:
                        keyvals = TypedVector[KeyValue]([])
                        header_hash = HeaderHash(payload)
                        from jam.block.block_view import viewer, BlockStatus
                        if header_hash is not None:
                            block = viewer.load_ghost(header_hash)
                            if block.status == BlockStatus.audited:
                                st = State.load(block.header)
                                for key, val in st.transform().items():
                                    # Ensure key is 31 bytes
                                    key_31 = key[:31].ljust(31, b'\x00') if len(key) < 31 else key[:31]
                                    keyvals.append(KeyValue(key=Bytes[31](key_31), value=Bytes(val)))
                            elif block.status == BlockStatus.unaudited:
                                st = State.load(block.parent.header)
                                for key, val in st.transform().items():
                                    # Ensure key is 31 bytes
                                    key_31 = key[:31].ljust(31, b'\x00') if len(key) < 31 else key[:31]
                                    keyvals.append(KeyValue(key=Bytes[31](key_31), value=Bytes(val)))

                        # state_response = State(keyvals=keyvals)
                        state_response = keyvals
                        if record_enabled and json_data:
                            json_data["post_state"] = state_response.to_json()
                        
                        send_message(conn, TAG_STATE, state_response.encode())
                    except Exception as e:
                        print(f"❌ GetState failed: {e}", file=sys.stderr)
                        error_msg = ErrorMessage(message=String(f"GetState failed: {str(e)}"))
                        send_message(conn, TAG_ERROR, error_msg.encode())

                else:
                    print(f"❓ Received unexpected message with tag {tag}. Closing connection.", file=sys.stderr)
                    break

                print("\n---------\n")

async def run_fuzzer_target(
    db_path: str,
    socket_path: str = "/tmp/jam_conformance.sock",
    record_path: Optional[str] = None
) -> None:
    """
    Run the JAM fuzzer target server.
    
    Args:
        db_path: Path to database directory
        socket_path: Unix socket path to listen on
        record_path: Optional path to record session data
    """
    
    os.makedirs(db_path, exist_ok=True)

    from jam.log_setup import setup_logging
    setup_logging("default", "fuzzer-target")
    _print_fuzzer_system_info(db_path, socket_path, record_path)

    # Ensure the socket does not already exist
    if os.path.exists(socket_path):
        os.remove(socket_path)

    # Create a UDS socket
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    
    if not db_path.endswith("/"):
        db_path = db_path + "/"
        
    try:
        sock.bind(socket_path)
        os.chmod(socket_path, 0o777)
        sock.listen(1)
        print(f"🛰️  Tessera JAM Fuzzer Target | Listening on {sock.getsockname()}")
        run_fuzzer_target_loop(sock, db_path, record_path)
    except KeyboardInterrupt:
        print("\n🛑 Fuzzer target stopped by user")
    except Exception as e:
        print(f"❌ Fuzzer target error: {e}", file=sys.stderr)
        raise
    finally:
        sock.close()
        if os.path.exists(socket_path):
            os.remove(socket_path)
        print("🧹 Cleanup complete.")
