# smooth_streamlit_dual_yaxis.py
import streamlit as st
import paho.mqtt.client as mqtt
import threading
import ast
import pandas as pd
import plotly.graph_objects as go
import time

# MQTT settings
broker = "test.mosquitto.org"
port = 1883
topic = "Win/MQTT_test/modbus_data"

latest_data = {"coil": None, "analog": None}
update_event = threading.Event()

if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["timestamp", "analog", "coil"])

def on_connect(client, userdata, flags, rc):
    client.subscribe(topic)

def on_message(client, userdata, msg):
    try:
        payload = ast.literal_eval(msg.payload.decode())
        analog_val = payload.get("analog")
        coil_val = payload.get("coil")
        if analog_val is not None and coil_val is not None:
            latest_data["analog"] = analog_val
            latest_data["coil"] = coil_val
            update_event.set()
    except Exception as e:
        print(f"Message parse error: {e}")

def mqtt_thread():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(broker, port)
    client.loop_forever()

if "mqtt_thread_started" not in st.session_state:
    threading.Thread(target=mqtt_thread, daemon=True).start()
    st.session_state.mqtt_thread_started = True

st.title("Live Modbus Data via MQTT")

col1, col2 = st.columns(2)
with col1:
    analog_metric = st.metric("Analog Value", "N/A")
with col2:
    coil_metric = st.metric("Coil State", "N/A")

plot_placeholder = st.empty()

while True:
    if update_event.wait(timeout=1):
        update_event.clear()

        ts = time.strftime("%H:%M:%S")
        new_row = {"timestamp": ts, "analog": latest_data["analog"], "coil": latest_data["coil"]}
        st.session_state.history = pd.concat([
            st.session_state.history,
            pd.DataFrame([new_row])
        ], ignore_index=True)

        if len(st.session_state.history) > 30:
            st.session_state.history = st.session_state.history.iloc[-30:]

        analog_metric.metric("Analog Value", latest_data["analog"])
        coil_metric.metric("Coil State", latest_data["coil"])

        df = st.session_state.history
        fig = go.Figure()

        # Analog on primary y-axis
        fig.add_trace(go.Scatter(
            x=df["timestamp"], y=df["analog"],
            mode="lines+markers", name="Analog",
            line=dict(color="blue")
        ))

        # Coil on secondary y-axis
        fig.add_trace(go.Scatter(
            x=df["timestamp"], y=df["coil"],
            mode="lines+markers", name="Coil",
            line=dict(color="red", dash="dot"),
            yaxis="y2"
        ))

        fig.update_layout(
            title="Real-Time Modbus Data (Analog & Coil)",
            xaxis_title="Time",
            yaxis=dict(title="Analog Value", side="left"),
            yaxis2=dict(title="Coil State", overlaying="y", side="right", range=[-0.2, 1.2]),
            legend=dict(x=0.01, y=0.99),
            template="plotly_white",
            height=450
        )

        plot_placeholder.plotly_chart(fig, use_container_width=True)
    else:
        time.sleep(0.1)
