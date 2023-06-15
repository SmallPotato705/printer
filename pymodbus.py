import time
import logging
from pyModbusTCP.client import ModbusClient
import pandas as pd

# =============================================================================
# 參數設置
# =============================================================================
NOW_X_AXIS = 4019
NOW_Y_AXIS = 4015
NOW_Z_AXIS = 4106


ORIGIN_FLAG = 4025
PC_TO_PLC_READY_LAMP = 4001
PC_TO_PLC_ALARM_LAMP = 4002
PC_TO_PLC_ALIVE_LAMP = 4000

PLC_PERMISSION = 4003
MOTOR_START = 4007

WRITE_X_AXIS = 4006
WRITE_Y_AXIS = 4005
WRITE_Z_AXIS = 4013

OPEN_WATER = 4011

ROW_SPACING = 10

ip = "192.168.1.250"

NUMBER_OF_ERRORS = 5

csvPath = r"D:\Mark\CO2\output.csv"




    
# =============================================================================
# 
# =============================================================================
logging.basicConfig(filename = "Modbus.log", format = "%(levelname)-10s %(asctime)s %(message)s", level = logging.DEBUG)

PLC = ModbusClient(host = ip, port = 502, unit_id = 1, auto_open = True)


# def tagSearch():
#      pathData = pd.read_csv(r"D:\Mark\CO2\tag.csv")
 
#      t2 = []
#      for i in range(len(pathData)):
#          t2.append(PLC.read_holding_registers(pathData["index"][i]))

#     for i in range(8000):
#         if t[i] != t2[i]:
#             print(pathData["index"][i])

def readCSV(path):
    
    dx = pd.read_csv(path)
    
    return dx

def startMotor():
    # =============================================================================
    # 伺服器開啟的狀態， 0切到1，執行一次，要在切回0。
    # =============================================================================
    PLC.write_single_register(MOTOR_START, 0)
    PLC.write_single_register(MOTOR_START, 1)
    PLC.write_single_register(MOTOR_START, 0)

# =============================================================================
# 讀取當前X Y Z座標數值
# =============================================================================
def getNowCoordinate():
    nowX = PLC.read_holding_registers(NOW_X_AXIS)
    nowY = PLC.read_holding_registers(NOW_Y_AXIS)
    nowZ = PLC.read_holding_registers(NOW_Z_AXIS)
    
    return nowX[0], nowY[0], nowZ[0]

# =============================================================================
#  偵測機器是否有在運作
# =============================================================================
def faultDetection(X, Y, Z):
    count = 0
    
    [nowX, nowY, nowZ] = getNowCoordinate()
    
    lastX = nowX
    lastY = nowY
    lastZ = nowZ
    
    while nowX != X or nowY != Y or nowZ != Z:
        time.sleep(1)

        [nowX, nowY, nowZ] = getNowCoordinate()
        if lastX == nowX and lastY == nowY and lastZ == nowZ:
            count += 1
            if count >= NUMBER_OF_ERRORS:
                return True

        lastX = nowX
        lastY = nowY
        lastZ = nowZ
        
    return False

# =============================================================================
# PLC權限模式  PLC主控 = 2, 1和0 PLC都不能控制。
# 可以透過下面程式，修改權限
# PLC.write_single_register(PLC_PERMISSION, 2)
# permissionState = PLC.read_holding_registers(PLC_PERMISSION)
# =============================================================================
def permission():
    permissionState = PLC.read_holding_registers(PLC_PERMISSION)
    
    logging.info("當前PLC權限為: " + str(permissionState[0]))
    
    if permissionState[0] != 2: 
        logging.info("無法寫入指令至PLC")
        return False
   
    return True

# =============================================================================
# 回歸原點
# =============================================================================
def initialization():
    # 復歸指令
    setSingleControl_XYZ(0,0,0)
    PLC.write_single_register(OPEN_WATER, 0)

    logging.info("啟動復歸指令")
    
    PLC.write_single_register(PC_TO_PLC_READY_LAMP, 0)
    PLC.write_single_register(PC_TO_PLC_ALIVE_LAMP, 1)
    
    faultState = faultDetection(0, 0, 0)
    
    PLC.write_single_register(PC_TO_PLC_ALIVE_LAMP, 0)
    
    if faultState == True:
        PLC.write_single_register(PC_TO_PLC_ALARM_LAMP, 1)
        logging.info("XYZ軸沒有移動")
        
        return False
        
    elif faultState == False:
        PLC.write_single_register(PC_TO_PLC_READY_LAMP, 1)
        logging.info("完成復歸")
        
        return True
        
    

def setSingleControl_XYZ(X = None, Y = None, Z = None):
    [nowX, nowY, nowZ] = getNowCoordinate()
    
    nextX = nowX
    nextY = nowY
    nextZ = nowZ
    # =============================================================================
    #  X 數值為0 - 720
    # =============================================================================
    if X != None:
        if X >= 0 and X <= 720:
            PLC.write_single_register(WRITE_X_AXIS, X)
            nextX = X
            logging.info("X移動: " + str(X))
        else:
            logging.info("X輸入值超出上下限，輸入值為: " + str(X))
           
    # =============================================================================
    #  Y 數值為0 - 600
    # =============================================================================
    if Y != None:
        if Y >= 0 and Y <= 600:
            PLC.write_single_register(WRITE_Y_AXIS, Y)
            nextY = Y
            logging.info("Y移動: " + str(Y))
        else:
            logging.info("Y輸入值超出上下限，輸入值為: " + str(Y))
            
    # =============================================================================
    #  Z 數值為 0 or 1
    # =============================================================================
    if Z != None:
        if Z == 0 or Z == 1:
            PLC.write_single_register(WRITE_Z_AXIS, Z)
            nextZ = Z
            logging.info("Z移動: " + str(Z))
        else:
            logging.info("Z輸入值超出上下限，輸入值為: " + str(Z))
            
    startMotor()

    faultState = faultDetection(nextX, nextY, nextZ)

    if faultState == True:
        PLC.write_single_register(PC_TO_PLC_ALARM_LAMP, 1)
        logging.info("XYZ軸沒有移動")

# =============================================================================
# 0 0 0 0 1 0 0
# 0 0 0 1 1 0 0
# 0 1 0 0 0 0 0
# 1 1 1 0 0 0 0
# 0 1 0 0 0 0 0
# 0 0 0 1 0 0 0
# 0 0 0 1 0 0 0
# =============================================================================

def autoClean():
    PLC.write_single_register(PC_TO_PLC_READY_LAMP, 0)
    PLC.write_single_register(PC_TO_PLC_ALIVE_LAMP, 1)
    
    pathData = readCSV(csvPath)
    
    for i in range(len(pathData)):
        
        if pathData["shot"][i] == 1:
            setSingleControl_XYZ(X = pathData["x"][i], Y = pathData["y"][i], Z = 1)
            PLC.write_single_register(OPEN_WATER, pathData["shot"][i])
            
        elif pathData["shot"][i] == 0:
            setSingleControl_XYZ(X = pathData["x"][i], Y = pathData["y"][i], Z = 1)
            PLC.write_single_register(OPEN_WATER, pathData["shot"][i])
            
    setSingleControl_XYZ(X = 0, Y = 0, Z = 0)
    
    PLC.write_single_register(PC_TO_PLC_READY_LAMP, 1)
    PLC.write_single_register(PC_TO_PLC_ALIVE_LAMP, 0)
    
def autoCleanALL():
    count = 0
    PLC.write_single_register(PC_TO_PLC_READY_LAMP, 0)
    PLC.write_single_register(PC_TO_PLC_ALIVE_LAMP, 1)
    
    setSingleControl_XYZ(X = 0, Y = 0, Z = 1)
    faultState = faultDetection(0, 0, 1)

    if faultState == False:
        for row in range(0, 720, ROW_SPACING):
            PLC.write_single_register(OPEN_WATER, 1)
            
            if row > 720:
                break
            
            if count == 0:
                setSingleControl_XYZ(X = row, Y = 600, Z = 1)
                faultState = faultDetection(row, 600, 1)
                
                if row + ROW_SPACING <= 720:
                    setSingleControl_XYZ(X = row + ROW_SPACING, Y = 600, Z = 1)
                    faultState = faultDetection(row + 10, 600, 1)
                
                count = 1
                
            else:
                setSingleControl_XYZ(X = row, Y = 0, Z = 1)
                faultState = faultDetection(row, 0, 1)
                
                if row + ROW_SPACING <= 720:
                    setSingleControl_XYZ(X = row + ROW_SPACING, Y = 0, Z = 1)
                    faultState = faultDetection(row + 10, 0, 1)
                    
                count = 0
            
            if faultState == True:
                PLC.write_single_register(PC_TO_PLC_ALARM_LAMP, 1)
                PLC.write_single_register(PC_TO_PLC_ALIVE_LAMP, 0)
                
                logging.info("XYZ軸沒有移動")
                
                break
            
    PLC.write_single_register(OPEN_WATER, 0)
    setSingleControl_XYZ(X = 0, Y = 0, Z = 0)
    faultState = faultDetection(0, 0, 0)
    
if __name__ == "__main__":
    
    plcIsOpen= permission()
    
    if plcIsOpen == True:
        
        alarm = PLC.read_holding_registers(PC_TO_PLC_ALARM_LAMP)
        # =============================================================================
        #  alarm燈亮，請確認機器是否有無故障。
        #  確定無故障，請手動輸入下面指令，將alarm燈滅掉
        #  PLC.write_single_register(PC_TO_PLC_ALARM_LAMP, 0)
        # =============================================================================
        if alarm[0] == 0:
            
            initialIsOk = initialization()
            
            if initialIsOk == True:
                autoClean()
                
        else:
            print("alarm燈亮，請確認機器是否有無故障")
            logging.info("alarm燈亮，請確認機器是否有無故障")
        
        
# =============================================================================
# plcIsOpen= permission()
# =============================================================================


# =============================================================================
# alarm = PLC.read_holding_registers(PC_TO_PLC_ALARM_LAMP)
# =============================================================================

# 故障驗證
# =============================================================================
# faultDetection(100, 100, 0)   會回傳True
# =============================================================================
# =============================================================================
# setSingleControl_XYZ(X = 100, Y = 100, Z = 1)
# faultDetection(100, 100, 1)   
# =============================================================================

# 初始化
# =============================================================================
# initialization()
# =============================================================================
            
# =============================================================================
# for i in range(200, 250, 1):
#     setSingleControl_XYZ(X = i, Y = 100, Z = 1)
# =============================================================================

# 噴水的驗證
# =============================================================================
# PLC.write_single_register(OPEN_WATER, 1)
# PLC.write_single_register(OPEN_WATER, 0)
# =============================================================================


from pymodbus.client.sync import ModbusTcpClient

client = ModbusTcpClient(ip)

inputAddress = 0
result = client.read_discrete_inputs(inputAddress, 1)
xx = result.bits[0]

client.write_coil(0, True)

client.close()
