import pygame
import random
import sys
import math

# ============================
# CONFIGURAÇÕES INICIAIS
# ============================
pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()
clock = pygame.time.Clock()

CELL = HEIGHT // 6 
BOARD_SIZE = CELL * 3
OFFSET_X = (WIDTH - BOARD_SIZE) // 2
OFFSET_Y = 120 

board = [" "] * 9
scores = {"X": 0, "O": 0, "E": 0}
modo_demo = False
confianca, confianca_alvo = 0.5, 0.5
tempo_proxima_jogada = 0
delay_demo = 500 # Aumentado para garantir estabilidade total

texto_vitoria = ""
timer_vitoria = 0 

UI_PANEL_Y = OFFSET_Y + BOARD_SIZE + 30
BOTAO_X = (WIDTH // 2) - 120
botao_demo = pygame.Rect(BOTAO_X, UI_PANEL_Y + 110, 240, 50)
botao_reset = pygame.Rect(BOTAO_X, UI_PANEL_Y + 170, 240, 50)
memo = {}
# ============================
# LÓGICA DA IA (OTIMIZADA)
# ============================
def vencedor(b):
    for a, b_idx, c in [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]:
        if b[a] != " " and b[a] == b[b_idx] == b[c]: return b[a]
    return "empate" if " " not in b else None



def minimax(b, depth, is_max, alpha, beta):
    key = "".join(b) + str(is_max) + str(depth)

    if key in memo:
        return memo[key]

    res = vencedor(b)
    if res == "O":
        return 1
    if res == "X":
        return -1
    if res == "empate":
        return 0

    

    moves = [i for i, v in enumerate(b) if v == " "]

    if is_max:
        best = -2
        for i in moves:
            b[i] = "O"
            val = minimax(b, depth + 1, False, alpha, beta)
            b[i] = " "

            best = max(best, val)
            alpha = max(alpha, best)

            # 🔥 PODA
            if beta <= alpha:
                break
    else:
        best = 2
        for i in moves:
            b[i] = "X"
            val = minimax(b, depth + 1, True, alpha, beta)
            b[i] = " "

            best = min(best, val)
            beta = min(beta, best)

            # 🔥 PODA
            if beta <= alpha:
                break

    memo[key] = best
    return best

def calcular_confianca():
    global confianca_alvo
    # Só calcula se houver peças no tabuleiro
    if board.count(" ") > 7:
        confianca_alvo = 0.5
        return
    
    val = minimax(board[:], 0, True, -999, 999)
    if val > 0: confianca_alvo = random.uniform(0.88, 0.99)
    elif val < 0: confianca_alvo = random.uniform(0.01, 0.12)
    else: confianca_alvo = 0.5 + (random.uniform(-0.1, 0.1))

def melhor_jogada(p_atual):
    moves = [i for i, v in enumerate(board) if v == " "]
    if not moves: return None
    global memo
    memo = {}
    melhores = []
    if p_atual == "O":
        val_alvo = -2
        for m in moves:
            board[m] = "O"; res = minimax(board, 0, False, -999, 999); board[m] = " "
            if res > val_alvo: val_alvo = res; melhores = [m]
            elif res == val_alvo: melhores.append(m)
    else:
        val_alvo = 2
        for m in moves:
            board[m] = "X"; res = minimax(board, 0, True, -999, 999); board[m] = " "
            if res < val_alvo: val_alvo = res; melhores = [m]
            elif res == val_alvo: melhores.append(m)
    
    return random.choice(melhores) if melhores else None

# ============================
# INTERFACE (CORES VIVAS)
# ============================
drops = [[random.randint(0, WIDTH), random.randint(0, HEIGHT), random.randint(10, 30)] for _ in range(40)]

def draw_ui():
    global confianca, timer_vitoria
    screen.fill((5, 12, 5)) # Fundo verde muito escuro
    
    for d in drops:
        pygame.draw.line(screen, (0, 255, 60), (d[0], d[1]), (d[0], d[1] + d[2]), 2)
        d[1] = (d[1] + d[2]) % HEIGHT
        
    # Texto de Vitória no Topo
    if timer_vitoria > 0:
        timer_vitoria -= 1
        cor = (int(127+127*math.sin(timer_vitoria*0.1)), 255, 100)
        img = pygame.font.SysFont("Consolas", 95, bold=True).render(texto_vitoria, True, cor)
        screen.blit(img, img.get_rect(center=(WIDTH//2, 60)))

    # Tabuleiro Ultra-Neon
    for i in range(1, 3):
        pygame.draw.line(screen, (0, 255, 255), (OFFSET_X, OFFSET_Y + i*CELL), (OFFSET_X + BOARD_SIZE, OFFSET_Y + i*CELL), 9)
        pygame.draw.line(screen, (0, 255, 255), (OFFSET_X + i*CELL, OFFSET_Y), (OFFSET_X + i*CELL, OFFSET_Y + BOARD_SIZE), 9)
    
    for i, v in enumerate(board):
        x, y = OFFSET_X + (i % 3) * CELL, OFFSET_Y + (i // 3) * CELL
        if v == "X":
            pygame.draw.line(screen, (255, 0, 110), (x+40, y+40), (x+CELL-40, y+CELL-40), 16)
            pygame.draw.line(screen, (255, 0, 110), (x+CELL-40, y+40), (x+40, y+CELL-40), 16)
        elif v == "O":
            pygame.draw.circle(screen, (0, 255, 150), (x+CELL//2, y+CELL//2), CELL//2-40, 16)

    # Painel Inferior
    f_ui = pygame.font.SysFont("Consolas", 35, bold=True)
    txt_s = f_ui.render(f"X:{scores['X']} | O:{scores['O']} | E:{scores['E']}", True, (255, 255, 255))
    screen.blit(txt_s, txt_s.get_rect(center=(WIDTH//2, UI_PANEL_Y)))
    
    # Barra de Confiança
    confianca += (confianca_alvo - confianca) * 0.05
    c_r = int(max(0, min(255, (1 - confianca) * 510)))
    c_g = int(max(0, min(255, confianca * 510)))
    
    pygame.draw.rect(screen, (20, 40, 20), (OFFSET_X, UI_PANEL_Y + 45, BOARD_SIZE, 55), border_radius=15)
    pygame.draw.rect(screen, (c_r, c_g, 150), (OFFSET_X, UI_PANEL_Y + 45, BOARD_SIZE * confianca, 55), border_radius=15)
    
    pct_img = pygame.font.SysFont("Consolas", 38, bold=True).render(f"{int(confianca*100)}%", True, (255, 255, 255))
    screen.blit(pct_img, pct_img.get_rect(center=(WIDTH//2, UI_PANEL_Y + 72)))

    for b, t, c in [(botao_demo, f"DEMO: {'ON' if modo_demo else 'OFF'}", (0, 200, 255) if modo_demo else (180, 180, 180)),
                    (botao_reset, "LIMPAR TUDO", (255, 50, 50))]:
        pygame.draw.rect(screen, c, b, 5, border_radius=15)
        img = pygame.font.SysFont("Consolas", 26, bold=True).render(t, True, c)
        screen.blit(img, img.get_rect(center=b.center))

# ============================
# LOOP PRINCIPAL
# ============================
while True:
    draw_ui()
    agora = pygame.time.get_ticks()

    # 1. EVENTOS (Sem bloqueio)
    for event in pygame.event.get():
        if event.type == pygame.QUIT: pygame.quit(); sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if botao_demo.collidepoint(event.pos): 
                modo_demo = not modo_demo
                board = [" "] * 9; timer_vitoria = 0; confianca_alvo = 0.5
            elif botao_reset.collidepoint(event.pos): 
                board = [" "] * 9; scores = {"X":0,"O":0,"E":0}; timer_vitoria = 0; confianca_alvo = 0.5
            elif not modo_demo:
                mx, my = event.pos
                if OFFSET_X < mx < OFFSET_X + BOARD_SIZE and OFFSET_Y < my < OFFSET_Y + BOARD_SIZE:
                    idx = int((mx - OFFSET_X) // CELL + ((my - OFFSET_Y) // CELL) * 3)
                    if board[idx] == " ":
                        board[idx] = "X"
                        res = vencedor(board)
                        if res:
                            texto_vitoria = "VENCEU!" if res != "empate" else "EMPATE!"
                            scores[res[0].upper() if res != "empate" else "E"] += 1
                            timer_vitoria = 90; board = [" "] * 9; confianca_alvo = 0.5
                        else:
                            m = melhor_jogada("O")
                            if m is not None: board[m] = "O"
                            calcular_confianca()
                            res = vencedor(board)
                            if res:
                                texto_vitoria = "IA VENCEU!" if res != "empate" else "EMPATE!"
                                scores[res[0].upper() if res != "empate" else "E"] += 1
                                timer_vitoria = 90; board = [" "] * 9; confianca_alvo = 0.5

    # 2. LÓGICA DEMO (Executada apenas quando o cronómetro permite)
    if modo_demo and agora > tempo_proxima_jogada:
        res = vencedor(board)
        if res:
            texto_vitoria = f"{res.upper()} GANHOU!" if res != "empate" else "EMPATE!"
            scores[res[0].upper() if res != "empate" else "E"] += 1
            timer_vitoria = 90; board = [" "] * 9; confianca_alvo = 0.5
        else:
            turno = "X" if board.count("X") <= board.count("O") else "O"
            m = melhor_jogada(turno)
            if m is not None: board[m] = turno
            calcular_confianca()
        tempo_proxima_jogada = agora + delay_demo

    pygame.display.update()
    clock.tick(60)
