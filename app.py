import streamlit as st
import pandas as pd
import os
import requests
from datetime import date, timedelta

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ------------------------------------------------------------------
# 1. CONFIGURATION
# ------------------------------------------------------------------
TIME_SLOTS = []
for i in range(24):
    start_m = 9 * 60 + i * 30
    end_m = start_m + 30
    sh, sm = divmod(start_m, 60)
    eh, em = divmod(end_m, 60)
    label = f"{sh:02d}:{sm:02d} – {eh:02d}:{em:02d}"
    TIME_SLOTS.append((label, 4, 0.5))
SLOT_CAPACITY = {s[0]: s[1] for s in TIME_SLOTS}
SLOT_HOURS = {s[0]: s[2] for s in TIME_SLOTS}

# Supabase REST API (st.secrets on Cloud, .env locally)
SUPABASE_URL = st.secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL", ""))
SUPABASE_KEY = st.secrets.get("SUPABASE_SERVICE_KEY", os.getenv("SUPABASE_SERVICE_KEY", ""))

def _req(method, path, data=None, params=None):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }
    url = f"{SUPABASE_URL}/rest/v1/{path}"
    if data is not None:
        headers["Content-Type"] = "application/json"
        headers["Prefer"] = "return=minimal"
        r = requests.request(method, url, headers=headers, json=data, params=params)
    else:
        r = requests.request(method, url, headers=headers, params=params)
    r.raise_for_status()
    return r

# ------------------------------------------------------------------
# 1b. TRANSLATIONS
# ------------------------------------------------------------------
DAY_NAMES = {
    "en": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    "es": ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"],
}
MONTHS = {
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "es": ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
           "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
}

T = {
    # ---- Login screen ----
    "title":                   {"en": "Time Slot Coordinator",    "es": "Coordinador de Horarios"},
    "who_are_you":             {"en": "Who are you?",             "es": "¿Quién eres?"},
    "existing_users":          {"en": "Existing users",            "es": "Usuarios existentes"},
    "or_create_new_user":      {"en": "Or create a new user",      "es": "O crea un nuevo usuario"},
    "your_name":               {"en": "Your name",                 "es": "Tu nombre"},
    "enter_name_placeholder":  {"en": "Enter your name",           "es": "Escribe tu nombre"},
    "please_enter_name":       {"en": "Please enter a name.",      "es": "Por favor, escribe un nombre."},
    "enter_btn":               {"en": "Enter",                     "es": "Entrar"},

    # ---- Logged-in header ----
    "switch_user":             {"en": "Switch user",               "es": "Cambiar usuario"},
    "logged_in_as":            {"en": "Logged in as",              "es": "Conectado como"},
    "date_range":              {"en": "Next two weeks — from {start} to {end}",
                                 "es": "Próximas dos semanas — del {start} al {end}"},

    # ---- Metrics ----
    "total_bookings":          {"en": "Total Bookings",            "es": "Reservas Totales"},
    "bookings_across":         {"en": "{n} across {t} slots",      "es": "{n} de {t} turnos"},
    "your_bookings":           {"en": "Your bookings ({user})",    "es": "Tus reservas ({user})"},
    "slots_hours":             {"en": "{s} slots · {h} h",         "es": "{s} turnos · {h} h"},
    "your_waitlist":           {"en": "Waitlisted ({user})",       "es": "En espera ({user})"},
    "waitlist_count":          {"en": "{n} waitlisted",            "es": "{n} en espera"},

    # ---- Calendar ----
    "schedule_calendar":       {"en": "Schedule Calendar",          "es": "Calendario de Turnos"},
    "week_1":                  {"en": "Week 1 — {start} to {end}", "es": "Semana 1 — {start} al {end}"},
    "week_2":                  {"en": "Week 2 — {start} to {end}", "es": "Semana 2 — {start} al {end}"},
    "editing":                 {"en": "Editing",                   "es": "Editando"},

    # ---- Cell buttons / labels ----
    "book":                    {"en": "Book",                       "es": "Reservar"},
    "book_n":                  {"en": "Book · {free} free",         "es": "Reservar · {free} libre"},
    "book_1":                  {"en": "Book · 1 free",              "es": "Reservar · 1 libre"},
    "full":                    {"en": "Full",                       "es": "Lleno"},
    "you_n":                   {"en": "✓ You ({n}/{cap})",          "es": "✓ Tú ({n}/{cap})"},
    "unbook_header":           {"en": "Unbook:",                    "es": "Liberar:"},
    "unbook_btn_you":          {"en": "✕ Unbook me",                "es": "✕ Liberar turno"},
    "yes_unbook_me":           {"en": "Yes, unbook myself",         "es": "Sí, liberar mi turno"},
    "no_keep":                 {"en": "No, keep",                   "es": "No, mantener"},
    "close":                   {"en": "Close",                      "es": "Cerrar"},

    # ---- Waitlist ----
    "join_waitlist":           {"en": "Join waitlist",              "es": "Lista de espera"},
    "join_waitlist_n":         {"en": "Waitlist ({n}/{cap} +{w})", "es": "Espera ({n}/{cap} +{w})"},
    "waitlisted_you":          {"en": "✓ Waitlisted",               "es": "✓ En espera"},
    "waitlisted_you_n":        {"en": "✓ Waitlisted (#{pos})",      "es": "✓ En espera (#{pos})"},
    "waitlist_header":         {"en": "Waitlist:",                  "es": "Lista de espera:"},
    "leave_waitlist":          {"en": "Leave waitlist",             "es": "Salir de la lista"},
    "promoted_from_waitlist":  {"en": "{name} promoted from waitlist!",
                                 "es": "¡{name} promovido de la lista de espera!"},

    # ---- Leaderboard ----
    "all_bookings_hours":      {"en": "All Bookings & Hours",      "es": "Todas las Reservas y Horas"},
    "col_participant":         {"en": "Participant",                "es": "Participante"},
    "col_total_hours":         {"en": "Total Hours",                "es": "Horas Totales"},
    "col_slots":               {"en": "Slots",                      "es": "Turnos"},
    "full_schedule":           {"en": "Full Schedule",              "es": "Horario Completo"},
    "col_date":                {"en": "Date",                       "es": "Fecha"},
    "col_time":                {"en": "Time",                       "es": "Hora"},
    "col_hours":               {"en": "Hours",                      "es": "Horas"},
    "no_bookings_yet":         {"en": "No bookings yet. Click any cell in the calendar above to book!",
                                 "es": "No hay reservas aún. ¡Haz clic en una celda del calendario para reservar!"},

    # ---- Errors / status ----
    "slot_full":               {"en": "This slot is now full ({n}/{cap}).",
                                 "es": "Este turno ya está lleno ({n}/{cap})."},
    "already_booked":          {"en": "You have already booked this slot.",
                                 "es": "Ya has reservado este turno."},
    "already_waitlisted":      {"en": "You are already on the waitlist.",
                                 "es": "Ya estás en la lista de espera."},

    # ---- Dialog ----
    "slot_details":            {"en": "Slot details",               "es": "Detalles del turno"},
    "export_calendar":         {"en": "Export to calendar",         "es": "Exportar a calendario"},
    "no_bookings_to_export":   {"en": "No bookings to export.",      "es": "No hay reservas para exportar."},

    # ---- Calendar name setup ----
    "calendar_name_title":     {"en": "Welcome!",                   "es": "¡Bienvenido!"},
    "calendar_name_prompt":    {"en": "What's the name of this calendar?",
                                 "es": "¿Cómo se llama este calendario?"},
    "calendar_name_placeholder": {"en": "e.g. Football Team, Study Group...",
                                   "es": "ej. Equipo de Fútbol, Grupo de Estudio..."},
    "calendar_name_submit":    {"en": "Get started",                "es": "Empezar"},
    "calendar_name_required":  {"en": "Please enter a calendar name.",
                                 "es": "Por favor, escribe un nombre para el calendario."},
    "default_title":           {"en": "Time Slot Coordinator",    "es": "Coordinador de Horarios"},
    "ics_summary":             {"en": "{name} – {slot}",            "es": "{name} – {slot}"},
    "owner_label":             {"en": "(owner)",                    "es": "(admin)"},

    # ---- Batch booking ----
    "batch_booking":           {"en": "Batch booking",              "es": "Reserva por lotes"},
    "day":                     {"en": "Day",                        "es": "Día"},
    "start_time":              {"en": "Start time",                 "es": "Hora inicio"},
    "slots":                   {"en": "Slots",                      "es": "Turnos"},
    "booked_ok":               {"en": "Booked!",                    "es": "¡Reservado!"},
    "unbook_all":              {"en": "Unbook all ({n} slots · {h}h)",
                                 "es": "Liberar todo ({n} turnos · {h}h)"},
    "batch_preview":           {"en": "Preview:",                   "es": "Vista previa:"},
    "will_book":               {"en": "Will book",                  "es": "Reservará"},
    "will_skip":               {"en": "Will skip (taken)",          "es": "Ignorará (ocupado)"},

    # ---- Mobile ----
    "slot_mobile":             {"en": "slot",                       "es": "turno"},
    "slots_mobile":            {"en": "slots",                      "es": "turnos"},
    "free_mobile":             {"en": "free",                       "es": "libre"},
    "h_short":                 {"en": "h",                          "es": "h"},

    # ---- Lang selector ----
    "language":                {"en": "Language",                   "es": "Idioma"},
}


def t(key, **kwargs):
    lang = st.session_state.get("lang", "en")
    entry = T.get(key, {})
    text = entry.get(lang, entry.get("en", key))
    if kwargs:
        return text.format(**kwargs)
    return text


def day_name(date_obj):
    lang = st.session_state.get("lang", "en")
    return DAY_NAMES[lang][date_obj.weekday()]


def month_name(date_obj):
    lang = st.session_state.get("lang", "en")
    return MONTHS[lang][date_obj.month - 1]


def format_date_range(start, end):
    return (f"{day_name(start)} {start.day} {month_name(start)}",
            f"{day_name(end)} {end.day} {month_name(end)} {end.year}")


def _parse_slot_times(slot_label):
    """Extract (start_time, end_time) strings like ('163000','190000') from slot label."""
    parts = slot_label.split(" – ")
    def _to_ical(t):
        t = t.strip().replace(":", "")
        return t if len(t) == 6 else t + "00"
    return _to_ical(parts[0]), _to_ical(parts[1])


def generate_ics(user_name, df_bookings, cal_name):
    """Generate an .ics calendar file with the user's bookings."""
    name = cal_name or "Team Schedule"
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", f"PRODID:-//Schedully//{name}//EN"]
    my_rows = df_bookings[df_bookings["participant_name"] == user_name]
    for _, row in my_rows.iterrows():
        date_str = row["slot_date"].replace("-", "")
        start, end = _parse_slot_times(row["slot_time"])
        lines.extend([
            "BEGIN:VEVENT",
            f"DTSTART:{date_str}T{start}",
            f"DTEND:{date_str}T{end}",
            f"SUMMARY:{name} – {row['slot_time']}",
            "END:VEVENT",
        ])
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)


# ------------------------------------------------------------------
# 2. DATABASE (Supabase REST API)
# ------------------------------------------------------------------
SETUP_SQL = """-- Run this once in Supabase SQL Editor (https://supabase.com/dashboard):
CREATE TABLE IF NOT EXISTS bookings (id SERIAL PRIMARY KEY, slot_date TEXT NOT NULL, slot_time TEXT NOT NULL, participant_name TEXT NOT NULL, UNIQUE(slot_date, slot_time, participant_name));
CREATE TABLE IF NOT EXISTS waitlist (id SERIAL PRIMARY KEY, slot_date TEXT NOT NULL, slot_time TEXT NOT NULL, participant_name TEXT NOT NULL, UNIQUE(slot_date, slot_time, participant_name));
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);"""


def _clear_read_caches():
    get_bookings.clear()
    get_waitlist.clear()
    get_setting_cached.clear()


@st.cache_data(ttl=300, show_spinner=False)
def get_setting_cached(key):
    try:
        r = _req("GET", "settings", params={"select": "value", "key": f"eq.{key}"})
        data = r.json()
        return data[0]["value"] if data else None
    except Exception:
        return None


def get_setting(key, default=None):
    val = get_setting_cached(key)
    return val if val is not None else default


def set_setting(key, value):
    _req("POST", "settings", data={"key": key, "value": value},
         params={"on_conflict": "key"})
    _clear_read_caches()


@st.cache_data(ttl=300, show_spinner=False)
def get_bookings():
    try:
        r = _req("GET", "bookings", params={
            "select": "*", "order": "slot_date.asc,slot_time.asc"
        })
        data = r.json()
        return pd.DataFrame(data) if data else pd.DataFrame(
            columns=["id", "slot_date", "slot_time", "participant_name"]
        )
    except Exception:
        return pd.DataFrame(columns=["id", "slot_date", "slot_time", "participant_name"])


@st.cache_data(ttl=300, show_spinner=False)
def get_waitlist():
    try:
        r = _req("GET", "waitlist", params={
            "select": "*", "order": "id.asc"
        })
        data = r.json()
        return pd.DataFrame(data) if data else pd.DataFrame(
            columns=["id", "slot_date", "slot_time", "participant_name"]
        )
    except Exception:
        return pd.DataFrame(columns=["id", "slot_date", "slot_time", "participant_name"])


def get_slot_count(slot_date, slot_time):
    """Count from cached DataFrame — zero HTTP calls."""
    df = get_bookings()
    mask = (df["slot_date"] == slot_date) & (df["slot_time"] == slot_time)
    return mask.sum() if "slot_date" in df.columns else 0


def book_slot(slot_date, slot_time, name, silent=False):
    capacity = SLOT_CAPACITY[slot_time]
    current = get_slot_count(slot_date, slot_time)
    if current >= capacity:
        if not silent:
            st.error(t("slot_full", n=current, cap=capacity))
        return False
    try:
        _req("POST", "bookings", data={
            "slot_date": slot_date, "slot_time": slot_time, "participant_name": name
        })
        _clear_read_caches()
        return True
    except Exception:
        if not silent:
            st.error(t("already_booked"))
        return False


def add_to_waitlist(slot_date, slot_time, name):
    try:
        _req("POST", "waitlist", data={
            "slot_date": slot_date, "slot_time": slot_time, "participant_name": name
        })
        _clear_read_caches()
        return True
    except Exception:
        st.error(t("already_waitlisted"))
        return False


def remove_from_waitlist(slot_date, slot_time, name):
    try:
        _req("DELETE", "waitlist", params={
            "slot_date": f"eq.{slot_date}",
            "slot_time": f"eq.{slot_time}",
            "participant_name": f"eq.{name}",
        })
        _clear_read_caches()
    except Exception:
        pass


def unbook_slot(slot_date, slot_time, name):
    try:
        _req("DELETE", "bookings", params={
            "slot_date": f"eq.{slot_date}",
            "slot_time": f"eq.{slot_time}",
            "participant_name": f"eq.{name}",
        })
    except Exception:
        pass
    # Auto-promote first person on waitlist
    promoted_name = None
    try:
        r = _req("GET", "waitlist", params={
            "select": "participant_name",
            "slot_date": f"eq.{slot_date}",
            "slot_time": f"eq.{slot_time}",
            "order": "id.asc",
            "limit": "1",
        })
        data = r.json()
        if data:
            promoted_name = data[0]["participant_name"]
            _req("POST", "bookings", data={
                "slot_date": slot_date, "slot_time": slot_time,
                "participant_name": promoted_name,
            })
            _req("DELETE", "waitlist", params={
                "slot_date": f"eq.{slot_date}",
                "slot_time": f"eq.{slot_time}",
                "participant_name": f"eq.{promoted_name}",
            })
    except Exception:
        pass
    _clear_read_caches()
    if promoted_name:
        st.success(t("promoted_from_waitlist", name=promoted_name))


# ------------------------------------------------------------------
# 3. INIT & FETCH
# ------------------------------------------------------------------
df_bookings = get_bookings()
df_waitlist = get_waitlist()

booking_lookup = {}
existing_users = set()
if not df_bookings.empty:
    for _, row in df_bookings.iterrows():
        key = (row["slot_date"], row["slot_time"])
        booking_lookup.setdefault(key, []).append(row["participant_name"])
        existing_users.add(row["participant_name"])

# Waitlist lookup: {(date, time): [(name, position), ...]}
waitlist_lookup = {}
if not df_waitlist.empty:
    for _, row in df_waitlist.iterrows():
        key = (row["slot_date"], row["slot_time"])
        waitlist_lookup.setdefault(key, []).append(row["participant_name"])

# Also include waitlisted users in "existing users"
for wl_list in waitlist_lookup.values():
    existing_users.update(wl_list)

existing_users = sorted(existing_users)

# Calendar name and owner from settings
calendar_name = get_setting("calendar_name", "")
owner_name = get_setting("owner", "")

# Session state
if "lang" not in st.session_state:
    st.session_state.lang = "es"
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "dialog_cell" not in st.session_state:
    st.session_state.dialog_cell = None  # (date_str, slot_label) or None
if "_dialog_shown" not in st.session_state:
    st.session_state._dialog_shown = False
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "mobile"





# Check database is set up
if SUPABASE_URL and SUPABASE_KEY and SUPABASE_KEY != "YOUR_SERVICE_ROLE_KEY_HERE":
    try:
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/bookings?select=count",
            headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"},
            timeout=5,
        )
        if r.status_code == 404:
            st.error("Tables not found. Run this SQL in your Supabase SQL Editor:")
            st.code(SETUP_SQL, language="sql")
            st.stop()
    except requests.exceptions.ConnectionError:
        st.warning("Cannot reach Supabase — check your SUPABASE_URL and network connection.")
        st.stop()
elif not SUPABASE_URL or not SUPABASE_KEY or SUPABASE_KEY == "YOUR_SERVICE_ROLE_KEY_HERE":
    st.info("Add your SUPABASE_URL and SUPABASE_SERVICE_KEY to the .env file.")
    st.code(SETUP_SQL, language="sql")
    st.stop()

# Generate 14 days from today
today = date.today()
all_days = [today + timedelta(days=i) for i in range(14)]
week1 = all_days[:7]
week2 = all_days[7:14]

st.set_page_config(page_title=calendar_name or t("default_title"), page_icon="📅", layout="wide")


# ------------------------------------------------------------------
# 4. CALENDAR NAME SETUP SCREEN
# ------------------------------------------------------------------
def render_calendar_setup():
    st.title(t("calendar_name_title"))
    st.markdown(
        "<div style='text-align:center;font-size:2.5em;margin:0.5em 0 0.2em 0;'>📅</div>",
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown(f"**{t('calendar_name_prompt')}**")
        with st.form("calendar_name_form"):
            cal_name = st.text_input(
                t("calendar_name_prompt"),
                placeholder=t("calendar_name_placeholder"),
                label_visibility="collapsed",
            ).strip()
            submitted = st.form_submit_button(
                t("calendar_name_submit"), use_container_width=True, type="primary"
            )
            if submitted:
                if cal_name:
                    set_setting("calendar_name", cal_name)
                    st.rerun()
                else:
                    st.warning(t("calendar_name_required"))
    st.stop()


# ------------------------------------------------------------------
# 5. USER SELECTION SCREEN
# ------------------------------------------------------------------
def render_login():
    st.title(calendar_name or t("default_title"))
    st.markdown(
        "<div style='text-align:center;font-size:3em;margin:0.5em 0 0.2em 0;'>📅</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div style='text-align:center;margin-bottom:1.5em;'>{t('who_are_you')}</div>",
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 1.5, 1])

    with col2:
        if existing_users:
            st.markdown(f"**{t('existing_users')}**")
            cols_per_row = 3
            for i in range(0, len(existing_users), cols_per_row):
                user_cols = st.columns(cols_per_row, gap="small")
                for j, user_name in enumerate(existing_users[i:i + cols_per_row]):
                    with user_cols[j]:
                        label = f"{user_name} {t('owner_label')}" if user_name == owner_name else user_name
                        if st.button(label, key=f"login_{user_name}", use_container_width=True,
                                     type="primary"):
                            if not owner_name:
                                set_setting("owner", user_name)
                            st.session_state.current_user = user_name
                            st.rerun()

        st.markdown("---")
        st.markdown(f"**{t('or_create_new_user')}**")
        with st.form("new_user_form"):
            new_name = st.text_input(
                t("your_name"), placeholder=t("enter_name_placeholder")
            ).strip()
            submitted = st.form_submit_button(
                t("enter_btn"), use_container_width=True, type="primary"
            )
            if submitted:
                if new_name:
                    if not owner_name:
                        set_setting("owner", new_name)
                    st.session_state.current_user = new_name
                    st.rerun()
                else:
                    st.warning(t("please_enter_name"))

    st.stop()


# ------------------------------------------------------------------
# 5. DIALOG (for unbook / cell details)
# ------------------------------------------------------------------
@st.dialog(t("slot_details"))
def render_cell_dialog():
    if not st.session_state.get("dialog_cell"):
        return
    date_str, slot_label = st.session_state.dialog_cell
    user = st.session_state.current_user

    # Build the list of all slot labels to compute the max slots available
    all_slots = [s[0] for s in TIME_SLOTS]
    slot_idx = all_slots.index(slot_label) if slot_label in all_slots else 0

    people = booking_lookup.get((date_str, slot_label), [])
    waiting = waitlist_lookup.get((date_str, slot_label), [])
    capacity = SLOT_CAPACITY[slot_label]
    booked = len(people)
    user_is_in = user in people
    user_on_waitlist = user in waiting
    full = booked >= capacity

    d = date.fromisoformat(date_str)
    st.markdown(f"**{day_name(d)} {d.day} {month_name(d)} — {slot_label}**")

    # Find consecutive slots this user has booked (for unbook all)
    my_consecutive = []
    if user_is_in:
        my_consecutive.append(slot_label)
        # Check forward
        for k in range(1, len(all_slots) - slot_idx):
            sl = all_slots[slot_idx + k]
            names = booking_lookup.get((date_str, sl), [])
            if user in names:
                my_consecutive.append(sl)
            else:
                break
        # Check backward
        for k in range(1, slot_idx + 1):
            sl = all_slots[slot_idx - k]
            names = booking_lookup.get((date_str, sl), [])
            if user in names:
                my_consecutive.insert(0, sl)
            else:
                break

    # Booked list
    if people:
        st.markdown(f"**{t('col_participant')}:**")
        for name in people:
            mark = f" {t('owner_label')}" if name == user else ""
            st.markdown(f"- {name}{mark}")

    # Waitlist
    if waiting:
        st.markdown(f"**{t('waitlist_header')}**")
        for pos, name in enumerate(waiting, 1):
            mark = f" {t('owner_label')}" if name == user else ""
            st.markdown(f"{pos}. {name}{mark}")

    st.markdown("---")

    # Actions
    if user_is_in:
        if len(my_consecutive) > 1:
            total_h = len(my_consecutive) * 0.5
            st.caption(f"{len(my_consecutive)} consecutive slots · {total_h:g}h")
        if st.button(t("unbook_btn_you"), use_container_width=True, type="primary"):
            unbook_slot(date_str, slot_label, user)
            st.session_state.dialog_cell = None
            st.rerun()
        if len(my_consecutive) > 1:
            total_h = len(my_consecutive) * 0.5
            if st.button(f"Unbook all ({len(my_consecutive)} slots · {total_h:g}h)", use_container_width=True):
                for sl in my_consecutive:
                    unbook_slot(date_str, sl, user)
                st.session_state.dialog_cell = None
                st.rerun()
    elif user_on_waitlist:
        if st.button(t("leave_waitlist"), use_container_width=True):
            remove_from_waitlist(date_str, slot_label, user)
            st.session_state.dialog_cell = None
            st.rerun()
    elif not full:
        if st.button(t("book"), use_container_width=True, type="primary"):
            if book_slot(date_str, slot_label, user):
                st.session_state.dialog_cell = None
                st.rerun()
    elif not user_is_in and not user_on_waitlist:
        if st.button(t("join_waitlist"), use_container_width=True):
            if add_to_waitlist(date_str, slot_label, user):
                st.session_state.dialog_cell = None
                st.rerun()

    if st.button(t("close"), use_container_width=True):
        st.session_state.dialog_cell = None
        st.rerun()


# ------------------------------------------------------------------
# 6. CALENDAR RENDERING
# ------------------------------------------------------------------
def _render_cell_content(date_str, slot_label, capacity, people, waiting, user, user_is_in, user_on_waitlist, booked, full, cell_id, show_names=True):
    """Shared cell rendering used by both desktop grid and mobile cards."""
    if user_is_in:
        if st.button(
            f"✓{booked}", key=f"btn_{cell_id}", use_container_width=True, type="primary",
        ):
            st.session_state.dialog_cell = (date_str, slot_label)
            st.rerun()
    elif user_on_waitlist:
        if st.button(
            f"☐", key=f"btn_{cell_id}", use_container_width=True,
        ):
            remove_from_waitlist(date_str, slot_label, user)
            st.rerun()
    elif full:
        st.button(
            f"{booked}/{capacity}", key=f"btn_{cell_id}", use_container_width=True, disabled=True,
        )
    elif people:
        if st.button(
            f"{booked}/{capacity}", key=f"btn_{cell_id}", use_container_width=True,
        ):
            book_slot(date_str, slot_label, user)
            st.rerun()
    else:
        if st.button(
            f"0/{capacity}", key=f"btn_{cell_id}", use_container_width=True,
        ):
            book_slot(date_str, slot_label, user)
            st.rerun()

    # Tiny name labels below
    if show_names:
        all_names = list(people) + [f"☐{n}" for n in waiting]
        if all_names:
            st.markdown(
                f"<div style='font-size:0.5em;line-height:1;color:#aaa;"
                f"text-align:center;overflow:hidden;white-space:nowrap;"
                f"margin:-2px 0 0 0;'>{', '.join(all_names[:3])}</div>",
                unsafe_allow_html=True,
            )


def render_week_grid(week_days, week_label):
    st.markdown(f"#### {week_label}")
    user = st.session_state.current_user

    # ---- Day headers ----
    cols = st.columns([0.6] + [1] * 7, gap=None)
    with cols[0]:
        st.markdown("&nbsp;", unsafe_allow_html=True)
    for i, d in enumerate(week_days):
        with cols[i + 1]:
            st.markdown(
                f"<div style='text-align:center;font-weight:700;font-size:0.85em;"
                f"background:#f0f2f6;padding:0.3em 0;border-radius:6px 6px 0 0;"
                f"line-height:1.2;'>{day_name(d)}<br>"
                f"<span style='font-size:0.75em;color:#666;'>{d.day}</span></div>",
                unsafe_allow_html=True,
            )

    # ---- Time-slot rows ----
    for j, (slot_label, capacity, hours) in enumerate(TIME_SLOTS):
        # Show hour label only on the hour (:00) or on first slot
        time_short = slot_label.split(chr(8211))[0].strip()
        is_hour = time_short.endswith(":00") or j == 0

        cols = st.columns([0.6] + [1] * 7, gap=None)
        with cols[0]:
            if is_hour:
                st.markdown(
                    f"<div style='font-size:0.68em;font-weight:600;color:#555;"
                    f"text-align:right;padding:0;line-height:1.6;'>{time_short}</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    "<div style='line-height:0;height:0;'>&nbsp;</div>",
                    unsafe_allow_html=True,
                )

        for i, d in enumerate(week_days):
            date_str = d.isoformat()
            people = booking_lookup.get((date_str, slot_label), [])
            waiting = waitlist_lookup.get((date_str, slot_label), [])
            booked = len(people)
            full = booked >= capacity
            cell_id = f"{date_str}|{slot_label}"
            user_is_in = user in people
            user_on_waitlist = user in waiting

            with cols[i + 1]:
                _render_cell_content(date_str, slot_label, capacity, people, waiting, user, user_is_in, user_on_waitlist, booked, full, cell_id)


def render_week_grid_mobile(week_days, week_label):
    """Mobile layout: each day as an expandable card with vertical time slots."""
    st.markdown(f"#### {week_label}")
    user = st.session_state.current_user

    for d in week_days:
        date_str = d.isoformat()
        day_bookings = 0
        free_hours = 0.0
        day_slots = []
        for slot_label, capacity, hours in TIME_SLOTS:
            people = booking_lookup.get((date_str, slot_label), [])
            waiting = waitlist_lookup.get((date_str, slot_label), [])
            booked = len(people)
            if booked > 0:
                day_bookings += 1
            if booked < capacity:
                free_hours += 0.5
            day_slots.append((slot_label, capacity, people, waiting, booked))

        slot_word = t("slot_mobile") if day_bookings == 1 else t("slots_mobile")
        expander_label = f"{day_name(d)} {d.day} {month_name(d)}"
        parts = []
        if day_bookings > 0:
            parts.append(f"{day_bookings} {slot_word}")
        if free_hours > 0:
            h_label = f"{free_hours:g}{t('h_short')} {t('free_mobile')}"
            parts.append(h_label)
        if parts:
            expander_label += " (" + " · ".join(parts) + ")"

        with st.expander(expander_label):
            for slot_label, capacity, people, waiting, booked in day_slots:
                full = booked >= capacity
                waiting_count = len(waiting)
                user_is_in = user in people
                user_on_waitlist = user in waiting
                cell_id = f"{date_str}|{slot_label}"

                mc1, mc2, mc3 = st.columns([1.6, 1, 2.4])
                with mc1:
                    # Time + occupancy bar (● = filled, ○ = empty)
                    filled = min(booked, capacity)
                    free = capacity - filled
                    bar = "●" * filled + "○" * free
                    st.markdown(
                        f"<span style='font-size:0.78em;font-weight:600;color:#555;'>"
                        f"{slot_label.split(chr(8211))[0].strip()}</span>"
                        f"<span style='font-size:0.6em;letter-spacing:-1px;margin-left:2px;'>{bar}</span>",
                        unsafe_allow_html=True,
                    )
                with mc2:
                    _render_cell_content(date_str, slot_label, capacity, people, waiting, user, user_is_in, user_on_waitlist, booked, full, cell_id, show_names=False)
                with mc3:
                    parts = []
                    if people:
                        parts.append(", ".join(people))
                    if waiting:
                        parts.append(f"☐ {len(waiting)}")
                    if parts:
                        st.markdown(
                            f"<div style='font-size:0.62em;line-height:1.3;color:#666;"
                            f"margin-top:3px;'>{'  ·  '.join(parts)}</div>",
                            unsafe_allow_html=True,
                        )


# ------------------------------------------------------------------
# 6. MAIN
# ------------------------------------------------------------------

# Language selector — always visible, top-right
_, lang_col = st.columns([5.5, 1.5])
with lang_col:
    current_lang = st.session_state.lang
    lang_labels = {"en": "🇬🇧 EN", "es": "🇪🇸 ES"}
    options = list(lang_labels.keys())
    new_lang = st.segmented_control(
        t("language"),
        options,
        default=current_lang,
        format_func=lambda x: lang_labels[x],
        key="lang_selector",
    )
    if new_lang != st.session_state.lang:
        st.session_state.lang = new_lang
        st.rerun()

# Calendar name setup (first connection)
if not calendar_name:
    render_calendar_setup()

if st.session_state.current_user is None:
    render_login()

# Dialog (opens above the calendar)
if st.session_state.get("dialog_cell"):
    if st.session_state.get("_dialog_shown"):
        # Dialog was dismissed via native X on previous run — clear it
        st.session_state.dialog_cell = None
        st.session_state._dialog_shown = False
    else:
        render_cell_dialog()
        st.session_state._dialog_shown = True
else:
    st.session_state._dialog_shown = False

# ---- Logged-in header ----
user = st.session_state.current_user

col_title, col_switch = st.columns([4, 1])
with col_title:
    st.title(calendar_name or t("default_title"))
    start_str, end_str = format_date_range(week1[0], week2[-1])
    st.caption(t("date_range", start=start_str, end=end_str))
with col_switch:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button(t("switch_user"), use_container_width=True):
        st.session_state.current_user = None
        st.session_state.dialog_cell = None
        st.rerun()
    st.caption(f"{t('logged_in_as')} **{user}**")

col1, col2 = st.columns([3, 1], gap="medium")
with col1:
    total_cells = len(all_days) * len(TIME_SLOTS)
    total_bookings = len(df_bookings) if not df_bookings.empty else 0
    total_waitlisted = len(df_waitlist) if not df_waitlist.empty else 0

    my_bookings = 0
    my_hours = 0.0
    my_waitlisted = 0
    if not df_bookings.empty:
        my_rows = df_bookings[df_bookings["participant_name"] == user]
        my_bookings = len(my_rows)
        if not my_rows.empty:
            my_hours = my_rows["slot_time"].map(SLOT_HOURS).sum()
    if not df_waitlist.empty:
        my_waitlisted = len(df_waitlist[df_waitlist["participant_name"] == user])

    st.metric(label=t("total_bookings"), value=t("bookings_across", n=total_bookings, t=total_cells))
    st.metric(label=t("your_bookings", user=user), value=t("slots_hours", s=my_bookings, h=my_hours))
    if my_waitlisted:
        st.metric(label=t("your_waitlist", user=user), value=t("waitlist_count", n=my_waitlisted))

with col2:
    # Export current user's bookings as .ics
    if not df_bookings.empty and user in df_bookings["participant_name"].values:
        ics_data = generate_ics(user, df_bookings, calendar_name)
        st.download_button(
            label=t("export_calendar"),
            data=ics_data,
            file_name=f"schedully_{user}.ics",
            mime="text/calendar",
            use_container_width=True,
        )

st.markdown("---")

# ---- BATCH BOOKING PANEL ----
all_slots_labels = [s[0] for s in TIME_SLOTS]

with st.expander(t("batch_booking"), expanded=False):
    day_options = [d.isoformat() for d in all_days]
    day_labels_list = [f"{day_name(d)} {d.day} {month_name(d)}" for d in all_days]

    bc1, bc2, bc3, bc4 = st.columns([2, 1.5, 1, 1])
    with bc1:
        batch_day = st.selectbox(t("day"), day_options, format_func=lambda x: day_labels_list[day_options.index(x)], key="batch_day")
    with bc2:
        batch_time = st.selectbox(t("start_time"), all_slots_labels, key="batch_time")
    with bc3:
        slot_idx_b = all_slots_labels.index(batch_time) if batch_time in all_slots_labels else 0
        max_b = len(all_slots_labels) - slot_idx_b
        batch_n = st.number_input(t("slots"), min_value=1, max_value=max_b, value=1, step=1, key="batch_n")
    with bc4:
        total_h = batch_n * 0.5
        st.caption(f"{total_h:g}h")
        if st.button(t("book"), use_container_width=True, type="primary", key="batch_go"):
            for k in range(batch_n):
                if slot_idx_b + k >= len(all_slots_labels):
                    break
                sl = all_slots_labels[slot_idx_b + k]
                book_slot(batch_day, sl, user, silent=True)
            st.rerun()

    # Preview as compact visual timeline
    blocks = []
    count_book = 0
    count_skip = 0
    for k in range(min(batch_n, max_b)):
        sl = all_slots_labels[slot_idx_b + k]
        cur = get_slot_count(batch_day, sl)
        cap = SLOT_CAPACITY[sl]
        if cur >= cap or user in booking_lookup.get((batch_day, sl), []):
            blocks.append("<span style='display:inline-block;width:10px;height:10px;"
                          "background:#ddd;border-radius:2px;margin:1px;' title='skip'></span>")
            count_skip += 1
        else:
            blocks.append("<span style='display:inline-block;width:10px;height:10px;"
                          "background:#4caf50;border-radius:2px;margin:1px;' title='book'></span>")
            count_book += 1
    time_start = all_slots_labels[slot_idx_b].split(chr(8211))[0].strip()
    time_end = all_slots_labels[min(slot_idx_b + batch_n - 1, len(all_slots_labels) - 1)].split(chr(8211))[1].strip()
    st.markdown(
        f"**{t('batch_preview')}** {time_start}–{time_end} "
        f"<span style='color:#4caf50;'>{count_book} {t('will_book').lower()}</span> "
        f"<span style='color:#888;'>{count_skip} {t('will_skip').lower()}</span>",
        unsafe_allow_html=True,
    )
    st.markdown("".join(blocks), unsafe_allow_html=True)

# ---- CALENDAR ----
col_cal, col_toggle = st.columns([4, 1])
with col_cal:
    st.subheader(t("schedule_calendar"))
with col_toggle:
    if st.session_state.view_mode == "mobile":
        if st.button("🖥️ Desktop", use_container_width=True, key="to_desktop"):
            st.session_state.view_mode = "desktop"
            st.rerun()
    else:
        if st.button("📱 Mobile", use_container_width=True, key="to_mobile"):
            st.session_state.view_mode = "mobile"
            st.rerun()

w1_start, w1_end = format_date_range(week1[0], week1[-1])
w2_start, w2_end = format_date_range(week2[0], week2[-1])

if st.session_state.view_mode == "mobile":
    render_week_grid_mobile(week1, t("week_1", start=w1_start, end=w1_end))
    st.markdown("<br>", unsafe_allow_html=True)
    render_week_grid_mobile(week2, t("week_2", start=w2_start, end=w2_end))
else:
    render_week_grid(week1, t("week_1", start=w1_start, end=w1_end))
    st.markdown("<br>", unsafe_allow_html=True)
    render_week_grid(week2, t("week_2", start=w2_start, end=w2_end))

st.markdown("---")

# ---- SUMMARY ----
st.subheader(t("all_bookings_hours"))

if not df_bookings.empty:
    # Leaderboard (work on a copy, never mutate the cached DataFrame)
    df_bk = df_bookings.copy()
    df_bk["hours"] = df_bk["slot_time"].map(SLOT_HOURS)

    # Slot count per participant (before sorting)
    slots_df = df_bk.groupby("participant_name").size().reset_index(name="cnt")

    # Hours tally
    tally = df_bk.groupby("participant_name")["hours"].sum().reset_index()
    tally.columns = [t("col_participant"), t("col_total_hours")]

    # Merge slot count — ensures alignment regardless of sort order
    tally = tally.merge(slots_df, left_on=t("col_participant"), right_on="participant_name", how="left")
    tally[t("col_slots")] = tally["cnt"]
    tally = tally.drop(columns=["participant_name", "cnt"])
    tally = tally.sort_values(t("col_total_hours"), ascending=False)
    st.dataframe(tally, hide_index=True, use_container_width=True)

    # Calendar grid view of the full schedule
    st.subheader(t("full_schedule"))

    def _render_schedule_table(week_days):
        rows = []
        for slot_label, _, _ in TIME_SLOTS:
            cells = []
            for d in week_days:
                date_str = d.isoformat()
                booked = booking_lookup.get((date_str, slot_label), [])
                waiting = waitlist_lookup.get((date_str, slot_label), [])
                parts = []
                if booked:
                    parts.append("<b>" + ", ".join(booked) + "</b>")
                if waiting:
                    parts.append(
                        "<span style='font-size:0.82em;color:#997700;'>"
                        + "☐ " + ", ".join(waiting) + "</span>"
                    )
                cells.append(" &nbsp;·&nbsp; ".join(parts) if parts else "—")
            rows.append(f"<tr><td style='font-weight:600;font-size:0.82em;white-space:nowrap'>"
                        f"{slot_label}</td>" + "".join(f"<td style='font-size:0.82em'>{c}</td>" for c in cells) + "</tr>")

        headers = "".join(f"<th style='font-size:0.82em'>{day_name(d)}<br>{d.day} {month_name(d)}</th>" for d in week_days)
        return (
            "<table style='width:100%;border-collapse:collapse;text-align:center;vertical-align:top'>"
            f"<thead><tr><th></th>{headers}</tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table>"
        )

    st.markdown(_render_schedule_table(week1), unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(_render_schedule_table(week2), unsafe_allow_html=True)
else:
    st.info(t("no_bookings_yet"))
