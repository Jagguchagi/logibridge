"""Switch a running simulator's mode (simulator must be started with --control).
Usage: python -m data_pipeline.control combined     then later: python -m data_pipeline.control none"""
import argparse

from data_pipeline.simulator import MODES


def main():
    import paho.mqtt.client as mqtt
    p = argparse.ArgumentParser()
    p.add_argument('mode', choices=MODES)
    p.add_argument('--truck-id', default='T001')
    p.add_argument('--host', default='localhost')
    a = p.parse_args()
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    c.connect(a.host, 1883)
    c.loop_start()
    try:
        c.publish(f'logibridge/trucks/{a.truck_id}/control/anomaly', a.mode, qos=1).wait_for_publish(timeout=5)
        print(f'requested mode={a.mode}')
    finally:
        c.loop_stop()
        c.disconnect()


if __name__ == '__main__':
    main()
