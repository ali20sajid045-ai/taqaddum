"""مشروع تقدم - خريطة ملاحية تشاركية للعراق (Streamlit + Folium)."""
from datetime import datetime

import folium
import requests
import streamlit as st
from streamlit_folium import st_folium

# ───────────────────────── الإعدادات العامة ─────────────────────────
st.set_page_config(
    page_title="مشروع تقدم - Taqaddum Map",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BAGHDAD = (33.3152, 44.3661)
HEADERS = {"User-Agent": "taqaddum-map/1.0"}
REPORT_TYPES = {
    "bump": ("⚠️", "مطب"),
    "accident": ("💥", "حادث"),
    "defect": ("🛠️", "خلل بالشارع"),
}

# ───────────────────────── التصميم (CSS) ─────────────────────────
st.markdown(
    """
<style>
    [data-testid="stToolbar"], [data-testid="stDecoration"], footer {display: none !important;}
    [data-testid="stHeader"] {background: transparent !important;}
    .block-container {padding: 0 !important; max-width: 100% !important;}
    [data-testid="stSidebar"] {direction: rtl; text-align: right;}

    /* أزرار التبليغ */
    .st-key-reports {position: fixed; left: 14px; top: 30%; z-index: 1000; width: auto !important;}
    .st-key-reports button {
        width: 58px; height: 58px; border-radius: 50%; border: 2px solid #fff;
        font-size: 24px; padding: 0; box-shadow: 0 4px 12px rgba(0,0,0,.6);
    }
    .st-key-btn_bump button {background: #ff9800;}
    .st-key-btn_accident button {background: #f44336;}
    .st-key-btn_defect button {background: #9c27b0;}

    /* مربع المسار */
    .st-key-routebox {
        position: fixed; bottom: 18px; left: 50%; transform: translateX(-50%);
        width: 92%; max-width: 430px; z-index: 1000; direction: rtl;
        background: rgba(18,18,18,.94); border: 2px solid #FFD700; border-radius: 18px;
        padding: 14px; box-shadow: 0 8px 25px rgba(0,0,0,.85); backdrop-filter: blur(10px);
    }
    .st-key-routebox input {background: #2a2a2a !important; color: #fff !important; text-align: right;}
    .st-key-routebox button {background: #FFD700; color: #000; font-weight: bold; width: 100%; border: 0;}
    .route-title {color: #FFD700; font-weight: bold; text-align: center; margin-bottom: 6px;}
    .route-info {color: #eee; text-align: center; font-size: 14px; margin-top: 6px;}

    /* مؤشر المنتصف */
    .crosshair {
        position: fixed; top: 50%; left: 50%; width: 40px; height: 40px;
        margin: -20px 0 0 -20px; z-index: 999; pointer-events: none;
        color: #FFD700; font: bold 34px/40px sans-serif; text-align: center;
        text-shadow: 0 0 8px #000, 0 0 4px #000;
    }
</style>
<div class="crosshair">+</div>
""",
    unsafe_allow_html=True,
)

# ───────────────────────── حالة التطبيق ─────────────────────────
defaults = {
    "reports": [],
    "center": BAGHDAD,       # آخر مركز للخريطة (يحدّثه المستخدم بالتحريك)
    "start_view": (BAGHDAD, 13),
    "map_key": 0,
    "route": None,
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)


# ───────────────────────── الخدمات الخارجية ─────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def geocode(query: str):
    """تحويل اسم مكان إلى إحداثيات (داخل العراق)."""
    r = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": query, "format": "json", "limit": 1, "countrycodes": "iq"},
        headers=HEADERS,
        timeout=10,
    )
    r.raise_for_status()
    data = r.json()
    return (float(data[0]["lat"]), float(data[0]["lon"])) if data else None


@st.cache_data(ttl=600, show_spinner=False)
def get_route(a: tuple, b: tuple):
    """حساب مسار القيادة بين نقطتين."""
    r = requests.get(
        f"https://router.project-osrm.org/route/v1/driving/{a[1]},{a[0]};{b[1]},{b[0]}",
        params={"overview": "full", "geometries": "geojson"},
        headers=HEADERS,
        timeout=15,
    )
    r.raise_for_status()
    j = r.json()
    if j.get("code") != "Ok" or not j.get("routes"):
        return None
    rt = j["routes"][0]
    return {
        "coords": [(lat, lng) for lng, lat in rt["geometry"]["coordinates"]],
        "km": rt["distance"] / 1000,
        "min": rt["duration"] / 60,
    }


# ───────────────────────── الأحداث ─────────────────────────
def add_report(kind: str):
    lat, lng = st.session_state.center
    st.session_state.reports.append(
        {"kind": kind, "lat": lat, "lng": lng, "time": datetime.now().strftime("%H:%M")}
    )
    st.toast(f"تم تسجيل بلاغ: {REPORT_TYPES[kind][1]}", icon=REPORT_TYPES[kind][0])


def clear_reports():
    st.session_state.reports = []


# ───────────────────────── القائمة الجانبية ─────────────────────────
with st.sidebar:
    st.title("☰ القائمة الرئيسية")
    st.subheader("مشروع تقدم - العراق")
    st.divider()
    st.markdown("👤 **حسابي**")
    st.markdown("🏪 **إدارة المتاجر والمحلات**")
    st.markdown("⚙️ **إعدادات الخريطة والتنبيهات**")
    st.divider()
    st.metric("عدد البلاغات", len(st.session_state.reports))
    st.button("🗑️ مسح كل البلاغات", on_click=clear_reports, use_container_width=True)
    st.caption("تطبيق ملاحي تشاركي - خدمة الشارع العراقي")

# ───────────────────────── أزرار التبليغ ─────────────────────────
with st.container(key="reports"):
    for kind, (icon, name) in REPORT_TYPES.items():
        st.button(icon, key=f"btn_{kind}", help=f"تبليغ عن {name}", on_click=add_report, args=(kind,))

# ───────────────────────── مربع المسار ─────────────────────────
with st.container(key="routebox"):
    st.markdown('<div class="route-title">📍 تحديد المسار</div>', unsafe_allow_html=True)
    origin = st.text_input("الانطلاق", placeholder="🎯 موقع الانطلاق (فارغ = مركز الخريطة +)", label_visibility="collapsed")
    dest = st.text_input("الوصول", placeholder="🏁 موقع الوصول (الوجهة)", label_visibility="collapsed")
    go = st.button("ابدأ المسار", key="go")
    route_slot = st.empty()

if go:
    if not dest.strip():
        st.toast("اكتب الوجهة أولاً", icon="⚠️")
    else:
        try:
            with st.spinner("جاري حساب المسار..."):
                a = geocode(origin.strip()) if origin.strip() else tuple(st.session_state.center)
                b = geocode(dest.strip())
                if a is None or b is None:
                    st.toast("لم أجد أحد المكانين، جرّب اسماً أوضح", icon="❌")
                else:
                    route = get_route(tuple(a), tuple(b))
                    if route is None:
                        st.toast("لا يوجد مسار بين النقطتين", icon="❌")
                    else:
                        st.session_state.route = route
                        st.session_state.start_view = (a, 12)
                        st.session_state.map_key += 1  # إعادة بناء الخريطة على مكان المسار
        except requests.RequestException:
            st.toast("مشكلة اتصال بخدمة الخرائط، حاول مرة ثانية", icon="📡")

if st.session_state.route:
    rt = st.session_state.route
    route_slot.markdown(
        f'<div class="route-info">🚗 {rt["km"]:.1f} كم - ⏱️ {round(rt["min"])} دقيقة</div>',
        unsafe_allow_html=True,
    )

# ───────────────────────── بناء الخريطة ─────────────────────────
start_center, start_zoom = st.session_state.start_view
m = folium.Map(location=list(start_center), zoom_start=start_zoom, tiles=None, zoom_control=False, max_zoom=19)

folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr="Esri",
    name="صور جوية",
    max_zoom=19,
).add_to(m)
folium.TileLayer(
    tiles="https://{s}.basemaps.cartocdn.com/rastertiles/voyager_only_labels/{z}/{x}/{y}{r}.png",
    attr="CartoDB",
    name="أسماء الشوارع",
    max_zoom=19,
    overlay=True,
).add_to(m)

# العناصر الديناميكية (بلاغات + مسار) في مجموعة منفصلة حتى لا تتغير زاوية الخريطة
fg = folium.FeatureGroup(name="البلاغات والمسار")
for r in st.session_state.reports:
    icon, name = REPORT_TYPES[r["kind"]]
    folium.Marker(
        [r["lat"], r["lng"]],
        popup=f"{name} - {r['time']}",
        icon=folium.DivIcon(html=f'<div style="font-size:26px;text-shadow:0 0 4px #000">{icon}</div>'),
    ).add_to(fg)
if st.session_state.route:
    folium.PolyLine(st.session_state.route["coords"], color="#FFD700", weight=7, opacity=0.9).add_to(fg)

out = st_folium(
    m,
    key=f"map_{st.session_state.map_key}",
    feature_group_to_add=fg,
    height=800,
    use_container_width=True,
    returned_objects=["center"],
)

# حفظ مركز الخريطة الحالي ليُستخدم في البلاغات (يُقرأ في التشغيل التالي)
if out and out.get("center"):
    st.session_state.center = (round(out["center"]["lat"], 6), round(out["center"]["lng"], 6))
