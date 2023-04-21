#Importando as bibliotecas necessárias

import cv2
import numpy as np
from sklearn.metrics import pairwise
import sim                  
import sys


#Declarando variáveis globais que serão usadas ao longo da função

background = None
v0=2
accumulated_weight = 0.5

# Definindo manualmente nossa Região de Interesse (ROI) para pegar a mão.

roi_top = 20
roi_bottom = 300
roi_right = 300
roi_left = 600

sim.simxFinish(-1) # fechando todas as conexões abertas

clientID=sim.simxStart('127.0.0.1',19999,True,True,5000,5)

if clientID!=-1: # verifica se a conexão do cliente foi bem-sucedida
    print ('Conectado ao servidor do API :)')
    
else:
    print ('Não conseguiu conectar :(, certifique de a cena do coppelia estar no play antes de dar run nesse programa')
    sys.exit('Não conectou')


# obter os manipuladores dos motores
errorCode,left_motor_handle=sim.simxGetObjectHandle(clientID,'junta_E',sim.simx_opmode_oneshot_wait)
errorCode,right_motor_handle=sim.simxGetObjectHandle(clientID,'junta_D',sim.simx_opmode_oneshot_wait)
# DIREÇÕES DO CARRO 
def frente():
    v0=2
    errorCode=sim.simxSetJointTargetVelocity(clientID,left_motor_handle,v0, sim.simx_opmode_streaming)
    errorCode=sim.simxSetJointTargetVelocity(clientID,right_motor_handle,v0, sim.simx_opmode_streaming)

    
def esquerda():
    v0=2
    errorCode=sim.simxSetJointTargetVelocity(clientID,left_motor_handle,0, sim.simx_opmode_streaming)
    errorCode=sim.simxSetJointTargetVelocity(clientID,right_motor_handle,v0, sim.simx_opmode_streaming)

    
def direita():
    v0=2
    
    errorCode=sim.simxSetJointTargetVelocity(clientID,left_motor_handle,v0, sim.simx_opmode_streaming)
    errorCode=sim.simxSetJointTargetVelocity(clientID,right_motor_handle,0, sim.simx_opmode_streaming)

def atras():
    v0=-2
    errorCode=sim.simxSetJointTargetVelocity(clientID,left_motor_handle,v0, sim.simx_opmode_streaming)
    errorCode=sim.simxSetJointTargetVelocity(clientID,right_motor_handle,v0, sim.simx_opmode_streaming)

def parar():
    v0=0
    errorCode=sim.simxSetJointTargetVelocity(clientID,left_motor_handle,v0, sim.simx_opmode_streaming)
    errorCode=sim.simxSetJointTargetVelocity(clientID,right_motor_handle,v0, sim.simx_opmode_streaming)



"""A seguinte função é usada para calcular a soma ponderada
da imagem de entrada src e do acumulador dst para que dst se torne uma
média móvel de uma sequência de frames"""

def calc_accum_avg(frame, accumulated_weight):

    
    # pega o background
    global background
    
    # Para a primeira vez, crie o background a partir de uma cópia do frame.
    if background is None:
        background = frame.copy().astype("float")
        return None

    # calcule a média ponderada
    cv2.accumulateWeighted(frame, background, accumulated_weight)
    
    
    #Segmenta a região da mão no frame

def segment(frame, threshold=25):
    global background
    
    #  Calcula a diferença absoluta entre o background e o frame passado
    diff = cv2.absdiff(background.astype("uint8"), frame)

    # Aplica um limiar à imagem
    # Precisamos apenas do limiar, então descartaremos o primeiro item
    _ , thresholded = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)

    # Pegue os contornos externos da imagem
    # Novamente, pegando apenas o que precisamos aqui e descartando o restante
    contours, hierarchy = cv2.findContours(thresholded.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if len(contours) == 0:
        return None
    else:
    
        hand_segment = max(contours, key=cv2.contourArea)
        return (thresholded, hand_segment)
    
    
def count_fingers(thresholded, hand_segment):
    
    conv_hull = cv2.convexHull(hand_segment)

    top    = tuple(conv_hull[conv_hull[:, :, 1].argmin()][0])
    bottom = tuple(conv_hull[conv_hull[:, :, 1].argmax()][0])
    left   = tuple(conv_hull[conv_hull[:, :, 0].argmin()][0])
    right  = tuple(conv_hull[conv_hull[:, :, 0].argmax()][0])

    cX = (left[0] + right[0]) // 2
    cY = (top[1] + bottom[1]) // 2

    distance = pairwise.euclidean_distances([(cX, cY)], Y=[left, right, top, bottom])[0]
    
    max_distance = distance.max()

    radius = int(0.8 * max_distance)
    circumference = (2 * np.pi * radius)

    circular_roi = np.zeros(thresholded.shape[:2], dtype="uint8")
    
    cv2.circle(circular_roi, (cX, cY), radius, 255, 10)
    
    
    circular_roi = cv2.bitwise_and(thresholded, thresholded, mask=circular_roi)

    contours, hierarchy = cv2.findContours(circular_roi.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    # contar os dedos começando no zero
    count = 0
    for cnt in contours:
        
        (x, y, w, h) = cv2.boundingRect(cnt)

        out_of_wrist = ((cY + (cY * 0.25)) > (y + h))
        
        limit_points = ((circumference * 0.25) > cnt.shape[0])
        
        if  out_of_wrist and limit_points:
            count += 1

    return count

#qual a camera selecionada (altere para 0)
cam = cv2.VideoCapture(1)

# Iniciar a contagem de frames
num_frames = 0

# continuar rodando até a camera abrir
while cam.isOpened():
    # frame atual
    ret, frame = cam.read()

    frame = cv2.flip(frame, 1)

    frame_copy = frame.copy()

    roi = frame[roi_top:roi_bottom, roi_right:roi_left]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (7, 7), 0)
    fingers=0
    # para os primeiros 30 frames vai calcular o comum
    if num_frames < 60:
        calc_accum_avg(gray, accumulated_weight)
        if num_frames <= 59:
            #definindo a cor e a posição da frase abaixo
            cv2.putText(frame_copy, "ESPERE! CALCULANDO O BACKGROUND", (30, 450), cv2.FONT_HERSHEY_TRIPLEX, 1, (255, 0,0), 2)
            cv2.imshow("MÃO PRA CIMA ;)",frame_copy)
            
    else:
        # região da mão
        hand = segment(gray)

        if hand is not None:
            
            thresholded, hand_segment = hand

            #desenhar o contorno dos dedos
            cv2.drawContours(frame_copy, [hand_segment + (roi_right, roi_top)], -1, (255, 0, 0),1)

            # definindo as direções com base nos números dos dedos
            fingers = count_fingers(thresholded, hand_segment)
            directions=['PARADO','FRENTE','ESQUERDA','DIREITA','ATRAS','ERRO']
            if fingers not in [0,1,2,3,4]:
                fingers=0
                
            cv2.putText(frame_copy, directions[fingers], (70, 45), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,255), 2)

            cv2.imshow("Thesholded", thresholded)

    # Dimensões do ROI para pegar os frames das mãos
    cv2.rectangle(frame_copy, (roi_left, roi_top), (roi_right, roi_bottom), (0, 255, 0), 5)
    # incrementando o numero de frames
    num_frames += 1
    # mostrar a janela de frame
    cv2.imshow("MÃO PRA CIMA ;)", frame_copy)
    # Fechar as janelas
    k = cv2.waitKey(1)
    if k == 27:
        break
    elif k==ord('b'): #reseta a configuração do frame
        num_frames=0
    else:
        pass
    if fingers==1:
        frente()
    elif fingers==2:
        esquerda()
    elif fingers==3:
        direita()
    elif fingers==4:
        atras()
    else:
        parar()
# tirar a camera, e fechar todas as janelas
returnCode=sim.simxStopSimulation(clientID,sim.simx_opmode_oneshot)
cam.release()
cv2.destroyAllWindows()