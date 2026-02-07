# Modbus レジスタ完全解説

このシステムで使用されているModbusレジスタについて、アドレスマッピング、データフロー、注意点を詳しく解説します。

---

## 📊 使用レジスタ一覧

| 論理名 | Dobot側<br>書き込み | Dobot側<br>読み取り | PC側<br>受信 | PC側<br>送信 | データ型 | 用途 |
|--------|-------------------|-------------------|------------|------------|---------|------|
| **撮影トリガー** | `41025` | `41025` | `41025` | `41025` | U16 | 撮影開始指令 (0/1) |
| **完了フラグ** | - | `1025` | - | `1025` | U16 | 撮影完了通知 (0/1) |

---

## 🔍 レジスタ詳細

### 1️⃣ **撮影トリガーレジスタ (41025)**

#### **役割**
Dobotから外部PCへの撮影開始指令

#### **データフロー**
```
【Dobot → PC】
Dobot側: SetHoldRegs(id, 41025, 1, {1})
    ↓
PC側: server.data_bank.get_holding_registers(41025, 1) → [1]
    ↓
PC側: カメラ撮影処理を開始
```

#### **状態遷移**
```
初期状態: 41025 = 0 (待機中)
    ↓
Dobot: 41025 = 1 (撮影指令)
    ↓
PC: 指令を検出して撮影実行
    ↓
Dobot: 41025 = 0 (リセット)
    ↓
初期状態に戻る
```

#### **コード例**

**Dobot側（送信）:**
```lua
-- トリガーをON
SetHoldRegs(id, 41025, 1, {1}, "U16")

-- トリガーをOFF（リセット）
SetHoldRegs(id, 41025, 1, {0}, "U16")
```

**PC側（受信）:**
```python
# トリガーを監視
trigger_value = server.data_bank.get_holding_registers(41025, 1)
if trigger_value and trigger_value[0] == 1:
    # 撮影処理を実行
    capture_image()
```

---

### 2️⃣ **完了フラグレジスタ (1025)**

#### **役割**
外部PCからDobotへの撮影完了通知

#### **データフロー**
```
【PC → Dobot】
PC側: server.data_bank.set_holding_registers(1025, [1])
    ↓
Dobot側: GetHoldRegs(id, 1025, 1, "U16") → {1}
    ↓
Dobot側: 撮影完了を検出して次の動作へ
```

#### **状態遷移**
```
初期状態: 1025 = 0 (処理中)
    ↓
PC: 1025 = 1 (撮影完了)
    ↓
Dobot: 完了を検出
    ↓
Dobot: トリガーリセット (41025 = 0)
    ↓
PC: 1025 = 0 (リセット)
    ↓
初期状態に戻る
```

#### **コード例**

**PC側（送信）:**
```python
# 完了フラグをON
server.data_bank.set_holding_registers(1025, [1])

# 完了フラグをOFF（リセット）
server.data_bank.set_holding_registers(1025, [0])
```

**Dobot側（受信）:**
```lua
-- 完了フラグを監視
local done_flag = GetHoldRegs(id, 1025, 1, "U16")
if done_flag and done_flag[1] == 1 then
    -- 完了を検出
    print("撮影完了")
end
```

---

## 🔢 アドレスマッピングの詳細

### **PLCアドレス vs Modbusアドレス**

Modbus通信には2つのアドレス表記法があります：

#### **PLCアドレス（4xxxx形式）**
- 人間が読みやすい形式
- `40001`から始まる
- **Dobot側はこの形式を使用**

#### **Modbusプロトコルアドレス（0始まり）**
- 実際の通信で使用
- `0`から始まる
- **変換式**: `PLCアドレス - 40001 = Modbusアドレス`

---

### **アドレス変換表**

| PLCアドレス | Modbusアドレス | 計算式 |
|------------|---------------|--------|
| `40001` | `0` | 40001 - 40001 = 0 |
| `40002` | `1` | 40002 - 40001 = 1 |
| `41025` | `1024` | 41025 - 40001 = 1024 |
| `41026` | `1025` | 41026 - 40001 = 1025 |

---

### **実際の動作における特殊な挙動**

このシステムでは、以下の特殊な挙動が確認されています：

```python
# Python側（pyModbusTCP）の挙動

# ケース1: トリガーレジスタ
server.data_bank.set_holding_registers(41025, [1])
# → Dobot側は 41025 から読み取れる ✅

# ケース2: 完了フラグレジスタ
server.data_bank.set_holding_registers(1025, [1])
# → Dobot側は 1025 から読み取れる ✅

server.data_bank.set_holding_registers(41026, [1])
# → Dobot側は 1025 から読み取れない ❌
```

**重要な発見:**
- pyModbusTCPは内部的にアドレス変換を行う
- **トリガー**: PLCアドレス（41025）で統一可能
- **完了フラグ**: Modbusアドレス（1025）を使用する必要がある

---

## 🔄 完全な通信シーケンス

### **タイムライン付きシーケンス図**

```
時刻   Dobot側                レジスタ状態                PC側
      (Client)              41025  1025              (Server)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

T0    [初期状態]              0      0               [待機中]
                              │      │
T1    SetHoldRegs             │      │
      (41025, 1) ──────────► [1]    [0] ◄────────── 監視中
                                     │
T2                                   │               トリガー検出
                                     │               ↓
                                     │               撮影処理開始
                                     │               (2秒間)
                                     │
T4                            [1]   [0]              ↓
                                    │               撮影完了
                                    │               ↓
                                    │               SetHoldRegs
T5    GetHoldRegs            [1]   [1] ◄────────── (1025, 1)
      (1025) ──────────────►       │
      → 1を検出                    │
                                    │
T6    SetHoldRegs                   │
      (41025, 0) ──────────► [0]   [1]
                              │     │
T7                            │     │               リセット検出
                              │     │               ↓
                              │     │               SetHoldRegs
T8    [待機状態]              [0]  [0] ◄────────── (1025, 0)
                              │     │
                              │     │               [待機状態]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 📋 レジスタ値の意味

### **撮影トリガー (41025)**

| 値 | 意味 | 誰が設定 | タイミング |
|----|------|---------|-----------|
| `0` | 待機状態 | Dobot | 初期状態、リセット後 |
| `1` | 撮影指令 | Dobot | 撮影開始時 |

### **完了フラグ (1025)**

| 値 | 意味 | 誰が設定 | タイミング |
|----|------|---------|-----------|
| `0` | 未完了 | PC | 初期状態、リセット後 |
| `1` | 完了 | PC | 撮影処理完了時 |

---

## 🔐 レジスタアクセスパターン

### **Dobot側のアクセスパターン**

```lua
-- 【書き込み専用】撮影トリガー
SetHoldRegs(id, 41025, 1, {1}, "U16")    -- トリガーON
SetHoldRegs(id, 41025, 1, {0}, "U16")    -- トリガーOFF

-- 【読み取り専用】完了フラグ
local done = GetHoldRegs(id, 1025, 1, "U16")
```

### **PC側のアクセスパターン**

```python
# 【読み取り専用】撮影トリガー
trigger = server.data_bank.get_holding_registers(41025, 1)

# 【書き込み専用】完了フラグ
server.data_bank.set_holding_registers(1025, [1])    # 完了ON
server.data_bank.set_holding_registers(1025, [0])    # 完了OFF
```

---

## ⚠️ よくある間違いとトラブルシューティング

### **❌ 間違い 1: 完了フラグのアドレスミス**

```lua
-- ❌ 間違い
local done = GetHoldRegs(id, 41026, 1, "U16")  -- 常に0が返る

-- ✅ 正しい
local done = GetHoldRegs(id, 1025, 1, "U16")   -- 正しく読み取れる
```

**原因:**
- PC側が`1025`に書き込んでいる
- `41026`は使用していない

---

### **❌ 間違い 2: トリガーのリセット忘れ**

```lua
-- ❌ 間違い（リセットなし）
SetHoldRegs(id, 41025, 1, {1}, "U16")
while true do
    local done = GetHoldRegs(id, 1025, 1, "U16")
    if done and done[1] == 1 then
        break
    end
end
-- ここでトリガーをリセットしていない！

-- ✅ 正しい
SetHoldRegs(id, 41025, 1, {1}, "U16")
while true do
    local done = GetHoldRegs(id, 1025, 1, "U16")
    if done and done[1] == 1 then
        break
    end
end
SetHoldRegs(id, 41025, 1, {0}, "U16")  -- 必ずリセット
```

**問題:**
- PC側がトリガーのリセット（41025 = 0）を待ち続ける
- タイムアウトエラーが発生

---

### **❌ 間違い 3: データ型の不一致**

```lua
-- ❌ 間違い
SetHoldRegs(id, 41025, 1, {1}, "S16")  -- 符号付き整数

-- ✅ 正しい
SetHoldRegs(id, 41025, 1, {1}, "U16")  -- 符号なし整数
```

**理由:**
- Modbusレジスタは16ビット符号なし整数が標準
- PC側も`U16`で扱っている

---

## 🧪 デバッグ用レジスタ確認コード

### **Dobot側: 全レジスタ状態確認**

```lua
function check_all_registers(id)
    local addrs = {0, 1, 1024, 1025, 1026, 41025, 41026}
    print("=== レジスタ状態 ===")
    for _, addr in ipairs(addrs) do
        local value = GetHoldRegs(id, addr, 1, "U16")
        if value then
            print(string.format("  %5d: %d", addr, value[1]))
        else
            print(string.format("  %5d: 読み取り失敗", addr))
        end
    end
    print("==================")
end

-- 使用例
check_all_registers(id)
```

### **PC側: 全レジスタ状態確認**

```python
def check_all_registers(server):
    addrs = [0, 1, 1024, 1025, 1026, 41025, 41026]
    print("=== レジスタ状態 ===")
    for addr in addrs:
        values = server.data_bank.get_holding_registers(addr, 1)
        if values:
            print(f"  {addr:5d}: {values[0]}")
        else:
            print(f"  {addr:5d}: 読み取り失敗")
    print("==================")

# 使用例
check_all_registers(server)
```

---

## 📈 レジスタ使用パターンの拡張例

### **複数カメラ対応**

```python
# レジスタ割り当て
ADDR_TRIGGER_CAM1 = 41025
ADDR_TRIGGER_CAM2 = 41027
ADDR_DONE_CAM1 = 1025
ADDR_DONE_CAM2 = 1027
```

### **エラーコード通知**

```python
# レジスタ割り当て
ADDR_TRIGGER = 41025
ADDR_DONE = 1025
ADDR_ERROR_CODE = 1029  # エラーコード (0=正常, 1=カメラエラー, 2=保存エラー)
```

---

## 📝 レジスタ設計のベストプラクティス

### ✅ **推奨事項**

1. **アドレスを文書化する**
   - README、コメントに必ず記載
   - アドレスマッピング表を作成

2. **定数を使用する**
   ```lua
   local ADDR_TRIGGER = 41025
   local ADDR_DONE = 1025
   SetHoldRegs(id, ADDR_TRIGGER, 1, {1}, "U16")
   ```

3. **初期化を明示的に行う**
   ```python
   server.data_bank.set_holding_registers(ADDR_TRIGGER, [0])
   server.data_bank.set_holding_registers(ADDR_DONE, [0])
   ```

4. **ハンドシェイクを完結させる**
   - トリガー送信 → 完了待機 → トリガーリセット → 完了リセット

---

このレジスタ設計により、シンプルで信頼性の高いDobot-PC間通信を実現しています。