import pygame
import random
import sys
import asyncio

# --- 1. 初始化 ---
pygame.init()
WIDTH, HEIGHT = 640, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pokemon Game Web")
clock = pygame.time.Clock()

# --- 修正：更安全的字體載入 ---
def get_font(size):
    # 優先順序：網頁通用字體 -> 系統字體 -> 預設字體
    try:
        return pygame.font.SysFont("sans-serif, Arial", size)
    except:
        return pygame.font.Font(None, size)

# 顏色
WHITE, BLACK, GRAY = (255, 255, 255), (0, 0, 0), (200, 200, 200)
HP_GREEN = (0, 255, 0)

# --- 2. 遊戲數據 (將 Key 改為英文避免路徑解析出錯) ---
PKMN_DATA = {
    "Charmander": {"name": "小火龍", "moves": ["Scratch", "Growl"], "rival": "Squirtle"},
    "Bulbasaur": {"name": "妙蛙種子", "moves": ["Tackle", "Growl"], "rival": "Charmander"},
    "Squirtle": {"name": "傑尼龜", "moves": ["Tackle", "Tail Whip"], "rival": "Bulbasaur"}
}

# --- 3. 核心類別 ---
class Pokemon:
    def __init__(self, key, is_player=True):
        self.key = key
        self.display_name = PKMN_DATA[key]["name"]
        self.hp = 25
        self.max_hp = 25
        self.is_player = is_player
        
        # 圖片載入 (檔名請確認為 Charmander_front.png 等)
        suffix = "back" if is_player else "front"
        filename = f"{key}_{suffix}.png"
        try:
            img = pygame.image.load(filename).convert_alpha()
            self.image = pygame.transform.scale(img, (200, 200) if is_player else (160, 160))
        except:
            # 如果圖還是載不到，畫一個圓形，至少讓遊戲能玩
            self.image = pygame.Surface((160, 160), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (255, 0, 0), (80, 80), 70)

# --- 4. 主遊戲邏輯 (簡化版確保執行) ---
async def main():
    # 預載入：這是網頁版最重要的步驟
    await asyncio.sleep(0.5)
    
    # 簡單的選擇介面狀態
    selected_pkmn = "Charmander"
    player = Pokemon(selected_pkmn, True)
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                # 點擊畫面後改變訊息，測試互動是否正常
                print("Clicked!")

        # 繪圖
        screen.fill((240, 248, 255)) # 背景色
        
        # 顯示圖片
        screen.blit(player.image, (60, 160))
        
        # 顯示文字
        font = get_font(30)
        txt = font.render(f"Name: {player.display_name}", True, BLACK)
        screen.blit(txt, (20, 20))
        
        info = get_font(20)
        hint = info.render("Click screen to start", True, GRAY)
        screen.blit(hint, (200, 400))

        pygame.display.flip()
        await asyncio.sleep(0) # 必須存在
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    asyncio.run(main())
