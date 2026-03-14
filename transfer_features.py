import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def _detect_numeric_start(df):
    if df.shape[1] < 2:
        return 0
    col0 = pd.to_numeric(df.iloc[:, 0], errors="coerce")
    col1 = pd.to_numeric(df.iloc[:, 1], errors="coerce")
    mask = col0.notna() & col1.notna()
    idx = np.where(mask.values)[0]
    return int(idx[0]) if idx.size else 0


def _sniff_delimiter_and_cols(file_path, max_lines=50):
    delimiters = [",", "\t", ";"]
    best_delim = ","
    best_cols = 0
    try:
        with open(file_path, "r", errors="ignore") as f:
            lines = []
            for _ in range(max_lines):
                line = f.readline()
                if not line:
                    break
                lines.append(line)
    except OSError:
        return best_delim, 2

    for delim in delimiters:
        max_cols = 0
        for line in lines:
            parts = line.rstrip("\n").split(delim)
            if len(parts) > max_cols:
                max_cols = len(parts)
        if max_cols > best_cols:
            best_cols = max_cols
            best_delim = delim

    if best_cols < 2:
        best_cols = 2
    return best_delim, best_cols


def load_transfer_data(file_path):
    delim, ncols = _sniff_delimiter_and_cols(file_path)
    df = pd.read_csv(
        file_path,
        header=None,
        sep=delim,
        names=list(range(ncols)),
        engine="python",
        on_bad_lines="skip",
    )

    if df.empty or df.shape[1] < 2:
        return None, None

    start = _detect_numeric_start(df)
    data = df.iloc[start:].copy()

    vg = pd.to_numeric(data.iloc[:, 0], errors="coerce")
    idc = pd.to_numeric(data.iloc[:, 1], errors="coerce")
    valid = vg.notna() & idc.notna()
    return vg[valid].values, idc[valid].values


def split_sweeps_by_turning_point(x, y):
    x = np.asarray(x)
    y = np.asarray(y)
    if x.size < 3:
        return [("sweep1", x, y)]

    dx = np.diff(x)
    non_zero = np.where(dx != 0)[0]
    if non_zero.size == 0:
        return [("sweep1", x, y)]

    direction = np.sign(dx[non_zero[0]])
    if direction == 0:
        return [("sweep1", x, y)]

    change_idx = None
    for i in range(non_zero[0] + 1, dx.size):
        if dx[i] == 0:
            continue
        if np.sign(dx[i]) != direction:
            change_idx = i + 1
            break

    if change_idx is None:
        return [("sweep1", x, y)]

    return [
        ("sweep1", x[:change_idx], y[:change_idx]),
        ("sweep2", x[change_idx:], y[change_idx:]),
    ]


def infer_device_type(vg, idc):
    id_abs = np.abs(idc)
    id_abs[id_abs <= 0] = 1e-20
    log_id = np.log10(id_abs)
    if len(vg) < 2:
        return "n"
    slope = np.polyfit(vg, log_id, 1)[0]
    return "n" if slope >= 0 else "p"


def compute_onoff_ratio(idc):
    id_abs = np.abs(idc)
    id_abs[id_abs <= 0] = 1e-20
    id_min = id_abs.min()
    id_max = id_abs.max()
    onoff = id_max / id_min if id_min != 0 else np.inf
    return onoff, id_min, id_max


def compute_ss(vg, idc):
    id_abs = np.abs(idc)
    id_abs[id_abs <= 0] = 1e-20
    log_id = np.log10(id_abs)
    mask = (log_id > -10) & (log_id < -6)
    if np.sum(mask) < 5:
        mask = (log_id > log_id.min() + 0.2) & (log_id < log_id.min() + 4)

    vg_fit = vg[mask]
    log_id_fit = log_id[mask]
    if len(vg_fit) < 2:
        return np.nan, None

    coeff = np.polyfit(vg_fit, log_id_fit, 1)
    slope = coeff[0]
    ss = 1 / abs(slope) if slope != 0 else np.nan
    return ss, (vg_fit, np.polyval(coeff, vg_fit))


def compute_gm(vg, idc):
    if len(vg) < 2:
        return np.array([]), np.nan
    gm = np.gradient(idc, vg)
    if gm.size == 0:
        return gm, np.nan
    max_gm = np.nanmax(np.abs(gm))
    return gm, max_gm


def compute_vth_info(vg, idc, device_type):
    y = np.sqrt(np.abs(idc))
    slopes = np.gradient(y, vg)
    slopes = np.where(np.isfinite(slopes), slopes, np.nan)
    if np.all(np.isnan(slopes)):
        return {
            "Vth": np.nan,
            "x0": np.nan,
            "y0": np.nan,
            "slope": np.nan,
            "tangent_x": np.array([]),
            "tangent_y": np.array([]),
        }

    if device_type == "p":
        idx = int(np.nanargmin(slopes))
    else:
        idx = int(np.nanargmax(slopes))

    x0 = vg[idx]
    y0 = y[idx]
    slope = slopes[idx]
    Vth = x0 - y0 / slope if slope not in (0, np.nan) else np.nan

    tangent_x = np.linspace(np.min(vg), np.max(vg), 200)
    tangent_y = y0 + slope * (tangent_x - x0)
    mask = tangent_y >= 0
    tangent_x = tangent_x[mask]
    tangent_y = tangent_y[mask]

    return {
        "Vth": Vth,
        "x0": x0,
        "y0": y0,
        "slope": slope,
        "tangent_x": tangent_x,
        "tangent_y": tangent_y,
    }


def plot_transfer_summary(
    vg,
    idc,
    ss_fit,
    gm,
    vth_info,
    onoff,
    max_id,
    max_gm,
    device_type,
    title,
    output_path,
):
    id_abs = np.abs(idc)
    id_abs[id_abs <= 0] = 1e-20
    log_id = np.log10(id_abs)
    sqrt_id = np.sqrt(id_abs)

    plt.figure(figsize=(12, 9))

    ax1 = plt.subplot(2, 2, 1)
    ax1.plot(vg, id_abs, "b.-")
    ax1.set_yscale("log")
    ax1.set_xlabel("Vg (V)")
    ax1.set_ylabel("|Id| (A)")
    ax1.set_title("|Id| vs Vg (log)")
    ax1.grid(True, which="both", linestyle="--", alpha=0.5)
    ax1.text(0.02, 0.98, f"On/Off: {onoff:.2e}\nMax |Id|: {max_id:.2e}",
             transform=ax1.transAxes, va="top")

    ax2 = plt.subplot(2, 2, 2)
    ax2.plot(vg, sqrt_id, "b.-", label="sqrt|Id|")
    if vth_info["tangent_x"].size > 0:
        ax2.plot(vth_info["tangent_x"], vth_info["tangent_y"], "r--", label="Tangent")
    if np.isfinite(vth_info["Vth"]):
        ax2.scatter(vth_info["Vth"], 0, c="green", s=30, label=f"Vth={vth_info['Vth']:.3f}")
    ax2.set_xlabel("Vg (V)")
    ax2.set_ylabel(r"$\sqrt{|Id|}$")
    ax2.set_title(f"Vth ({device_type}-type)")
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(loc="best")

    ax3 = plt.subplot(2, 2, 3)
    ax3.plot(vg, log_id, "b.-", label="log|Id|")
    if ss_fit is not None:
        fit_vg, fit_line = ss_fit
        ax3.plot(fit_vg, fit_line, "r--", label="SS fit")
    ax3.set_xlabel("Vg (V)")
    ax3.set_ylabel("log|Id| (A)")
    ax3.set_title("Subthreshold region")
    ax3.grid(True, linestyle="--", alpha=0.5)
    ax3.legend(loc="best")

    ax4 = plt.subplot(2, 2, 4)
    if gm.size > 0:
        ax4.plot(vg, gm, "b.-")
    ax4.set_xlabel("Vg (V)")
    ax4.set_ylabel("gm (S)")
    ax4.set_title("gm vs Vg")
    ax4.grid(True, linestyle="--", alpha=0.5)
    ax4.text(0.02, 0.98, f"Max |gm|: {max_gm:.2e}",
             transform=ax4.transAxes, va="top")

    plt.suptitle(title)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(output_path, dpi=300)
    plt.close()


def extract_features_for_sweep(vg, idc, device_type):
    if device_type == "auto":
        device_type = infer_device_type(vg, idc)

    onoff, _, max_id = compute_onoff_ratio(idc)
    ss, ss_fit = compute_ss(vg, idc)
    gm, max_gm = compute_gm(vg, idc)
    vth_info = compute_vth_info(vg, idc, device_type)

    return {
        "device_type": device_type,
        "onoff": onoff,
        "ss": ss,
        "max_id": max_id,
        "max_gm": max_gm,
        "gm": gm,
        "vth_info": vth_info,
        "ss_fit": ss_fit,
    }


def ensure_dir(path):
    if path and not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
