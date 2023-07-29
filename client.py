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


def all_func_testing(stub):

    res = checkRoleList(stub,role=[1,1,2,2,1],room_name="1")
    print(res)
    role , room_name = startGame(stub,role=[1,1,2,2,1],room_name="1")
    print(role,room_name)

    stage , stage_name = nextStage(stub,room_name="1",stage_name="1-0-werewolf")
    print(stage)
    print(stage_name)
    # print(stage_name)

    res = sendUserOperation(stub,user=4,operation="vote",target=1,chat="",room_name="1",stage_name="1-1-werewolf")
    print(res)

    player_state = voteInfo(stub,room_name="1",stage_name="1-0-werewolf")
    print(player_state)

def print_info(user:int,info:str,stage:str):

    print(f"uesr: {user}, operation: {info.operation}, target: {info.target}, description: {info.description}, stage: {stage}")

def print_operation_info(user:int,target:int,description:str):

    return f"user: {user}, target: {target}, description: {description}"


need_send_operation = ["vote","vote_or_not","dialogue"]

def flow(stub,room_name,stage:list,stage_name:str):
    
    for each_operation in stage :
        
        for each_user in each_operation.user:
            print_info(user=each_user,info=each_operation,stage=stage_name)
            if each_operation.operation in need_send_operation:
                # if each_operation
                target = random.choice(each_operation.target)

                if sendUserOperation(stub,user=each_user,operation=each_operation.operation,target=target,chat=each_operation.description,room_name=room_name,stage_name=stage_name):
                    print(f"send successful ,{print_operation_info(user=each_user,target=target,description=each_operation.description)}\n")
                else :
                    print("send failed\n")

def run():

    channel = grpc.insecure_channel('localhost:50051')
    stub = p_wkpg.werewolf_killStub(channel)

    room_name = "1"
    print(checkRoleList(stub,role=[1,1,3,3,1],room_name=room_name))
    
    role , room_name = startGame(stub,role=[1,0,2,2,1],room_name=room_name)
    print(role)
    stage , stage_name = nextStage(stub,room_name="1",stage_name="")
    flow(stub=stub,room_name=room_name,stage=stage,stage_name=stage_name)

    stage , stage_name = nextStage(stub,room_name="1",stage_name="")
    flow(stub=stub,room_name=room_name,stage=stage,stage_name=stage_name)

    stage , stage_name = nextStage(stub,room_name="1",stage_name="")
    flow(stub=stub,room_name=room_name,stage=stage,stage_name=stage_name)

    

    


if __name__ == '__main__':
    logging.basicConfig()
    run()