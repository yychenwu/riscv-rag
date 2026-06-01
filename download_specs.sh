#!/bin/bash
# RISC-V Spec Downloader — 36 specs from Synopsys ARC-V RHX-11x reference list
# Usage: bash download_specs.sh
# PDFs are saved to ./data/

set -e
DATA_DIR="$(dirname "$0")/data"
mkdir -p "$DATA_DIR"

download() {
  local name="$1"
  local url="$2"
  local dest="$DATA_DIR/$name"
  if [ -f "$dest" ]; then
    echo "  [SKIP] $name (already exists)"
  else
    echo "  [DL]   $name"
    curl -fsSL -o "$dest" "$url" && echo "  [OK]   $name" || echo "  [FAIL] $name — $url"
  fi
}

echo "=============================="
echo "  RISC-V Spec Downloader"
echo "  目標: $DATA_DIR"
echo "=============================="
echo ""

# ── ISA Manual (unified Vol1 + Vol2 + Privileged) ──────────────────────────
echo "[Group 1] ISA Manual (covers #1, #2, #3, #4)"
download "riscv-isa-manual-20260601.pdf" \
  "https://github.com/riscv/riscv-isa-manual/releases/download/riscv-isa-release-57a68b9-2026-06-01/riscv-spec.pdf"

# ── Extensions ─────────────────────────────────────────────────────────────
echo ""
echo "[Group 2] ISA Extensions"

# #7 Bit-Manipulation
download "riscv-bitmanip-1.0.0.pdf" \
  "https://github.com/riscv/riscv-bitmanip/releases/download/1.0.0/bitmanip-1.0.0-38-g865e7a7.pdf"

# #8 Zicond
download "riscv-zicond-1.0.pdf" \
  "https://github.com/riscv/riscv-zicond/releases/download/v1.0/riscv-zicond-v1.0.pdf"

# #12 Sstc (stimecmp/vstimecmp)
download "riscv-sstc-0.5.4.pdf" \
  "https://github.com/riscv/riscv-time-compare/releases/download/v0.5.4/Sstc.pdf"

# #13 Vector V 1.0
download "riscv-vector-1.0.pdf" \
  "https://github.com/riscv/riscv-v-spec/releases/download/v1.0/riscv-v-spec-1.0.pdf"

# #27 Scalar Cryptography 1.0.1
download "riscv-crypto-scalar-1.0.1.pdf" \
  "https://github.com/riscv/riscv-crypto/releases/download/v1.0.1-scalar/riscv-crypto-spec-scalar-v1.0.1.pdf"

# #36 Zaamo / Zalrsc 1.0.0
download "riscv-zaamo-zalrsc-1.0.0.pdf" \
  "https://github.com/riscv/riscv-zaamo-zalrsc/releases/download/v1.0.0/riscv-zaamo-zalrsc.pdf"

# ── Interrupt & Memory Protection ──────────────────────────────────────────
echo ""
echo "[Group 3] Interrupt & Memory Protection"

# #18 AIA 1.0
download "riscv-aia-1.0.pdf" \
  "https://github.com/riscv/riscv-aia/releases/download/20250312/riscv-interrupts-20250312.pdf"

# #20 / #30 PLIC 1.0.0
download "riscv-plic-1.0.0.pdf" \
  "https://github.com/riscv/riscv-plic-spec/releases/download/1.0.0/riscv-plic-1.0.0.pdf"

# #10 SPMP v1.0.rc4
download "riscv-spmp-1.0-rc4.pdf" \
  "https://github.com/riscv/riscv-spmp/releases/download/v1.0.0-rc4/rv-spmp-spec.pdf"

# #23 Double Trap v1.0-rc1
download "riscv-double-trap-1.0-rc1.pdf" \
  "https://github.com/riscv/riscv-double-trap/releases/download/v1.0-rc1/riscv-double-trap.pdf"

# #24 Supervisor Software Events (Ssqosid as proxy)
download "riscv-ssqosid-1.0.pdf" \
  "https://github.com/riscv/riscv-ssqosid/releases/download/v1.0/riscv-ssqosid.pdf"

# ── I/O & Platform ─────────────────────────────────────────────────────────
echo ""
echo "[Group 4] I/O & Platform"

# #28 IOMMU
download "riscv-iommu-20260222.pdf" \
  "https://github.com/riscv-non-isa/riscv-iommu/releases/download/20260222/riscv-iommu.pdf"

# #31 SBI (latest v3.0)
download "riscv-sbi-3.0.pdf" \
  "https://github.com/riscv-non-isa/riscv-sbi-doc/releases/download/v3.0/riscv-sbi.pdf"

# ── Debug & Trace ───────────────────────────────────────────────────────────
echo ""
echo "[Group 5] Debug & Trace"

# #16 / #35 Debug 1.0-STABLE
download "riscv-debug-1.0-stable.pdf" \
  "https://github.com/riscv/riscv-debug-spec/releases/download/1.0/riscv-debug-specification.pdf"

# #32 N-Trace (Nexus-based)
download "riscv-ntrace-1.0.pdf" \
  "https://github.com/riscv-non-isa/riscv-nexus-trace/releases/download/1.0_Ratified/RISC-V-N-Trace.pdf"

# #22 / #33 Trace Control Interface
download "riscv-trace-control-1.0.pdf" \
  "https://github.com/riscv-non-isa/riscv-nexus-trace/releases/download/1.0_Ratified/RISC-V-Trace-Control-Interface.pdf"

# #34 Trace Connectors
download "riscv-trace-connectors-1.0.pdf" \
  "https://github.com/riscv-non-isa/riscv-nexus-trace/releases/download/1.0_Ratified/RISC-V-Trace-Connectors.pdf"

# ── Profiles ────────────────────────────────────────────────────────────────
echo ""
echo "[Group 6] Profiles"

# #15 Profiles (RVA23 / RVB23)
download "riscv-profiles-rva23.pdf" \
  "https://github.com/riscv/riscv-profiles/releases/download/rva23-rvb23-ratified/rva23-profile.pdf"
download "riscv-profiles-rvb23.pdf" \
  "https://github.com/riscv/riscv-profiles/releases/download/rva23-rvb23-ratified/rvb23-profile.pdf"

echo ""
echo "=============================="
echo "  下載完成，請手動補充以下項目："
echo "=============================="
echo ""
echo "  ❌ #5  Smcsrind/Sscsrind (Indirect CSR Access v1.0.0_rc7)"
echo "         → https://github.com/riscv/riscv-indirect-csr-access (無 PDF release)"
echo ""
echo "  ❌ #6  Zc* Compressed Extension v1.0.4-2"
echo "         → https://github.com/riscv/riscv-code-size-reduction (無 PDF release)"
echo ""
echo "  ❌ #9  Smepmp v1.0 (PMP Enhancements)"
echo "         → https://github.com/riscv/riscv-tee (無獨立 PDF，含於 Privileged ISA)"
echo ""
echo "  ❌ #11 SPMP for Hypervisor v0.2"
echo "         → https://github.com/riscv/riscv-spmp (無 Hypervisor 版本 release)"
echo ""
echo "  ❌ #14 CMO v1.0.1-b34ea8a (Base Cache Management Operation)"
echo "         → https://github.com/riscv/riscv-CMOs (無 PDF release)"
echo ""
echo "  ❌ #21 Zfinx/Zicsr (FP in Integer Registers) v1.0.0"
echo "         → https://github.com/riscv/riscv-zfinx (無 PDF release)"
echo ""
echo "  ❌ #25 Platform Security Model v0.1"
echo "         → https://github.com/riscv/riscv-platform-security-model (無 PDF release)"
echo ""
echo "  ❌ #26 WorldGuard v0.4"
echo "         → https://github.com/riscv/riscv-worldguard (無 PDF release)"
echo ""
echo "  ❌ #29 IOPMP (I/O Physical Memory Protection)"
echo "         → https://github.com/riscv-non-isa/iopmp-spec (無 PDF release)"
echo ""
echo "  以上 9 份建議到 https://riscv.org/technical/specifications/ 手動下載"
echo "  或請用：/usr/bin/python3 src/ingest.py 重建向量庫"
echo ""
ls -lh "$DATA_DIR"/*.pdf 2>/dev/null | awk '{print "  ✅ " $NF, "(" $5 ")"}'
