import pygame
import random
import math
import sys

# --- 1. 初始化與視窗設定 ---
pygame.init()
WIDTH, HEIGHT = 640, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("寶可夢：經典序章整合版")
clock = pygame.time.Clock()

# 顏色定義
WHITE, BLACK, GRAY = (255, 255, 255), (0, 0, 0), (200, 200, 200)
HP_GREEN, HP_YELLOW, HP_RED = (0, 255, 0), (255, 255, 0), (255, 0, 0)

try:
    FONT = pygame.font.SysFont("microsoftjhenghei", 20)
    MSG_FONT = pygame.font.SysFont("microsoftjhenghei", 24)
except:
    FONT = pygame.font.SysFont(None, 24)
    MSG_FONT = pygame.font.SysFont(None, 28)

# --- 2. 遊戲數據 ---
PKMN_DATA = {
    "小火龍": {"base": [39, 52, 43, 65, 50], "moves": ["抓", "叫聲"], "rival": "傑尼龜"},
    "妙蛙種子": {"base": [45, 49, 49, 45, 65], "moves": ["撞擊", "叫聲"], "rival": "小火龍"},
    "傑尼龜": {"base": [44, 48, 65, 43, 50], "moves": ["撞擊", "搖尾巴"], "rival": "妙蛙種子"}
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
        self.iv = 15
        self.max_hp = math.floor((data["base"][0]+self.iv)*2*5/100)+20
        self.hp = self.max_hp
        self.base_atk = math.floor((data["base"][1]+self.iv)*2*5/100)+5
        self.base_def = math.floor((data["base"][2]+self.iv)*2*5/100)+5
        self.spd = math.floor((data["base"][3]+self.iv)*2*5/100)+5
        self.moves = {m: MOVES_DB[m] for m in data["moves"]}
        self.atk_stage = 0
        self.def_stage = 0
        
        # 尺寸統一化：玩家 200x200, 勁敵 160x160
        self.is_player = is_player
        size = (200, 200) if is_player else (160, 160)
        
        try:
            suffix = "back" if is_player else "front"
            img = pygame.image.load(f"{name}_{suffix}.png").convert_alpha()
            self.image = pygame.transform.scale(img, size)
        except:
            self.image = pygame.Surface(size)
            color = (255, 100, 100) if name == "小火龍" else (100, 255, 100) if name == "妙蛙種子" else (100, 100, 255)
            self.image.fill(color)

    def get_atk(self): return self.base_atk * (2/(2+abs(self.atk_stage)) if self.atk_stage < 0 else (2+self.atk_stage)/2)
    def get_def(self): return self.base_def * (2/(2+abs(self.def_stage)) if self.def_stage < 0 else (2+self.def_stage)/2)

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
        
        # 預載入選擇畫面預覽圖
        self.previews = {}
        for name in PKMN_DATA.keys():
            try:
                img = pygame.image.load(f"{name}_front.png").convert_alpha()
                self.previews[name] = pygame.transform.scale(img, (140, 140))
            except:
                surf = pygame.Surface((140, 140))
                surf.fill(GRAY)
                self.previews[name] = surf

    def handle_click(self, pos):
        if self.state == "STORY_OAK":
            self.state = "SELECT"
            self.msg = "請點擊下方的寶可夢圖示進行選擇"
        elif self.state == "SELECT":
            for i, name in enumerate(PKMN_DATA.keys()):
                rect = pygame.Rect(60 + i*190, 130, 160, 160)
                if rect.collidepoint(pos):
                    self.player_pkmn = Pokemon(name, is_player=True)
                    self.rival_pkmn = Pokemon(PKMN_DATA[name]["rival"], is_player=False)
                    self.state = "STORY_RIVAL"
                    self.msg = f"小茂：『既然我們都是訓練家了，那就來場對戰吧！』"
                    break
        elif self.state == "STORY_RIVAL":
            self.state = "BATTLE"
            self.is_waiting_input = True
            self.msg = "你要做什麼？"
        elif self.state == "BATTLE":
            if self.is_waiting_input:
                for i, m_name in enumerate(self.player_pkmn.moves.keys()):
                    btn_rect = pygame.Rect(350 + (i%2)*140, 370 + (i//2)*50, 120, 40)
                    if btn_rect.collidepoint(pos):
                        self.start_turn(m_name)
                        break
            else:
                self.next_step()

    def start_turn(self, p_move):
        self.is_waiting_input = False
        r_move = random.choice(list(self.rival_pkmn.moves.keys()))
        order = [(self.player_pkmn, self.rival_pkmn, p_move, "玩家"), 
                 (self.rival_pkmn, self.player_pkmn, r_move, "小茂")]
        if self.rival_pkmn.spd > self.player_pkmn.spd: order.reverse()

        for atk, dfd, m_name, side in order:
            if atk.hp <= 0: continue
            self.msg_queue.append({"t": f"{side}的 {atk.name} 使用了 {m_name}！"})
            move = atk.moves[m_name]
            if move["type"] == "damage":
                crit, dmg = self.calc_dmg(atk, dfd, move["power"])
                def act(d=dfd, am=dmg): 
                    d.hp = max(0, d.hp-am)
                    self.flash_target = d
                    self.flash_timer = 20
                if crit: self.msg_queue.append({"t": "擊中要害！", "a": act})
                else: self.msg_queue.append({"t": "", "a": act})
            else:
                def s_act(d=dfd, m=m_name):
                    if m == "叫聲": d.atk_stage -= 1
                    else: d.def_stage -= 1
                self.msg_queue.append({"t": f"{dfd.name} 的能力下降了！", "a": s_act})
            def check(d=dfd):
                if d.hp <= 0: self.msg_queue.append({"t": f"{d.name} 倒下了！"})
            self.msg_queue.append({"t": "", "a": check})

    def calc_dmg(self, atk, dfd, pwr):
        crit = random.random() < 0.1
        a = atk.base_atk if crit else atk.get_atk()
        d = dfd.base_def if crit else dfd.get_def()
        dmg = math.floor((((2*5/5+2)*pwr*a/d)/50+2) * (random.randint(217, 255)/255) * (2 if crit else 1))
        return crit, dmg

    def next_step(self):
        if self.msg_queue:
            step = self.msg_queue.pop(0)
            if step["t"]: self.msg = step["t"]
            if "a" in step: step["a"]()
        else:
            if self.player_pkmn.hp > 0 and self.rival_pkmn.hp > 0:
                self.is_waiting_input = True
                self.msg = "你要做什麼？"
            else:
                self.msg = "戰鬥結束！點擊退出。"

    def draw(self, surf):
        surf.fill(WHITE)
        if self.state == "SELECT":
            for i, name in enumerate(PKMN_DATA.keys()):
                x_pos = 60 + i * 190
                rect = pygame.Rect(x_pos, 130, 160, 160)
                pygame.draw.rect(surf, GRAY, rect)
                pygame.draw.rect(surf, BLACK, rect, 2)
                surf.blit(self.previews[name], (x_pos + 10, 140))
                surf.blit(FONT.render(name, True, BLACK), (x_pos + 45, 300))
                
        elif self.state in ["STORY_RIVAL", "BATTLE"]:
            if not (self.flash_target == self.rival_pkmn and self.flash_timer > 0 and (self.flash_timer // 4) % 2 == 0):
                surf.blit(self.rival_pkmn.image, (420, 40))
            if not (self.flash_target == self.player_pkmn and self.flash_timer > 0 and (self.flash_timer // 4) % 2 == 0):
                surf.blit(self.player_pkmn.image, (60, 180))
            
            if self.state == "BATTLE":
                self.draw_hp(surf, self.rival_pkmn, 50, 50, False)
                self.draw_hp(surf, self.player_pkmn, 380, 240, True)

        pygame.draw.rect(surf, BLACK, (0, 350, 640, 130))
        pygame.draw.rect(surf, WHITE, (5, 355, 630, 120), 3)
        surf.blit(MSG_FONT.render(self.msg, True, WHITE), (30, 385))
        
        if self.state == "BATTLE" and self.is_waiting_input:
            for i, m_name in enumerate(self.player_pkmn.moves.keys()):
                x, y = 350 + (i%2)*140, 370 + (i//2)*50
                pygame.draw.rect(surf, WHITE, (x, y, 120, 40), 2)
                surf.blit(FONT.render(m_name, True, WHITE), (x+10, y+8))

    def draw_hp(self, surf, p, x, y, is_p):
        hp_ratio = p.hp / p.max_hp
        pygame.draw.rect(surf, BLACK, (x, y, 210, 75), 2)
        surf.blit(FONT.render(f"{p.name} Lv5", True, BLACK), (x + 10, y + 5))
        pygame.draw.rect(surf, (50, 50, 50), (x + 10, y + 35, 150, 12))
        color = HP_GREEN if hp_ratio > 0.5 else HP_YELLOW if hp_ratio > 0.2 else HP_RED
        pygame.draw.rect(surf, color, (x + 10, y + 35, 150 * hp_ratio, 12))
        if is_p:
            surf.blit(FONT.render(f"HP: {p.hp}/{p.max_hp}", True, BLACK), (x + 85, y + 50))

# --- 4. 主迴圈 ---
mgr = GameManager()
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: pygame.quit(); sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            mgr.handle_click(event.pos)
    
    if mgr.flash_timer > 0: mgr.flash_timer -= 1
    else: mgr.flash_target = None
    
    mgr.draw(screen)
    pygame.display.flip()
    clock.tick(60)