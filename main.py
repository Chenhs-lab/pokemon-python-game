# pygame-exe
import pygame
import random
import math
import sys
import asyncio

# --- 1. 初始化 ---
pygame.init()
WIDTH, HEIGHT = 640, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pokemon Web Final")
clock = pygame.time.Clock()

# 顏色定義
WHITE, BLACK, GRAY = (255, 255, 255), (0, 0, 0), (200, 200, 200)
HP_GREEN, HP_YELLOW, HP_RED = (0, 255, 0), (255, 255, 0), (255, 0, 0)

# --- 修正：確保中文字體在網頁版顯示 ---
def get_font(size):
    # Pygbag 環境下 sans-serif 對中文支援度最高
    return pygame.font.SysFont("sans-serif, Arial, Microsoft JhengHei", size)

# --- 2. 遊戲數據 ---
PKMN_DATA = {
    "小火龍": {"base": [39, 52, 43, 65, 50], "moves": ["抓", "叫聲"], "rival": "傑尼龜", "color": (255, 100, 100)},
    "妙蛙種子": {"base": [45, 49, 49, 45, 65], "moves": ["撞擊", "叫聲"], "rival": "小火龍", "color": (100, 255, 100)},
    "傑尼龜": {"base": [44, 48, 65, 43, 50], "moves": ["撞擊", "搖尾巴"], "rival": "妙蛙種子", "color": (100, 100, 255)}
}
MOVES_DB = {
    "抓": {"type": "damage", "power": 40},
    "撞擊": {"type": "damage", "power": 35},
    "叫聲": {"type": "status"},
    "搖尾巴": {"type": "status"}
}

# --- 3. 核心類別 ---
class Pokemon:
    def __init__(self, name, is_player=True):
        data = PKMN_DATA[name]
        self.name = name
        self.level = 5
        self.max_hp = 25
        self.hp = 25
        self.moves = {m: MOVES_DB[m] for m in data["moves"]}
        self.is_player = is_player
        size = (200, 200) if is_player else (160, 160)
        
        # 嘗試載入圖片，失敗則畫圓
        suffix = "back" if is_player else "front"
        try:
            img = pygame.image.load(f"{name}_{suffix}.png").convert_alpha()
            self.image = pygame.transform.scale(img, size)
        except:
            self.image = pygame.Surface(size, pygame.SRCALPHA)
            pygame.draw.circle(self.image, data["color"], (size[0]//2, size[1]//2), size[0]//2 - 10)

class GameManager:
    def __init__(self):
        self.state = "SELECT"
        self.player_pkmn = None
        self.rival_pkmn = None
        self.msg = "請選擇你的夥伴..."
        self.msg_queue = []
        self.is_waiting_input = False
        self.flash_target = None
        self.flash_timer = 0
        self.previews = {}
        for name in PKMN_DATA.keys():
            try:
                img = pygame.image.load(f"{name}_front.png").convert_alpha()
                self.previews[name] = pygame.transform.scale(img, (140, 140))
            except:
                surf = pygame.Surface((140, 140)); surf.fill(GRAY)
                pygame.draw.circle(surf, PKMN_DATA[name]["color"], (70, 70), 50)
                self.previews[name] = surf

    def handle_click(self, pos):
        if self.state == "SELECT":
            for i, name in enumerate(PKMN_DATA.keys()):
                if pygame.Rect(60 + i * 190, 130, 160, 160).collidepoint(pos):
                    self.player_pkmn = Pokemon(name, is_player=True)
                    self.rival_pkmn = Pokemon(PKMN_DATA[name]["rival"], is_player=False)
                    self.state = "BATTLE"; self.is_waiting_input = True; self.msg = "你要做什麼？"
                    break
        elif self.state == "BATTLE":
            if self.is_waiting_input:
                for i, m_name in enumerate(self.player_pkmn.moves.keys()):
                    if pygame.Rect(350 + (i%2)*140, 370 + (i//2)*50, 120, 40).collidepoint(pos):
                        self.start_turn(m_name); break
            else: self.next_step()

    def start_turn(self, p_move):
        self.is_waiting_input = False
        r_move = random.choice(list(self.rival_pkmn.moves.keys()))
        order = [(self.player_pkmn, self.rival_pkmn, p_move, "玩家"), (self.rival_pkmn, self.player_pkmn, r_move, "小茂")]
        for atk, dfd, m_name, side in order:
            if atk.hp <= 0: continue
            self.msg_queue.append({"t": f"{side}的 {atk.name} 使用了 {m_name}！"})
            if MOVES_DB[m_name]["type"] == "damage":
                def act(df=dfd): df.hp = max(0, df.hp-5); self.flash_target = df; self.flash_timer = 15
                self.msg_queue.append({"t": "", "a": act})
            else:
                self.msg_queue.append({"t": f"{dfd.name}的能力下降了！"})
            def check(df=dfd):
                if df.hp <= 0: self.msg_queue.append({"t": f"{df.name} 倒下了！"})
            self.msg_queue.append({"t": "", "a": check})

    def next_step(self):
        if self.msg_queue:
            step = self.msg_queue.pop(0)
            if step["t"]: self.msg = step["t"]
            if "a" in step: step["a"]()
        else:
            if self.player_pkmn.hp > 0 and self.rival_pkmn.hp > 0:
                self.is_waiting_input = True; self.msg = "你要做什麼？"
            else: self.state = "END"; self.msg = "戰鬥結束！"

    def draw(self, surf):
        surf.fill((240, 248, 255))
        f_small, f_mid = get_font(20), get_font(24)
        if self.state == "SELECT":
            for i, name in enumerate(PKMN_DATA.keys()):
                x = 60 + i * 190; rect = pygame.Rect(x, 130, 160, 160)
                pygame.draw.rect(surf, GRAY, rect); pygame.draw.rect(surf, BLACK, rect, 2)
                surf.blit(self.previews[name], (x + 10, 140))
                surf.blit(f_small.render(name, True, BLACK), (x + 45, 300))
        elif self.state in ["BATTLE", "END"]:
            if not (self.flash_target == self.rival_pkmn and self.flash_timer > 0 and (self.flash_timer // 3) % 2 == 0):
                surf.blit(self.rival_pkmn.image, (420, 10))
            if not (self.flash_target == self.player_pkmn and self.flash_timer > 0 and (self.flash_timer // 3) % 2 == 0):
                surf.blit(self.player_pkmn.image, (60, 160))
            self.draw_hp(surf, self.rival_pkmn, 50, 50, False, f_small)
            self.draw_hp(surf, self.player_pkmn, 380, 260, True, f_small)
        
        pygame.draw.rect(surf, BLACK, (0, 350, 640, 130))
        pygame.draw.rect(surf, WHITE, (5, 355, 630, 120), 3)
        surf.blit(f_mid.render(self.msg, True, WHITE), (30, 385))
        if self.state == "BATTLE" and self.is_waiting_input:
            for i, m_name in enumerate(self.player_pkmn.moves.keys()):
                x, y = 350 + (i%2)*140, 370 + (i//2)*50
                pygame.draw.rect(surf, WHITE, (x, y, 120, 40), 2)
                surf.blit(f_small.render(m_name, True, WHITE), (x+10, y+8))

    def draw_hp(self, surf, p, x, y, is_p, font
