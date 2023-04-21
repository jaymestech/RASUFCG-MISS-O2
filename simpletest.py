# Certifique-se de que o lado do servidor está sendo executado no CoppeliaSim:
# em um script filho de uma cena do CoppeliaSim, adicione o seguinte comando
# para ser executado apenas uma vez, no início da simulação:

try:
    import sim
except:
    print ('--------------------------------------------------------------')
    print ('"sim.py" não pôde ser importado. Isso provavelmente significa que')
    print ('o "sim.py" ou a biblioteca remoteApi não pôde ser encontrada.')
    print ('Certifique-se de que ambos estejam na mesma pasta deste arquivo,')
    print ('ou ajuste adequadamente o arquivo "sim.py"')
    print ('--------------------------------------------------------------')
    print ('')

import time

print ('Programa iniciado')
sim.simxFinish(-1) # fecha todas as conexões abertas, caso existam
clientID=sim.simxStart('127.0.0.1',19999,True,True,5000,5) # Conecta-se ao CoppeliaSim
if clientID!=-1:
    print ('Conectado ao servidor API remoto')

    # Tenta agora recuperar dados de forma bloqueante (ou seja, uma chamada de serviço):
    res,objs=sim.simxGetObjects(clientID,sim.sim_handle_all,sim.simx_opmode_blocking)
    if res==sim.simx_return_ok:
        print ('Número de objetos na cena: ',len(objs))
    else:
        print ('A chamada da função API remota retornou com código de erro: ',res)

    time.sleep(2)

    # Agora recupere dados em streaming (ou seja, de forma não bloqueante):
    startTime=time.time()
    sim.simxGetIntegerParameter(clientID,sim.sim_intparam_mouse_x,sim.simx_opmode_streaming) # Inicializa o streaming
    while time.time()-startTime < 5:
        returnCode,data=sim.simxGetIntegerParameter(clientID,sim.sim_intparam_mouse_x,sim.simx_opmode_buffer) # Tenta recuperar os dados em streaming
        if returnCode==sim.simx_return_ok: # Depois da inicialização do streaming, levará alguns milissegundos até que o primeiro valor chegue, portanto, verifique o código de retorno
            print ('Posição x do mouse: ',data) # A posição x do mouse é atualizada quando o cursor está sobre a janela do CoppeliaSim
        time.sleep(0.005)

    # Agora envie alguns dados para o CoppeliaSim de forma não bloqueante:
    sim.simxAddStatusbarMessage(clientID,'Olá CoppeliaSim!',sim.simx_opmode_oneshot)

    # Antes de fechar a conexão com o CoppeliaSim, certifique-se de que o último comando enviado chegou. Você pode garantir isso com (por exemplo):
    sim.simxGetPingTime(clientID)

    # Agora feche a conexão com o CoppeliaSim:
    sim.simxFinish(clientID)
else:
    print ('Falha ao conectar-se ao servidor API remoto')
print ('Programa finalizado')
