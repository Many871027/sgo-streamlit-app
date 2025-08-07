import streamlit as st
import requests
import pandas as pd
from datetime import date, timedelta
import re

# --- Page Configuration ---
st.set_page_config(
    page_title="SGO - Limpieza e Higiene HGSZ 33",
    page_icon="📋",
    layout="wide"
)

# --- API Configuration ---
API_URL = "https://sgo-api-service-479752447685.us-central1.run.app"

# --- User Authentication ---
VALID_USERS = {
    "supervisores.33": "sgo2025",
    "ayudante.matutino": "pass123",
    "ayudante.vespertino": "pass456"
}

def check_password():
    """Returns `True` if the user is logged in, `False` otherwise."""
    if st.session_state.get("logged_in", False):
        return True

    st.title("SGO - Inicio de Sesión")
    st.write("Por favor, ingrese sus credenciales para continuar.")

    with st.form("login_form"):
        username = st.text_input("Usuario", key="login_user").lower()
        password = st.text_input("Contraseña", type="password", key="login_pass")
        submitted = st.form_submit_button("Iniciar Sesión")

        if submitted:
            if username in VALID_USERS and VALID_USERS[username] == password:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")
    return False

# --- Data Fetching Functions ---
@st.cache_data(ttl=300)
def get_plazas():
    try:
        response = requests.get(f"{API_URL}/plazas/")
        response.raise_for_status()
        df = pd.DataFrame(response.json())
        df['display_name'] = df['nombre_actual'] + " (" + df['plaza'] + ")"
        return df
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to API: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def get_incidentes(fecha):
    try:
        params = {"fecha": fecha.isoformat()}
        response = requests.get(f"{API_URL}/incidentes/", params=params)
        response.raise_for_status()
        return {item['plaza_id']: item['tipo_incidencia'] for item in response.json()}
    except requests.exceptions.RequestException:
        return {}

@st.cache_data(ttl=60)
def get_asignaciones(fecha, turno):
    try:
        params = {"fecha": fecha.isoformat(), "turno": turno}
        response = requests.get(f"{API_URL}/asignaciones/", params=params)
        response.raise_for_status()
        return {item['plaza_id']: item['area_servicio'] for item in response.json()}
    except requests.exceptions.RequestException:
        return {}

@st.cache_data(ttl=60)
def get_overtime_records(start_date, end_date):
    try:
        params = {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()}
        response = requests.get(f"{API_URL}/tiempo-extra/", params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return []

@st.cache_data(ttl=60)
def get_substitutions_by_range(start_date, end_date):
    try:
        params = {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()}
        response = requests.get(f"{API_URL}/sustituciones/range/", params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return []

@st.cache_data(ttl=60)
def get_coverage_needs():
    try:
        response = requests.get(f"{API_URL}/coberturas-necesarias/")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return []

# --- Helper Function to Determine Day Off ---
def is_day_off(selected_date, descanso_str):
    if pd.isna(descanso_str) or descanso_str.strip() == "": return False
    weekday = selected_date.weekday()
    descanso = str(descanso_str).upper().strip()
    if "LAV" in descanso: return weekday in [0, 1, 2, 3, 4]
    day_checks = {
        0: ["L", "LUNES", "L M"], 1: ["M", "MARTES", "M M"], 2: ["X", "MIERCOLES", "M M"],
        3: ["J", "JUEVES", "J V"], 4: ["V", "VIERNES", "V S"], 5: ["S", "SABADO", "V S", "S D"],
        6: ["D", "DOMINGO", "D L", "S D"]
    }
    for check_str in day_checks.get(weekday, []):
        if check_str in descanso: return True
    return False

# --- Definitive Shift Filtering Logic ---
def get_active_workers_for_shift(plazas_df, selected_date, selected_shift):
    selected_weekday = selected_date.weekday()  # Monday is 0, Sunday is 6
    active_workers = []

    # Mapa de días de descanso: Asocia el string de descanso con los números de día de la semana
    # Lunes=0, Martes=1, Miércoles=2, Jueves=3, Viernes=4, Sábado=5, Domingo=6
    rest_day_map = {
        "L M": [0, 1], "M M": [1, 2], "M J": [2, 3],
        "J V": [3, 4], "V S": [4, 5], "S D": [5, 6],
        "D L": [6, 0]
    }
    # Mapa de descanso para turno nocturno
    night_shift_pattern = {
        'DOMINGO': [0, 2, 4], 'SABADO': [6, 1, 3], 'VIERNES': [5, 0, 2],
        'JUEVES': [4, 6, 1], 'MIERCOLES': [3, 5, 0], 'MARTES': [2, 4, 6],
        'LUNES': [1, 3, 5]
    }
    day_map = {'L': 0, 'M': 1, 'X': 2, 'J': 3, 'V': 4, 'S': 5, 'D': 6}

    for index, worker in plazas_df.iterrows():
        is_active = False
        horario = str(worker.get('horario', '')).upper()
        descanso = str(worker.get('dias_descanso', '')).upper().strip()

        # Case 1: Jornada Acumulada (LAV descanso)
        if "LAV" in descanso:
            if selected_weekday == 5 and selected_shift in ["Matutino", "Vespertino"]:
                is_active = True
            elif selected_weekday == 6:  # Sunday, active in all shifts
                is_active = True
        
        # Case 2: Turno Nocturno
        elif "A 08.10" in horario and selected_shift == "Nocturno":
            # Use the full name of the rest day for the pattern
            if descanso in night_shift_pattern:
                if selected_weekday in night_shift_pattern[descanso]:
                    is_active = True

        # Case 3: Turno Matutino/Vespertino (LÓGICA CORREGIDA)
        # Case 2: Turno Nocturno (sin cambios)
        elif "A 08.10" in horario and selected_shift == "Nocturno":
            if descanso in night_shift_pattern:
                if selected_weekday in night_shift_pattern[descanso]:
                    is_active = True

        # Case 3: Turno Matutino/Vespertino (LÓGICA CORREGIDA)
        else:
            is_matutino = "7.00" in horario and selected_shift == "Matutino"
            is_vespertino = "14.00" in horario and selected_shift == "Vespertino"
            
            if is_matutino or is_vespertino:
                # Se asume que el trabajador labora, a menos que se demuestre lo contrario
                is_active = True 
                
                # Verificamos si el día seleccionado coincide con sus días de descanso
                if descanso in rest_day_map:
                    if selected_weekday in rest_day_map[descanso]:
                        is_active = False # Si está de descanso, no está activo
                
        if is_active:
            active_workers.append(worker)

    return pd.DataFrame(active_workers)


# --- Main Application Logic ---
def main_app():
    st.sidebar.title(f"Bienvenido, {st.session_state['username']}!")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state["logged_in"] = False
        st.rerun()

    st.title("📋 SGO - Limpieza e Higiene HGSZ 33")

    plazas_df = get_plazas()

    if plazas_df.empty:
        st.warning("Could not load employee data from the API.")
    else:
        tab1, tab2, tab3, tab4 = st.tabs(["Registrar Incidencia", "Registrar Sustitución", "Registrar Tiempo Extra", "Asignar Servicios"])

        with tab1:
            st.header("Registro de Incidencias por Turno")
            col1, col2 = st.columns(2)
            with col1:
                inc_date = st.date_input("Seleccione la Fecha:", value=date.today(), key="inc_page_date")
            with col2:
                inc_turno = st.selectbox("Seleccione el Turno:", ["Matutino", "Vespertino", "Nocturno"], key="inc_page_turno")

            active_workers_df = get_active_workers_for_shift(plazas_df, inc_date, inc_turno)
            
            incidentes_existentes = get_incidentes(inc_date)
            st.markdown("---")
            st.subheader(f"Personal Activo del Turno {inc_turno} para el {inc_date.strftime('%d/%m/%Y')}")
            
            if active_workers_df.empty:
                st.info("No hay personal programado para este turno en la fecha seleccionada.")
            else:
                incident_options = ["Asistencia", "Falta", "Incapacidad", "TXT", "Pase", "Vacaciones", "Beca", "Licencia", "Comision"]
                incident_selections = {}

                for index, row in active_workers_df.iterrows():
                    default_incidente = incidentes_existentes.get(row['plaza'], "Asistencia")
                    try:
                        default_index = incident_options.index(default_incidente)
                    except ValueError:
                        default_index = 0
                    c1, c2 = st.columns([2, 3])
                    with c1:
                        st.write(row['nombre_actual'])
                        st.caption(f"Plaza: {row['plaza']}")
                    with c2:
                        incident_selections[row['plaza']] = st.selectbox("Estatus:", options=incident_options, index=default_index, key=f"incident_select_{row['plaza']}")
                
                if st.button("Guardar Incidencias del Turno", key="save_incidents"):
                    with st.spinner("Guardando..."):
                        for plaza_id, tipo_incidencia in incident_selections.items():
                            payload = {"plaza_id": plaza_id, "fecha_incidente": inc_date.isoformat(), "tipo_incidencia": tipo_incidencia, "descripcion": f"Registrado desde la plantilla del turno {inc_turno}"}
                            try:
                                requests.post(f"{API_URL}/incidentes/", json=payload).raise_for_status()
                            except requests.exceptions.RequestException as e:
                                st.warning(f"No se pudo guardar la incidencia para la plaza {plaza_id}: {e}")
                        st.success("¡Se guardaron los registros con éxito!")
                        st.cache_data.clear()

        with tab2:
            st.header("Planificación y Registro de Sustituciones")
            st.subheader("Dashboard de Planeación Quincenal de Sustituciones")
            
            sub_q_start_date = st.date_input("Seleccione el inicio de la quincena:", value=date.today(), key="sub_q_date")
            sub_q_end_date = sub_q_start_date + timedelta(days=14)
            
            substitution_records = get_substitutions_by_range(sub_q_start_date, sub_q_end_date)
            
            sub_daily_assignments = {}
            if substitution_records:
                plaza_to_name_map = plazas_df.set_index('plaza')['nombre_actual'].to_dict()
                plaza_to_horario_map = plazas_df.set_index('plaza')['horario'].to_dict()

                for record in substitution_records:
                    record_date = date.fromisoformat(record['fecha'])
                    ausente_name = plaza_to_name_map.get(record['plaza_ausente_id'], 'N/A')
                    suplente_name = plaza_to_name_map.get(record['plaza_suplente_id'], 'N/A')
                    ausente_horario = plaza_to_horario_map.get(record['plaza_ausente_id'], '')
                    
                    shift_display = "N/A"
                    if "7.00" in ausente_horario: shift_display = "Mat."
                    elif "14.00" in ausente_horario: shift_display = "Vesp."
                    elif "A 08.10" in ausente_horario: shift_display = "Noct."
                    
                    display_text = f"{ausente_name} ({shift_display}) ➡️ {suplente_name}"
                    
                    if record_date not in sub_daily_assignments:
                        sub_daily_assignments[record_date] = []
                    sub_daily_assignments[record_date].append(display_text)

            st.markdown("---")
            
            days_of_week = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
            current_date = sub_q_start_date
            
            for week in range(3):
                cols = st.columns(7)
                for i in range(7):
                    if current_date <= sub_q_end_date:
                        day_str = days_of_week[current_date.weekday()]
                        assigned_subs = sub_daily_assignments.get(current_date, [])
                        
                        with cols[i]:
                            if assigned_subs:
                                st.info(f"**{day_str} {current_date.day}**")
                                with st.expander(f"Sustituciones: {len(assigned_subs)}"):
                                    for sub in assigned_subs: st.write(f"• {sub}")
                            else:
                                st.success(f"**{day_str} {current_date.day}**")
                                st.caption("Sin Sustituciones")
                        current_date += timedelta(days=1)
                if current_date > sub_q_end_date:
                    break
            
            st.markdown("---")

            st.subheader("Formulario de Sustitución de Trabajador")
            with st.form("substitution_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    sustituido_display = st.selectbox("Trabajador Sustituido (Ausente):", options=plazas_df['display_name'], key="sub_sustituido")
                    sustituido_details = plazas_df[plazas_df['display_name'] == sustituido_display].iloc[0]
                    st.caption(f"**Categoría:** {sustituido_details['categoria']}\n\n**Horario:** {sustituido_details['horario']}")
                with col2:
                    sustituto_display = st.selectbox("Trabajador Sustituto (Cubre):", options=plazas_df['display_name'], key="sub_sustituto")
                    sustituto_details = plazas_df[plazas_df['display_name'] == sustituto_display].iloc[0]
                    st.caption(f"**Categoría:** {sustituto_details['categoria']}\n\n**Horario:** {sustituto_details['horario']}")
                st.markdown("---")
                sustitucion_date = st.date_input("Fecha de Sustitución:", value=date.today(), key="sub_date")
                horario_a_sustituir = st.text_input("Horario a Sustituir:", placeholder="Ej: 07:00 a 15:00")
                motivo_sub = st.text_input("Motivo Adicional (Opcional):", key="sub_motivo")
                if st.form_submit_button("Registrar Sustitución"):
                    if sustituido_display == sustituto_display:
                        st.error("El trabajador sustituido y el sustituto no pueden ser la misma persona.")
                    else:
                        sustituido_id = sustituido_details['plaza']
                        sustituto_id = sustituto_details['plaza']
                        full_motivo = f"Horario a sustituir: {horario_a_sustituir}. Motivo: {motivo_sub or 'N/A'}"
                        payload = {"fecha": sustitucion_date.isoformat(), "plaza_ausente_id": sustituido_id, "plaza_suplente_id": sustituto_id, "motivo": full_motivo}
                        try:
                            requests.post(f"{API_URL}/sustituciones/", json=payload).raise_for_status()
                            st.success("¡Sustitución registrada con éxito!")
                            st.cache_data.clear()
                            st.rerun()
                        except requests.exceptions.RequestException as e:
                            st.error(f"Error al registrar la sustitución: {e}")

        with tab3:
            st.header("Planificación y Registro de Tiempo Extraordinario")
            st.subheader("Planificar Coberturas Necesarias")

            with st.form("coverage_need_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    absent_worker_display = st.selectbox("Trabajador Ausente:", options=plazas_df['display_name'])
                with col2:
                    absence_period = st.date_input("Periodo de Ausencia (Del - Al):", [date.today(), date.today() + timedelta(days=7)])
                
                if st.form_submit_button("Añadir Necesidad de Cobertura"):
                    if len(absence_period) == 2:
                        absent_plaza_id = plazas_df[plazas_df['display_name'] == absent_worker_display]['plaza'].iloc[0]
                        payload = {
                            "plaza_id_ausente": absent_plaza_id,
                            "start_date": absence_period[0].isoformat(),
                            "end_date": absence_period[1].isoformat()
                        }
                        try:
                            requests.post(f"{API_URL}/coberturas-necesarias/", json=payload).raise_for_status()
                            st.cache_data.clear()
                        except requests.exceptions.RequestException as e:
                            st.error(f"No se pudo guardar la necesidad: {e}")
                    else:
                        st.warning("Por favor seleccione un rango de dos fechas.")

            planned_needs = get_coverage_needs()
            if planned_needs:
                st.write("Coberturas Planificadas:")
                for need in planned_needs:
                    worker_name = plazas_df[plazas_df['plaza'] == need['plaza_id_ausente']]['nombre_actual'].iloc[0]
                    c1, c2 = st.columns([4, 1])
                    c1.info(f"Cubrir a **{worker_name}** del {need['start_date']} al {need['end_date']}")
                    if c2.button("X", key=f"del_need_{need['id']}", help="Eliminar esta planificación"):
                        try:
                            requests.delete(f"{API_URL}/coberturas-necesarias/{need['id']}").raise_for_status()
                            st.cache_data.clear()
                            st.rerun()
                        except requests.exceptions.RequestException as e:
                            st.error("No se pudo eliminar.")
            
            st.markdown("---")
            
            st.subheader("Dashboard de Planeación Quincenal")
            
            q_start_date = st.date_input("Seleccione el inicio de la quincena:", value=date.today())
            q_end_date = q_start_date + timedelta(days=14)
            
            overtime_records = get_overtime_records(q_start_date, q_end_date)
            
            daily_assignments = {}
            if overtime_records:
                plaza_to_name_map = plazas_df.set_index('plaza')['nombre_actual'].to_dict()
                display_name_to_horario_map = plazas_df.set_index('display_name')['horario'].to_dict()
                for record in overtime_records:
                    record_date = date.fromisoformat(record['fecha'])
                    plaza_id = record['plaza_id']
                    worker_name = plaza_to_name_map.get(plaza_id, 'Desconocido')
                    motivo = record.get('motivo_cobertura', '')
                    match = re.search(r"Cubre a: (.*)\. Folio:", motivo)
                    covered_worker_display_name = match.group(1) if match else "N/A"
                    covered_horario = display_name_to_horario_map.get(covered_worker_display_name, '')
                    shift_display = "N/A"
                    if "7.00" in covered_horario: shift_display = "Mat."
                    elif "14.00" in covered_horario: shift_display = "Vesp."
                    elif "A 08.10" in covered_horario: shift_display = "Noct."
                    assignment_info = {"id": record['id'], "display_text": f"{worker_name} (Cubre {shift_display})"}
                    if record_date not in daily_assignments:
                        daily_assignments[record_date] = []
                    daily_assignments[record_date].append(assignment_info)

            coverage_needs_dict = {}
            for need in planned_needs:
                worker_info = plazas_df[plazas_df['plaza'] == need['plaza_id_ausente']].iloc[0]
                delta = date.fromisoformat(need['end_date']) - date.fromisoformat(need['start_date'])
                for i in range(delta.days + 1):
                    day = date.fromisoformat(need['start_date']) + timedelta(days=i)
                    if not is_day_off(day, worker_info['dias_descanso']):
                        horario = worker_info['horario']
                        shift_display = "N/A"
                        if "7.00" in horario: shift_display = "Mat."
                        elif "14.00" in horario: shift_display = "Vesp."
                        elif "A 08.10" in horario: shift_display = "Noct."
                        display_text = f"{worker_info['nombre_actual']} ({shift_display})"
                        if day not in coverage_needs_dict:
                            coverage_needs_dict[day] = []
                        coverage_needs_dict[day].append(display_text)

            days_of_week = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
            current_date = q_start_date
            
            for week in range(3):
                cols = st.columns(7)
                for i in range(7):
                    if current_date <= q_end_date:
                        day_str = days_of_week[current_date.weekday()]
                        assigned_workers_info = daily_assignments.get(current_date, [])
                        needed_coverage = coverage_needs_dict.get(current_date, [])
                        
                        with cols[i]:
                            if needed_coverage and not assigned_workers_info:
                                st.info(f"**{day_str} {current_date.day}**")
                                with st.expander(f"Necesita: {len(needed_coverage)}"):
                                    for worker in needed_coverage: st.write(f"- {worker}")
                            elif assigned_workers_info:
                                st.success(f"**{day_str} {current_date.day}**")
                                with st.expander(f"Cubierto por: {len(assigned_workers_info)}", expanded=True):
                                    for assignment in assigned_workers_info:
                                        st.write(f"- {assignment['display_text']}")
                                        if st.button("Eliminar", key=f"del_{assignment['id']}", help="Eliminar esta asignación"):
                                            st.session_state.confirming_delete_id = assignment['id']
                                        
                                        if st.session_state.get('confirming_delete_id') == assignment['id']:
                                            st.warning(f"¿Seguro que quiere eliminar la asignación de **{assignment['display_text']}**?")
                                            c1, c2 = st.columns(2)
                                            if c1.button("Sí, eliminar", key=f"confirm_del_{assignment['id']}"):
                                                try:
                                                    requests.delete(f"{API_URL}/tiempo-extra/{assignment['id']}").raise_for_status()
                                                    st.session_state.confirming_delete_id = None
                                                    st.cache_data.clear()
                                                    st.rerun()
                                                except requests.exceptions.RequestException as e:
                                                    st.error("No se pudo eliminar.")
                                            if c2.button("No, cancelar", key=f"cancel_del_{assignment['id']}"):
                                                st.session_state.confirming_delete_id = None
                                                st.rerun()
                            else:
                                st.error(f"**{day_str} {current_date.day}**")
                                st.caption("No Disponible")
                        current_date += timedelta(days=1)
                if current_date > q_end_date:
                    break
            
            st.markdown("---")

            st.subheader("Registrar Tiempo Extra Asignado")
            with st.form("overtime_form", clear_on_submit=True):
                ot_employee_display = st.selectbox("Seleccione el Empleado que realiza el tiempo extra:", options=plazas_df['display_name'], key="ot_employee")
                ot_employee_details = plazas_df[plazas_df['display_name'] == ot_employee_display].iloc[0]
                st.caption(f"**Categoría:** {ot_employee_details['categoria']}")
                st.markdown("---")
                covered_employee_display = st.selectbox("Seleccione el Empleado Cubierto (a quien se le cubre la ausencia):", options=plazas_df['display_name'], key="ot_covered_employee")
                folio_convenio = st.text_input("Folio de Convenio:", placeholder="Ej: VACACIONES, INCAPACIDAD, 12345/2025")
                ot_date = st.date_input("Periodo (Fecha del Tiempo Extra):", value=date.today(), key="ot_date")
                ot_hours = st.number_input("Num. Horas Diarias:", min_value=0.5, max_value=24.0, value=8.0, step=0.5)
                if st.form_submit_button("Registrar Tiempo Extra"):
                    plaza_id = ot_employee_details['plaza']
                    motivo_final = f"Cubre a: {covered_employee_display}. Folio: {folio_convenio}"
                    payload = {"plaza_id": plaza_id, "fecha": ot_date.isoformat(), "horas": ot_hours, "motivo_cobertura": motivo_final}
                    try:
                        requests.post(f"{API_URL}/tiempo-extra/", json=payload).raise_for_status()
                        st.success("¡Tiempo extra registrado con éxito!")
                        st.cache_data.clear()
                        st.rerun()
                    except requests.exceptions.RequestException as e:
                        st.error(f"Error al registrar el tiempo extra: {e}")

        with tab4:
            st.header("Asignación de Servicios por Turno")
            col1_assign, col2_assign = st.columns(2)
            with col1_assign:
                assign_date = st.date_input("Seleccione la Fecha:", value=date.today(), key="assign_page_date")
            with col2_assign:
                assign_turno = st.selectbox("Seleccione el Turno:", ["Matutino", "Vespertino", "Nocturno"], key="assign_page_turno")
            
            turno_df_assign = get_active_workers_for_shift(plazas_df, assign_date, assign_turno)
            
            asignaciones_existentes = get_asignaciones(assign_date, assign_turno)
            
            st.markdown("---")
            st.subheader(f"Plantilla del Turno {assign_turno} para el {assign_date.strftime('%d/%m/%Y')}")

            if turno_df_assign.empty:
                st.info("No hay personal programado para este turno en la fecha seleccionada.")
            else:
                service_options = ["", "Gob/Ens", "Cons/Far", "Urg", "Grls/Rx", "Rop/RPBI", "Pedia", "UTQ/Aneste", "QX/CE", "Pisos", "Hospi", "Lab", "ExahusCE", "Cam", "Ayudantia", "QX/UTQ/CE", "Grls/Cons", "Rop/Lab"]
                service_selections = {}

                for index, row in turno_df_assign.iterrows():
                    default_assignment = asignaciones_existentes.get(row['plaza'], "")
                    try:
                        default_index = service_options.index(default_assignment)
                    except ValueError:
                        default_index = 0
                    c1_assign, c2_assign = st.columns([2, 3])
                    with c1_assign:
                        st.write(row['nombre_actual'])
                        st.caption(f"Plaza: {row['plaza']}")
                    with c2_assign:
                        service_selections[row['plaza']] = st.selectbox("Área de Servicio:", options=service_options, index=default_index, key=f"service_select_{row['plaza']}")

                if st.button("Guardar Cambios de Asignación"):
                    with st.spinner("Guardando..."):
                        for plaza_id, area_servicio in service_selections.items():
                            if area_servicio:
                                payload = {"plaza_id": plaza_id, "fecha": assign_date.isoformat(), "turno": assign_turno, "area_servicio": area_servicio}
                                try:
                                    requests.post(f"{API_URL}/asignaciones/", json=payload).raise_for_status()
                                except requests.exceptions.RequestException as e:
                                    st.error(f"Error al guardar asignación para la plaza {plaza_id}: {e}")
                        st.success("¡Todas las asignaciones han sido guardadas con éxito!")
                        st.cache_data.clear()

# --- Main Script Execution ---
if check_password():
    main_app()
