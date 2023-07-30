import logging

import grpc
import protobufs.werewolf_kill_pb2 as p_wkp
import protobufs.werewolf_kill_pb2_grpc as p_wkpg

import random

def checkRoleList(stub,role:list,room_name:str)->bool:
    role_list  = p_wkp.roleList(role=role,room_name=room_name)
    return stub.checkRoleList(request=role_list).result

def startGame(stub,role:list,room_name:str)->tuple[list,str]:
    role_list  = p_wkp.roleList(role=role,room_name=room_name)
    assign_role_list = stub.startGame(request=role_list)
    return assign_role_list.role , assign_role_list.room_name

def nextStage(stub,room_name:str,stage_name:str)->tuple[list,str]:
    room_info = p_wkp.roomInfo(room_name=room_name,stage_name=stage_name)
    stage_info = stub.nextStage(request=room_info)
    return stage_info.stage ,stage_info.stage_name

def sendUserOperation(stub,user:int,operation:str,target:int,chat:str,room_name:str,stage_name:str):

    room_info = p_wkp.roomInfo(room_name=room_name,stage_name=stage_name)
    user_operation = p_wkp.userOperation(user=user,operation=operation,target=target,chat=chat,room=room_info)
    return stub.sendUserOperation(request=user_operation).result

def voteInfo(stub,room_name:str,stage_name:str):
    room_info = p_wkp.roomInfo(room_name=room_name,stage_name=stage_name)
    return stub.voteInfo(request=room_info).state



def print_stage(grpc_return):
    stage , stage_name = grpc_return
    print(stage_name)
    for i in stage:
        print("  user :" , i.user)
        print("  operation :" , i.operation)
        print("  target :" , i.target)
        print("  description :" , i.description)
        print("")


def run():

    channel = grpc.insecure_channel('localhost:50051')
    stub = p_wkpg.werewolf_killStub(channel)

    room_name = "TESTROOM"
    
    #### checkRoleList test ####
    print(checkRoleList(stub,role=[1,1,2,2,1] , room_name=room_name)) # true
    print(checkRoleList(stub,role=[2,1,1,2,1] , room_name=room_name)) # false
    print(checkRoleList(stub,role=[1,1,1,2,2] , room_name=room_name)) # false
    print(checkRoleList(stub,role=[1,1,1,3,1] , room_name=room_name)) # false
    ############################
    

    #### startGame test ####
    role , room_name = startGame(stub,role=[1,1,2,2,1] ,room_name=room_name)
    print("start_game : " , role) # [0,1,2,2,3,3,4]
    ############################

    #### 第一天狼人投票 ####
    print_stage(nextStage(stub,room_name=room_name , stage_name=""))
    
    #### 4投4 5投4 ####
    print(sendUserOperation(stub , user=4 , operation="vote" , target=5 , chat="" , room_name=room_name , stage_name="1-0-werewolf"))
    print(sendUserOperation(stub , user=5 , operation="vote" , target=4 , chat="" , room_name=room_name , stage_name="1-0-werewolf"))
    print(sendUserOperation(stub , user=4 , operation="vote" , target=4 , chat="" , room_name=room_name , stage_name="1-0-werewolf"))

    #### 第一天預言家驗人 ####
    print_stage(nextStage(stub,room_name=room_name , stage_name="1-0-werewolf"))
    #### 0投2 ####
    print(sendUserOperation(stub , user=0 , operation="vote" , target=2 , chat="" , room_name=room_name , stage_name="1-0-seer"))

    #### 第一天女巫 及 預言家結果 ####
    print_stage(nextStage(stub,room_name=room_name , stage_name="1-0-seer"))

    #### 1投4(救人) ####
    print(sendUserOperation(stub , user=1 , operation="vote_or_not" , target=4 , chat="save" , room_name=room_name , stage_name="1-0-witch"))
    print(sendUserOperation(stub , user=1 , operation="vote_or_not" , target=6 , chat="poison" , room_name=room_name , stage_name="1-0-witch")) # false

    ### 平安夜 ###
    print_stage(nextStage(stub,room_name=room_name , stage_name="1-0-check_end1"))

    #### 第一天發言 ####
    print_stage(nextStage(stub,room_name=room_name , stage_name="1-0-dialogue"))

    for i in range(6):
        print_stage(nextStage(stub,room_name=room_name , stage_name="1-0-dialogue"))
        # print(sendUserOperation(stub , user=5 , operation="dialogue" , target=5 , chat="123456" , room_name=room_name , stage_name="1-1-dialogue"))
    
    #### 第一天投票 ####
    #### 0,1,2,3,4,5,6 存活 ####
    print_stage(nextStage(stub,room_name=room_name , stage_name="1-0-vote1"))
    #### 0,1,2,3投6 4,5,6投3 ####
    for i in range(7):
        target = 6 if i<4 else 3
        print(sendUserOperation(stub , user=i , operation="vote_or_not" , target=target , chat="" , room_name=room_name , stage_name="1-1-vote1"))

    print("vote info : " , voteInfo(stub , room_name=room_name , stage_name="1-1-vote1"))

    ### 獵人stage
    print_stage(nextStage(stub,room_name=room_name , stage_name="1-1-hunter2"))
    #### 第一天6獵人死掉發言及發動技能 ####
    #### 0,1,2,3,4,5 存活 ####
    print(sendUserOperation(stub , user=6 , operation="vote_or_not" , target=4 , chat="" , room_name=room_name , stage_name="1-1-hunter2"))
    print(sendUserOperation(stub , user=6 , operation="dialogue" , target=0 , chat="12345" , room_name=room_name , stage_name="1-1-hunter2"))
    ####################

    #### 第一天4被獵人殺掉發言 ####
    #### 0,1,2,3,5 存活 ####
    print_stage(nextStage(stub,room_name=room_name , stage_name="1-1-check_end3"))
    
    #### 第二天狼人投票 ####
    print_stage(nextStage(stub,room_name=room_name , stage_name="1-1-check_end3"))
    #### 5投0 ####
    print(sendUserOperation(stub , user=5 , operation="vote" , target=0 , chat="" , room_name=room_name , stage_name="2-0-werewolf"))

    #### 第二天預言家驗人 ####

    print_stage(nextStage(stub,room_name=room_name , stage_name="2-0-werewolf"))
    ####################

    #### 第二天女巫 ####
    print_stage(nextStage(stub,room_name=room_name , stage_name="2-0-seer"))
    #### 第二天公告誰死了 ####
    print_stage(nextStage(stub,room_name=room_name , stage_name="2-1-dialogue"))
    #### 1,2,3,5 存活 ####
    
    #### 第二天發言 ####
    
    print_stage(nextStage(stub,room_name=room_name , stage_name="2-1-dialogue"))
    print_stage(nextStage(stub,room_name=room_name , stage_name="2-1-dialogue"))
    print_stage(nextStage(stub,room_name=room_name , stage_name="2-1-dialogue"))
    print_stage(nextStage(stub,room_name=room_name , stage_name="2-1-dialogue"))

    
    #### 第二天投票 ####
    print_stage(nextStage(stub,room_name=room_name , stage_name="2-1-vote1"))

    #### 1,2 投5 3,5投3 ####
    for i in [1,2,3,5]:
        target = 5 if i<3 else 3
        print(sendUserOperation(stub , user=i , operation="vote_or_not" , target=target , chat="" , room_name=room_name , stage_name="2-1-vote1"))
    print("vote info : " , voteInfo(stub , room_name=room_name , stage_name="2-1-vote1"))

    #### 第二天二次投票 ####
    print_stage(nextStage(stub,room_name=room_name , stage_name="2-1-vote1"))

    #### 5投3 ####
    print(sendUserOperation(stub , user=5 , operation="vote_or_not" , target=3 , chat="" , room_name=room_name , stage_name="2-1-vote2"))
    

    #### 第二天3死了發表遺言 ####
    print_stage(nextStage(stub,room_name=room_name , stage_name="2-1-vote1"))
    print(sendUserOperation(stub , user=3 , operation="dialogue" , target=0 , chat="12345" , room_name=room_name , stage_name="2-1-check_end3"))
    #### 1,2,5 存活 ####
    
    print_stage(nextStage(stub,room_name=room_name , stage_name="2-1-vote1"))
    #### 第三天狼人投票 ####
    print(sendUserOperation(stub , user=5 , operation="vote" , target=1, chat="" , room_name=room_name , stage_name="3-0-werewolf"))
    #### 5投1 ####
    

    #### 第三天預言家驗人 ####
    print_stage(nextStage(stub,room_name=room_name , stage_name="2-1-check_end3"))
    
    #### 第三天女巫 ####
    print_stage(nextStage(stub,room_name=room_name , stage_name="3-0-werewolf"))
    print(sendUserOperation(stub , user=1 , operation="vote_or_not" , target=5 , chat="poison" , room_name=room_name , stage_name="3-0-witch"))
    
    #### 遊戲結束 ####
    print_stage(nextStage(stub,room_name=room_name , stage_name="3-0-seer"))

if __name__ == '__main__':
    logging.basicConfig()
    run()