import cv2
import mediapipe as mp

# Inicializa o objeto de captura de vídeo
video = cv2.VideoCapture(1)

# Define a solução para detectar as mãos
hands = mp.solutions.hands
Hands = hands.Hands(max_num_hands=2)
# Carrega as funções de desenho dos pontos e conexões da solução
mpDraw = mp.solutions.drawing_utils

while True:
    # Lê o quadro mais recente do vídeo
    success, img = video.read()
    # Converte o quadro para RGB, que é o formato esperado pela solução
    frameRGB = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
    # Processa o quadro RGB usando a solução de detecção de mãos
    results = Hands.process(frameRGB)
    # Extrai os pontos das mãos detectadas (se houver alguma)
    handPoints = results.multi_hand_landmarks
    # Obtém a largura e altura do quadro
    h, w, _ = img.shape
    # Inicializa a lista de pontos das mãos
    pontos = []
    # Desenha os pontos e conexões das mãos detectadas (se houver alguma)
    if handPoints:
        for points in handPoints:
            mpDraw.draw_landmarks(img, points,hands.HAND_CONNECTIONS)
            # Podemos enumerar esses pontos da seguinte forma
            for id, cord in enumerate(points.landmark):
                cx, cy = int(cord.x * w), int(cord.y * h)
                # Adiciona as coordenadas do ponto à lista de pontos das mãos
                pontos.append((cx,cy))
            
            # Define a lista de dedos que serão verificados
            dedos = [8,12,16,20]
            # Inicializa o contador de dedos levantados
            contador = 0
            if pontos:
                # Verifica se o dedo indicador está levantado (comparando as coordenadas X dos pontos 4 e 3)
                if pontos[4][0] < pontos[3][0]:
                    contador += 1
                # Verifica se os outros dedos selecionados estão levantados (comparando as coordenadas Y dos pontos)
                for x in dedos:
                   if pontos[x][1] < pontos[x-2][1]:
                       contador +=1

            # Desenha um retângulo para mostrar a área de exibição do contador
            cv2.rectangle(img, (80, 10), (200,110), (255, 0, 0), -1)
            # Escreve o número de dedos levantados dentro do retângulo
            cv2.putText(img,str(contador),(100,100),cv2.FONT_HERSHEY_SIMPLEX,4,(255,255,255),5)
            #print(contador)

    # Mostra o quadro processado na janela "Imagem"
    cv2.imshow('Imagem',img)
    # Espera uma tecla ser pressionada para continuar o loop
    cv2.waitKey(1)
