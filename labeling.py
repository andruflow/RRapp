import streamlit as st
import pandas as pd
import io
import os
from pathlib import Path
from datetime import datetime
from typing import cast

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Validación de Pacientes",
    page_icon="🏥",
    layout="wide",
)

# ── Styling ────────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
  /* Header bar */
  .header-bar {
    background: linear-gradient(90deg, #1565C0, #1976D2);
    color: white;
    padding: 14px 28px;
    border-radius: 10px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
  }
  .header-bar h1 { margin: 0; font-size: 1.6rem; }
  .header-bar .meta { font-size: 0.85rem; opacity: 0.9; text-align: right; }

  /* Subject cards in sidebar */
  .subject-card {
    background: #f0f4ff;
    border-left: 4px solid #1976D2;
    border-radius: 6px;
    padding: 8px 12px;
    margin-bottom: 6px;
    cursor: pointer;
    font-size: 0.85rem;
  }
  .subject-card.done {
    background: #f0faf3;
    border-left-color: #2e7d32;
    opacity: 0.7;
  }
  .badge-pending {
    background: #1976D2; color: white;
    border-radius: 12px; padding: 2px 8px; font-size: 0.75rem;
  }
  .badge-done {
    background: #2e7d32; color: white;
    border-radius: 12px; padding: 2px 8px; font-size: 0.75rem;
  }

  /* Field labels */
  .field-label {
    font-weight: 600; font-size: 0.8rem;
    color: #555; margin-bottom: 2px;
  }
  .field-value {
    background: #f5f5f5;
    border-radius: 6px; padding: 8px 12px;
    font-size: 0.9rem; min-height: 36px;
  }
  .field-value.report {
    font-size: 0.78rem; min-height: 130px;
    white-space: pre-wrap; line-height: 1.5;
    overflow-y: auto; max-height: 200px;
  }

  /* Progress bar */
  .progress-wrap { margin: 12px 0; }

  /* Action buttons */
  div[data-testid="stButton"] > button {
    border-radius: 8px !important;
  }
  div[data-testid="stButton"] > button[kind="primary"] {
    background-color: #1976D2 !important;
  }
</style>
""",
    unsafe_allow_html=True,
)

# ── Constants ──────────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).resolve().parent / "Data"
RAW_DIR = DATA_DIR / "Raw"
PROCESSED_DIR = DATA_DIR / "Processed"

ETIQUETA_OPTIONS = [
    "Sin hallazgos",
    "Cambios degenerativos de la columna dorsal",
    "Ateromatosis",
    "Refuerzo Intersticial Central",
    "Cardiomegalia",
    "Atelectasia",
    "Aorta elongada",
    "Hiperexpansión pulmonar",
    "Congestión Broncovascular",
    "Descartado",
    "Infiltrados reticulares",
    "Escoliosis",
    "Disminución en el tamaño pulmonar",
    "Derrame pleural",
    "Elevación del hemidiafragma",
    "Calcificaciones pulmonares residuales",
    "Fracturas de costillas",
    "Ocupación del espacio alveolar",
    "Cicatrices apicales",
    "Fractura vertebral dorsal",
    "Nódulo pulmonar",
    "Hernia hiatal",
    "Masa pulmonar",
    "Pectus excavatum",
    "Fractura de clavícula",
    "Sobrecarga de volumen",
    "Neumotórax",
    "Pectum carinatum",
    "Pneumomediastino",
]
COINCIDENCIA_OPTIONS = ["Si", "No"]
DISPOSITIVOS_OPTIONS = [
    "Sin Dispositivos",
    "Electrodos",
    "Catéter central",
    "Material de osteosíntesis",
    "Clips quirúrgicos",
    "Joyería",
    "Marcapasos",
    "Suturas de esternotomía",
    "Prótesis valvulares",
    "Desfibrilador automático implantable (DAI)",
    "Tubos pleurales",
    "Tubo torácico",
    "Estimulador nervio vago",
    "Neuroestimulador Espinal",
    "Tubos endotraqueales",
    "Stent esofágico",
    "Sonda Nasogástrica",
    "Cánula de oxígeno",
    "Traqueostomías",
    "Catéter de derivación VP",
]


# ── Session state init ─────────────────────────────────────────────────────────
def init_state():
    if "df" not in st.session_state:
        st.session_state.df = None
    if "current_idx" not in st.session_state:
        st.session_state.current_idx = None
    if "labeled_ids" not in st.session_state:
        st.session_state.labeled_ids = set()
    if "save_path" not in st.session_state:
        st.session_state.save_path = None  # path on disk to auto-save into
    if "original_filename" not in st.session_state:
        st.session_state.original_filename = "validacion.csv"
    if "last_saved" not in st.session_state:
        st.session_state.last_saved = None  # timestamp of last auto-save


init_state()


# ── Auto-save helper ───────────────────────────────────────────────────────────
def autosave():
    """Write the current dataframe back to the save_path on disk."""
    if st.session_state.df is not None and st.session_state.save_path:
        st.session_state.df.to_csv(
            st.session_state.save_path, sep=";", index=False, encoding="utf-8-sig"
        )
        st.session_state.last_saved = datetime.now().strftime("%H:%M:%S")


def get_csv_bytes():
    """Return the current dataframe as UTF-8-sig encoded CSV bytes."""
    if st.session_state.df is None:
        return b""
    return st.session_state.df.to_csv(sep=";", index=False).encode("utf-8-sig")


# ── Header ─────────────────────────────────────────────────────────────────────
now = datetime.now()
st.markdown(
    f"""
<div class="header-bar">
  <div>🏥 <strong>Validación de Pacientes</strong></div>
  <div class="meta">{now.strftime("%B %Y").capitalize()}</div>
</div>
""",
    unsafe_allow_html=True,
)


# ── Load CSV ───────────────────────────────────────────────────────────────────
def load_csv_bytes(content: bytes):
    # Try both delimiters
    for sep in [";", ","]:
        try:
            df = pd.read_csv(
                io.BytesIO(content), sep=sep, encoding="utf-8-sig", dtype=str
            )
            if len(df.columns) > 3:
                df = df.fillna("")
                return df
        except Exception:
            continue
    return None


def get_data_paths(original_filename: str):
    """
    Map an uploaded CSV filename to:
    - Data/Raw/<original_filename>
    - Data/Processed/<base>_validado.csv
    """
    base = os.path.splitext(original_filename)[0]
    raw_path = RAW_DIR / original_filename
    processed_path = PROCESSED_DIR / f"{base}_validado.csv"
    return raw_path, processed_path


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📂 Cargar archivo")
    uploaded = st.file_uploader(
        "CSV de pacientes", type=["csv"], label_visibility="collapsed"
    )

    if uploaded:
        # Only reload if it's a new file (avoid resetting on every rerun)
        if (
            uploaded.name != st.session_state.original_filename
            or st.session_state.df is None
        ):
            # Read once so we can both persist the raw file and parse it
            content = uploaded.read()
            df = load_csv_bytes(content)
            if df is not None:
                RAW_DIR.mkdir(parents=True, exist_ok=True)
                PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

                raw_path, processed_path = get_data_paths(uploaded.name)
                # Store the uploaded "book" in Data/Raw
                raw_path.write_bytes(content)

                st.session_state.df = df
                st.session_state.original_filename = uploaded.name

                # Store the continuously updated validated CSV in Data/Processed
                st.session_state.save_path = str(processed_path)
                # Write initial state to disk
                df.to_csv(
                    st.session_state.save_path,
                    sep=";",
                    index=False,
                    encoding="utf-8-sig",
                )
                # Auto-detect already labeled rows
                if "Etiqueta" in df.columns:
                    already = {
                        cast(int, i)
                        for i in df[df["Etiqueta"].str.strip() != ""].index.tolist()
                    }
                    st.session_state.labeled_ids = already
                st.success(f"{len(df)} registros cargados")

    st.markdown("---")

    if st.session_state.df is not None:
        df = st.session_state.df
        total = len(df)
        done = len(st.session_state.labeled_ids)
        pending = total - done

        # Progress
        pct = int(done / total * 100) if total > 0 else 0
        st.markdown(f"**Progreso:** {done}/{total} ({pct}%)")
        st.progress(pct / 100)

        st.markdown(f"🔵 **Pendientes:** {pending}   ✅ **Completados:** {done}")

        # ── Auto-save status + download ────────────────────────────────────────
        st.markdown("---")
        if st.session_state.last_saved:
            st.markdown(f"💾 **Guardado automático:** {st.session_state.last_saved}")
        else:
            st.markdown("💾 *Sin cambios aún*")

        # Single download button always visible once file is loaded
        csv_bytes = get_csv_bytes()
        dl_name = (
            os.path.splitext(st.session_state.original_filename)[0] + "_validado.csv"
        )
        st.download_button(
            label="⬇️ Descargar CSV actualizado",
            data=csv_bytes,
            file_name=dl_name,
            mime="text/csv",
            use_container_width=True,
            type="primary",
        )

        st.markdown("---")

        # Subject list
        st.markdown("### 📋 Lista de pacientes")

        # Filter toggle
        show_all = st.checkbox("Mostrar completados", value=False)

        for idx, row in df.iterrows():
            sid = row.get("subject_id", f"ID {idx}")
            is_done = idx in st.session_state.labeled_ids

            if not show_all and is_done:
                continue

            badge = (
                f'<span class="badge-done">✓</span>'
                if is_done
                else f'<span class="badge-pending">•</span>'
            )
            card_class = "subject-card done" if is_done else "subject-card"
            is_active = st.session_state.current_idx == idx

            label = f"{'✅' if is_done else '🔵'} {sid}"
            if st.button(
                label,
                key=f"btn_{idx}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state.current_idx = idx
                st.rerun()

# ── Main panel ─────────────────────────────────────────────────────────────────
if st.session_state.df is None:
    st.info("Carga un archivo CSV para comenzar.")


elif st.session_state.current_idx is None:
    pending_indices = [
        i for i in st.session_state.df.index if i not in st.session_state.labeled_ids
    ]
    if pending_indices:
        st.info(
            f"Selecciona un paciente de la lista. Hay **{len(pending_indices)}** pendientes."
        )
        if st.button("▶️ Iniciar con el primero", type="primary"):
            st.session_state.current_idx = pending_indices[0]
            st.rerun()
    else:
        st.success("¡Todos los pacientes han sido etiquetados!")

else:
    df = st.session_state.df
    idx = st.session_state.current_idx
    row = df.loc[idx]

    # Navigation helpers
    all_indices = list(df.index)
    pending_indices = [i for i in all_indices if i not in st.session_state.labeled_ids]
    pos_in_all = all_indices.index(idx) + 1

    # Top navigation bar
    col_nav1, col_nav2, col_nav3, col_nav4 = st.columns([2, 2, 2, 4])
    with col_nav1:
        prev_idx = (
            all_indices[all_indices.index(idx) - 1]
            if all_indices.index(idx) > 0
            else None
        )
        if st.button("◀ Anterior", disabled=prev_idx is None, use_container_width=True):
            st.session_state.current_idx = prev_idx
            st.rerun()
    with col_nav2:
        next_idx = (
            all_indices[all_indices.index(idx) + 1]
            if all_indices.index(idx) < len(all_indices) - 1
            else None
        )
        if st.button(
            "Siguiente ▶", disabled=next_idx is None, use_container_width=True
        ):
            st.session_state.current_idx = next_idx
            st.rerun()
    with col_nav3:
        if pending_indices:
            if st.button("⏭ Próximo pendiente", use_container_width=True):
                st.session_state.current_idx = pending_indices[0]
                st.rerun()
    with col_nav4:
        status = (
            "✅ Ya etiquetado"
            if idx in st.session_state.labeled_ids
            else "🔵 Pendiente"
        )
        st.markdown(
            f"**Registro {pos_in_all}/{len(all_indices)}** &nbsp; {status}",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ── Form ───────────────────────────────────────────────────────────────────
    with st.form(key=f"form_{idx}"):
        # Row 1: subject_id + study_id
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<p class="field-label">subject_id</p>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="field-value">{row.get("subject_id", "")}</div>',
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown('<p class="field-label">study_id</p>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="field-value">{row.get("study_id", "")}</div>',
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Row 2: Reporte
        st.markdown('<p class="field-label">Reporte</p>', unsafe_allow_html=True)
        report_text = row.get("Reporte", "").replace("\n", "  \n")
        st.markdown(
            """
    <style>
      textarea[disabled] {
        color: #1a1a1a !important;
        -webkit-text-fill-color: #1a1a1a !important;
        opacity: 1 !important;
      }
    </style>
    """,
            unsafe_allow_html=True,
        )
        st.text_area(
            "Reporte_display",
            value=row.get("Reporte", ""),
            height=400,
            disabled=True,
            label_visibility="collapsed",
        )

        # Row 3: URL Imagen + Coincidencia
        c3, c4 = st.columns(2)
        with c3:
            st.markdown('<p class="field-label">URL Imagen</p>', unsafe_allow_html=True)
            url_val = row.get("URL", "")
            if url_val:
                st.markdown(
                    f'<div class="field-value"><a href="{url_val}" target="_blank">🔗 Abrir imagen</a></div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown('<div class="field-value">—</div>', unsafe_allow_html=True)
        with c4:
            current_coinc = row.get("Coincidencia", "")
            coinc_idx = (
                COINCIDENCIA_OPTIONS.index(current_coinc)
                if current_coinc in COINCIDENCIA_OPTIONS
                else 0
            )
            coincidencia = st.selectbox(
                "* Coincidencia", COINCIDENCIA_OPTIONS, index=coinc_idx
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Row 4: Dispositivos + Etiqueta
        c5, c6 = st.columns(2)
        with c5:
            current_disp = row.get("Dispositivos_", "")
            current_disp_list = (
                [d.strip() for d in current_disp.split(",") if d.strip()]
                if isinstance(current_disp, str) and current_disp
                else (current_disp if isinstance(current_disp, list) else [])
            )
            dispositivos = st.multiselect(
                "* Dispositivos",
                DISPOSITIVOS_OPTIONS,
                default=[d for d in current_disp_list if d in DISPOSITIVOS_OPTIONS],
            )
        with c6:
            current_etiq = row.get("Etiqueta", "")
            current_etiq_list = (
                [e.strip() for e in current_etiq.split(",") if e.strip()]
                if isinstance(current_etiq, str) and current_etiq
                else (current_etiq if isinstance(current_etiq, list) else [])
            )

            etiqueta = st.multiselect(
                "* Etiqueta",
                ETIQUETA_OPTIONS,
                default=[e for e in current_etiq_list if e in ETIQUETA_OPTIONS],
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Row 5: Observacion
        current_obs = row.get("Observacion", "")
        observacion = st.text_area("Observacion", value=current_obs, height=120)

        st.markdown("<br>", unsafe_allow_html=True)

        # Submit
        col_s1, col_s2, col_s3 = st.columns([2, 2, 4])
        with col_s1:
            submitted = st.form_submit_button(
                "💾 Agregar", type="primary", use_container_width=True
            )
        with col_s2:
            skip = st.form_submit_button("⏩ Omitir", use_container_width=True)

        if submitted:
            # Validate required fields
            if not coincidencia:
                st.error("⚠️ El campo **Coincidencia** es obligatorio.")
            elif not dispositivos:
                st.error("⚠️ El campo **Dispositivos** es obligatorio.")
            else:
                # Save back to dataframe
                st.session_state.df.at[idx, "Coincidencia"] = coincidencia
                st.session_state.df.at[idx, "Dispositivos_"] = dispositivos
                st.session_state.df.at[idx, "Etiqueta"] = etiqueta
                st.session_state.df.at[idx, "Observacion"] = observacion
                st.session_state.df.at[idx, "Modificado"] = datetime.now().strftime(
                    "%m/%d/%Y %I:%M:00 %p"
                )
                # Mark as labeled
                st.session_state.labeled_ids.add(cast(int, idx))
                # ── Auto-save to disk ──────────────────────────────────────
                autosave()
                st.success(
                    f"✅ Paciente **{row.get('subject_id', '')}** guardado — archivo actualizado automáticamente."
                )
                # Auto-advance to next pending
                remaining = [i for i in pending_indices if i != idx]
                if remaining:
                    st.session_state.current_idx = remaining[0]
                else:
                    st.session_state.current_idx = None
                st.rerun()

        if skip:
            if next_idx is not None:
                st.session_state.current_idx = next_idx
            elif pending_indices:
                st.session_state.current_idx = pending_indices[0]
            st.rerun()

    st.markdown("---")

# ── Export note ────────────────────────────────────────────────────────────────
# Download button lives in the sidebar; no separate export section needed.
