import logging

import grpc
import protobufs.werewolf_kill_pb2 as p_wkp
import protobufs.werewolf_kill_pb2_grpc as p_wkpg

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

def run():

    channel = grpc.insecure_channel('localhost:50051')
    stub = p_wkpg.werewolf_killStub(channel)

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


if __name__ == '__main__':
    logging.basicConfig()
    run()