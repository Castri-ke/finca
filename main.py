import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import date

# ================== CONFIGURACIÓN DE LA APP ==================
st.set_page_config(page_title="Finca ERP", page_icon="🚜", layout="wide")

# 🚨 REEMPLAZA ESTO CON TUS CLAVES DE SUPABASE 🚨
SUPABASE_URL = "https://bkwjzcsxuznuojijegzj.supabase.co"
SUPABASE_KEY = "sb_publishable_FVoKLvcRDQOwdEn1oOyJmQ_bFvCO2nf"

# Conexión a la nube
@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    supabase: Client = init_connection()
except Exception as e:
    st.error("⚠️ Error de conexión. Revisa tus claves.")
    st.stop()

# ================== MENÚ LATERAL ==================
st.sidebar.title("🚜 Finca ERP")
st.sidebar.markdown("---")
menu = st.sidebar.radio("Navegación", [
    "📊 Dashboard", 
    "💰 Finanzas y Cobros", 
    "👥 Personal y Nómina", 
    "🌱 Cultivos e Insumos", 
    "🔧 Maquinaria"
])

# ================== 1. DASHBOARD ==================
if menu == "📊 Dashboard":
    st.title("¡Bienvenido al Panel Gerencial!")
    
    # Traer datos de la nube
    finanzas = supabase.table("finanzas").select("*").execute().data
    cobros = supabase.table("cuentas_cobrar").select("*").execute().data
    trabajadores = supabase.table("trabajadores").select("*").execute().data
    
    ingresos = sum(f['monto'] for f in finanzas if f['tipo'] == 'INGRESO')
    egresos = sum(f['monto'] for f in finanzas if f['tipo'] == 'EGRESO')
    deudas = sum(c['saldo_pendiente'] for c in cobros if c['estado'] == 'PENDIENTE')
    activos = len([t for t in trabajadores if t['estado'] == 'ACTIVO'])

    col1, col2, col3 = st.columns(3)
    with col1:
        st.success("💰 Balance Total")
        st.metric("Ingresos", f"${ingresos:,.0f}")
        st.metric("Egresos", f"${egresos:,.0f}")
    with col2:
        st.error("🚨 Por Cobrar")
        st.metric("Dinero en la calle", f"${deudas:,.0f}")
    with col3:
        st.info("🌱 Operaciones")
        st.metric("Trabajadores Activos", activos)

# ================== 2. FINANZAS ==================
elif menu == "💰 Finanzas y Cobros":
    st.title("Gestión Financiera")
    tab1, tab2 = st.tabs(["Nuevo Movimiento", "Cuentas por Cobrar"])
    
    with tab1:
        with st.form("form_movimiento"):
            col1, col2 = st.columns(2)
            tipo = col1.selectbox("Tipo", ["INGRESO", "EGRESO"])
            cat = col2.text_input("Categoría (Ej. Venta Guanábana)")
            monto = col1.number_input("Monto ($)", min_value=0.0, step=1000.0)
            bolsillo = col2.selectbox("Bolsillo", ["EFECTIVO", "BANCO"])
            desc = st.text_input("Descripción")
            if st.form_submit_button("Guardar Movimiento"):
                if cat and monto > 0:
                    supabase.table("finanzas").insert({"tipo": tipo, "categoria": cat, "monto": monto, "bolsillo": bolsillo, "descripcion": desc, "fecha": str(date.today())}).execute()
                    st.success("Movimiento guardado exitosamente!")
                    st.rerun()
                else:
                    st.error("Llena todos los campos.")
        
        st.subheader("Historial")
        historial = supabase.table("finanzas").select("*").order("id", desc=True).execute().data
        if historial: st.dataframe(pd.DataFrame(historial))

        with st.expander("❌ Eliminar un Movimiento"):
            id_borrar = st.number_input("ID del movimiento a borrar", min_value=0, step=1)
            if st.button("Eliminar Movimiento"):
                supabase.table("finanzas").delete().eq("id", id_borrar).execute()
                st.rerun()

    with tab2:
        with st.form("form_cobros"):
            col1, col2 = st.columns(2)
            cliente = col1.text_input("Cliente")
            tel = col2.text_input("Teléfono")
            monto_deuda = col1.number_input("Monto de la deuda ($)", min_value=0.0, step=1000.0)
            fecha_limite = col2.date_input("Fecha Límite")
            if st.form_submit_button("Añadir Deuda"):
                supabase.table("cuentas_cobrar").insert({"cliente": cliente, "telefono": tel, "monto_total": monto_deuda, "saldo_pendiente": monto_deuda, "fecha_limite": str(fecha_limite)}).execute()
                st.success("Deuda registrada!")
                st.rerun()
                
        st.subheader("Cartera Pendiente")
        deudas = supabase.table("cuentas_cobrar").select("*").eq("estado", "PENDIENTE").execute().data
        if deudas: st.dataframe(pd.DataFrame(deudas))
        
        with st.expander("❌ Eliminar una Deuda"):
            id_borrar = st.number_input("ID de la deuda a borrar", min_value=0, step=1, key="del_deuda")
            if st.button("Eliminar Deuda"):
                supabase.table("cuentas_cobrar").delete().eq("id", id_borrar).execute()
                st.rerun()

# ================== 3. NÓMINA ==================
elif menu == "👥 Personal y Nómina":
    st.title("Personal y Nómina")
    tab1, tab2 = st.tabs(["Trabajadores", "Vales / Adelantos"])
    
    with tab1:
        with st.form("form_trabajador"):
            col1, col2 = st.columns(2)
            nombre = col1.text_input("Nombre")
            cedula = col2.text_input("Cédula")
            frecuencia = col1.selectbox("Pago", ["DIARIO", "SEMANAL", "QUINCENAL", "MENSUAL"])
            if st.form_submit_button("Registrar Trabajador"):
                count = len(supabase.table("trabajadores").select("*").execute().data) + 1
                codigo = f"TR-{count:04d}"
                supabase.table("trabajadores").insert({"codigo": codigo, "nombre": nombre, "cedula": cedula, "frecuencia_pago": frecuencia}).execute()
                st.success("Trabajador guardado!")
                st.rerun()
                
        st.subheader("Lista de Trabajadores")
        trabajadores = supabase.table("trabajadores").select("*").execute().data
        if trabajadores: st.dataframe(pd.DataFrame(trabajadores)[['codigo', 'nombre', 'cedula', 'frecuencia_pago']])
        
        with st.expander("❌ Eliminar Trabajador"):
            cod_borrar = st.text_input("Código (Ej. TR-0001)")
            if st.button("Eliminar"):
                supabase.table("trabajadores").delete().eq("codigo", cod_borrar).execute()
                st.rerun()

    with tab2:
        trabajadores = supabase.table("trabajadores").select("codigo, nombre").execute().data
        lista_tr = [f"{t['codigo']} - {t['nombre']}" for t in trabajadores] if trabajadores else ["Sin personal"]
        
        with st.form("form_vales"):
            trab_sel = st.selectbox("Trabajador", lista_tr)
            monto_vale = st.number_input("Monto del Vale ($)", min_value=0.0, step=1000.0)
            if st.form_submit_button("Otorgar Vale"):
                cod = trab_sel.split(" - ")[0]
                supabase.table("vales").insert({"codigo_trabajador": cod, "fecha": str(date.today()), "monto": monto_vale}).execute()
                st.success("Vale guardado!")
                st.rerun()
                
        st.subheader("Adelantos Pendientes")
        vales = supabase.table("vales").select("*").eq("estado", "PENDIENTE").execute().data
        if vales: st.dataframe(pd.DataFrame(vales))

# ================== 4. CULTIVOS Y POLINIZACIÓN ==================
elif menu == "🌱 Cultivos e Insumos":
    st.title("Cultivos, Insumos y Polinización")
    tab1, tab2 = st.tabs(["🌺 Polinización Guanábana", "📦 Inventario"])
    
    with tab1:
        trabajadores = supabase.table("trabajadores").select("nombre").execute().data
        lista_tr = [t['nombre'] for t in trabajadores] if trabajadores else ["Sin personal"]
        
        with st.form("form_pol"):
            lote = st.text_input("Lote (Ej. Lote Central)")
            trab = st.selectbox("Trabajador a cargo", lista_tr)
            col1, col2, col3 = st.columns(3)
            pol = col1.number_input("Flores Polinizadas", min_value=0)
            malas = col2.number_input("Flores Malas", min_value=0)
            emb = col3.number_input("Embolsadas", min_value=0)
            if st.form_submit_button("Registrar Actividad"):
                supabase.table("polinizacion_guanabana").insert({"fecha": str(date.today()), "lote": lote, "trabajador": trab, "flores_polinizadas": pol, "flores_malas": malas, "frutos_embolsados": emb}).execute()
                st.success("Actividad de campo registrada!")
                st.rerun()
                
        st.subheader("Historial de Polinización")
        historial = supabase.table("polinizacion_guanabana").select("*").order("id", desc=True).execute().data
        
        if historial:
            # Resumen Automático
            tot_pol = sum(h['flores_polinizadas'] for h in historial)
            tot_mal = sum(h['flores_malas'] for h in historial)
            tot_emb = sum(h['frutos_embolsados'] for h in historial)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Tot. Polinizadas", tot_pol)
            c2.metric("Tot. Malas", tot_mal)
            c3.metric("Tot. Embolsadas", tot_emb)
            
            st.dataframe(pd.DataFrame(historial)[['id', 'fecha', 'lote', 'trabajador', 'flores_polinizadas', 'flores_malas', 'frutos_embolsados']])
            
            with st.expander("❌ Eliminar Actividad"):
                id_borrar = st.number_input("ID de registro a borrar", min_value=0, step=1, key="del_pol")
                if st.button("Eliminar Registro"):
                    supabase.table("polinizacion_guanabana").delete().eq("id", id_borrar).execute()
                    st.rerun()

    with tab2:
        st.info("Aquí puedes añadir la lógica de inventario, funciona igual que el resto!")

# ================== 5. MAQUINARIA ==================
elif menu == "🔧 Maquinaria":
    st.title("Maquinaria y Mantenimiento")
    st.success("Módulo conectado exitosamente a la nube. ¡Agrega tus equipos aquí!")