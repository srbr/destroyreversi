import tkinter as tk
from tkinter import scrolledtext
import openai

BOARD_SIZE = 8
STONE_NONE = 0
STONE_BLACK = 1
STONE_WHITE = 2

apikey = ""
# apikey.txtからAPIキーを読み込む
with open("apikey.txt", "r") as f:
    apikey = f.read().strip()
openai_client = openai.OpenAI(api_key=apikey)

# +-----------------------------------------------------------
# |色定義
# +-----------------------------------------------------------
BG_COLOR = "#090"  # 背景色
COLOR_NONE = "#090"  # 石が無い時の色(背景色と同じにする)
COLOR_BLACK = "#000"  # 黒石の色
COLOR_WHITE = "#FFF"  # 白石の色
COLOR_BORDER = "#000"  # ボードの枠線の色

player_first = True  # プレイヤーが先手かどうか
turn_count = 1 # ターン数
player_cost = 0 # プレイヤーのコスト
cpu_cost = 0 # CPUのコスト
can_put_cells = [] # 置けるマスのリスト
destroy_cost = 3 # 除外に必要なコスト

def is_player_turn():
    global player_first, turn_count
    return ((turn_count % 2) == 1) == player_first

def count_player_stones():
    global board
    return sum(row.count(STONE_BLACK if player_first else STONE_WHITE) for row in board)

def count_cpu_stones():
    global board
    return sum(row.count(STONE_WHITE if player_first else STONE_BLACK) for row in board)

root = tk.Tk()
root.title("Destroy Reversi")
root.geometry("1024x768")

# +-----------------------------------------------------------
# |キャンバスオブジェクトの宣言
# +-----------------------------------------------------------
canvas = None
canvas_bg = 0
canvas_vertical_lines = [0 for _ in range(BOARD_SIZE + 1)]
canvas_horizontal_lines = [0 for _ in range(BOARD_SIZE + 1)]
canvas_stones = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

# +-----------------------------------------------------------
# |キャンバスオブジェクトの初期化
# +-----------------------------------------------------------
def init_canvas():
    global canvas, canvas_bg, canvas_vertical_lines, canvas_horizontal_lines, canvas_stones
    canvas_bg = canvas.create_rectangle(0, 0, 0, 0, fill=BG_COLOR, outline="")
    canvas_vertical_lines = [canvas.create_line(0, 0, 0, 0, fill=COLOR_BORDER) for _ in range(BOARD_SIZE + 1)]
    canvas_horizontal_lines = [canvas.create_line(0, 0, 0, 0, fill=COLOR_BORDER) for _ in range(BOARD_SIZE + 1)]
    canvas_stones = [[canvas.create_oval(0, 0, 0, 0, fill=COLOR_NONE, outline="") for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    update_canvas()

# +-----------------------------------------------------------
# |キャンバスオブジェクトの更新
# +-----------------------------------------------------------
def update_canvas():
    global canvas, canvas_bg, canvas_vertical_lines, canvas_horizontal_lines, canvas_stones
    w = canvas.winfo_width()
    h = canvas.winfo_height()
    min_size = min(w, h)

    # 中央揃えの為に左上の座標を計算
    left = (w - min_size) // 2
    top = (h - min_size) // 2

    canvas.coords(canvas_bg, left, top, left + min_size, top + min_size)
    for i in range(BOARD_SIZE + 1):
        x = left + i * (min_size - 1) // BOARD_SIZE
        canvas.coords(canvas_vertical_lines[i], x, top, x, top + min_size)
        y = top + i * (min_size - 1) // BOARD_SIZE
        canvas.coords(canvas_horizontal_lines[i], left, y, left + min_size, y)
    for iy in range(BOARD_SIZE):
        for ix in range(BOARD_SIZE):
            x = left + ix * min_size // BOARD_SIZE
            y = top + iy * min_size // BOARD_SIZE
            margin = min_size // BOARD_SIZE // 10
            canvas.coords(canvas_stones[iy][ix], x + margin, y + margin, x + min_size // BOARD_SIZE - margin, y + min_size // BOARD_SIZE - margin)
            if board[iy][ix] == STONE_BLACK:
                canvas.itemconfig(canvas_stones[iy][ix], fill=COLOR_BLACK)
            elif board[iy][ix] == STONE_WHITE:
                canvas.itemconfig(canvas_stones[iy][ix], fill=COLOR_WHITE)
            else:
                canvas.itemconfig(canvas_stones[iy][ix], fill=COLOR_NONE)

# +-----------------------------------------------------------
# |レイアウト
# +-----------------------------------------------------------
log_area = scrolledtext.ScrolledText(bg="cyan", bd=0, relief="flat", height=8, state="disabled")
log_area.pack(side="top", fill="x", padx=0, pady=0)
status_frame = tk.Frame(root, relief="flat", bd=0, bg="white", width=256)
status_frame.pack(side="right", fill="y", padx=0, pady=0)
status_frame.pack_propagate(False)
status_cpu = tk.Frame(status_frame, bg="white", bd=0, relief="flat")
status_cpu.pack(side="top", fill="both", expand=True, padx=0, pady=0)
status_cpu_label = tk.Label(status_cpu, text="CPU", bg="cyan", bd=0, relief="flat")
status_cpu_label.pack(fill="both", expand=True, padx=0, pady=0)
status_player = tk.Frame(status_frame, bg="white", bd=0, relief="flat")
status_player.pack(side="bottom", fill="both", expand=True, padx=0, pady=0)
status_player_label = tk.Label(status_player, text="Player", bg="white", bd=0, relief="flat")
status_player_label.pack(fill="both", expand=True, padx=0, pady=0)
canvas = tk.Canvas(root, bg="white", highlightthickness=0, bd=0)
canvas.pack(expand=True, fill="both", padx=0, pady=0)
canvas.bind("<Configure>", lambda _: update_canvas())

# ステータス表記の更新
def update_status():
    global player_first, turn_count, status_cpu_label, status_player_label, player_cost, cpu_cost
    cpu_stones = count_cpu_stones()
    player_stones = count_player_stones()
    player_turn_text = "あなたの番です" if is_player_turn() else ""
    cpu_turn_text = "思考中" if not is_player_turn() else ""
    status_cpu_label.config(text=f"CPU\n石数: {cpu_stones}\nコスト: {cpu_cost}\n{cpu_turn_text}")
    status_player_label.config(text=f"Player\n石数: {player_stones}\nコスト: {player_cost}\n{player_turn_text}")

# +-----------------------------------------------------------
# |ゲーム初期化
# +-----------------------------------------------------------
board = [[STONE_NONE] * BOARD_SIZE for _ in range(BOARD_SIZE)]
mid = BOARD_SIZE // 2
# 初期配置
board[mid - 1][mid - 1] = STONE_WHITE
board[mid - 1][mid] = STONE_BLACK
board[mid][mid - 1] = STONE_BLACK
board[mid][mid] = STONE_WHITE

if player_first:
    player_cost += 1
else:
    cpu_cost += 1

init_canvas()

# +-----------------------------------------------------------
# |置けるセルのリストアップ
# +-----------------------------------------------------------
def check_can_put_cells():
    global board, can_put_cells
    can_put_cells = []
    for y in range(BOARD_SIZE):
        for x in range(BOARD_SIZE):
            if board[y][x] == STONE_NONE:
                put_stone = STONE_BLACK if turn_count % 2 == 1 else STONE_WHITE
                reverse_stone = STONE_WHITE if turn_count % 2 == 1 else STONE_BLACK
                ways = [(-1, -1), (0, -1), (1, -1),
                        (-1, 0),           (1, 0),
                        (-1, 1),  (0, 1),  (1, 1)]
                for dx, dy in ways:
                    can_put = False
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE and board[ny][nx] == reverse_stone:
                        while 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
                            if board[ny][nx] == STONE_NONE:
                                break
                            elif board[ny][nx] == put_stone:
                                can_put_cells.append((x, y))
                                can_put = True
                                break
                            nx += dx
                            ny += dy
                    if can_put:
                        break
    #print(f"置けるマス: {can_put_cells}")

# +-----------------------------------------------------------
# |石を置く処理
# +-----------------------------------------------------------
def put_stone(x, y, color):
    #print(f"石を置く: ({x}, {y}) {color}")
    global board
    board[y][x] = color
    ways = [(-1, -1), (0, -1), (1, -1),
            (-1, 0),           (1, 0),
            (-1, 1),  (0, 1),  (1, 1)]
    for dx, dy in ways:
        nx, ny = x + dx, y + dy
        if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE and board[ny][nx] != color and board[ny][nx] != STONE_NONE:
            while 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
                if board[ny][nx] == STONE_NONE:
                    break
                elif board[ny][nx] == color:
                    while True:
                        nx -= dx
                        ny -= dy
                        if nx == x and ny == y:
                            break
                        board[ny][nx] = color
                    break
                nx += dx
                ny += dy

# キャンバスクリックイベント
def on_canvas_click(event):
    global turn_count, player_cost, cpu_cost, player_first, can_put_cells
    w = canvas.winfo_width()
    h = canvas.winfo_height()
    min_size = min(w, h)
    left = (w - min_size) // 2
    top = (h - min_size) // 2

    # クリックがボード外なら無視
    if not (left <= event.x < left + min_size and top <= event.y < top + min_size):
        return

    cell_size = min_size // BOARD_SIZE
    ix = (event.x - left) // cell_size
    iy = (event.y - top) // cell_size

    # 範囲外チェック
    if 0 <= ix < BOARD_SIZE and 0 <= iy < BOARD_SIZE:
        #print(f"クリックされたマス: ({ix}, {iy})")
        # ここでマスに対する処理を追加できます
        if is_player_turn():
            # 石を置く処理
            if (ix, iy) in can_put_cells:
                player_color = STONE_BLACK if player_first else STONE_WHITE
                put_stone(ix, iy, player_color)

                turn_count += 1
                check_can_put_cells()
                cpu_cost += 1
                update_canvas()
                update_status()
                # 1フレーム遅延してAI思考を実行
                root.after(1, ai_think)
            # 石を除外する処理
            elif player_cost >= destroy_cost and board[iy][ix] != STONE_NONE:
                # 除外処理を実行（ここでは単純に空きマスにする）
                board[iy][ix] = STONE_NONE
                # コストを消費
                player_cost -= destroy_cost
                turn_count += 1
                check_can_put_cells()
                cpu_cost += 1
                update_canvas()
                update_status()
                # 1フレーム遅延してAI思考を実行
                root.after(1, ai_think)


# +-----------------------------------------------------------
# |AIに送るプロンプトを生成
# +-----------------------------------------------------------
def generate_prompt():
    board_string = "'],\n  ['".join(["', '".join(["." if cell == STONE_NONE else "B" if cell == STONE_BLACK else "W" for cell in board[iy]]) for iy in range(BOARD_SIZE)])
    stone_name = "白番" if player_first else "黒番"
    stone_mark = "W" if player_first else "B"
    can_remove_cells = [(x, y) for x in range(BOARD_SIZE) for y in range(BOARD_SIZE) if board[y][x] != STONE_NONE]
    can_remove_text = f"あなたは除外することができます。\nあなたが除外できるマスは以下の通りです：\n{can_remove_cells}" if player_cost >= destroy_cost else "あなたは除外することができません。"
    return f"""
[Background]
あなたは戦略に優れたAIです。このゲームは、オセロに以下の特殊ルールを加えた変則ルールで行われます：

- 各プレイヤーは「コスト」を持ち、ゲーム開始時点でコストは0です。
- 各ターンの開始時にコストが1増加します。
- 自分の手番では次のいずれかの行動を選べます：
  1. 通常のオセロのルールに従って石を1つ置く（コスト消費なし）
  2. コストを3消費して、盤上の任意の石を1つ除外（除去）する（石の色は問わない）

あなたは現在「{stone_name}（{stone_mark}）」で、以下の盤面とコスト状況に基づいて、最善の行動（置く or 除外）を1つ選んでください。

[Objective]
次の一手として、最善の行動（通常の着手または除外）を1つ選び、その理由を説明してください。

[Input]
盤面は 8x8 の二次元配列で与えられます。各セルは以下のいずれかです：
- '.'：空きマス
- 'B'：黒石
- 'W'：白石

配列の添字 `(x, y)` の意味は次の通りです：
- `x`: 横方向の位置（0〜7） → 左から右（0=A, 1=B, ..., 7=H）
- `y`: 縦方向の位置（0〜7） → 上から下（0=1段目, ..., 7=8段目）

あなたは{stone_name}（'{stone_mark}'）です。次に置くべき最善の手を 1 手だけ `(x, y)` 形式で出力し、その理由を説明してください。
黒の現在のコスト: {player_cost if player_first else cpu_cost}
白の現在のコスト: {cpu_cost if player_first else player_cost}

盤面:
[
  ['{board_string}']
]

あなたが次に置けるマスは以下の通りです：
{can_put_cells}（例: (0, 0)）
{can_remove_text}

[Output Format]
以下の形式で出力してください：

最善行動: [Put (x, y) または Remove (x, y)]
理由: [簡潔な戦略的説明]
    """

# +-----------------------------------------------------------
# |AIの思考処理
# +-----------------------------------------------------------
def ai_think():
    global board, turn_count, player_first, cpu_cost, player_cost
    prompt = generate_prompt()
    #print(f"AIへのプロンプト: {prompt}")
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=150,
        n=1,
        stop=None
    )
    # 修正: ドット記法でアクセス
    message = response.choices[0].message.content
    print(f"AIの応答:\n{message}")
    # 最善手を抽出
    best_move = message.split("最善行動: ")[1].split("\n")[0].strip()
    # 着手の場合
    if best_move.startswith("Put"):
        best_move = best_move[4:].strip()
        x, y = map(int, best_move[1:-1].split(","))
        # AIの手を実行
        ai_color = STONE_WHITE if player_first else STONE_BLACK
        put_stone(x, y, ai_color)
    # 除外の場合
    elif best_move.startswith("Remove"):
        best_move = best_move[7:].strip()
        x, y = map(int, best_move[1:-1].split(","))
        if board[y][x] == STONE_NONE:
            print("無効な除外です。")
            return
        # 除外処理を実行（ここでは単純に空きマスにする）
        board[y][x] = STONE_NONE
        # コストを消費
        cpu_cost -= destroy_cost
    else:
        print("無効な応答形式です。")
        return
    global turn_count
    turn_count += 1
    check_can_put_cells()
    player_cost += 1
    update_canvas()
    update_status()

check_can_put_cells()
# キャンバスにクリックイベントをバインド
canvas.bind("<Button-1>", on_canvas_click)
update_status()

root.mainloop()