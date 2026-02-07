from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
import threading
import time

print("pymodbus動作確認テスト")

# データストア
store = ModbusSlaveContext(
    hr=ModbusSequentialDataBlock(0, [0]*100)
)
context = ModbusServerContext(slaves=store, single=True)

# サーバー起動
def run_server():
    StartTcpServer(context=context, address=("0.0.0.0", 502))

thread = threading.Thread(target=run_server, daemon=True)
thread.start()

print("✅ サーバー起動成功")
print("Ctrl+C で終了")

# テスト: レジスタに値を書き込み
context[0].setValues(3, 1024, [123])
value = context[0].getValues(3, 1024, 1)[0]
print(f"テスト: レジスタ1024の値 = {value}")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n終了")