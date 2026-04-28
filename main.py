import pygame
import random
import math
import sys
import os
import asyncio  # 網頁版必備

# --- 1. 初始化與視窗設定 ---
pygame.init()
WIDTH, HEIGHT = 640, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("寶可夢小遊戲：網頁版")
clock = pygame.time.Clock()

# 顏色定義
WHITE, BLACK, GRAY = (255, 255, 255), (0, 0, 0), (200, 200, 200)
HP_GREEN, HP_YELLOW, HP_RED = (0, 255, 0), (255, 255, 0), (255, 0, 0)
BG_COLOR = (240, 248, 255)
GRASS_PAD = (100, 200, 100)
GRASS_BORDER = (60, 140, 60)

# --- 修正：解決中文方塊字 ---
def get_font(size):
    # Pygbag 對 sans-serif 的中文支援度最好
    return pygame.font.SysFont("sans-serif, Arial, Microsoft JhengHei", size)

# --- 2. 遊戲數據 ---
PKMN_DATA = {
    "小火龍": {"moves": ["抓", "叫聲"], "rival": "傑尼龜"},
    "妙蛙種子": {"moves": ["撞擊", "叫聲"], "rival": "小火龍"},
    "傑尼龜": {"moves": ["撞擊", "搖尾巴"], "rival": "妙蛙種子"}
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
        self.name = name
        self.max_hp = 25
        self.hp = 25
        self.moves = {m: MOVES_DB[m] for m in PKMN_DATA[name]["moves"]}
        self.is_player = is_player
        size = (200, 200) if is_player else (160, 160)
        
        # --- 修正：最單純的圖片載入 ---
        suffix = "back" if is_player else "front"
        filename = f"{name}_{suffix}.png"
        try:
            # 異步載入可能需要一點時間，但不要加路徑，檔名要完全一致
            img = pygame.image.load(filename).convert_alpha()
            self.image = pygame.transform.scale(img, size)
        except:
            # 色塊後備，確保不當機
            self.image = pygame.Surface(size, pygame.SRCALPHA)
            color = (255, 50, 50) if name == "小火龍" else (50, 255, 50) if name == "妙蛙種子" else (50, 50, 255)
            pygame.draw.circle(self.image, color, (size[0]//2, size[1]//2), size[0]//2 - 10)

class GameManager:
    def __init__(self):
        self.state = "STORY_OAK"
        self.player_pkmn = None
        self.rival_pkmn = None
        self.msg = "大木博士：『來吧，選擇你的夥伴！』"
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
                self.previews[name] = surf

    def handle_click(self, pos):
        if self.state == "STORY_OAK":
            self.state = "SELECT"
            self.msg = "請選擇你的夥伴..."
        elif self.state == "SELECT":
            for i, name in enumerate(PKMN_DATA.keys()):
                if pygame.Rect(60 + i * 190, 130, 160, 160).collidepoint(pos):
                    self.player_pkmn = Pokemon(name, is_player=True)
                    self.rival_pkmn = Pokemon(PKMN_DATA[name]["rival"], is_player=False)
                    self.state = "STORY_RIVAL"
                    self.msg = f"小茂：『既然是訓練家，就來對戰吧！』"
                    break
        elif self.state == "STORY_RIVAL":
            self.state = "BATTLE"; self.is_waiting_input = True; self.msg = "你要做什麼？"
        elif self.state == "BATTLE":
            if self.is_waiting_input:
                for i, m_name in enumerate(self.player_pkmn.moves.keys()):
                    if pygame.Rect(350 + (i%2)*140, 370 + (i//2)*50, 120, 40).collidepoint(pos):
                        self.start_turn(m_name); break
            else: self.next_step()
        elif self.state == "POST_BATTLE":
            pygame.quit(); sys.exit()

    def start_turn(self, p_move):
        self.is_waiting_input = False
        r_move = random.choice(list(self.rival_pkmn.moves.keys()))
        order = [(self.player_pkmn, self.rival_pkmn, p_move, "玩家"), (self.rival_pkmn, self.player_pkmn, r_move, "小茂")]
        if random.random() > 0.5: order.reverse()
        for atk, dfd, m_name, side in order:
            if atk.hp <= 0: continue
            self.msg_queue.append({"t": f"{side}的 {atk.name} 使用了 {m_name}！"})
            if MOVES_DB[m_name]["type"] == "damage":
                def act(df=dfd): df.hp = max(0, df.hp-5); self.flash_target = df; self.flash_timer = 15
                self.msg_queue.append({"t": "", "a": act})
            else:
                self.msg_queue.append({"t": f"{dfd.name}的能力下降了！"})
            def check(df=dfd):
                if df.hp <= 0:
                    self.msg_queue.append({"t": f"{df.name} 倒下了！"})
                    if not df.is_player: self.msg_queue.append({"t": "小茂：『可惡，結果不應該是這樣的...』"})
            self.msg_queue.append({"t": "", "a": check})

    def next_step(self):
        if self.msg_queue:
            step = self.msg_queue.pop(0)
            if step["t"]: self.msg = step["t"]
            if "a" in step: step["a"]()
        else:
            if self.player_pkmn.hp > 0 and self.rival_pkmn.hp > 0:
                self.is_waiting_input = True; self.msg = "你要做什麼？"
            else: self.state = "POST_BATTLE"

    def draw(self, surf):
        surf.fill(BG_COLOR)
        f_small = get_font(20)
        f_mid = get_font(24)
        if self.state == "SELECT":
            for i, name in enumerate(PKMN_DATA.keys()):
                x = 60 + i * 190; rect = pygame.Rect(x, 130, 160, 160)
                pygame.draw.rect(surf, GRAY, rect); pygame.draw.rect(surf, BLACK, rect, 2)
                surf.blit(self.previews[name], (x + 10, 140))
                surf.blit(f_small.render(name, True, BLACK), (x + 45, 300))
        elif self.state in ["STORY_RIVAL", "BATTLE", "POST_BATTLE"]:
            pygame.draw.ellipse(surf, GRASS_PAD, (380, 140, 240, 70))
            pygame.draw.ellipse(surf, GRASS_BORDER, (380, 140, 240, 70), 3)
            pygame.draw.ellipse(surf, GRASS_PAD, (20, 310, 300, 90))
            pygame.draw.ellipse(surf, GRASS_BORDER, (20, 310, 300, 90), 3)
            if not (self.flash_target == self.rival_pkmn and self.flash_timer > 0 and (self.flash_timer // 3) % 2 == 0):
                surf.blit(self.rival_pkmn.image, (420, 10))
            if not (self.flash_target == self.player_pkmn and self.flash_timer > 0 and (self.flash_timer // 3) % 2 == 0):
                surf.blit(self.player_pkmn.image, (60, 160))
            if self.state in ["BATTLE", "POST_BATTLE"]:
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

    def draw_hp(self, surf, p, x, y, is_p, font):
        ratio = p.hp / p.max_hp
        pygame.draw.rect(surf, WHITE, (x, y, 210, 75))
        pygame.draw.rect(surf, BLACK, (x, y, 210, 75), 2)
        surf.blit(font.render(f"{p.name} Lv5", True, BLACK), (x+10, y+5))
        pygame.draw.rect(surf, (50, 50, 50), (x+10, y+35, 150, 12))
        color = HP_GREEN if ratio > 0.5 else HP_YELLOW if ratio > 0.2 else HP_RED
        pygame.draw.rect(surf, color, (x+10, y+35, 150 * ratio, 12))
        if is_p: surf.blit(font.render(f"HP: {p.hp}/{p.max_hp}", True, BLACK), (x+85, y+50))

# --- 4. 網頁版異步主迴圈 (核心變動) ---
async def main():
    # 確保遊戲剛開始時有緩衝時間載入圖片
    await asyncio.sleep(0.5) 
    mgr = GameManager()
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN: mgr.handle_click(event.pos)
        
        if mgr.flash_timer > 0: mgr.flash_timer -= 1
        else: mgr.flash_target = None
        
        mgr.draw(screen)
        pygame.display.flip()
        
        # 關鍵：將控制權交還給瀏覽器，防止死鎖
        await asyncio.sleep(0)
        clock.tick(60)

if __name__ == "__main__":
    asyncio.run(main())
