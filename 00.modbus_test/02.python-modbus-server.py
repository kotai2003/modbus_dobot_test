from pyModbusTCP.server import ModbusServer
import time

SERVER_IP = "0.0.0.0"
SERVER_PORT = 502

ADDR_TRIGGER = 41025  # 撮影開始指令
ADDR_DONE    = 1025   # ★★★ ここを1025に変更 ★★★

def run_camera_simulator():
    server = ModbusServer(host=SERVER_IP, port=SERVER_PORT, no_block=True)
    
    # 初期値をセット
    server.data_bank.set_holding_registers(ADDR_TRIGGER, [0])
    server.data_bank.set_holding_registers(ADDR_DONE, [0])
    
    print("=" * 70)
    print("カメラシミュレーター起動")
    print("=" * 70)
    print(f"待ち受けアドレス: {SERVER_IP}:{SERVER_PORT}")
    print(f"トリガーアドレス: {ADDR_TRIGGER}")
    print(f"完了フラグアドレス: {ADDR_DONE}")  # ★1025と表示されるはず
    print("=" * 70)
    
    try:
        server.start()
        print("✅ サーバー起動成功")
        print("\nDobotからの撮影指令を待機中...\n")
        
        loop_count = 0
        
        while True:
            loop_count += 1
            
            # 10秒ごとに生存確認
            if loop_count % 200 == 0:
                print(f"[{time.strftime('%H:%M:%S')}] サーバー稼働中...")
            
            # トリガー監視
            trigger_value = server.data_bank.get_holding_registers(ADDR_TRIGGER, 1)
            
            if trigger_value and trigger_value[0] == 1:
                print(f"\n{'='*70}")
                print(f"[{time.strftime('%H:%M:%S')}] 📸 撮影指令を受信")
                print(f"{'='*70}")
                
                # カメラ撮影をシミュレート
                print("📷 カメラ撮影処理を開始...")
                for i in range(1, 5):
                    time.sleep(0.5)
                    print(f"  処理中... {i*25}%")
                
                print("✅ 撮影完了。データを保存しました。")
                
                # 完了フラグをセット
                server.data_bank.set_holding_registers(ADDR_DONE, [1])
                print(f"📤 完了通知を送信 (1025 = 1)")  # ★1025と表示
                
                # Dobot側がトリガーをリセットするのを待機
                print("\n⏳ Dobotのトリガーリセットを待機中...")
                wait_count = 0
                while True:
                    trigger_check = server.data_bank.get_holding_registers(ADDR_TRIGGER, 1)
                    if trigger_check and trigger_check[0] == 0:
                        print(f"✅ トリガーがリセットされました")
                        break
                    
                    wait_count += 1
                    if wait_count > 200:
                        print("⚠️  警告: リセットタイムアウト")
                        break
                    
                    time.sleep(0.05)
                
                # 完了フラグをリセット
                server.data_bank.set_holding_registers(ADDR_DONE, [0])
                print("🔄 システムをリセット")
                print(f"{'='*70}\n")
                print("⏸️  次の撮影指令を待機中...\n")

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\n\n🛑 シミュレーターを停止します")
    finally:
        server.stop()
        print("サーバーを終了しました")

if __name__ == "__main__":
    run_camera_simulator()