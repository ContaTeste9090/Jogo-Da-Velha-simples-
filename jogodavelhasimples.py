import pygame
import random
import sys
import math

# ============================
# CONFIGURAÇÕES INICIAIS
# ============================
pygame.init()
WIDTH, HEIGHT = 600, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tic-Tac-Toe IA: Daniel & Pedro")
clock = pygame.time.Clock()

# Cores Neon
GREEN = (0, 255, 70)
RED = (255, 50, 50)
BLUE = (0, 200, 255)
BLACK = (10, 10, 10)

# Geometria do Tabuleiro
CELL = 150
BOARD_SIZE = CELL * 3
OFFSET_X = (WIDTH - BOARD_SIZE) // 2
OFFSET_Y = 50

# Estado do Jogo
board = [" "] * 9
player, ai = "X", "O"
scores = {"player": 0, "ai": 0, "draw": 0}
status_ia = "Aguardando..."
confianca_animada = 0.5
ultimo_score_ia = 0

# Efeito Matrix (Simplificado sem arquivos)
cols = WIDTH // 20
drops = [random.randint(-HEIGHT, 0) for _ in range(cols)]

# ============================
# LÓGICA DA IA (MINIMAX)
# ============================
def vencedor(b):
    linhas = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
    for a, b_idx, c in linhas:
        if b[a] != " " and b[a] == b[b_idx] == b[c]:
            return b[a]
    return "empate" if " " not in b else None

def minimax(b, is_max):
    win = vencedor(b)
    if win == ai: return 1
    if win == player: return -1
    if win == "empate": return 0

    if is_max:
        melhor = -float('inf')
        for i in [i for i, v in enumerate(b) if v == " "]:
            b[i] = ai
            melhor = max(melhor, minimax(b, False))
            b[i] = " "
        return melhor
    else:
        melhor = float('inf')
        for i in [i for i, v in enumerate(b) if v == " "]:
            b[i] = player
            melhor = min(melhor, minimax(b, True))
            b[i] = " "
        return melhor

def melhor_jogada():
    global ultimo_score_ia, status_ia
    status_ia = "Analisando..."
    melhor_val = -float('inf')
    move = -1
    for i in [i for i, v in enumerate(board) if v == " "]:
        board[i] = ai
        val = minimax(board, False)
        board[i] = " "
        if val > melhor_val:
            melhor_val = val
            move = i
    ultimo_score_ia = melhor_val
    status_ia = "IA Jogou"
    return move

# ============================
# RENDERIZAÇÃO
# ============================
def draw_matrix():
    for i in range(len(drops)):
        x = i * 20
        y = drops[i]
        hue = (i * 10 + pygame.time.get_ticks() // 20) % 360
        cor = pygame.Color(0)
        cor.hsva = (hue, 80, 100, 100)
        pygame.draw.rect(screen, cor, (x, y, 2, 10))
        drops[i] = drops[i] + 5 if drops[i] < HEIGHT else random.randint(-100, 0)

def draw_ui():
    # Tabuleiro
    for i in range(1, 3):
        pygame.draw.line(screen, GREEN, (OFFSET_X + i*CELL, OFFSET_Y), (OFFSET_X + i*CELL, OFFSET_Y + BOARD_SIZE), 3)
        pygame.draw.line(screen, GREEN, (OFFSET_X, OFFSET_Y + i*CELL), (OFFSET_X + BOARD_SIZE, OFFSET_Y + i*CELL), 3)

    # Peças
    font = pygame.font.SysFont("Consolas", 80, bold=True)
    for i, v in enumerate(board):
        x = OFFSET_X + (i % 3) * CELL + CELL//2
        y = OFFSET_Y + (i // 3) * CELL + CELL//2
        if v != " ":
            cor = RED if v == "X" else BLUE
            txt = font.render(v, True, cor)
            screen.blit(txt, txt.get_rect(center=(x, y)))

    # Painel Inferior
    font_small = pygame.font.SysFont("Consolas", 20)
    panel_y = OFFSET_Y + BOARD_SIZE + 40
    
    # Barra de Confiança
    global confianca_animada
    alvo = 1.0 if ultimo_score_ia == 1 else 0.5 if ultimo_score_ia == 0 else 0.1
    confianca_animada += (alvo - confianca_animada) * 0.1
    
    pygame.draw.rect(screen, (30, 30, 30), (OFFSET_X, panel_y, BOARD_SIZE, 20))
    pygame.draw.rect(screen, GREEN, (OFFSET_X, panel_y, int(BOARD_SIZE * confianca_animada), 20))
    screen.blit(font_small.render(f"Confiança IA: {int(confianca_animada*100)}%", True, GREEN), (OFFSET_X, panel_y - 25))
    
    # Status
    screen.blit(font_small.render(f"IA: {status_ia}", True, GREEN), (OFFSET_X, panel_y + 40))
    screen.blit(font_small.render(f"Placar - Você: {scores['player']} | IA: {scores['ai']}", True, WHITE := (255,255,255)), (OFFSET_X, panel_y + 70))
    
    # Assinatura
    
    

# ============================
# LOOP PRINCIPAL
# ============================
while True:
    screen.fill(BLACK)
    draw_matrix()
    draw_ui()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            if OFFSET_X < mx < OFFSET_X + BOARD_SIZE and OFFSET_Y < my < OFFSET_Y + BOARD_SIZE:
                col = (mx - OFFSET_X) // CELL
                row = (my - OFFSET_Y) // CELL
                idx = int(col + row * 3)

                if board[idx] == " ":
                    board[idx] = player
                    if not vencedor(board):
                        move = melhor_jogada()
                        if move != -1: board[move] = ai
                    
                    # Checar Fim de Jogo
                    res = vencedor(board)
                    if res:
                        if res == "X": scores["player"] += 1
                        elif res == "O": scores["ai"] += 1
                        else: scores["draw"] += 1
                        pygame.display.update()
                        pygame.time.wait(1000)
                        board = [" "] * 9
                        status_ia = "Reiniciando..."

    pygame.display.update()
    clock.tick(60)
