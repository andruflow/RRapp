# RRAv0_1.py - Validación de Pacientes

## Run
`streamlit run RRAv0_1.py`

## How to use
1. In the sidebar, upload the patient CSV (`.csv`). The app accepts `;` or `,` as the delimiter.
2. For each patient, fill:
   - `Coincidencia` (required)
   - `Dispositivos` (required; select at least one)
   - `Etiqueta`
   - `Observacion`
3. Click `Agregar` to save the updates for that patient.
4. Use `Descargar CSV actualizado` in the sidebar to download the latest validated CSV.

## Files written to disk
- Uploaded CSV is stored as `Data/Raw/<original_filename>`.
- Validated CSV is continuously saved to `Data/Processed/<base>_validado.csv`,
  where `<base>` is the uploaded filename without the extension (e.g. `Book1.csv` -> `Data/Processed/Book1_validado.csv`).

## Expected columns
The app reads columns like `subject_id`, `study_id`, `Reporte`, `URL`, `Etiqueta`, `Dispositivos_`, `Coincidencia`, and `Observacion`.
If `Etiqueta` exists, already-labeled rows (non-empty `Etiqueta`) are detected automatically.

