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
delay_demo = 300 # Um pouco mais lento para estabilidade

texto_vitoria = ""
timer_vitoria = 0 

UI_PANEL_Y = OFFSET_Y + BOARD_SIZE + 30
BOTAO_X = (WIDTH // 2) - 120
botao_demo = pygame.Rect(BOTAO_X, UI_PANEL_Y + 110, 240, 50)
botao_reset = pygame.Rect(BOTAO_X, UI_PANEL_Y + 170, 240, 50)

# ============================
# LÓGICA DA IA (ULTRA OTIMIZADA)
# ============================
def vencedor(b):
    for a, b_idx, c in [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]:
        if b[a] != " " and b[a] == b[b_idx] == b[c]: return b[a]
    return "empate" if " " not in b else None

def minimax(b, depth, is_max):
    res = vencedor(b)
    if res == "O": return 1
    if res == "X": return -1
    if res == "empate": return 0
    if depth > 6: return 0 # Limite de profundidade para não travar
    
    moves = [i for i, v in enumerate(b) if v == " "]
    if is_max:
        best = -2
        for i in moves:
            b[i] = "O"; v = minimax(b, depth + 1, False); b[i] = " "
            if v > best: best = v
        return best
    else:
        best = 2
        for i in moves:
            b[i] = "X"; v = minimax(b, depth + 1, True); b[i] = " "
            if v < best: best = v
        return best

def melhor_jogada(p_atual):
    moves = [i for i, v in enumerate(board) if v == " "]
    if not moves: return None
    
    # Se tabuleiro vazio, joga no centro/canto aleatório (rápido)
    if len(moves) == 9: return random.choice([0, 2, 4, 6, 8])

    melhores = []
    if p_atual == "O":
        val_alvo = -2
        for m in moves:
            board[m] = "O"; res = minimax(board, 0, False); board[m] = " "
            if res > val_alvo: val_alvo = res; melhores = [m]
            elif res == val_alvo: melhores.append(m)
    else:
        val_alvo = 2
        for m in moves:
            board[m] = "X"; res = minimax(board, 0, True); board[m] = " "
            if res < val_alvo: val_alvo = res; melhores = [m]
            elif res == val_alvo: melhores.append(m)
    
    # Atualiza confiança baseado no resultado do minimax
    global confianca_alvo
    if val_alvo > 0: confianca_alvo = 0.9
    elif val_alvo < 0: confianca_alvo = 0.1
    else: confianca_alvo = 0.5
    
    return random.choice(melhores) if melhores else None

# ============================
# INTERFACE
# ============================
drops = [[random.randint(0, WIDTH), random.randint(0, HEIGHT), random.randint(10, 30)] for _ in range(50)]

def draw_ui():
    global confianca, timer_vitoria
    screen.fill((2, 8, 2))
    
    for d in drops:
        pygame.draw.line(screen, (0, 255, 50), (d[0], d[1]), (d[0], d[1] + d[2]), 2)
        d[1] = (d[1] + d[2]) % HEIGHT
        
    # Texto de Vitória (No Topo, não bloqueia clique)
    if timer_vitoria > 0:
        timer_vitoria -= 1
        cor = (int(127+127*math.sin(timer_vitoria*0.1)), 255, 180)
        img = pygame.font.SysFont("Consolas", 85, bold=True).render(texto_vitoria, True, cor)
        screen.blit(img, img.get_rect(center=(WIDTH//2, 60)))

    # Tabuleiro
    for i in range(1, 3):
        pygame.draw.line(screen, (0, 255, 200), (OFFSET_X, OFFSET_Y + i*CELL), (OFFSET_X + BOARD_SIZE, OFFSET_Y + i*CELL), 8)
        pygame.draw.line(screen, (0, 255, 200), (OFFSET_X + i*CELL, OFFSET_Y), (OFFSET_X + i*CELL, OFFSET_Y + BOARD_SIZE), 8)
    
    for i, v in enumerate(board):
        x, y = OFFSET_X + (i % 3) * CELL, OFFSET_Y + (i // 3) * CELL
        if v == "X":
            pygame.draw.line(screen, (255, 20, 120), (x+40, y+40), (x+CELL-40, y+CELL-40), 15)
            pygame.draw.line(screen, (255, 20, 120), (x+CELL-40, y+40), (x+40, y+CELL-40), 15)
        elif v == "O":
            pygame.draw.circle(screen, (0, 230, 255), (x+CELL//2, y+CELL//2), CELL//2-40, 15)

    # Painel Barra e Placar
    f_ui = pygame.font.SysFont("Consolas", 35, bold=True)
    txt_s = f_ui.render(f"X:{scores['X']} | O:{scores['O']} | E:{scores['E']}", True, (255, 255, 255))
    screen.blit(txt_s, txt_s.get_rect(center=(WIDTH//2, UI_PANEL_Y)))
    
    confianca += (confianca_alvo - confianca) * 0.1
    c_r, c_g = int((1-confianca)*255), int(confianca*255)
    pygame.draw.rect(screen, (10, 30, 10), (OFFSET_X, UI_PANEL_Y + 45, BOARD_SIZE, 50), border_radius=15)
    pygame.draw.rect(screen, (c_r, c_g, 100), (OFFSET_X, UI_PANEL_Y + 45, BOARD_SIZE * confianca, 50), border_radius=15)
    
    pct_img = pygame.font.SysFont("Consolas", 32, bold=True).render(f"{int(confianca*100)}%", True, (255, 255, 255))
    screen.blit(pct_img, pct_img.get_rect(center=(WIDTH//2, UI_PANEL_Y + 70)))

    # Botões
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

    # 1. EVENTOS (Prioridade máxima)
    for event in pygame.event.get():
        if event.type == pygame.QUIT: pygame.quit(); sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if botao_demo.collidepoint(event.pos): 
                modo_demo = not modo_demo
                board = [" "] * 9; timer_vitoria = 0
            elif botao_reset.collidepoint(event.pos): 
                board = [" "] * 9; scores = {"X":0,"O":0,"E":0}; timer_vitoria = 0
            elif not modo_demo:
                mx, my = event.pos
                if OFFSET_X < mx < OFFSET_X + BOARD_SIZE and OFFSET_Y < my < OFFSET_Y + BOARD_SIZE:
                    idx = int((mx - OFFSET_X) // CELL + ((my - OFFSET_Y) // CELL) * 3)
                    if board[idx] == " ":
                        board[idx] = "X"
                        res = vencedor(board)
                        if res:
                            texto_vitoria = "VITÓRIA!" if res != "empate" else "EMPATE!"
                            scores[res[0].upper() if res != "empate" else "E"] += 1
                            timer_vitoria = 80; board = [" "] * 9
                        else:
                            m = melhor_jogada("O")
                            if m is not None: board[m] = "O"
                            res = vencedor(board)
                            if res:
                                texto_vitoria = "IA VENCEU!" if res != "empate" else "EMPATE!"
                                scores[res[0].upper() if res != "empate" else "E"] += 1
                                timer_vitoria = 80; board = [" "] * 9

    # 2. IA NO MODO DEMO (Controlada por tempo)
    if modo_demo and agora > tempo_proxima_jogada:
        res = vencedor(board)
        if res:
            texto_vitoria = f"{res.upper()} GANHOU!" if res != "empate" else "EMPATE!"
            scores[res[0].upper() if res != "empate" else "E"] += 1
            timer_vitoria = 80; board = [" "] * 9
        else:
            turno = "X" if board.count("X") <= board.count("O") else "O"
            m = melhor_jogada(turno)
            if m is not None: board[m] = turno
        tempo_proxima_jogada = agora + delay_demo

    pygame.display.update()
    clock.tick(60)
