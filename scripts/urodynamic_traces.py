#!/usr/bin/env python3
"""Synthetic urodynamic tracings for the urodynamics lab (data/urodynamic-tracings.json).

Each tracing comes from a small deterministic model that follows the conventions of the
International Continence Society (ICS):

* Pdet = Pves − Pabd. Coughs, straining and breathing reach both lines equally, so a well
  transmitted cough leaves only a small blip in Pdet. Rectal contractions reach Pabd only and
  therefore swing Pdet negative.
* Bladder filling raises Pdet according to compliance (ΔV/ΔPdet); detrusor overactivity is a
  phasic rise of Pdet, sometimes with leakage that the flowmeter registers.
* During voiding, urine flows once Pdet exceeds the opening pressure and Pdet = Popen + R·Q²,
  which ties the pressure at maximum flow (PdetQmax) to Qmax as in a pressure-flow study.

The curves are teaching drawings, not recordings of real patients. Every value a question asks
the player to read is pinned in the data and listed under "readings"; scripts/manage.py checks
the readings against the curves whenever it validates the game.

    python scripts/urodynamic_traces.py          # rewrite data/urodynamic-tracings.json
    python scripts/urodynamic_traces.py --check  # exit 1 if the file is out of date
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "urodynamic-tracings.json"
DT = 0.25  # model resolution in seconds; the stored curves keep fewer, shape-preserving samples
REST = {"sitting": (31.0, 3.0), "supine": (12.0, 2.0), "standing": (38.0, 3.0)}  # resting Pabd and Pdet, cmH2O
DIGITS = {"pves": 1, "pabd": 1, "flow": 1, "vinf": 0, "vvoid": 0, "emg": 0}
# Largest vertical error the simplified curve may show in each channel.
TOLERANCE = {"pves": 0.6, "pabd": 0.6, "pdet": 0.6, "flow": 0.15, "vinf": 1.0, "vvoid": 1.0, "emg": 2.5}
MAX_GAP = 4.0  # seconds; keeps the cursor readout smooth on long flat stretches


def L(en: str, de: str, es: str) -> dict:
    return {"en": en, "de": de, "es": es}


def smoothstep(x: float) -> float:
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


SKEW = 0.8
PEAK = 0.5 ** (1 / SKEW)  # where hump() peaks


def hump(x: float, skew: float = SKEW) -> float:
    """A smooth single wave on 0..1 that rises a little faster than it falls."""
    if x <= 0 or x >= 1:
        return 0.0
    return math.sin(math.pi * x ** skew) ** 2


# A cough rises and falls within about one second.
COUGH = ((-0.25, 0.0), (0.0, 0.32), (0.25, 0.88), (0.5, 1.0), (0.75, 0.46), (1.0, 0.13), (1.25, 0.0))


def cough_shape(d: float) -> float:
    for (x0, y0), (x1, y1) in zip(COUGH, COUGH[1:]):
        if x0 <= d <= x1:
            return y0 + (y1 - y0) * (d - x0) / (x1 - x0)
    return 0.0


# Where the pelvic floor contracts during a staccato void (fractions of the flow time); the EMG bursts there too.
STACCATO = (0.16, 0.29, 0.42, 0.55, 0.68, 0.81)


def flow_shape(kind: str, u: float) -> float:
    """Flow curve on 0..1 with a peak near 1: the shapes that ICS teaching material names."""
    if u <= 0 or u >= 1:
        return 0.0
    if kind == "bell":  # normal: quick rise, peak in the first third, smooth decline
        a, b = 1.15, 2.1
    elif kind == "prolonged":  # compressive obstruction or weak detrusor: low, flat and long
        a, b = 0.85, 1.75
    elif kind == "plateau":  # constrictive obstruction such as a stricture: box-like
        return smoothstep(u / 0.07) * smoothstep((1 - u) / 0.09) * (0.985 + 0.015 * math.sin(2 * math.pi * 7 * u))
    elif kind == "staccato":  # dysfunctional voiding: continuous, with sharp peaks and troughs that never reach zero
        base = flow_shape("bell", u)
        level = 1.0
        for centre in STACCATO:
            level *= 1 - 0.56 * math.exp(-((u - centre) / 0.024) ** 2)
            level += 0.13 * math.exp(-((u - centre - 0.045) / 0.016) ** 2)
        return base * level
    else:
        raise ValueError(kind)
    return (u ** a * (1 - u) ** b) / ((a / (a + b)) ** a * (b / (a + b)) ** b)


class Study:
    """One urodynamic study on a fixed time grid. Components add up; finish() returns the stored curves."""

    def __init__(self, seed: str, duration: float, position: str = "sitting", *, pabd_rest: float | None = None,
                 pdet_rest: float | None = None, emg: bool = True):
        self.rng = random.Random(seed)
        self.n = int(round(duration / DT)) + 1
        self.t = [k * DT for k in range(self.n)]
        rest_abd, rest_det = REST[position]
        self.pabd_rest = rest_abd if pabd_rest is None else pabd_rest
        self.pdet_rest = rest_det if pdet_rest is None else pdet_rest
        self.both = [0.0] * self.n       # transients that reach both lines (coughs, straining)
        self.ves_only = [0.0] * self.n   # imperfect cough transmission into the vesical line
        self.abd_only = [0.0] * self.n   # rectal contractions
        self.waves: list[dict] = []      # detrusor contractions during filling
        self.absolute = [None] * self.n  # detrusor pressure during voiding (absolute, cmH2O)
        self.flow = [0.0] * self.n
        self.vinf = [0.0] * self.n
        self.restarts: set[int] = set()  # bladder emptied through the catheter: volume starts again at zero
        self.void_starts: set[int] = set()  # the flowmeter's voided volume starts again at each void
        self.emg = emg
        self.bursts = [0.0] * self.n     # pelvic floor EMG activity added on top of the resting level
        self.emg_factor = [1.0] * self.n
        self.events: list[dict] = []
        self.keep: set[int] = {0, self.n - 1}
        self.pins: list[tuple] = []
        self.damp: tuple[int, float, int] | None = None
        self.lost: list[tuple[int, int]] = []
        self.busy: list[tuple[float, float]] = []  # waves, voids and straining: no cough test inside (see clear())
        phase = self.rng.uniform(0, 2 * math.pi)
        self.common = [0.8 * math.sin(2 * math.pi * x / 4.2 + phase) + 0.5 * math.sin(2 * math.pi * x / 97 + phase / 2)
                       for x in self.t]

    def i(self, t: float) -> int:
        return max(0, min(self.n - 1, int(round(t / DT))))

    def event(self, t: float, kind: str, **extra) -> float:
        k = self.i(t)
        self.keep.add(k)
        self.events.append({"t": round(k * DT, 2), "type": kind, **extra})
        return k * DT

    def clear(self, x: float, gap: float = 6.0) -> float:
        """The time nearest to x, in 5 s steps, that is at least gap seconds from every marker and outside every
        detrusor wave, rectal wave, void and straining episode. A cough on a marker would make the cursor read the
        cough there, and a cough just before a wave would look like cough-associated overactivity (ICS GUP 2016)."""
        marks = [e["t"] for e in self.events if e["type"] != "cough"]

        def free(y: float) -> bool:
            return all(abs(y - m) >= gap for m in marks) and all(not a <= y <= b for a, b in self.busy)

        for shift in (0, 5, -5, 10, -10, 15, -15, 20, -20, 25, -25, 30, -30):
            if 0 < x + shift < self.t[-1] and free(x + shift):
                return x + shift
        raise ValueError(f"no free time for a cough near {x} s")

    # --- storage phase -------------------------------------------------------------------
    def fill(self, t0: float, volume: float, rate: float) -> float:
        """Infuse at rate ml/min from t0 until volume is reached; returns the end time."""
        t1 = t0 + volume / rate * 60
        i0, i1 = self.i(t0), self.i(t1)
        for k in range(i0, self.n):
            self.vinf[k] = rate / 60 * (min(k, i1) - i0) * DT
        self.keep.update({i0, i1})
        return i1 * DT

    def empty(self, t: float) -> None:
        """Drain the bladder through the catheter; infused volume and outflow start again at zero."""
        k0 = self.i(t)
        for k in range(k0, self.n):
            self.vinf[k] = 0.0
        self.restarts.add(k0)
        self.keep.add(k0)

    def cough(self, t: float, amp: float, *, leak: float = 0.0, mismatch: float | None = None) -> None:
        """A cough test; leak is the volume (ml) that escapes with it."""
        m = self.rng.uniform(-0.04, 0.05) if mismatch is None else mismatch
        for k in range(self.i(t - 0.5), self.i(t + 1.5) + 1):
            s = cough_shape(self.t[k] - t)
            self.both[k] += amp * s
            self.ves_only[k] += amp * s * m
            self.bursts[k] += 36 * s
        if leak:
            self.leak(t + 0.75, 1.75, leak)
            self.event(t + 0.75, "leak")
        self.event(t, "cough")
        self.keep.add(self.i(t + 0.5))

    def valsalva(self, t: float, amp: float, duration: float, *, leak_at: float, leak: float) -> int:
        """Straining with a ramp; leakage (ml) starts once the abdominal rise reaches leak_at. Returns that index."""
        end = t + duration
        self.busy.append((t - 3, end + 4))
        leak_index = -1
        for k in range(self.i(t), self.i(end + 1.5) + 1):
            x = self.t[k]
            level = smoothstep((x - t) / (duration * 0.6)) * (1 - smoothstep((x - end) / 1.2))
            self.both[k] += amp * level
            if leak_index < 0 and amp * level >= leak_at:
                leak_index = k
        self.leak(self.t[leak_index] + 0.25, end - self.t[leak_index], leak)
        self.keep.add(leak_index)
        self.event(t, "valsalva")
        self.event(self.t[leak_index], "leak")
        return leak_index

    def rectal(self, t: float, amp: float, duration: float) -> None:
        self.busy.append((t - 3, t + duration + 3))
        for k in range(self.i(t), self.i(t + duration) + 1):
            self.abd_only[k] += amp * hump((self.t[k] - t) / duration, 0.9)
        self.keep.add(self.i(t + duration * 0.45))

    def contraction(self, t: float, duration: float, *, peak: float | None = None, amp: float | None = None,
                    leak: float = 0.0, urgency: bool = True, emg: float = 0.0) -> float:
        """Phasic detrusor overactivity. peak is the absolute Pdet at the top of the wave; amp a rise above the baseline;
        leak the volume (ml) that escapes during the wave."""
        self.waves.append({"k0": self.i(t), "k1": self.i(t + duration), "t": t, "duration": duration, "peak": peak, "amp": amp})
        self.busy.append((t - 6, t + duration + 3))
        top = t + duration * PEAK
        self.keep.add(self.i(top))
        if emg:
            for k in range(self.i(t), self.i(t + duration) + 1):
                self.bursts[k] += emg * hump((self.t[k] - t) / duration) * (0.7 + 0.3 * math.sin(self.t[k] * 4.7))
        if urgency:
            self.event(t + duration * 0.22, "urgency")
        if leak:
            self.leak(t + duration * 0.36, duration * 0.48, leak)
            self.event(t + duration * 0.4, "leak")
        return self.i(top) * DT

    def leak(self, t: float, duration: float, volume: float) -> None:
        """Leakage of exactly volume ml, shaped as a short wave on the flowmeter."""
        ks = range(self.i(t), self.i(t + duration) + 1)
        shape = [hump((self.t[k] - t) / duration, 0.7) for k in ks]
        scale = volume / (sum(shape) * DT)
        for k, x in zip(ks, shape):
            self.flow[k] += scale * x

    # --- voiding phase -------------------------------------------------------------------
    def void(self, t: float, *, qmax: float, voided: float, pdet_qmax: float = 0.0, popen: float = 0.0,
             shape: str = "bell", opening: float = 7.0, relax: float = 6.0, emg: str = "quiet", marker: bool = True) -> dict:
        """Permission to void at t. Flow follows `shape` with exactly qmax and voided; Pdet = Popen + R·Q² during flow."""
        if marker:
            self.event(t, "void")
        self.void_starts.add(self.i(t))
        start = t + opening
        mean = sum(flow_shape(shape, (j + 0.5) / 400) for j in range(400)) / 400
        duration = voided / (qmax * mean)
        q = []
        for _ in range(8):  # sampling moves the area a little; converge on the voided volume
            q = [flow_shape(shape, (x - start) / duration) for x in self.t]
            top = max(q)
            q = [v * qmax / top for v in q]
            duration *= voided / (sum(q) * DT)
        q = [flow_shape(shape, (x - start) / duration) for x in self.t]
        peak = max(range(self.n), key=lambda k: q[k])
        q = [v * qmax / q[peak] for v in q]
        others = sum(v for k, v in enumerate(q) if k != peak) * DT
        factor = (voided - qmax * DT) / others
        q = [qmax if k == peak else v * factor for k, v in enumerate(q)]
        r = (pdet_qmax - popen) / qmax ** 2
        end = start + duration
        i_end = self.i(end)
        self.busy.append((t - 4, end + 4))
        for k in range(self.i(t), self.n):
            x = self.t[k]
            if x < start:
                level = popen * smoothstep((x - t) / opening)
            elif k <= i_end:
                level = popen + r * q[k] ** 2
            else:
                level = popen * math.exp(-(x - end) / relax)
            if level > 0.05:
                self.absolute[k] = max(self.absolute[k] or 0.0, level)
            self.flow[k] += q[k]
            # The striated sphincter relaxes at permission to void, before the detrusor pressure rises (Yalla and
            # Resnick 1997), stays quiet while urine flows and regains its tone afterwards.
            if emg == "quiet" and t <= x <= end + 5:
                if x < t + 1.5:
                    quiet = 1 - 0.82 * smoothstep((x - t) / 1.5)
                elif x <= end + 3:
                    quiet = 0.18
                else:
                    quiet = 0.18 + 0.82 * smoothstep((x - end - 3) / 2)
                self.emg_factor[k] = min(self.emg_factor[k], quiet)
        self.keep.update({peak, self.i(start), i_end})
        return {"t": t, "peak": peak, "tpeak": peak * DT, "start": start, "end": end}

    def strain(self, t: float, amp: float, duration: float) -> None:
        """Abdominal straining: both lines rise together, so Pdet does not change."""
        self.busy.append((t - 2, t + duration + 3))
        for k in range(self.i(t - 0.5), self.i(t + duration + 1.5) + 1):
            x = self.t[k]
            self.both[k] += amp * smoothstep((x - t) / 1.2) * (1 - smoothstep((x - t - duration) / 1.2))
        self.keep.update({self.i(t + 1.2), self.i(t + duration)})

    def dampen(self, t: float, tau: float, until: float | None = None) -> None:
        """An air bubble in the vesical line from t until the line is flushed: Pves follows changes only through a
        low-pass filter."""
        self.damp = (self.i(t), tau, self.i(until) if until is not None else self.n)

    def lose_catheter(self, t0: float, t1: float) -> None:
        """The vesical catheter has slipped out until t1: Pves drops suddenly, usually well below zero (ICS GUP 2016;
        NBT artefact slides), and no longer follows a cough."""
        self.lost.append((self.i(t0), self.i(t1)))
        self.keep.update({self.i(t0), self.i(t1)})

    def emg_bursts_at(self, times: list, amp: float, width: float) -> None:
        for centre in times:
            for k in range(self.i(centre - 3 * width), self.i(centre + 3 * width) + 1):
                self.bursts[k] += amp * math.exp(-((self.t[k] - centre) / width) ** 2)
            self.keep.add(self.i(centre))

    def pin(self, t: float, channel: str, value: float) -> None:
        """Make one reading exact. The model already passes close to it; the pin only removes noise and rounding."""
        self.pins.append(("at", self.i(t), channel, value))
        self.keep.add(self.i(t))

    def pin_peak(self, t0: float, t1: float, channel: str, value: float, *, base: float) -> None:
        """Scale the excursion of channel between t0 and t1 around its level at time base, so that the highest sample
        (found after damping) becomes value. Pinning that one sample alone would leave its neighbours above it."""
        if channel == "pdet":
            raise ValueError("pin_peak works on a recorded channel")
        self.pins.append(("peak", (self.i(t0), self.i(t1), self.i(base)), channel, value))

    # --- assembly --------------------------------------------------------------------------
    def finish(self, compliance=None, *, capacity: float | None = None) -> dict:
        """compliance(V) gives the passive rise of Pdet with bladder volume V; a list of (t, function) switches by time."""
        rng = self.rng
        segments = compliance if isinstance(compliance, list) else [(0.0, compliance or (lambda v: v / 120))]
        outflow, volume = 0.0, []
        for k in range(self.n):
            if k in self.restarts:
                outflow = 0.0
            outflow += self.flow[k] * DT
            volume.append(max(0.0, self.vinf[k] - outflow))
        base = []
        for k in range(self.n):
            passive = [f for start, f in segments if self.t[k] >= start][-1]
            base.append(self.pdet_rest + max(0.0, passive(volume[k])))
        det = list(base)
        for wave in self.waves:
            top = self.i(wave["t"] + wave["duration"] * PEAK)
            amp = wave["amp"] if wave["amp"] is not None else wave["peak"] - base[top]
            for k in range(wave["k0"], wave["k1"] + 1):
                det[k] += amp * hump((self.t[k] - wave["t"]) / wave["duration"])
        for k, level in enumerate(self.absolute):
            if level is not None:
                det[k] = max(det[k], level)
        cap = capacity or max(volume) or 1.0
        pabd, pves, emg = [], [], []
        for k in range(self.n):
            abd = self.pabd_rest + self.common[k] + self.both[k] + self.abd_only[k] + rng.gauss(0, 0.1)
            ves = self.pabd_rest + self.common[k] + self.both[k] + self.ves_only[k] + det[k] + rng.gauss(0, 0.1)
            pabd.append(abd)
            pves.append(ves)
            resting = (4.5 + 9 * min(1.0, volume[k] / cap)) * self.emg_factor[k]
            emg.append(max(1.0, resting + self.bursts[k] + rng.gauss(0, 1.0)))
        if self.damp:
            start, tau, stop = self.damp
            for k in range(start, stop):
                pves[k] = pves[k - 1] + (DT / tau) * (pves[k] - pves[k - 1])
        for k0, k1 in self.lost:
            for k in range(k0, k1 + 1):
                pves[k] = -10.0 + rng.gauss(0, 0.3)
        vvoid, total = [], 0.0
        void_starts = {self.i(e["t"]) for e in self.events if e["type"] == "void"} | self.void_starts | self.restarts
        for k in range(self.n):
            if k in void_starts:
                total = 0.0
            total += self.flow[k] * DT  # the flowmeter collects voided urine and leakage alike
            vvoid.append(total)
        curves = {"pves": pves, "pabd": pabd, "flow": self.flow, "vinf": self.vinf, "vvoid": vvoid}
        if self.emg:
            curves["emg"] = emg
        resolved = []
        for kind, where, channel, value in self.pins:  # in order: a peak scales around levels pinned before it
            if kind == "peak":
                k0, k1, kb = where
                values = curves[channel]
                where = max(range(k0, k1 + 1), key=lambda k: values[k])
                level = values[kb]
                factor = (value - level) / (values[where] - level)
                for k in range(k0, k1 + 1):
                    values[k] = level + (values[k] - level) * factor
            if channel == "pdet":
                curves["pves"][where] = curves["pabd"][where] + value
            else:
                curves[channel][where] = value
            resolved.append((where, channel, value))
            self.keep.add(where)
        keep = simplify(self.t, curves, self.keep)
        stored = {"t": [round(self.t[k], 2) for k in keep]}
        for name, values in curves.items():
            digits = DIGITS[name]
            stored[name] = [round(values[k], digits) if digits else int(round(values[k])) for k in keep]
        index = {k: j for j, k in enumerate(keep)}
        for k, channel, value in resolved:  # rounding must not move a pinned reading
            j = index[k]
            if channel == "pdet":
                stored["pves"][j] = round(stored["pabd"][j] + value, 1)
            else:
                stored[channel][j] = round(value, DIGITS[channel]) if DIGITS[channel] else int(round(value))
        stored["events"] = sorted(self.events, key=lambda e: (e["t"], e["type"]))
        return stored


def simplify(t: list, curves: dict, keep: set) -> list:
    """Multi-channel Ramer–Douglas–Peucker: drop samples every channel can interpolate within tolerance."""
    pdet = [v - a for v, a in zip(curves["pves"], curves["pabd"])]
    series = [(values, TOLERANCE[name]) for name, values in curves.items()] + [(pdet, TOLERANCE["pdet"])]
    n = len(t)
    marked = [False] * n
    for k in keep:
        marked[k] = True
    marked[0] = marked[-1] = True
    anchors = [k for k in range(n) if marked[k]]
    stack = list(zip(anchors, anchors[1:]))
    while stack:
        a, b = stack.pop()
        if b - a < 2:
            continue
        worst, where = 0.0, -1
        for k in range(a + 1, b):
            f = (t[k] - t[a]) / (t[b] - t[a])
            err = max(abs(values[k] - (values[a] + (values[b] - values[a]) * f)) / tol for values, tol in series)
            if err > worst:
                worst, where = err, k
        if worst > 1.0 or t[b] - t[a] > MAX_GAP:
            if worst <= 1.0:
                where = (a + b) // 2
            marked[where] = True
            stack.append((a, where))
            stack.append((where, b))
    return [k for k in range(n) if marked[k]]


# --- helpers for the cases ----------------------------------------------------------------------

def coughs_every(study: Study, t0: float, t1: float, step: float = 60.0, amp: float = 95.0) -> None:
    """A cough test about every minute during filling (NBT: every minute or 50 ml), moved off markers and waves.
    Register markers, waves and voids before calling it."""
    x = t0
    while x <= t1:
        study.cough(study.clear(x), amp * study.rng.uniform(0.88, 1.1))
        x += step


def bracket_void(study: Study, void: dict, amp: float = 92.0, *, before: float = 8.0, after: float = 7.0) -> None:
    """Cough tests immediately before permission to void and after the flow ends (NBT); GUP 2016: a cough check of
    the catheter position is always required after pressure-flow."""
    if before:
        study.cough(void["t"] - before, amp)
    if after:
        study.cough(void["end"] + after, amp)


def at_volume(rate: float, volume: float, t0: float = 20.0) -> float:
    return t0 + volume / rate * 60


def sensations(study: Study, rate: float, fs: float | None, fd: float | None, sd: float | None, t0: float = 20.0) -> None:
    for kind, vol in (("fs", fs), ("fd", fd), ("sd", sd)):
        if vol:
            study.event(at_volume(rate, vol, t0), kind)


def compliance(c: float):
    """Linear passive rise of Pdet: c ml per cmH2O."""
    return lambda v: v / c


def window(view_id: str, label: dict, t0: float, t1: float) -> dict:
    return {"id": view_id, "label": label, "t": [round(max(0.0, t0), 2), round(t1, 2)]}


ALL = {"id": "all", "label": L("Whole study", "Gesamte Messung", "Estudio completo")}


def fill_view(t1: float) -> dict:
    return window("fill", L("Filling", "Füllphase", "Llenado"), 0, t1)


def void_view(t0: float, t1: float) -> dict:
    return window("void", L("Voiding", "Miktion", "Micción"), t0, t1)


def span(step: str, t0: float, t1: float, label: dict, channel: str | None = None, tone: str = "key") -> dict:
    item = {"step": step, "kind": "span", "t0": round(t0, 2), "t1": round(t1, 2), "label": label, "tone": tone}
    if channel:
        item["channel"] = channel
    return item


def point(step: str, t: float, channel: str, label: dict, tone: str = "key") -> dict:
    return {"step": step, "kind": "point", "t": round(t, 2), "channel": channel, "label": label, "tone": tone}


def same(text: str) -> dict:
    return L(text, text, text)


def pressure_flow(s: Study, t: float, **void) -> dict:
    """A void with its pressure-flow reading pinned and the Qmax marker the software sets."""
    info = s.void(t, **void)
    s.pin(info["tpeak"], "flow", void["qmax"])
    s.pin(info["tpeak"], "pdet", void["pdet_qmax"])
    s.event(info["tpeak"], "qmax")
    return info


# --------------------------------------------------------------------------------------------
# The cases. Each function returns the stored tracing for one case of the urodynamics lab.
# --------------------------------------------------------------------------------------------

def bpo_indices() -> dict:
    """Obstruction with normal contractility before HoLEP: PdetQmax 82 cmH2O at Qmax 9 ml/s."""
    s = Study("udy-bpo", 670)
    rate, cap = 50, 400
    end = s.fill(20, cap, rate)
    s.cough(8, 92)
    sensations(s, rate, 160, 250, 380)
    coughs_every(s, 80, end - 10)
    s.cough(end + 8, 96)
    v = pressure_flow(s, end + 20, qmax=9.0, voided=340, pdet_qmax=82, popen=57, shape="prolonged", opening=9)
    s.cough(v["end"] + 6, 90)
    data = s.finish(compliance(95))
    data.update(kind="pressure-flow", fillingRate=rate, position="sitting",
                views=[ALL, fill_view(end + 15), void_view(end + 12, v["end"] + 12)],
                steps={"classify": "void", "counsel": "void"},
                annotations=[point("classify", v["tpeak"], "pdet", same("PdetQmax 82 cmH2O")),
                             point("classify", v["tpeak"], "flow", same("Qmax 9 ml/s")),
                             span("classify", v["start"], v["end"], same("BOOI 82 − 2 × 9 = 64 · BCI 82 + 5 × 9 = 127"), "pdet")],
                readings={"capacity": cap, "qmax": 9.0, "pdetQmax": 82, "pvesQmax": 113, "pabdQmax": 31, "voided": 340, "residual": 60})
    return data


def dhic() -> dict:
    """Detrusor overactivity during filling, a weak contraction during voiding, no obstruction."""
    s = Study("udy-dhic", 730)
    rate, cap = 50, 420
    end = s.fill(20, cap, rate)
    s.cough(8, 90)
    sensations(s, rate, 140, 200, None)
    t210 = at_volume(rate, 210)
    tops = [s.contraction(t210 + offset, dur, peak=peak) for offset, peak, dur in
            ((3, 19, 18), (48, 24, 20), (96, 28, 22), (146, 30, 24), (196, 27, 22))]
    s.pin(tops[3], "pdet", 30.0)
    v = pressure_flow(s, end + 18, qmax=5.0, voided=160, pdet_qmax=24, popen=18, shape="prolonged", opening=10)
    coughs_every(s, 80, end - 15, amp=88)  # between the waves, so that none of them looks cough-associated
    bracket_void(s, v, 88, before=9)
    data = s.finish(compliance(130))
    data.update(kind="pressure-flow", fillingRate=rate, position="sitting",
                views=[ALL, fill_view(end + 12), void_view(end + 10, v["end"] + 12)],
                steps={"pattern": "all", "turp": "void", "plan": "all"},
                annotations=[span("pattern", t210, end, L("Detrusor overactivity from 210 ml, up to 30 cmH2O, with urgency",
                                                            "Detrusorüberaktivität ab 210 ml, bis 30 cmH2O, mit Drang",
                                                            "Hiperactividad del detrusor desde 210 ml, hasta 30 cmH2O, con urgencia"), "pdet"),
                             point("pattern", v["tpeak"], "pdet", same("PdetQmax 24")),
                             point("pattern", v["tpeak"], "flow", L("Qmax 5 · BOOI 14 · BCI 49", "Qmax 5 · BOOI 14 · BCI 49", "Qmax 5 · BOOI 14 · BCI 49"))],
                readings={"capacity": cap, "qmax": 5.0, "pdetQmax": 24, "voided": 160, "residual": 260,
                          "overactivityFrom": 210, "overactivityMax": 30})
    return data


def pbno() -> dict:
    """Primary bladder neck obstruction: high pressure, low flow, silent pelvic floor EMG."""
    s = Study("udy-pbno", 690)
    rate, cap = 50, 380
    end = s.fill(20, cap, rate)
    s.cough(8, 100)
    sensations(s, rate, 150, 240, 360)
    v = pressure_flow(s, end + 15, qmax=6.0, voided=310, pdet_qmax=96, popen=79, shape="prolonged", opening=11)
    coughs_every(s, 80, end - 10, amp=100)
    s.cough(v["end"] + 6, 96)
    bracket_void(s, v, 98, after=0)
    data = s.finish(compliance(110))
    data.update(kind="video-pressure-flow", fillingRate=rate, position="sitting",
                views=[ALL, fill_view(end + 10), void_view(end + 8, v["end"] + 12)],
                steps={"localise": "void", "treat": "void"},
                annotations=[point("localise", v["tpeak"], "pdet", same("PdetQmax 96")),
                             point("localise", v["tpeak"], "flow", same("Qmax 6 · BOOI 84")),
                             span("localise", v["t"], v["end"], L("Pelvic floor EMG silent while voiding", "Beckenboden-EMG während der Miktion stumm",
                                                                      "EMG del suelo pélvico silente durante la micción"), "emg")],
                readings={"capacity": cap, "qmax": 6.0, "pdetQmax": 96, "voided": 310, "residual": 70})
    return data


def msa() -> dict:
    """Parkinsonism: overactivity with leakage from 120 ml and a weak, unobstructed contraction."""
    s = Study("udy-msa", 560)
    rate, cap = 50, 320
    end = s.fill(20, cap, rate)
    s.cough(8, 85)
    sensations(s, rate, 90, 120, None)
    t120 = at_volume(rate, 120)
    s.contraction(t120 + 4, 18, peak=22)
    s.contraction(t120 + 66, 22, peak=37, leak=8)
    s.contraction(t120 + 128, 24, peak=42, leak=12)
    v = pressure_flow(s, end + 12, qmax=6.0, voided=110, pdet_qmax=28, popen=21, shape="prolonged", opening=9)
    coughs_every(s, 80, end - 20, amp=85)
    bracket_void(s, v, 85, before=7)
    data = s.finish(compliance(120))
    data.update(kind="video-pressure-flow", fillingRate=rate, position="sitting",
                views=[ALL, fill_view(end + 8), void_view(end + 6, v["end"] + 12)],
                steps={"vuds": "all", "letter": "all"},
                annotations=[span("vuds", t120, end, L("Overactivity from 120 ml with leakage", "Detrusorüberaktivität ab 120 ml mit Leckage",
                                                       "Hiperactividad desde 120 ml con escape"), "pdet"),
                             point("vuds", v["tpeak"], "pdet", same("PdetQmax 28 · BOOI 16")),
                             point("vuds", v["tpeak"], "flow", same("Qmax 6"))],
                readings={"capacity": cap, "leaked": 20, "qmax": 6.0, "pdetQmax": 28, "voided": 110, "residual": 190, "overactivityFrom": 120})
    return data


def female_boo() -> dict:
    """Obstruction after a midurethral sling: PdetQmax 52 cmH2O at Qmax 7 ml/s, quiet EMG."""
    s = Study("udy-sling", 690)
    rate, cap = 50, 400
    end = s.fill(20, cap, rate)
    s.cough(8, 88)
    sensations(s, rate, 120, 210, 340)
    v = pressure_flow(s, end + 15, qmax=7.0, voided=220, pdet_qmax=52, popen=37, shape="prolonged", opening=8)
    coughs_every(s, 80, end - 10, amp=88)
    s.cough(v["end"] + 6, 88)
    bracket_void(s, v, 88, after=0)
    data = s.finish(compliance(100))
    data.update(kind="video-pressure-flow", fillingRate=rate, position="sitting",
                views=[ALL, fill_view(end + 10), void_view(end + 8, v["end"] + 12)],
                steps={"calc": "void", "treat": "void"},
                annotations=[point("calc", v["tpeak"], "pdet", same("PdetQmax 52")),
                             point("calc", v["tpeak"], "flow", same("Qmax 7")),
                             span("calc", v["start"], v["end"], L("BOOIf 52 − 2.2 × 7 = 36.6", "BOOIf 52 − 2,2 × 7 = 36,6", "BOOIf 52 − 2,2 × 7 = 36,6"), "pdet")],
                readings={"capacity": cap, "qmax": 7.0, "pdetQmax": 52, "voided": 220, "residual": 180})
    return data


def fowler() -> dict:
    """A large, poorly sensate bladder without a detrusor contraction on attempted voiding."""
    s = Study("udy-fowler", 1290)
    rate, cap = 50, 950
    end = s.fill(20, cap, rate)
    s.cough(8, 90)
    sensations(s, rate, 410, 650, 900)
    s.event(end + 15, "void")
    coughs_every(s, 80, end - 10, amp=90)
    s.cough(end + 105, 92)
    s.cough(end + 7, 90)  # immediately before the attempt to void
    data = s.finish(compliance(160))
    data.update(kind="cystometry", fillingRate=rate, position="sitting",
                views=[ALL, fill_view(end + 10), window("void", L("Attempt to void", "Miktionsversuch", "Intento miccional"), end + 5, end + 115)],
                steps={"emg": "all", "therapy": "all"},
                annotations=[point("emg", at_volume(rate, 650), "vol", L("First desire only at 650 ml", "Erster Harndrang erst bei 650 ml", "Primer deseo solo a 650 ml")),
                             span("emg", end + 15, end + 100, L("No detrusor contraction, no flow", "Keine Detrusorkontraktion, kein Fluss", "Sin contracción del detrusor, sin flujo"), "pdet")],
                readings={"capacity": cap, "firstDesire": 650})
    return data


def occult_sui() -> dict:
    """Coughs at 300 ml: dry with the prolapse in place, leakage once it is reduced."""
    s = Study("udy-occult", 490)
    rate, cap = 50, 300
    end = s.fill(20, cap, rate)
    s.cough(8, 95)
    sensations(s, rate, 130, 200, None)
    coughs_every(s, 80, end - 20, amp=95)
    for x in (end + 12, end + 24, end + 36):
        s.cough(x, 112)
    s.event(end + 52, "reduction")
    for x in (end + 66, end + 78, end + 90):
        s.cough(x, 110, leak=5.0)
    data = s.finish(compliance(110))
    data.update(kind="cystometry", fillingRate=rate, position="sitting",
                views=[ALL, window("test", L("Cough test at 300 ml", "Hustentest bei 300 ml", "Prueba de tos a 300 ml"), end, end + 102)],
                steps={"result": "test", "counsel": "test"},
                annotations=[span("result", end + 10, end + 40, L("Prolapse in place: dry", "Prolaps nicht reponiert: trocken", "Prolapso sin reducir: seco"), "flow", "neutral"),
                             span("result", end + 64, end + 94, L("Prolapse reduced: leakage with each cough, Pdet flat",
                                                                  "Prolaps reponiert: Leckage bei jedem Husten, Pdet flach",
                                                                  "Prolapso reducido: escape con cada tos, Pdet plana"), "flow")],
                readings={"capacity": cap})
    return data


def low_compliance() -> dict:
    """Spinal cord injury: a steady Pdet rise at 30 ml/min, then a repeat fill at 15 ml/min."""
    s = Study("udy-compliance", 2030, "supine", pdet_rest=0.0)
    first = s.fill(30, 260, 30)
    s.cough(10, 70)
    coughs_every(s, 90, first - 20, step=120, amp=66)
    s.event(first, "leak")
    s.leak(first + 0.5, 12, 15)
    s.pin(30, "pdet", 5.0)
    s.pin(first, "pdet", 45.0)
    drain = first + 25
    s.event(drain, "drain")
    s.empty(drain)
    start2 = drain + 60
    second = s.fill(start2, 320, 15)
    s.cough(start2 - 15, 68)
    coughs_every(s, start2 + 60, second - 30, step=150, amp=66)
    t300 = at_volume(15, 300, start2)
    s.pin(start2, "pdet", 5.0)
    s.pin(t300, "pdet", 40.0)
    # The same bladder looks stiffer when filled faster than physiologically.
    fast = lambda v: 5 + 40 * (v / 260) ** 1.25
    slow = lambda v: 5 + 35 * (v / 300) ** 1.35
    data = s.finish([(0.0, fast), (drain, slow)])
    data.update(kind="video-cystometry", fillingRate=30, rates=[[0.0, 30], [round(start2, 2), 15]], position="supine",
                views=[ALL, window("fill1", L("Fill 1 · 30 ml/min", "Füllung 1 · 30 ml/min", "Llenado 1 · 30 ml/min"), 0, drain + 12),
                       window("fill2", L("Fill 2 · 15 ml/min", "Füllung 2 · 15 ml/min", "Llenado 2 · 15 ml/min"), drain + 30, second + 20)],
                steps={"compliance": "fill1", "rate": "fill1", "plan": "fill2"},
                # The repeat fill at a slower rate is the answer to "rate": it stays hidden until then.
                conceal=[{"from": round(drain + 15, 2), "until": "rate"}],
                annotations=[span("compliance", 30, first, L("ΔV 260 ml / ΔPdet (45 − 5) cmH2O = 6.5 ml/cmH2O",
                                                             "ΔV 260 ml / ΔPdet (45 − 5) cmH2O = 6,5 ml/cmH2O",
                                                             "ΔV 260 ml / ΔPdet (45 − 5) cmH2O = 6,5 ml/cmH2O"), "pdet"),
                             point("plan", t300, "pdet", L("Pdet 40 cmH2O at 300 ml", "Pdet 40 cmH2O bei 300 ml", "Pdet 40 cmH2O a 300 ml"))],
                readings={"pdetStart": 5, "leakPdet": 45, "leakVolume": 260, "compliance": 6.5, "secondFillRate": 15, "volumeAtPdet40": 300})
    return data


def paediatric_flow() -> dict:
    """Two uroflowmetries with pelvic floor EMG: continuous but jerky (staccato) flow."""
    s = Study("udy-staccato", 150, pabd_rest=0.0, pdet_rest=0.0)
    first = s.void(4, qmax=13.0, voided=160, shape="staccato", opening=2, emg="active", marker=False)
    second = s.void(78, qmax=14.0, voided=180, shape="staccato", opening=2, emg="active", marker=False)
    for v, amp in ((first, 46), (second, 50)):  # each trough of the flow is a burst of pelvic floor activity
        s.emg_bursts_at([v["start"] + u * (v["end"] - v["start"]) for u in STACCATO], amp, 0.9)
    s.pin(first["tpeak"], "flow", 13.0)
    s.pin(second["tpeak"], "flow", 14.0)
    s.event(first["tpeak"], "qmax")
    s.event(second["tpeak"], "qmax")
    data = s.finish(lambda v: 0.0)
    for key in ("pves", "pabd", "vinf"):
        data.pop(key)
    data.update(kind="uroflow-emg", position="sitting", channels=["flow", "vvoid", "emg"],
                views=[window("void1", L("Flow 1", "Flow 1", "Flujo 1"), 0, first["end"] + 6),
                       window("void2", L("Flow 2", "Flow 2", "Flujo 2"), 74, second["end"] + 6)],
                steps={"curve": "void1", "treat": "void1"},
                annotations=[span("curve", first["start"], first["end"], L("Continuous but jerky flow (staccato) with pelvic floor EMG activity",
                                                                           "Kontinuierlicher, aber ruckartiger Fluss (Staccato) mit Beckenboden-EMG-Aktivität",
                                                                           "Flujo continuo pero irregular, con picos y valles bruscos (staccato), con actividad del EMG del suelo pélvico"), "flow")],
                readings={"voided1": 160, "voided2": 180, "qmax1": 13.0, "qmax2": 14.0})
    return data


def artefacts() -> dict:
    """Rectal contractions at 180 ml, then a damped vesical line at 260 ml (cough +38 versus +100 cmH2O); after the
    decision, filling stops, the line is flushed and a repeat cough shows equal deflections again."""
    s = Study("udy-artefacts", 376, pabd_rest=31.0, pdet_rest=3.0)
    rate = 50
    t260 = at_volume(rate, 260)
    stop, flush = t260 + 8, t260 + 16
    s.fill(20, (stop - 20) * rate / 60, rate)  # filling continues only after a correct cough test
    s.cough(6, 96, mismatch=0.0)
    s.cough(14, 102, mismatch=0.01)
    s.pin(2, "pabd", 31.0)
    s.pin(2, "pves", 34.0)
    coughs_every(s, 80, 200, amp=96)
    t180 = at_volume(rate, 180)
    for offset in (2, 26, 50):
        s.rectal(t180 + offset, 12, 15)
    s.dampen(at_volume(rate, 245), 1.15, until=flush)
    s.cough(t260, 100, mismatch=0.0)
    s.pin(t260 - 0.75, "pabd", 31.0)
    s.pin(t260 - 0.75, "pves", 34.0)
    s.pin(t260 + 0.5, "pabd", 131.0)
    s.pin_peak(t260 - 0.5, t260 + 6, "pves", 72.0, base=t260 - 0.75)
    s.event(stop, "stop")
    s.event(flush, "flush")
    s.cough(flush + 10, 100, mismatch=0.0)  # the repeat check after flushing: equal peaks
    for x in (t180 - 6, t180 + 70):  # regular cough tests also around the rectal waves, before the damping starts
        s.cough(s.clear(x), 96)
    data = s.finish(compliance(1500))
    data.update(kind="cystometry", fillingRate=rate, position="sitting",
                views=[ALL, window("start", L("Start", "Beginn", "Inicio"), 0, 30),
                       window("waves", L("At 180 ml", "Bei 180 ml", "A los 180 ml"), t180 - 12, t180 + 78),
                       window("cough", L("Cough at 260 ml", "Husten bei 260 ml", "Tos a los 260 ml"), t260 - 14, flush + 22)],
                steps={"baseline": "start", "waves": "waves", "transmission": "cough"},
                conceal=[{"from": round(t260 + 5, 2), "until": "transmission"}],
                annotations=[point("baseline", 2, "pdet", same("Pves 34 − Pabd 31 = Pdet 3")),
                             span("waves", t180, t180 + 67, L("Pabd waves, Pves unchanged: rectal contractions",
                                                             "Pabd-Wellen, Pves unverändert: Rektumkontraktionen",
                                                             "Ondas de Pabd, Pves sin cambios: contracciones rectales"), "pabd"),
                             span("transmission", t260 - 1, t260 + 3, L("Cough: Pves +38 versus Pabd +100 = 38%",
                                                                        "Husten: Pves +38 gegenüber Pabd +100 = 38 %",
                                                                        "Tos: Pves +38 frente a Pabd +100 = 38 %"), "pves"),
                             span("transmission", stop - 1, flush + 13, L("Filling stopped, line flushed: the repeat cough shows equal peaks in Pves and Pabd",
                                                                         "Füllung gestoppt, Leitung gespült: Der Kontrollhusten zeigt gleich hohe Ausschläge in Pves und Pabd",
                                                                         "Llenado detenido, línea purgada: la tos de control muestra picos iguales en Pves y Pabd"), "pves", "good")],
                readings={"baselinePves": 34, "baselinePabd": 31, "rectalWaves": 3, "rectalFrom": 180, "rectalRise": 12,
                          "coughAt": 260, "coughPves": 38, "coughPabd": 100})
    return data


# --- new cases of the urodynamics lab -----------------------------------------------------------

def normal_male() -> dict:
    """Normal storage and an unobstructed void with normal contractility (BOOI 4, BCI 130)."""
    s = Study("udy-normal-male", 710)
    rate, cap = 50, 470
    end = s.fill(20, cap, rate)
    s.cough(8, 95)
    coughs_every(s, 80, end - 10, amp=95)
    sensations(s, rate, 170, 280, 430)
    s.cough(end + 8, 96)
    s.pin(20, "pdet", 3.0)
    s.pin(end, "pdet", 7.0)
    v = pressure_flow(s, end + 20, qmax=18.0, voided=450, pdet_qmax=40, popen=27, shape="bell", opening=6)
    s.cough(v["end"] + 8, 92)
    data = s.finish(compliance(118))
    data.update(kind="pressure-flow", fillingRate=rate, position="sitting",
                views=[ALL, fill_view(end + 15), void_view(end + 12, v["end"] + 14)],
                steps={"storage": "fill", "voiding": "void", "plan": "all"},
                annotations=[span("storage", 20, end, L("No detrusor overactivity; Pdet 3 → 7 cmH2O over 470 ml (compliance about 118 ml/cmH2O)",
                                                        "Keine Detrusorüberaktivität; Pdet 3 → 7 cmH2O über 470 ml (Compliance etwa 118 ml/cmH2O)",
                                                        "Sin hiperactividad del detrusor; Pdet 3 → 7 cmH2O en 470 ml (distensibilidad de unos 118 ml/cmH2O)"), "pdet", "good"),
                             point("voiding", v["tpeak"], "pdet", same("PdetQmax 40"), "good"),
                             point("voiding", v["tpeak"], "flow", same("Qmax 18 · BOOI 4 · BCI 130"), "good")],
                readings={"capacity": cap, "qmax": 18.0, "pdetQmax": 40, "pvesQmax": 70, "voided": 450, "residual": 20,
                          "firstSensation": 170, "firstDesire": 280, "strongDesire": 430, "pdetStart": 3, "pdetEnd": 7, "compliance": 118})
    return data


def normal_female_oab() -> dict:
    """Early sensation without detrusor overactivity, then a normal low-pressure, high-flow void."""
    s = Study("udy-normal-female", 570)
    rate, cap = 50, 320
    end = s.fill(20, cap, rate)
    s.cough(8, 92)
    coughs_every(s, 80, end - 10, amp=92)
    sensations(s, rate, 90, 140, 230)
    s.event(at_volume(rate, 260), "provocation")
    s.cough(at_volume(rate, 290), 104)
    s.cough(at_volume(rate, 293), 108)
    v = pressure_flow(s, end + 18, qmax=26.0, voided=310, pdet_qmax=20, popen=12, shape="bell", opening=5)
    bracket_void(s, v, 92, before=9)
    data = s.finish(compliance(105))
    data.update(kind="pressure-flow", fillingRate=rate, position="sitting",
                views=[ALL, fill_view(end + 12), void_view(end + 10, v["end"] + 12)],
                steps={"storage": "fill", "voiding": "void", "plan": "all"},
                annotations=[span("storage", at_volume(rate, 90), end, L("Increased bladder sensation (first desire 140 ml); no detrusor overactivity despite provocation",
                                                                        "Gesteigerte Blasensensitivität (erster Harndrang 140 ml); keine Detrusorüberaktivität trotz Provokation",
                                                                        "Sensibilidad vesical aumentada (primer deseo a 140 ml); sin hiperactividad pese a la provocación"), "pdet"),
                             point("voiding", v["tpeak"], "flow", L("Qmax 26 at PdetQmax 20: a normal female void", "Qmax 26 bei PdetQmax 20: normale Miktion einer Frau",
                                                                    "Qmax 26 con PdetQmax 20: micción femenina normal"), "good")],
                readings={"capacity": cap, "qmax": 26.0, "pdetQmax": 20, "voided": 310, "residual": 10,
                          "firstSensation": 90, "firstDesire": 140, "strongDesire": 230, "pdetStart": 3, "pdetEnd": 6})
    return data


def do_incontinence() -> dict:
    """Idiopathic phasic detrusor overactivity with leakage at 230 ml, then an unobstructed void."""
    s = Study("udy-doi", 530)
    rate, cap = 50, 240
    end = s.fill(20, cap, rate)
    s.cough(8, 90)
    for x in (80, 140, 220, 270):  # cough tests between the detrusor waves, so that no wave looks cough-provoked
        s.cough(x, 90 * s.rng.uniform(0.88, 1.1))
    sensations(s, rate, 100, 130, None)  # first desire before the first wave and its urgency
    t140 = at_volume(rate, 140)
    s.contraction(t140 + 3, 18, peak=20)
    s.contraction(t140 + 50, 20, peak=31)
    top = s.contraction(t140 + 94, 22, peak=45, leak=15)
    s.pin(top, "pdet", 45.0)
    v = pressure_flow(s, end + 25, qmax=21.0, voided=200, pdet_qmax=24, popen=14, shape="bell", opening=5)
    s.cough(s.clear(168), 90)  # closes the gap between the coughs at 140 and 220 s
    bracket_void(s, v, 90)
    data = s.finish(compliance(95))
    data.update(kind="pressure-flow", fillingRate=rate, position="sitting",
                views=[ALL, fill_view(end + 15), void_view(end + 18, v["end"] + 12)],
                steps={"filling": "fill", "voiding": "void", "plan": "all"},
                annotations=[span("filling", t140, end, L("Phasic detrusor overactivity with urgency; leakage with the third wave at 45 cmH2O",
                                                          "Phasische Detrusorüberaktivität mit Drang; Leckage bei der dritten Welle mit 45 cmH2O",
                                                          "Hiperactividad fásica con urgencia; escape con la tercera onda a 45 cmH2O"), "pdet"),
                             point("voiding", v["tpeak"], "flow", L("Qmax 21 · PdetQmax 24 · residual 25 ml", "Qmax 21 · PdetQmax 24 · Restharn 25 ml",
                                                                    "Qmax 21 · PdetQmax 24 · residuo 25 ml"), "good")],
                readings={"capacity": cap, "leaked": 15, "qmax": 21.0, "pdetQmax": 24, "voided": 200, "residual": 25, "overactivityFrom": 140,
                          "contractionPeaks": [20, 31, 45], "leakPdet": 45})
    return data


def stress_incontinence() -> dict:
    """Leakage with coughs from 250 ml without a detrusor rise; leakage on straining at Pves 95 cmH2O."""
    s = Study("udy-usi", 790)
    rate, cap = 50, 450
    end = s.fill(20, cap, rate)
    s.cough(8, 95)
    sensations(s, rate, 160, 260, 400)
    for vol, leak in ((100, 0.0), (150, 0.0), (200, 0.0), (250, 3.0), (300, 3.0)):
        s.cough(at_volume(rate, vol), 108, leak=leak)
    tv = at_volume(rate, 275)  # straining between the coughs at 250 and 300 ml, inside the section the question names
    k_leak = s.valsalva(tv, 72, 6, leak_at=60, leak=8.0)
    s.pin(k_leak * DT, "pves", 95.0)
    for vol in (350, 400):
        s.cough(at_volume(rate, vol) + 10, 104, leak=3.0)
    v = pressure_flow(s, end + 22, qmax=28.0, voided=410, pdet_qmax=18, popen=11, shape="bell", opening=4)
    s.cough(at_volume(rate, 50), 100)  # a cough test at 50 ml too
    bracket_void(s, v, 100)
    data = s.finish(compliance(150))
    t250 = at_volume(rate, 250)
    data.update(kind="pressure-flow", fillingRate=rate, position="sitting",
                views=[ALL, fill_view(end + 15), window("leak", L("Cough tests 200–300 ml", "Hustentests 200–300 ml", "Pruebas de tos 200–300 ml"),
                                                           at_volume(rate, 195), at_volume(rate, 300) + 8), void_view(end + 15, v["end"] + 12)],
                steps={"leak": "leak", "lpp": "leak", "plan": "all"},
                annotations=[span("leak", t250 - 1, t250 + 3, L("Leakage with the cough, Pdet stays flat", "Leckage mit dem Husten, Pdet bleibt flach",
                                                                "Escape con la tos, la Pdet no sube"), "flow"),
                             point("lpp", k_leak * DT, "pves", L("Leakage on straining at Pves 95 cmH2O: confirms stress leakage, does not grade it",
                                                                "Leckage beim Pressen bei Pves 95 cmH2O: bestätigt die Belastungsleckage, stuft sie nicht ein",
                                                                "Escape al empujar con Pves 95 cmH2O: confirma el escape de esfuerzo, no lo gradúa")),
                             point("plan", v["tpeak"], "flow", L("Qmax 28 · PdetQmax 18 · residual 20 ml", "Qmax 28 · PdetQmax 18 · Restharn 20 ml",
                                                                 "Qmax 28 · PdetQmax 18 · residuo 20 ml"), "good")],
                readings={"capacity": cap, "leaked": 20, "qmax": 28.0, "pdetQmax": 18, "voided": 410, "residual": 20, "coughLeakFrom": 250,
                          "leakPointPves": 95})
    return data


def mixed_incontinence() -> dict:
    """Detrusor overactivity incontinence at 180 ml and stress leakage with coughs from 250 ml."""
    s = Study("udy-mui", 610)
    rate, cap = 50, 320
    end = s.fill(20, cap, rate)
    s.cough(8, 92)
    sensations(s, rate, 110, 160, 280)
    s.cough(at_volume(rate, 100), 96)
    t180 = at_volume(rate, 180)
    top = s.contraction(t180 - 3, 22, peak=34, leak=12)
    s.pin(top, "pdet", 34.0)
    s.cough(at_volume(rate, 220), 104)
    t250 = at_volume(rate, 250)
    s.cough(t250, 110, leak=4.0)
    s.cough(at_volume(rate, 290), 112, leak=4.0)
    v = pressure_flow(s, end + 20, qmax=22.0, voided=270, pdet_qmax=22, popen=13, shape="bell", opening=5)
    for x in (at_volume(rate, 50), at_volume(rate, 150)):  # regular cough tests before the overactivity
        s.cough(s.clear(x), 96)
    bracket_void(s, v, 100)
    data = s.finish(compliance(110))
    data.update(kind="pressure-flow", fillingRate=rate, position="sitting",
                views=[ALL, fill_view(end + 15), void_view(end + 14, v["end"] + 12)],
                steps={"read": "fill", "first": "fill", "counsel": "all"},
                annotations=[span("read", t180 - 3, t180 + 19, L("Detrusor overactivity incontinence at 180 ml (Pdet 34 cmH2O)",
                                                                 "Detrusorüberaktivitäts-Inkontinenz bei 180 ml (Pdet 34 cmH2O)",
                                                                 "Incontinencia por hiperactividad a los 180 ml (Pdet 34 cmH2O)"), "pdet"),
                             span("read", t250 - 1, t250 + 3, L("Stress leakage with the cough at 250 ml, no Pdet rise",
                                                                "Belastungsleckage beim Husten bei 250 ml, kein Pdet-Anstieg",
                                                                "Escape de esfuerzo con la tos a 250 ml, sin subida de Pdet"), "flow")],
                readings={"capacity": cap, "leaked": 20, "qmax": 22.0, "pdetQmax": 22, "voided": 270, "residual": 30, "overactivityLeak": 180,
                          "leakPdet": 34, "waveSeconds": 20, "coughLeakFrom": 250})
    return data


def ndo_dsd() -> dict:
    """Spinal cord injury at T4: neurogenic overactivity up to 85 cmH2O with rising sphincter EMG (DSD) and a blood
    pressure rise. After the decision the tracing shows filling stopped and the bladder drained through the catheter."""
    rate = 18
    start2 = at_volume(rate, 140)
    bp, stop, drain = start2 + 10, start2 + 13, start2 + 22
    s = Study("udy-ndo-dsd", drain + 14, "supine")
    s.fill(20, (stop - 20) * rate / 60, rate)
    cap = round((stop - 20) * rate / 60)
    s.cough(8, 22)  # abdominal muscles paralysed below T4: weak coughs, still enough to check transmission
    t110 = at_volume(rate, 110)
    s.contraction(t110, 26, peak=48, urgency=False, emg=55)
    top = s.contraction(start2, 24, peak=85, urgency=False, emg=72)
    for x in (start2 + 7, start2 + 11, start2 + 15):  # leakage escapes in spurts between sphincter bursts
        s.leak(x, 3.2, 6)
    s.event(start2 + 7, "leak")
    s.event(bp, "bloodPressure", value="178/96")
    s.event(stop, "stop")
    s.event(drain, "drain")
    s.empty(drain)
    coughs_every(s, 90, t110 + 65, step=120, amp=20)  # at 90, 210, 330 and 450 s, as before
    s.pin(top, "pdet", 85.0)
    data = s.finish(compliance(60))
    data.update(kind="video-cystometry", fillingRate=rate, position="supine",
                views=[ALL, window("contraction", L("At 140 ml", "Bei 140 ml", "A los 140 ml"), start2 - 25, drain + 12)],
                steps={"read": "all", "dysreflexia": "contraction", "plan": "all"},
                # What was done about the dysreflexia is the answer to "dysreflexia": it stays hidden until then.
                conceal=[{"from": round(bp + 0.5, 2), "until": "dysreflexia"}],
                annotations=[span("read", start2, start2 + 24, L("Detrusor contraction with rising sphincter EMG and interrupted leakage: DSD",
                                                                 "Detrusorkontraktion mit steigendem Sphinkter-EMG und unterbrochener Leckage: DSD",
                                                                 "Contracción del detrusor con EMG esfinteriano en aumento y escape entrecortado: DDE"), "emg"),
                             point("dysreflexia", top, "pdet", L("Pdet 85 cmH2O with blood pressure 178/96: autonomic dysreflexia",
                                                                 "Pdet 85 cmH2O mit Blutdruck 178/96: autonome Dysreflexie",
                                                                 "Pdet 85 cmH2O con presión arterial 178/96: disreflexia autonómica")),
                             span("dysreflexia", stop - 0.5, drain + 4, L("Filling stopped and the bladder drained through the catheter: the trigger is removed",
                                                                         "Füllung gestoppt und Blase über den Katheter abgelassen: Der Auslöser ist beseitigt",
                                                                         "Llenado detenido y vejiga vaciada por la sonda: se elimina el desencadenante"), "vol", "good")],
                readings={"maxPdet": 85, "contractionOnsets": [110, 140], "contractionPeaks": [48, 85], "capacity": cap})
    return data


def acontractile() -> dict:
    """Diabetes: late sensation, no detrusor contraction; voiding only by abdominal straining."""
    s = Study("udy-acontractile", 930)
    rate, cap = 50, 600
    end = s.fill(20, cap, rate)
    s.cough(8, 90)
    sensations(s, rate, 300, 450, 580)
    s.event(end + 15, "void")
    coughs_every(s, 80, end - 10, amp=90)
    strains = [(end + 30, 58, 7), (end + 46, 64, 9), (end + 64, 52, 6), (end + 80, 56, 8), (end + 97, 48, 6), (end + 113, 50, 7)]
    pieces = []
    for start, amp, dur in strains:
        s.strain(start, amp, dur)
        ks = list(range(s.i(start + 1.0), s.i(start + dur + 0.8) + 1))
        shape = [smoothstep((s.t[k] - start - 0.8) / 1.4) * (1 - smoothstep((s.t[k] - start - dur + 0.2) / 1.0)) * (0.96 + 0.04 * math.sin(s.t[k] * 3.3)) for k in ks]
        top = max(shape)
        pieces.append((ks, [x / top for x in shape], amp))
    # Flow runs only while the abdominal pressure is high: about 8 ml/s at the strongest strain.
    peaks = [8.0 * amp / 64 for _, _, amp in pieces]
    base = sum(sum(shape) * peak * DT for (ks, shape, _), peak in zip(pieces, peaks))
    target = 230.0
    others = sum(sum(shape) * peak * DT for (ks, shape, amp), peak in zip(pieces, peaks) if amp != 64)
    strongest = base - others
    scale = (target - strongest) / others
    for (ks, shape, amp), peak in zip(pieces, peaks):
        q = peak if amp == 64 else peak * scale
        for k, x in zip(ks, shape):
            s.flow[k] += q * x
    k_peak = max(range(s.n), key=lambda k: s.flow[k])
    s.pin(k_peak * DT, "flow", 8.0)
    s.event(k_peak * DT, "qmax")
    s.cough(end + 145, 88)
    s.cough(end + 7, 90)  # immediately before permission to void
    data = s.finish(compliance(190))
    data.update(kind="pressure-flow", fillingRate=rate, position="sitting",
                views=[ALL, fill_view(end + 10), void_view(end + 8, end + 152)],
                steps={"void": "void", "plan": "void", "later": "all"},
                annotations=[span("void", end + 28, end + 134, L("Flow only while straining (Pabd and Pves rise together); Pdet flat: acontractile detrusor",
                                                                 "Fluss nur beim Pressen (Pabd und Pves steigen gemeinsam); Pdet flach: akontraktiler Detrusor",
                                                                 "Flujo solo al empujar (Pabd y Pves suben juntas); Pdet plana: detrusor acontráctil"), "pdet"),
                             point("void", k_peak * DT, "flow", L("Qmax 8 only while straining", "Qmax 8 nur beim Pressen", "Qmax 8 solo al empujar")),
                             point("later", at_volume(rate, 450), "vol", L("First desire only at 450 ml, capacity 600 ml: catheterise by the clock, not by the urge",
                                                                          "Erster Harndrang erst bei 450 ml, Kapazität 600 ml: nach der Uhr katheterisieren, nicht nach dem Drang",
                                                                          "Primer deseo solo a 450 ml, capacidad 600 ml: cateterizar según el reloj, no según el deseo"))],
                readings={"capacity": cap, "qmax": 8.0, "pvesVoidMax": 102, "pdetVoidBelow": 10, "voided": 230, "residual": 370,
                          "firstSensation": 300, "firstDesire": 450, "strongDesire": 580})
    return data


def plateau_flow() -> dict:
    """Uroflowmetry with a plateau-shaped curve: Qmax 9 ml/s, 310 ml."""
    s = Study("udy-plateau", 52, "standing", pabd_rest=0.0, pdet_rest=0.0, emg=False)
    v = s.void(1.5, qmax=9.0, voided=310, shape="plateau", opening=1.5, marker=False)
    s.pin(v["tpeak"], "flow", 9.0)
    s.event(v["tpeak"], "qmax")
    data = s.finish(lambda vol: 0.0)
    for key in ("pves", "pabd", "vinf"):
        data.pop(key)
    data.update(kind="uroflow", position="standing", channels=["flow", "vvoid"],
                views=[window("all", L("Uroflowmetry", "Uroflowmetrie", "Flujometría"), 0, v["end"] + 4)],
                steps={"curve": "all", "next": "all", "treat": "all"},
                annotations=[span("curve", v["start"] + 2.5, v["end"] - 2.5, L("Plateau: flow hardly changes for most of the void",
                                                                               "Plateau: Der Fluss bleibt über den größten Teil der Miktion nahezu gleich",
                                                                               "Meseta: el flujo apenas cambia durante casi toda la micción"), "flow")],
                readings={"qmax": 9.0, "voided": 310, "flowTime": round(v["end"] - v["start"])})
    return data


def catheter_loss() -> dict:
    """The vesical catheter slips out early in voiding; the repeat study shows obstruction."""
    s = Study("udy-catheter", 1150)
    rate, cap = 50, 350
    end = s.fill(20, cap, rate)
    s.cough(8, 94)
    sensations(s, rate, 140, 220, 330)
    coughs_every(s, 80, end - 10, amp=94)
    first = s.void(end + 15, qmax=7.0, voided=280, pdet_qmax=70, popen=50, shape="prolonged", opening=9)
    loss = first["start"] + 5
    recath = first["end"] + 40
    s.lose_catheter(loss, recath)
    s.cough(first["end"] + 12, 92)
    s.event(recath, "recatheterise")
    s.empty(recath)
    start2 = recath + 30
    end2 = s.fill(start2, cap, rate)
    s.cough(start2 - 10, 94)
    coughs_every(s, start2 + 60, end2 - 10, amp=94)
    second = pressure_flow(s, end2 + 15, qmax=8.0, voided=300, pdet_qmax=74, popen=53, shape="prolonged", opening=9)
    s.cough(second["end"] + 8, 92)
    for void_start in (end + 7, end2 + 7):  # immediately before each permission to void
        s.cough(void_start, 94)
    data = s.finish(compliance(100))
    data.update(kind="pressure-flow", fillingRate=rate, position="sitting",
                views=[ALL, window("void1", L("Void 1", "Miktion 1", "Micción 1"), end + 8, first["end"] + 34),
                       window("void2", L("Repeat void", "Wiederholte Miktion", "Micción repetida"), end2 + 8, second["end"] + 14)],
                steps={"artefact": "void1", "next": "void1", "repeat": "void2"},
                conceal=[{"from": round(first["end"] + 34, 2), "until": "next"}],
                annotations=[span("artefact", loss, first["end"] + 34, L("Pves drops suddenly below zero and no longer follows the cough: the vesical catheter is out",
                                                                         "Pves fällt schlagartig unter null und folgt dem Husten nicht mehr: Blasenkatheter herausgerutscht",
                                                                         "La Pves cae de golpe por debajo de cero y ya no sigue la tos: la sonda vesical se ha salido"), "pves"),
                             point("repeat", second["tpeak"], "pdet", same("PdetQmax 74")),
                             point("repeat", second["tpeak"], "flow", same("Qmax 8 · BOOI 58 · BCI 114"))],
                readings={"pvesBeforeLossAbove": 80, "qmax1": 7.0, "capacity": cap, "qmax": 8.0, "pdetQmax": 74, "pvesQmax": 105,
                          "voided": 300, "residual": 50})
    return data


CASES = {
    "udy-bpo-pressure-flow-indices": bpo_indices,
    "udy-dhic-elderly-man-no-turp": dhic,
    "udy-pbno-young-man-vuds": pbno,
    "udy-msa-before-turp": msa,
    "udy-female-boo-after-sling": female_boo,
    "udy-fowler-retention-young-woman": fowler,
    "udy-occult-sui-prolapse-reduction": occult_sui,
    "udy-low-compliance-sci-filling-rate": low_compliance,
    "udy-paediatric-dysfunctional-voiding": paediatric_flow,
    "udy-artefacts-rectal-contraction-transmission": artefacts,
    "udy-normal-study-man": normal_male,
    "udy-normal-study-woman-oab": normal_female_oab,
    "udy-detrusor-overactivity-incontinence": do_incontinence,
    "udy-urodynamic-stress-incontinence": stress_incontinence,
    "udy-mixed-incontinence": mixed_incontinence,
    "udy-neurogenic-overactivity-dsd": ndo_dsd,
    "udy-acontractile-detrusor-straining": acontractile,
    "udy-plateau-flow-stricture": plateau_flow,
    "udy-catheter-loss-repeat": catheter_loss,
}


def generate() -> dict:
    tracings = {}
    for case_id, builder in CASES.items():
        data = builder()
        end = data["t"][-1]
        for view in data["views"]:  # a section must lie inside the recording
            if "t" in view and not (0 <= view["t"][0] < view["t"][1] <= end):
                raise ValueError(f"{case_id}: view {view['id']} {view['t']} outside 0..{end}")
        if "channels" not in data:
            data["channels"] = ["pves", "pabd", "pdet", "flow", "vol"] + (["emg"] if "emg" in data else [])
        tracings[case_id] = data
    return {"version": 1, "generator": "scripts/urodynamic_traces.py",
            "note": "Synthetic teaching curves that follow ICS conventions; not recordings of patients.", "tracings": tracings}


def render(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Write the synthetic urodynamic tracings.")
    parser.add_argument("--check", action="store_true", help="fail if data/urodynamic-tracings.json is out of date")
    args = parser.parse_args(argv)
    text = render(generate())
    if args.check:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
        if current != text:
            print(f"{OUTPUT.relative_to(ROOT)} is out of date; run python scripts/urodynamic_traces.py", file=sys.stderr)
            return 1
        print(f"{OUTPUT.relative_to(ROOT)} matches the generator.")
        return 0
    OUTPUT.write_text(text, encoding="utf-8")
    print(f"Wrote {len(json.loads(text)['tracings'])} tracings to {OUTPUT.relative_to(ROOT)} ({len(text) // 1000} kB).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
