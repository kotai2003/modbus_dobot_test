from pyModbusTCP.server import ModbusServer
import time

SERVER_IP = "0.0.0.0"
SERVER_PORT = 502

def run_address_test():
    server = ModbusServer(host=SERVER_IP, port=SERVER_PORT, no_block=True)
    
    print("=" * 70)
    print("Modbusアドレステストモード")
    print("=" * 70)
    
    try:
        server.start()
        print("✅ サーバー起動成功\n")
        
        # 監視する可能性のあるアドレス範囲
        test_ranges = [
            ("0-10", 0, 10),
            ("1024-1030", 1024, 1030),
            ("41025-41030", 41025, 41030)
        ]
        
        print("Dobotからの書き込みを待機中...")
        print("Dobot側で SetHoldRegs を実行してください\n")
        
        last_values = {}
        loop_count = 0
        
        while True:
            loop_count += 1
            
            # 5秒ごとに生存確認
            if loop_count % 100 == 0:
                print(f"[{time.strftime('%H:%M:%S')}] 監視中...")
            
            # すべての候補アドレスをスキャン
            for range_name, start, end in test_ranges:
                for addr in range(start, end + 1):
                    values = server.data_bank.get_holding_registers(addr, 1)
                    
                    if values and values[0] != 0:
                        current_value = values[0]
                        
                        # 値の変化を検出
                        if addr not in last_values or last_values[addr] != current_value:
                            print(f"\n{'='*70}")
                            print(f"[{time.strftime('%H:%M:%S')}] 🎯 値の変化を検出！")
                            print(f"アドレス: {addr}")
                            print(f"値: {last_values.get(addr, 0)} → {current_value}")
                            print(f"{'='*70}\n")
                            
                            last_values[addr] = current_value
                            
                            # 撮影シミュレーション（アドレス1024または41025の場合）
                            if addr in [1024, 41025] and current_value == 1:
                                print("📷 撮影処理を実行中...")
                                time.sleep(2)
                                
                                # 完了フラグをセット（複数候補を試す）
                                for done_addr in [1025, 41026]:
                                    server.data_bank.set_holding_registers(done_addr, [1])
                                    print(f"✅ 完了フラグセット: アドレス {done_addr} = 1")
            
            time.sleep(0.05)
    
    except KeyboardInterrupt:
        print("\n\n🛑 テストを終了します")
    finally:
        server.stop()

if __name__ == "__main__":
    run_address_test()