from __future__ import annotations

import csv
from io import BytesIO, StringIO

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import streamlit as st

PCIE = {
    "Gen 1 (2.5 GT/s)": {"rate": 2.5, "encoding": "8b/10b", "encoding_eff": 8 / 10},
    "Gen 2 (5.0 GT/s)": {"rate": 5.0, "encoding": "8b/10b", "encoding_eff": 8 / 10},
    "Gen 3 (8.0 GT/s)": {"rate": 8.0, "encoding": "128b/130b", "encoding_eff": 128 / 130},
    "Gen 4 (16 GT/s)": {"rate": 16.0, "encoding": "128b/130b", "encoding_eff": 128 / 130},
    "Gen 5 (32 GT/s)": {"rate": 32.0, "encoding": "128b/130b", "encoding_eff": 128 / 130},
}
LANES = (1, 2, 4, 8, 16)
SIZES = (1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024)


def bandwidth_gbps(generation: str, lanes: int) -> float:
    spec = PCIE[generation]
    return spec["rate"] * lanes * spec["encoding_eff"] / 8.0


def latency_us(payload_kib: float, payload_bandwidth_gbps: float,
               fixed_latency_us: float, switch_count: int,
               switch_latency_us: float) -> float:
    if payload_bandwidth_gbps <= 0:
        raise ValueError("Băng thông phải lớn hơn 0.")
    transfer_us = payload_kib * 1024.0 / (payload_bandwidth_gbps * 1e9) * 1e6
    return fixed_latency_us + switch_count * switch_latency_us + transfer_us


def csv_bytes(rows: list[list[object]]) -> bytes:
    output = StringIO(newline="")
    writer = csv.writer(output)
    writer.writerows(rows)
    return output.getvalue().encode("utf-8-sig")


def png_bytes(fig: plt.Figure) -> bytes:
    output = BytesIO()
    fig.savefig(output, format="png", dpi=180, bbox_inches="tight")
    return output.getvalue()


st.set_page_config(page_title="PCIe Modeler – Bandwidth & Latency", page_icon="📊", layout="wide")
st.title("MÔ HÌNH HÓA HIỆU NĂNG PCI EXPRESS")
st.caption("Tính băng thông lý thuyết sau mã hóa và ước lượng thời gian truyền payload theo các giả định mô phỏng.")

tab_band, tab_lat = st.tabs(["1. BANDWIDTH", "2. LATENCY"])

with tab_band:
    controls, chart = st.columns([1, 2.05], gap="large")
    with controls:
        st.subheader("Thông số đầu vào")
        gen_b = st.selectbox("Thế hệ PCIe", list(PCIE), index=2, key="band_gen")
        eff_b_pct = st.number_input("Hiệu suất giao thức (%)", min_value=1.0,
                                    max_value=100.0, value=90.0, step=1.0, key="band_eff")
        st.caption("Giá trị 90% chỉ là giả định để ước lượng payload; có thể đổi 100% để xem giới hạn sau mã hóa đường truyền.")
        eff_b = eff_b_pct / 100.0
        encoded = [bandwidth_gbps(gen_b, lane) for lane in LANES]
        payload_bw_values = [value * eff_b for value in encoded]
        spec = PCIE[gen_b]
        st.subheader("Kết quả cấu hình x16")
        st.metric("BW sau mã hóa", f"{encoded[-1]:.3f} GB/s")
        st.metric("BW payload ước tính", f"{payload_bw_values[-1]:.3f} GB/s")
        st.caption(f"Tốc độ: {spec['rate']:g} GT/s/lane | Mã hóa: {spec['encoding']}")

    with chart:
        st.subheader("Băng thông theo số lane (mỗi chiều truyền)")
        fig_b, ax_b = plt.subplots(figsize=(8, 5))
        positions = list(range(len(LANES)))
        width = 0.36
        ax_b.bar([p - width / 2 for p in positions], encoded, width, label="Sau mã hóa đường truyền")
        ax_b.bar([p + width / 2 for p in positions], payload_bw_values, width, label="Payload ước tính")
        ax_b.set_xticks(positions, [f"x{x}" for x in LANES])
        ax_b.set_xlabel("Số lane")
        ax_b.set_ylabel("Băng thông (GB/s)")
        ax_b.set_title(f"{gen_b} – hiệu suất giả định {eff_b_pct:.1f}%")
        ax_b.grid(axis="y", alpha=0.25)
        ax_b.legend()
        fig_b.tight_layout()
        st.pyplot(fig_b)
        band_rows = [
            ["PCIe generation", gen_b],
            ["Encoding", spec["encoding"]],
            ["Protocol efficiency assumption (%)", eff_b_pct],
            [],
            ["Lanes", "Encoded bandwidth GB/s per direction", "Estimated payload GB/s per direction"],
            *[[lane, f"{value:.6f}", f"{value * eff_b:.6f}"] for lane, value in zip(LANES, encoded)],
        ]
        button_a, button_b = st.columns(2)
        with button_a:
            st.download_button("⬇ Xuất dữ liệu CSV", csv_bytes(band_rows),
                               "pcie_bandwidth_data.csv", "text/csv", key="band_csv", use_container_width=True)
        with button_b:
            st.download_button("⬇ Lưu biểu đồ PNG", png_bytes(fig_b),
                               "pcie_bandwidth.png", "image/png", key="band_png", use_container_width=True)
        plt.close(fig_b)

with tab_lat:
    controls, chart = st.columns([1, 2.05], gap="large")
    with controls:
        st.subheader("Thông số đầu vào")
        gen_l = st.selectbox("Thế hệ PCIe", list(PCIE), index=2, key="lat_gen")
        lanes_l = st.selectbox("Số lane", LANES, index=2, format_func=lambda x: f"x{x}", key="lat_lanes")
        eff_l_pct = st.number_input("Hiệu suất payload (%)", min_value=1.0,
                                    max_value=100.0, value=90.0, step=1.0, key="lat_eff")
        payload_kib = st.number_input("Kích thước payload (KiB)", min_value=0.01,
                                      max_value=1_000_000.0, value=64.0, key="lat_payload")
        fixed = st.number_input("Độ trễ cố định T₀ (µs)", min_value=0.0,
                                max_value=1_000_000.0, value=2.0, key="lat_fixed")
        switches = st.number_input("Số PCIe Switch", min_value=0, max_value=100,
                                   value=0, step=1, key="lat_switches")
        switch_delay = st.number_input("Độ trễ mỗi Switch (µs)", min_value=0.0,
                                       max_value=1_000_000.0, value=0.5, key="lat_switch_delay")
        st.caption("T₀ và độ trễ Switch là GIẢ ĐỊNH minh họa, không phải trị số cố định của chuẩn PCIe. Mô hình chưa mô phỏng từng gói TLP/DLLP hay thời gian round-trip của lệnh đọc.")
        payload_bw = bandwidth_gbps(gen_l, lanes_l) * eff_l_pct / 100.0
        transfer = payload_kib * 1024.0 / (payload_bw * 1e9) * 1e6
        total = latency_us(payload_kib, payload_bw, fixed, switches, switch_delay)
        st.subheader("Kết quả tại payload nhập vào")
        st.metric("BW payload ước tính", f"{payload_bw:.3f} GB/s")
        st.metric("Thời gian truyền payload", f"{transfer:.3f} µs")
        st.metric("Tổng độ trễ mô hình", f"{total:.3f} µs")

    with chart:
        st.subheader("Độ trễ theo kích thước payload")
        times = [latency_us(size, payload_bw, fixed, switches, switch_delay) for size in SIZES]
        fig_l, ax_l = plt.subplots(figsize=(8, 5))
        ax_l.plot(SIZES, times, marker="o", label="Tổng độ trễ mô hình")
        ax_l.axvline(payload_kib, linestyle="--", alpha=0.7, label=f"Payload nhập: {payload_kib:g} KiB")
        ax_l.set_xscale("log", base=2)
        ax_l.set_xticks(SIZES, [str(size) for size in SIZES])
        ax_l.set_xlabel("Kích thước payload (KiB, thang log₂)")
        ax_l.set_ylabel("Thời gian (µs)")
        ax_l.set_title(f"{gen_l}, x{lanes_l} | BW payload = {payload_bw:.3f} GB/s")
        ax_l.grid(True, which="both", alpha=0.25)
        ax_l.legend()
        fig_l.tight_layout()
        st.pyplot(fig_l)
        latency_rows = [
            ["PCIe generation", gen_l],
            ["Lanes", lanes_l],
            ["Estimated payload bandwidth GB/s", f"{payload_bw:.6f}"],
            ["Protocol efficiency assumption (%)", eff_l_pct],
            ["Fixed latency T0 assumption (us)", fixed],
            ["Number of switches", switches],
            ["Latency per switch assumption (us)", switch_delay],
            [],
            ["Payload (KiB)", "Transfer time (us)", "Total modeled latency (us)"],
            *[[size, f"{size * 1024 / (payload_bw * 1e9) * 1e6:.6f}", f"{time:.6f}"]
              for size, time in zip(SIZES, times)],
        ]
        button_a, button_b = st.columns(2)
        with button_a:
            st.download_button("⬇ Xuất dữ liệu CSV", csv_bytes(latency_rows),
                               "pcie_latency_data.csv", "text/csv", key="lat_csv", use_container_width=True)
        with button_b:
            st.download_button("⬇ Lưu biểu đồ PNG", png_bytes(fig_l),
                               "pcie_latency.png", "image/png", key="lat_png", use_container_width=True)
        plt.close(fig_l)
