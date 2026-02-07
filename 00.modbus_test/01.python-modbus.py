from pyModbusTCP.server import ModbusServer
import time

# --- 設定項目 ---
SERVER_IP = "192.168.0.95"  # AI-PCのIPアドレス
SERVER_PORT = 502

# ModbusアドレスはPLCアドレス - 40001で計算
# PLC 41025 → Modbus 1024
# PLC 41026 → Modbus 1025
ADDR_TRIGGER = 1024  # 撮影開始指令
ADDR_DONE    = 1025  # 撮影完了通知

def run_camera_simulator():
    server = ModbusServer(host=SERVER_IP, port=SERVER_PORT, no_block=True)
    
    try:
        print(f"カメラシミュレーター起動中... ({SERVER_IP}:{SERVER_PORT})")
        server.start()
        print("Dobotからの接続を待機しています...\n")
        
        while True:
            # 1. 撮影トリガーを監視（リスト形式で取得される）
            trigger_value = server.data_bank.get_holding_registers(ADDR_TRIGGER, 1)
            
            if trigger_value and trigger_value[0] == 1:
                print("--- 撮影指令を受信 (41025 = 1) ---")
                
                # 2. カメラ撮影をシミュレート
                print("📷 カメラ撮影中...")
                time.sleep(2)  # AI処理をシミュレート
                print("✅ 撮影完了。データを保存しました。")
                
                # 3. 完了フラグをセット
                server.data_bank.set_holding_registers(ADDR_DONE, [1])
                print("完了通知を送信 (41026 = 1)\n")
                
                # 4. Dobot側がトリガーをリセット (0) するのを待機
                print("Dobotのトリガーリセットを待機中...")
                while True:
                    trigger_check = server.data_bank.get_holding_registers(ADDR_TRIGGER, 1)
                    if trigger_check and trigger_check[0] == 0:
                        print("トリガーがリセットされました (41025 = 0)")
                        break
                    time.sleep(0.05)
                
                # 5. 完了フラグをリセット（次回に備える）
                server.data_bank.set_holding_registers(ADDR_DONE, [0])
                print("システムをリセット (41026 = 0)\n")
                print("=" * 50)
                print("次の撮影指令を待機中...\n")

            time.sleep(0.05)  # 50ms周期でポーリング

    except KeyboardInterrupt:
        print("\nシミュレーターを停止します。")
    finally:
        server.stop()

if __name__ == "__main__":
    run_camera_simulator()