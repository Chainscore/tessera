import os
import re
import time as _time
from typing import TYPE_CHECKING, List, Optional

from jam.operations.dispatcher import NodeDispatcher
from jam.themes import Colors, RESET
from jam.utils.constants import (
    EPOCH_LENGTH,
    CORE_COUNT,
    VALIDATOR_COUNT,
    ROTATION_PERIOD,
    TICKET_SUBMISSION_END,
)

if TYPE_CHECKING:
    from jam.jam_node import JamNode

_ANSI_RE = re.compile(r"\033\[[0-9;]*m")
C = Colors
R = RESET


def _vlen(s: str) -> int:
    """Visible length of a string (strip ANSI codes)."""
    return len(_ANSI_RE.sub("", s))


def _peer_name(metadata_name) -> str:
    """Decode the 10-byte validator metadata name field."""
    try:
        raw = bytes(metadata_name)
        return raw.rstrip(b"\x00").decode("utf-8", errors="replace").strip() or "?"
    except Exception:
        return "?"


def _pad(text: str, width: int) -> str:
    """Pad *text* with spaces so its visible length equals *width*."""
    return text + " " * max(width - _vlen(text), 0)


def _truncate(text: str, width: int) -> str:
    """Truncate *text* to *width* visible characters."""
    vis = 0
    out: list[str] = []
    i = 0
    s = text
    while i < len(s):
        # Check for ANSI escape
        m = _ANSI_RE.match(s, i)
        if m:
            out.append(m.group())
            i = m.end()
            continue
        if vis >= width:
            break
        out.append(s[i])
        vis += 1
        i += 1
    return "".join(out)


class Monitor(NodeDispatcher):
    """
    Multi-column panel dashboard printed every slot.
    Auto-detects terminal width; 2-column layout.
    """

    def __init__(self, jam: "JamNode") -> None:
        super().__init__(jam)

    # ──────────────────────────────────────────────
    # Panel framing helpers
    # ──────────────────────────────────────────────

    @staticmethod
    def _make_panel(
        title: str,
        lines: List[str],
        width: int,
        stats: str = "",
    ) -> List[str]:
        """
        Wrap *lines* in a box of given *width* visible characters.

        Every line has exactly *width* visible chars:
          top:     " ┌─ title ───── stats ─┐"   (width)
          content: " │ text              │"   (width)
          bottom:  " └─────────────────────┘"   (width)
        """
        # content area: " │ " + inner + " │" = inner + 5
        inner = width - 5

        # ── top border ──
        title_str = f" {C.BOLD}{C.BCYAN}{title}{R} "
        title_vis = _vlen(title_str)
        if stats:
            stats_str = f" {C.DIM}{stats}{R} "
            stats_vis = _vlen(stats_str)
        else:
            stats_str = ""
            stats_vis = 0

        # " ┌" + dash_left + title + dash_right + stats + "┐" = width
        # 1 + 1 + dash_left + title_vis + dash_right + stats_vis + 1 = width
        dash_left = 1
        dash_right = max(width - 3 - dash_left - title_vis - stats_vis, 0)
        top = (
            f" {C.DIM}┌{'─' * dash_left}{R}{title_str}"
            f"{C.DIM}{'─' * dash_right}{R}{stats_str}{C.DIM}┐{R}"
        )

        # ── content rows ──
        rows = []
        for line in lines:
            vis = _vlen(line)
            pad = max(inner - vis, 0)
            rows.append(f" {C.DIM}│{R} {line}{' ' * pad} {C.DIM}│{R}")

        # ── bottom border ──
        # " └" + dashes + "┘" = 1 + 1 + dashes + 1 = width → dashes = width - 3
        bot = f" {C.DIM}└{'─' * (width - 3)}┘{R}"

        return [top] + rows + [bot]

    @staticmethod
    def _zip_panels(left: List[str], right: List[str]) -> List[str]:
        """Merge two panel column lists side-by-side with a single space gap."""
        height = max(len(left), len(right))
        # Pad shorter panel with blank lines of equal visible width
        if left:
            lw = _vlen(left[0])
        else:
            lw = 0
        if right:
            rw = _vlen(right[0])
        else:
            rw = 0
        while len(left) < height:
            left.append(" " * lw)
        while len(right) < height:
            right.append(" " * rw)

        return [f"{_pad(l, lw)} {r}" for l, r in zip(left, right)]

    # ──────────────────────────────────────────────
    # Panel builders
    # ──────────────────────────────────────────────

    def _build_status_panel(self, time_slot: int, width: int) -> List[str]:
        epoch = time_slot // EPOCH_LENGTH
        epoch_slot = time_slot % EPOCH_LENGTH
        remaining = EPOCH_LENGTH - epoch_slot

        from jam.utils.chainspec import chain_config

        name = chain_config.name
        v = chain_config.num_validators
        cc = chain_config.num_cores
        e = chain_config.epoch_duration

        lines = []
        lines.append(
            f"{C.BOLD}{C.BCYAN}◈ TESSERA{R}  {C.DIM}{name}{R}  "
            f"V:{C.BWHITE}{v}{R} C:{C.BWHITE}{cc}{R} E:{C.BWHITE}{e}{R}"
        )
        lines.append(
            f"Slot {C.BWHITE}{time_slot}{R}  "
            f"Epoch {C.BWHITE}{epoch}{R}  "
            f"Remaining: {C.BWHITE}{remaining}{R}"
        )

        # Flags
        flags = []
        if epoch_slot == 0:
            flags.append(f"{C.BOLD}{C.BWHITE}⚑ EPOCH CHANGED{R}")
        if epoch_slot < TICKET_SUBMISSION_END:
            flags.append(f"{C.BGREEN}● Tickets OPEN{R}")
        else:
            flags.append(f"{C.RED}● Tickets CLOSED{R}")
        lines.append("     ".join(flags))

        return self._make_panel("status", lines, width)

    def _build_cores_panel(self, time_slot: int, width: int) -> List[str]:
        lines = []
        inner = width - 4
        try:
            from jam.utils.assignment import assign_guarantors

            val_map, index_map = assign_guarantors(self.jam)

            # Rotation phase
            rot = (time_slot % EPOCH_LENGTH) // ROTATION_PERIOD if ROTATION_PERIOD else 0
            lines.append(f"{C.DIM}rot:{rot}{R}")

            # Core → validator list, compact
            core_strs = []
            for ci in sorted(index_map.keys()):
                vis = " ".join(f"v{int(vi)}" for vi in index_map[ci])
                core_strs.append(f" {C.BWHITE}{int(ci)}{R}: {C.DIM}{vis}{R}")

            # Fit cores on lines, ~2 cores per line
            line = ""
            for cs in core_strs:
                if _vlen(line) + _vlen(cs) + 4 > inner and line:
                    lines.append(line)
                    line = ""
                line += cs + "   "
            if line.strip():
                lines.append(line.rstrip())

            # Block author for this slot
            try:
                state = self.state
                gamma_s = state.gamma.s.unwrap()
                slot_idx = time_slot % EPOCH_LENGTH
                entry = gamma_s[slot_idx]
                # entry is either a TicketBody or BandersnatchPublic
                if hasattr(entry, "id"):
                    # TicketBody → show ticket id
                    tid = bytes(entry.id).hex()[:8]
                    lines.append(f"author  Ticket #{C.DIM}{tid}..{R}")
                else:
                    fbk = bytes(entry).hex()[:8]
                    lines.append(f"author  Fallback {C.DIM}{fbk}..{R}")
            except Exception:
                lines.append(f"author  {C.DIM}unknown{R}")

        except Exception:
            lines.append(f"{C.DIM}unavailable{R}")

        return self._make_panel("cores / author", lines, width)

    def _build_neighbors_panel(self, width: int, max_lines: int = 10) -> List[str]:
        lines = []
        stats = ""
        try:
            node = self.node
            state = self.state
            neighbor_keys = node.neighbors
            connected_keys = {
                conn.peer_ed_key for conn in node.all_connected if conn.peer_ed_key
            }
            n_connected = len(connected_keys & set(neighbor_keys))
            stats = f"{n_connected}/{len(neighbor_keys)}"

            our_key = self.settings.ed25519_public

            shown = 0
            for key in neighbor_keys:
                if shown >= max_lines:
                    remaining = len(neighbor_keys) - shown
                    lines.append(f"{C.DIM}+{remaining} more{R}")
                    break
                idx, val = state.kappa.find(key)
                if val is None:
                    continue
                name = _peer_name(val.metadata.name)
                port = int(val.metadata.port)
                connected = key in connected_keys
                dot = f"{C.BGREEN}●{R}" if connected else f"{C.RED}○{R}"
                name_color = C.BYELLOW if key == our_key else C.CYAN
                khex = key.hex()[:8]
                lines.append(
                    f"{dot} v{idx:<2} {name_color}{name:<12}{R} "
                    f":{C.DIM}{port:<5}{R}  {C.DIM}{khex}..{R}"
                )
                shown += 1
        except Exception:
            lines.append(f"{C.DIM}unavailable{R}")

        return self._make_panel("neighbors", lines, width, stats)

    def _build_validators_panel(self, width: int, max_lines: int = 10) -> List[str]:
        lines = []
        stats = ""
        try:
            node = self.node
            state = self.state
            all_conns = node.all_connected
            our_key = self.settings.ed25519_public

            # Build lookup: ed_key → connection info
            conn_map = {}
            for conn in all_conns:
                if conn.peer_ed_key:
                    role = "init" if conn.is_initiator else "resp"
                    up0 = f"{C.BGREEN}✓{R}" if conn.up0_stream is not None else f"{C.RED}✗{R}"
                    port = int(conn.port) if conn.port else 0
                    conn_map[conn.peer_ed_key] = (role, up0, port)

            up0_count = sum(
                1 for conn in all_conns if conn.up0_stream is not None
            )
            connected_count = len(conn_map)
            total_v = len(state.kappa)
            stats = f"{connected_count}/{total_v} up0:{up0_count}"

            shown = 0
            for idx, val in enumerate(state.kappa):
                if shown >= max_lines:
                    remaining = total_v - shown
                    lines.append(f"{C.DIM}+{remaining} more{R}")
                    break

                ed_key = val.ed25519
                name = _peer_name(val.metadata.name)
                is_us = ed_key == our_key
                name_color = C.BYELLOW if is_us else C.CYAN

                info = conn_map.get(ed_key)
                if info:
                    role, up0, port = info
                    dot = f"{C.BGREEN}●{R}"
                    detail = f"{role} {up0}  :{C.DIM}{port}{R}"
                elif is_us:
                    dot = f"{C.BGREEN}●{R}"
                    port = int(self.settings.port)
                    detail = f"{C.DIM}(self) :{port}{R}"
                else:
                    dot = f"{C.RED}◌{R}"
                    detail = ""

                lines.append(
                    f"{dot} v{idx:<2} {name_color}{name:<12}{R} {detail}"
                )
                shown += 1
        except Exception:
            lines.append(f"{C.DIM}unavailable{R}")

        return self._make_panel("validators", lines, width, stats)

    def _build_rpc_panel(self, width: int) -> List[str]:
        lines = []
        stats = ""
        rpc_on = False
        try:
            rpc_on = self.settings.rpc_flag
        except Exception:
            pass

        if not rpc_on:
            return self._make_panel("rpc", [f"{C.DIM}disabled{R}"], width)

        try:
            tracker = self.responder.active_subscriptions
            ts = tracker.get_stats()
            active = ts["active_subscriptions"]
            num_conns = ts["by_connection"]
            stats = f"{num_conns} ws"

            by_method = ts.get("by_method", {})
            lines.append(f"subs: {C.BWHITE}{active}{R}  methods: {C.BWHITE}{len(by_method)}{R}")
            for method, count in by_method.items():
                short = method.replace("subscribe", "")
                lines.append(f" {C.GREEN}{short:<22}{R} {count}")

            # Connection details
            by_conn = tracker._by_connection
            if by_conn:
                lines.append(f"conns:")
                conn_parts = []
                for cid, subs in by_conn.items():
                    short_id = cid[:4] if len(cid) >= 4 else cid
                    n = len(subs)
                    label = "sub" if n == 1 else "subs"
                    conn_parts.append(f" {C.DIM}{short_id}{R}: {n} {label}")
                lines.append("  ".join(conn_parts))
        except Exception:
            lines.append(f"{C.DIM}unavailable{R}")

        return self._make_panel("rpc", lines, width, stats)

    def _build_broker_panel(self, width: int) -> List[str]:
        lines = []
        stats = ""
        rpc_on = False
        try:
            rpc_on = self.settings.rpc_flag
        except Exception:
            pass

        if not rpc_on:
            return self._make_panel("broker", [f"{C.DIM}disabled{R}"], width)

        try:
            broker = self.responder.broker
            topics = broker._topics
            num_topics = len(topics)
            num_subs = sum(len(q) for q in topics.values())
            stats = f"{num_topics}t {num_subs}s"

            history = broker._history
            if history:
                for ts, method, delivered in reversed(history):
                    t = _time.strftime("%H:%M:%S", _time.localtime(ts))
                    short = method.replace("subscribe", "")
                    lines.append(
                        f"{C.DIM}{t}{R} {C.GREEN}{short:<18}{R} → {C.BWHITE}{delivered}{R}"
                    )
            else:
                lines.append(f"{C.DIM}no events yet{R}")
        except Exception:
            lines.append(f"{C.DIM}unavailable{R}")

        return self._make_panel("broker", lines, width, stats)

    # ──────────────────────────────────────────────
    # Main entry point
    # ──────────────────────────────────────────────

    async def run(self, time_slot: int):
        try:
            cols = os.get_terminal_size().columns
        except OSError:
            cols = 120

        # 2-column layout: each panel gets half minus gap
        pw = max((cols - 3) // 2, 40)

        # Row 1: status | cores
        p_status = self._build_status_panel(time_slot, pw)
        p_cores = self._build_cores_panel(time_slot, pw)
        row1 = self._zip_panels(p_status, p_cores)

        # Row 2: neighbors | validators
        p_neighbors = self._build_neighbors_panel(pw)
        p_validators = self._build_validators_panel(pw)
        row2 = self._zip_panels(p_neighbors, p_validators)

        # Row 3: rpc | broker
        p_rpc = self._build_rpc_panel(pw)
        p_broker = self._build_broker_panel(pw)
        row3 = self._zip_panels(p_rpc, p_broker)

        output = "\n".join(row1 + row2 + row3)
        self.logger.info("\n" + output)
