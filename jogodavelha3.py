import pygame
import random
import sys
import threading
import json
from collections import deque
import math
import json
import time
import gzip
pygame.init()
clock = pygame.time.Clock()
# ============================
# TAMANHO AJUSTADO
# ============================
CELL = 150
BOARD_SIZE = CELL * 3

WIDTH = BOARD_SIZE + 200
HEIGHT = BOARD_SIZE + 80

PANEL_X = BOARD_SIZE + 100

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("IA Aprendendo Jogo da Velha")
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)  # tela cheia
WIDTH, HEIGHT = screen.get_size()  # pega o tamanho real
# Altura da metade de cima = metade da tela
TAB_HEIGHT = HEIGHT // 2
TAB_WIDTH = WIDTH

# Cada célula vai se adaptar à metade da tela
CELL = TAB_HEIGHT // 3
BOARD_SIZE = CELL * 3  # agora o tabuleiro cabe certinho na metade de cima
# ============================
# VARIÁVEIS
# ============================
board = [" "] * 9
Q = {}

alpha = 0.3
gamma = 0.9
epsilon = 0.1

player = "X"
ai = "O"

player_score = 0
ai_score = 0
draw_score = 0

logs_ia = deque(maxlen=12)
ultima_jogada_ia = "-"
ultimo_score = "-"
total_opcoes = 0
status_ia = "Aguardando"
logs_tecnicos = deque(maxlen=6)
Y_PLACAR = BOARD_SIZE + 20
Y_INFO = BOARD_SIZE + 50
Y_LOGS = BOARD_SIZE + 80
Y_PAINEL = BOARD_SIZE + 140
Y_CONFIANCA = BOARD_SIZE + 300
X_LOG = BOARD_SIZE + 50
minimax_ativo = True
botao_rect = pygame.Rect(50, HEIGHT - 80, 200, 50)
font_botao = pygame.font.SysFont("Consolas", 24)
demo_musica_ativa = False  # flag pra demo
lock_q = threading.Lock()
ultimo_save = time.time()
pos_musica_normal = 0.0 

def salvar_q():
    try:
        with gzip.open("/storage/emulated/0/qtable.json.gz", "wt") as f:
            json.dump(Q, f)
        print("✅ IA salva (comprimida)")
    except Exception as e:
        print("❌ Erro ao salvar:", e)
def carregar_q():
    global Q
    try:
        with gzip.open("/storage/emulated/0/qtable.json.gz", "rt") as f:
            Q = json.load(f)
        print("✅ IA carregada (comprimida)")
    except Exception as e:
        print("⚠ Nenhum save encontrado ou erro:", e)
        Q = {}
def auto_save():
    global ultimo_save
    if time.time() - ultimo_save > 10:
        salvar_q()
        ultimo_save = time.time()


# ============================
# FUNDO MATRIX LEVE
# ============================
cols = WIDTH // 20
drops = [random.randint(-HEIGHT, 0) for _ in range(cols)]
particles = []
for _ in range(25):
    particles.append([
        random.randint(0, WIDTH),
        random.randint(0, HEIGHT),
        random.randint(1, 2)
    ])
# ============================
# FUNÇÕES IA
# ============================

# ============================
# BOTÃO DEMO
# ============================
botao_demo = pygame.Rect(250, HEIGHT - 80, 200, 50)  # posição e tamanho do botão
font_botao_demo = pygame.font.SysFont(None, 30)

botao_reset = pygame.Rect(480, HEIGHT - 80, 200, 50)
font_botao_reset = pygame.font.SysFont(None, 30)




modo_demo = False  # inicializa modo demo desligado
tempo_ultimo_move_demo = 0
delay_demo = 800  # ms entre jogadas automáticas
jogador_atual_demo = "X"



def desenhar_botao_demo():
    cor = (0,150,255) if modo_demo else (100,100,100)
    pygame.draw.rect(screen, cor, botao_demo)
    pygame.draw.rect(screen, (255,255,255), botao_demo, 2)
    txt = "DEMO ON" if modo_demo else "DEMO OFF"
    img = font_botao_demo.render(txt, True, (0,0,0))
    screen.blit(img, img.get_rect(center=botao_demo.center))

def alternar_demo():
    """Liga ou desliga o modo demo"""
    global modo_demo
    modo_demo = not modo_demo
    print("Demo:", "ON" if modo_demo else "OFF")

def jogada_demo():
    """Executa jogada automática no modo demo e mostra quem ganhou"""
    global board, tempo_ultimo_move_demo, jogador_atual_demo

    agora = pygame.time.get_ticks()
    if agora - tempo_ultimo_move_demo < delay_demo:
        return  # espera o delay

    # verifica se o jogo acabou
    win = vencedor(board)
    if win is not None:
        if win == "X":
            mostrar("X GANHOU")
        elif win == "O":
            mostrar("O GANHOU")
        elif win == "empate":
            mostrar("EMPATE")
        resetar()
        jogador_atual_demo = "X"
        tempo_ultimo_move_demo = agora
        return

    
    # calcula a melhor jogada usando minimax pra demo
    move = melhor_jogada(board, jogador_atual_demo)
    if move is not None:
        board[move] = jogador_atual_demo
        # alterna jogador
        jogador_atual_demo = "O" if jogador_atual_demo == "X" else "X"

        tempo_ultimo_move_demo = agora

    # mostra força da jogada (opcional)
    scores = avaliar_jogadas(board)
    draw_forca_jogadas(scores)

def log_tec(texto):
    logs_tecnicos.append(f"> {texto}")
def log(texto):
    logs_ia.append(texto)

def estado(b):
    return "".join(b)

def jogadas(b):
    return [i for i,v in enumerate(b) if v==" "]

def vencedor(b):
    linhas=[
        (0,1,2),(3,4,5),(6,7,8),
        (0,3,6),(1,4,7),(2,5,8),
        (0,4,8),(2,4,6)
    ]
    for a,b2,c in linhas:
        if b[a]!=" " and b[a]==b[b2]==b[c]:
            return b[a]
    if " " not in b:
        return "empate"
    return None

MAX_Q = 50000

def atualizar(s, move, recompensa):
    with lock_q:
        if len(Q) > MAX_Q:
            Q.clear()  # limpa tudo se ficar gigante (seguro pra feira)

        if s not in Q:
            Q[s] = {}

        atual = Q[s].get(move, 0)
        Q[s][move] = atual + alpha * (recompensa - atual)
def treino_auto():
    b = [" "] * 9
    historico = []
    jogador = "X"

    while True:
        s = estado(b)
        moves = jogadas(b)
        if not moves:
            break

        move = random.choice(moves)
        historico.append((s, move, jogador))
        b[move] = jogador

        win = vencedor(b)
        if win:
            for s, m, j in historico:
                if win == "empate":
                    recompensa = 0.3
                elif j == win:
                    recompensa = 1
                else:
                    recompensa = -1
                atualizar(s, m, recompensa)
            break

        jogador = "O" if jogador == "X" else "X"

def treino_continuo():
    while True:
        treino_auto()

# ============================
# MINIMAX
# ============================

memo = {}

def minimax(b, is_max):
    key = "".join(b) + str(is_max)
    if key in memo:
        return memo[key]
        
    win = vencedor(b)
    if win == ai:
        return 1
    elif win == player:
        return -1
    elif win == "empate":
        return 0

    if is_max:
        melhor = -999
        for m in jogadas(b):
            b[m] = ai
            score = minimax(b, False)
            b[m] = " "
            melhor = max(melhor, score)
    else:
        melhor = 999
        for m in jogadas(b):
            b[m] = player
            score = minimax(b, True)
            b[m] = " "
            melhor = min(melhor, score)

    memo[key] = melhor
    return melhor

def melhor_jogada(b, jogador):
    global ultima_jogada_ia, ultimo_score, total_opcoes, status_ia

    log_tec("IA iniciando análise")

    moves = jogadas(b)
    total_opcoes = len(moves)

    melhores = []
    melhor_score = -999

    for m in moves:
        b[m] = ai
        score = minimax(b, False)
        b[m] = " "

        log(f"Minimax: {m} score={score}")

        if score > melhor_score:
            melhor_score = score
            melhores = [m]
        elif score == melhor_score:
            melhores.append(m)

    melhor_move = random.choice(melhores)

    # atualização correta (uma vez só)
    ultima_jogada_ia = melhor_move
    ultimo_score = melhor_score
    status_ia = "Analisando"
    pygame.display.update()
    pygame.time.wait(200)

    status_ia = "Jogou"

    log_tec(f"IA escolheu posição {melhor_move}")
    if not minimax_ativo:
        return random.choice(jogadas(b))
    return melhor_move
            
    return random.choice(melhores)
    log_tec(f"Melhor jogada: {melhor_move}")
def avaliar_jogadas(b):
    scores = {}
    for m in jogadas(b):
        b[m] = ai
        score = minimax(b, False)
        b[m] = " "
        scores[m] = score
    return scores

# =========================
# Botão Reset
# =========================

def resetar():
    global board, jogador_atual_demo, modo_demo

    board = [" "] * 9
    jogador_atual_demo = "X"
    modo_demo = False  # opcional





# Inicializa o mixer do Pygame
pygame.mixer.init()

# ============================
# CAMINHOS ABSOLUTOS DAS MÚSICAS
# ============================
# carregar músicas
musica_normal = "/storage/emulated/0/Download/musica_jogo_da_velha/freemusiclab-dark-cyberpunk-i-free-background-music-i-free-music-lab-release-469493.mp3"
musica_vitoria = "/storage/emulated/0/Download/musica_jogo_da_velha/ronaldoreyz-energetic-futuristic-edm-universe-at-party-322220.mp3"
musica_demo = "/storage/emulated/0/Download/musica_jogo_da_velha/alexgrohl-energetic-action-sport-500409.mp3"
# inicia música normal em loop infinito
musica_atual = None       # qual música está tocando
demo_musica_ativa = False
vitoria_musica_ativa = False
pos_musica_normal = 0
def tocar_musica_normal():
    global musica_atual, pos_musica_normal
    if musica_atual != "normal":
        pygame.mixer.music.stop()
        pygame.mixer.music.load(musica_normal)
        pygame.mixer.music.set_volume(1.0)
        pygame.mixer.music.play(-1)  # loop infinito
        musica_atual = "normal"

def tocar_musica_demo():
    global musica_atual, demo_musica_ativa
    if musica_atual != "demo":
        pygame.mixer.music.stop()
        pygame.mixer.music.load(musica_demo)
        pygame.mixer.music.set_volume(1.0)
        pygame.mixer.music.play(-1)
        musica_atual = "demo"
        demo_musica_ativa = True

def tocar_musica_vitoria():
    global musica_atual, vitoria_musica_ativa, pos_musica_normal
    if musica_atual != "vitoria":
        # Salva a posição atual (convertendo ms para segundos)
        # O mixer.music.get_pos() retorna o tempo desde que o PLAY começou, 
        # então somamos à posição que ela já tinha começado.
        pos_musica_normal += pygame.mixer.music.get_pos() / 1000.0
        
        pygame.mixer.music.stop()
        pygame.mixer.music.load(musica_vitoria)
        pygame.mixer.music.play(0) # Toca uma vez
        musica_atual = "vitoria"
        vitoria_musica_ativa = True
def retomar_musica_normal():
    global musica_atual, vitoria_musica_ativa, pos_musica_normal
    pygame.mixer.music.stop()
    pygame.mixer.music.load(musica_normal)
    
    # Se a música for muito longa e o marcador exceder o tempo dela, 
    # o Pygame pode dar erro, então resetamos se necessário.
    try:
        pygame.mixer.music.play(-1, start=pos_musica_normal)
    except:
        pygame.mixer.music.play(-1, start=0)
        pos_musica_normal = 0
        
    musica_atual = "normal"
    vitoria_musica_ativa = False
    
def parar_demo():
    global demo_musica_ativa
    pygame.mixer.music.stop()
    demo_musica_ativa = False    
    

assinatura = "Daniel V, Pedro M"
assinatura_font = pygame.font.SysFont("Consolas", 28)
assinatura_x = 220 # posição horizontal
assinatura_y_base = HEIGHT - 200 # posição vertical base
assinatura_offset = 0
assinatura_dir = 1
assinatura_alpha = 128  # opacidade inicial (0-255)
assinatura_alpha_dir = 1

def draw_assinatura():
    global assinatura_offset, assinatura_dir, assinatura_alpha, assinatura_alpha_dir
    
    # animação vertical (sube e desce)
    assinatura_offset += assinatura_dir * 0.5  # velocidade
    if assinatura_offset > 10 or assinatura_offset < -10:
        assinatura_dir *= -1
    
    # animação de opacidade (fade)
    assinatura_alpha += assinatura_alpha_dir * 2
    if assinatura_alpha > 255 or assinatura_alpha < 50:
        assinatura_alpha_dir *= -1
        assinatura_alpha = max(50, min(255, assinatura_alpha))

    # animação de cor (opcional, muda gradualmente)
    r = (pygame.time.get_ticks() // 5) % 256
    g = (pygame.time.get_ticks() // 3) % 256
    b = (pygame.time.get_ticks() // 7) % 256
    cor = (r, g, b)

    # criar superfície transparente para controlar alpha
    text_surface = assinatura_font.render(assinatura, True, cor)
    text_surface.set_alpha(assinatura_alpha)
    
    # desenha na tela com offset vertical
    screen.blit(text_surface, (assinatura_x, assinatura_y_base + assinatura_offset))




def draw_glitch():
    """
    Desenha flashes/“glitchs” aleatórios por toda a tela.
    """
    # No início do programa, onde você cria as partículas:
particles = []
for _ in range(25):
    particles.append([
        random.randint(0, WIDTH),
        random.randint(0, HEIGHT),
        random.randint(1, 3), # Velocidade
        random.randint(0, 360) # Matiz inicial (HUE)
    ])

pulse = 0
pulse_dir = 1

def draw_pulse():
    global pulse, pulse_dir
    pulse += pulse_dir * 2
    if pulse > 50 or pulse < 0:
        pulse_dir *= -1
    pygame.draw.rect(screen, (0, 255, 0, pulse), (0, 0, WIDTH, 5))
def draw_complexidade():
    font = pygame.font.SysFont("Consolas", 22)
    txt = "Complexidade: O(b^d)"
    screen.blit(font.render(txt, True, (0,255,0)), (250, BOARD_SIZE + 260))
def draw_probabilidade():
    valor = calcular_confianca(ultimo_score)
    chance = int(valor * 100)

    font = pygame.font.SysFont("Consolas", 22)
    txt = f"Chance de vitória: {chance}%"
    screen.blit(font.render(txt, True, (0,255,0)), (250, BOARD_SIZE + 230))
def calcular_confianca(score):
    if score == 1:
        return 1.0
    elif score == 0:
        return 0.5
    else:
        return 0.1
def draw_confianca(offset_y):
    valor = conf_animada
    largura_max = 200
    largura = int(valor * largura_max)
    x = 50
    y = HEIGHT - 100

    # fundo
    pygame.draw.rect(screen, (30,30,30), (x, y, largura_max, 20))
    cor = (0,255,0) if valor>0.7 else (255,165,0) if valor>0.3 else (255,0,0)
    pygame.draw.rect(screen, cor, (x, y, largura, 20))
    pygame.draw.rect(screen, (0,255,0), (x, y, largura_max, 20), 2)

    font = pygame.font.SysFont("Consolas", 24)
    txt = font.render(f"Conf: {int(valor*100)}%", True, (0,255,0))
    screen.blit(txt, (x, y-25))

# =================================
# BARRA DE CONFIANÇA ANIMADA NEON
# =================================
conf_animada = 0  # valor animado que vai se aproximando do alvo

def update_confianca():
    """Atualiza o valor animado da barra de confiança"""
    global conf_animada
    alvo = calcular_confianca(ultimo_score)  # valor real: 0.0 a 1.0
    conf_animada += (alvo - conf_animada) * 0.2  # aproxima 20% da diferença

    # Corrige para que nunca fique faltando 1%
    if abs(conf_animada - alvo) < 0.01:
        conf_animada = alvo
def draw_confianca():
    valor = conf_animada
    largura_max = 200
    largura = int(valor * largura_max)

    x = 50
    y = PANEL_Y+ 300  # posição no painel

    pygame.draw.rect(screen, (30,30,30), (x, y, largura_max, 20))
    
    if valor > 0.7:
        cor = (0,255,0)
    elif valor > 0.3:
        cor = (255,165,0)
    else:
        cor = (255,0,0)

    pygame.draw.rect(screen, cor, (x, y, largura, 20))
    pygame.draw.rect(screen, (0,255,0), (x, y, largura_max, 20), 2)

    font = pygame.font.SysFont("Consolas", 24)
    txt = font.render(f"Conf: {int(valor*100)}%", True, (0,255,0))
    screen.blit(txt, (x, y - 25))
def draw_board():
    # linhas horizontais
    for i in range(1,3):
        pygame.draw.line(screen, (0,255,0), (0, i*CELL), (BOARD_SIZE, i*CELL), 4)
    # linhas verticais
    for i in range(1,3):
        pygame.draw.line(screen, (0,255,0), (i*CELL, 0), (i*CELL, BOARD_SIZE), 4)
def draw_figures():
    for i, v in enumerate(board):
        x = (i % 3) * CELL
        y = (i // 3) * CELL

        if v == "X":
            pygame.draw.line(screen, (255,50,50), (x+20, y+20), (x+CELL-20, y+CELL-20), 4)
            pygame.draw.line(screen, (255,50,50), (x+CELL-20, y+20), (x+20, y+CELL-20), 4)
        elif v == "O":
            pygame.draw.circle(screen, (0,200,255), (x+CELL//2, y+CELL//2), CELL//2-20, 4)
def draw_forca_jogadas(scores):
    for m, score in scores.items():
        x = (m % 3) * CELL
        y = (m // 3) * CELL

        if score >= 0.8:
            cor = (0,255,0)
        elif score >= 0.3:
            cor = (255,165,0)
        else:
            cor = (255,0,0)

        pygame.draw.rect(screen, cor, (x+5, y+5, CELL-10, CELL-10), 4)

def draw_logs():
    font = pygame.font.SysFont(None,24)
    y = 750
    for linha in list(logs_ia):
        img = font.render(linha, True, (0,255,0))
        screen.blit(img, (PANEL_X, y))
        y += 25

def placar():
    font=pygame.font.SysFont(None,30)
    
    txt=f"Voce:{player_score} IA:{ai_score} Empate:{draw_score}"
    img=font.render(txt,True,(0,255,0))
    screen.blit(img,(10,Y_PLACAR))

    info=f"Estados:{len(Q)}"
    img2=font.render(info,True,(0,255,0))
    screen.blit(img2,(10,Y_INFO))



mostrando_vitoria = False
texto_vitoria = ""
tempo_vitoria = 0


def mostrar(texto):
    font = pygame.font.SysFont(None, 60)

    inicio = pygame.time.get_ticks()
    duracao = 1200  # tempo total da animação

    while pygame.time.get_ticks() - inicio < duracao:
        screen.fill((0,0,0))

        # mantém o jogo desenhado atrás
        draw_background()
        draw_board()
        draw_figures()

        tempo = pygame.time.get_ticks()

        # 🌈 cor mudando
        r = int(128 + 127 * math.sin(tempo * 0.005))
        g = int(128 + 127 * math.sin(tempo * 0.005 + 2))
        b = int(128 + 127 * math.sin(tempo * 0.005 + 4))
        cor = (r, g, b)

        # 💥 efeito brilho (glow fake)
        for i in range(5, 0, -1):
            brilho = font.render(texto, True, cor)
            brilho.set_alpha(40)
            rect = brilho.get_rect(center=(BOARD_SIZE//2, BOARD_SIZE//2))
            rect.inflate_ip(i*4, i*4)
            screen.blit(brilho, rect)

        # texto principal
        img = font.render(texto, True, cor)
        rect = img.get_rect(center=(BOARD_SIZE//2, BOARD_SIZE//2))
        screen.blit(img, rect)

        pygame.display.update()
        clock.tick(60)

    resetar()
def draw_logs_tecnicos():
    font = pygame.font.SysFont("Consolas", 20)

    y = Y_LOGS

    for linha in logs_tecnicos:
        img = font.render(linha, True, (0,255,0))
        screen.blit(img, (10, y))
        y += 22
PANEL_Y = HEIGHT // 2  # metade inferior
def draw_bottom_panel():
    font = pygame.font.SysFont("Consolas", 24)
    y = PANEL_Y + 70

    screen.blit(font.render(f"IA: {status_ia}", True, (0,255,0)), (10, y))
    screen.blit(font.render(f"Última jogada: {ultima_jogada_ia}", True, (0,255,0)), (10, y+30))
    screen.blit(font.render(f"Score: {ultimo_score}", True, (0,255,0)), (250, y))
    screen.blit(font.render(f"Opções analisadas: {total_opcoes}", True, (0,255,0)), (250, y+30))

    # barra de confiança logo abaixo
    draw_confianca(PANEL_Y + 80)
    # barra de confiança
    
def draw_background():
    # 1. ATUALIZAÇÃO DOS DROPS (MATRIX ARCO-ÍRIS)
    for i in range(len(drops)):
        x = i * 20
        y = drops[i]

        # O cálculo da cor deve ficar FORA do 'if', para a cor existir sempre
        hue = (i * 5 + pygame.time.get_ticks() // 10) % 360
        cor_matrix = pygame.Color(0)
        cor_matrix.hsva = (hue, 100, 100, 100)

        # Desenha a linha
        pygame.draw.line(screen, cor_matrix, (x, y), (x, y + 15), 2)

        # Move a gota para baixo
        drops[i] += 5

        # Se sair da tela, reseta a posição
        if drops[i] > HEIGHT:
            drops[i] = random.randint(-100, 0)

        # 2. ATUALIZAÇÃO DAS PARTÍCULAS
    for p in particles:
        p[1] += p[2] # Move
        p[3] = (p[3] + 2) % 360 # Cor

        # O 'if' de resetar TEM que estar dentro do 'for'
        if p[1] > HEIGHT:
            p[0] = random.randint(0, WIDTH)
            p[1] = 0

        # O desenho também TEM que estar dentro do 'for'
        cor_particula = pygame.Color(0)
        cor_particula.hsva = (p[3], 100, 100, 100)
        pygame.draw.circle(screen, cor_particula, (int(p[0]), int(p[1])), 1)
 
def resetar():
    global board
    board=[" "] * 9

# ============================
# TREINO INICIAL
# ============================
#print("Treinando...")
#for _ in range(20000):
#    treino_auto()

#threading.Thread(target=treino_continuo, daemon=True).start()

# ============================
botao_rect = pygame.Rect(20, HEIGHT - 80, 200, 50)
font_botao = pygame.font.SysFont(None, 30)
# LOOP
carregar_q()
# ============================
while True:
    
    screen.fill((0,0,0))
    draw_background() 
    draw_glitch()   
    draw_board()
    draw_figures()
    placar()
    draw_logs()
    draw_logs_tecnicos()
    update_confianca()
    draw_confianca()
    draw_assinatura()
    
    
    cor = (0,200,0) if minimax_ativo else (200,0,0)
    pygame.draw.rect(screen, cor, botao_rect)
    pygame.draw.rect(screen, (255,255,255), botao_rect, 2)
    desenhar_botao_demo()
    pygame.draw.rect(screen, (200,50,50), botao_reset)
    pygame.draw.rect(screen, (255,255,255), botao_reset, 2)

    txt_reset = font_botao_reset.render("RESET", True, (0,0,0))
    screen.blit(txt_reset, txt_reset.get_rect(center=botao_reset.center))
    
    
    
    if modo_demo:
       jogada_demo()
       tocar_musica_demo()
    else:
        if not vitoria_musica_ativa:
            tocar_musica_normal()
    texto = "Minimax ON" if minimax_ativo else "Minimax OFF"
    img = font_botao.render(texto, True, (0,0,0))
    screen.blit(img, img.get_rect(center=botao_rect.center))
    for event in pygame.event.get():
        if event.type==pygame.QUIT:
            salvar_q()
            pygame.quit()
            sys.exit()
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos

    # 🔴 RESET (prioridade)
            if botao_reset.collidepoint(event.pos):
                resetar()

    # 🔵 BOTÃO MINIMAX
            elif botao_rect.collidepoint(event.pos):
                minimax_ativo = not minimax_ativo

    # 🟣 BOTÃO DEMO
            elif botao_demo.collidepoint(event.pos):
                alternar_demo()

    # 🎮 TABULEIRO
            elif x < BOARD_SIZE and y < BOARD_SIZE:
                pos = x//CELL + (y//CELL)*3

                if board[pos] == " ":
                    board[pos] = player

                    win=vencedor(board)

                    if win=="X":
                        player_score += 1                        
                        mostrar("VOCE GANHOU")    # mostra a mensagem enquanto música toca
                        tocar_musica_vitoria()      # toca a música de vitória
                        pygame.time.wait(1200)      # espera 3 segundos para mostrar o resultado
                        resetar()                   # limpa o tabuleiro
                        retomar_musica_normal()
                        
                        
                    elif win=="empate":
                        draw_score+=1
                        mostrar("EMPATE")

                    else:
                        scores = avaliar_jogadas(board)

                        draw_board()
                        draw_forca_jogadas(scores)
                        draw_figures()
                        pygame.display.update()
                        pygame.time.wait(300)

                        # calcula a melhor jogada usando minimax pra demo
                        move = melhor_jogada(board, jogador_atual_demo)
                        board[move]=ai

                        win=vencedor(board)

                        if win=="O":
                            ai_score+=1
                            mostrar("IA GANHOU")
                            
                        elif win=="empate":
                            draw_score+=1
                            mostrar("EMPATE")
                            
                        # Música de demo
                        if modo_demo and pygame.mixer.music.get_busy() == 0:
                            if not demo_musica_ativa:
                                tocar_demo()
                                
                        else:
                            if demo_musica_ativa:
                                parar_demo()
                                pygame.mixer.music.load(musica_normal)
                                pygame.mixer.music.play(-1)

# Música normal do jogo
                        if not modo_demo and pygame.mixer.music.get_busy() == 0:
                            tocar_musica_normal()
                            if pygame.mixer.music.get_busy() == 0:
                                pygame.mixer.music.load(musica_normal)
                                pygame.mixer.music.play(-1)
# Música de vitória
                        if win == "X":
                            tocar_musica_vitoria()      # toca a música de vitória
                            pygame.time.wait(1200)      # espera 3 segundos para mostrar o resultado
                            resetar()                   # limpa o tabuleiro
                            retomar_musica_normal()     # volta a música normal de onde parou
                        elif win == "O":                     
                            pos_musica = tocar_musica_vitoria()
                            pygame.time.wait(1200)  # espera 3 segundos
                            resetar()
                            retomar_musica_normal()
    clock.tick(60)
    pygame.display.update()