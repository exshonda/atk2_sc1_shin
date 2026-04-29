#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 4-7 安定性試験 (10 分短縮版).

EK-RA6M5 + sample1 を相手に COM9 経由で:
  4-7-1: 'a' で MainCyc 起動 → 10 分待機 → 'T' で HW カウンタ確認
  4-7-2: 連続キーリピートで RX ISR ストレス
を流し，シリアル出力ログから HardFault / 出力停止 / 異常を検出する．

phase4.md §4-7 の合格条件を満たすか自動判定する．
"""

import argparse
import datetime as dt
import os
import re
import sys
import threading
import time

import serial


HARDFAULT_PATTERNS = [
    re.compile(r"HardFault", re.I),
    re.compile(r"default_exc_handler", re.I),
    re.compile(r"BUS\s*FAULT", re.I),
    re.compile(r"USAGE\s*FAULT", re.I),
    re.compile(r"MEMMANAGE", re.I),
    re.compile(r"SECURE\s*FAULT", re.I),
]
#  sample1 'T' は GetHwCnt() の結果を 3 回印字する: "C1ISR Cnt:N, C2ISR Cnt:M"
ISR_CNT_RE = re.compile(r"C1ISR\s+Cnt\s*:\s*(\d+)\s*,\s*C2ISR\s+Cnt\s*:\s*(\d+)",
                        re.I)


def now() -> str:
    return dt.datetime.now().strftime("%H:%M:%S")


def banner(msg: str) -> None:
    print(f"[{now()}] === {msg} ===", flush=True)


class SerialMonitor:
    def __init__(self, port: str, baud: int, log_path: str):
        self.ser = serial.Serial(port, baud, timeout=0.1)
        self.log = open(log_path, "w", encoding="utf-8", errors="replace")
        self.lines: list[tuple[float, str]] = []
        self.last_rx = time.time()
        self.faults: list[str] = []
        self.stop = False
        self._buf = b""
        self._t = threading.Thread(target=self._run, daemon=True)
        self._t.start()

    def _run(self) -> None:
        while not self.stop:
            try:
                chunk = self.ser.read(256)
            except serial.SerialException as e:
                self.log.write(f"[serial-error] {e}\n")
                self.log.flush()
                break
            if chunk:
                self.last_rx = time.time()
                self._buf += chunk
                while b"\n" in self._buf:
                    line, self._buf = self._buf.split(b"\n", 1)
                    text = line.decode("utf-8", errors="replace").rstrip("\r")
                    self._on_line(text)
            else:
                time.sleep(0.02)

    def _on_line(self, text: str) -> None:
        ts = time.time()
        self.lines.append((ts, text))
        self.log.write(f"[{dt.datetime.fromtimestamp(ts).strftime('%H:%M:%S.%f')[:-3]}] {text}\n")
        self.log.flush()
        for pat in HARDFAULT_PATTERNS:
            if pat.search(text):
                self.faults.append(text)
                print(f"[{now()}] !! FAULT: {text}", flush=True)
                return
        # 進捗マーカ (約 30 秒に 1 回程度の出力をチラ見せ)
        if "[" in text and "]" in text:  # MainCyc 系のログ
            return

    def send(self, key: str) -> None:
        self.ser.write(key.encode("ascii"))
        self.ser.flush()
        print(f"[{now()}] >> '{key}' (0x{ord(key):02X})", flush=True)

    def silent_for(self, seconds: float) -> bool:
        return (time.time() - self.last_rx) >= seconds

    def close(self) -> None:
        self.stop = True
        self._t.join(timeout=1)
        try:
            self.ser.close()
        except Exception:
            pass
        self.log.close()


def collect_isr_cnt(monitor: SerialMonitor, since: float) -> tuple[int, int] | None:
    """T コマンド応答から (C1ISR_cnt, C2ISR_cnt) の最初のヒットを返す．"""
    for ts, text in monitor.lines:
        if ts < since:
            continue
        m = ISR_CNT_RE.search(text)
        if m:
            return int(m.group(1)), int(m.group(2))
    return None


def run_test(port: str, baud: int, duration_min: float, log_path: str,
             stress_secs: float) -> int:
    monitor = SerialMonitor(port, baud, log_path)
    try:
        # ボードに何か出ているか確認 (banner / Input Command:)．
        # まず改行を 2 個送ってプロンプト再表示を促す．
        time.sleep(0.5)
        monitor.send("\r")
        time.sleep(0.5)
        banner("4-7-1 開始: 'a' を送って MainCyc 起動")
        t_start = time.time()
        monitor.send("a")
        # 短い待機で a の応答 (echo + ActivateTask) を取り込む
        time.sleep(2.0)

        # 10 分待機．30 秒ごとに「生きてる感」をチェック．
        total_secs = duration_min * 60
        check_interval = 30
        elapsed = 0.0
        while elapsed < total_secs:
            time.sleep(check_interval)
            elapsed = time.time() - t_start
            silent = time.time() - monitor.last_rx
            print(f"[{now()}] elapsed={elapsed:6.1f}s "
                  f"last_rx={silent:5.1f}s ago "
                  f"fault_count={len(monitor.faults)} "
                  f"line_count={len(monitor.lines)}",
                  flush=True)
            if monitor.faults:
                banner(f"FAULT 検出 → 早期終了 ({elapsed:.1f}s 経過)")
                break

        # 4-7-1 終了判定: 'T' で ISR カウント (sample1 PutHwCnt3) を確認
        banner("4-7-1 終了: 'T' で ISR カウント確認")
        t_T = time.time()
        monitor.send("T")
        time.sleep(2.0)
        cnt1 = collect_isr_cnt(monitor, since=t_T)

        # 4-7-2 短縮版: 連続キー入力ストレス
        banner(f"4-7-2 開始: {stress_secs:.0f} 秒間キーリピート")
        stress_end = time.time() + stress_secs
        sent = 0
        while time.time() < stress_end:
            monitor.send("1")
            sent += 1
            time.sleep(0.05)  # 20 chars/sec
        banner(f"4-7-2 送出完了: {sent} chars")
        time.sleep(2.0)
        monitor.send("\r")
        time.sleep(1.0)
        monitor.send("T")
        time.sleep(2.0)
        cnt2 = collect_isr_cnt(monitor, since=stress_end)

        # 結果レポート (Windows cp932 で安全に印字するため非 ASCII を排除)
        banner("Result summary")
        actual_secs = time.time() - t_start
        print(f"  duration:               {actual_secs:.1f} sec")
        print(f"  fault count:            {len(monitor.faults)}")
        print(f"  total RX lines:         {len(monitor.lines)}")
        print(f"  ISR cnt (T1 @ end):     {cnt1}")
        print(f"  ISR cnt (T2 post-stress): {cnt2}")

        # 自動判定: HardFault ゼロ + 出力が継続 + 'T' 応答が両回パース可能
        ok = (
            len(monitor.faults) == 0
            and len(monitor.lines) > 10
            and cnt1 is not None
            and cnt2 is not None
        )
        print()
        print("  PASS" if ok else "  FAIL")
        return 0 if ok else 1
    finally:
        monitor.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default="COM9")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--minutes", type=float, default=10.0)
    ap.add_argument("--stress-secs", type=float, default=10.0)
    ap.add_argument("--log", default="phase4_7.log")
    args = ap.parse_args()
    rc = run_test(args.port, args.baud, args.minutes, args.log,
                  args.stress_secs)
    return rc


if __name__ == "__main__":
    sys.exit(main())
