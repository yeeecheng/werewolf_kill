import argparse
from concurrent import futures
import logging

import grpc
import protobufs.werewolf_kill_pb2 as p_wkp
import protobufs.werewolf_kill_pb2_grpc as p_wkpg

from environment  import env


class WerewolfKillService(p_wkpg.werewolf_killServicer):

    def __init__(self,opt):
        
        self.dict_game_env = dict()
        self.random = opt.random


    def checkRoleList(self,request,context):
        try:
            print("checkRoleList: No need room_name")
            print(f"passing value: role: {request.role}, room_name: {request.room_name}\n///")
            # print("checkRoleList:\n",request)
            return p_wkp.result(result=env.check_role_list(role_list=request.role))
        except:
            context.abort(grpc.StatusCode.NOT_FOUND, "Room Not found")

    def startGame(self,request,context):
        try:
            room_name = request.room_name
            self.dict_game_env[room_name] = env(role_list=request.role,random_assigned=self.random)
            role_list = self.dict_game_env[room_name].start_game()
            
            print(self.__current_state__(room_name=room_name))
            print(f"startGame() passing value: role: {request.role}, room_name: {request.room_name}\n///")
            return p_wkp.roleList(role=role_list,room_name=room_name)
        except:
            context.abort(grpc.StatusCode.NOT_FOUND, "Room Not found")

    def nextStage(self,request,context):
        try:
            room_name = request.room_name
            stage_name = request.stage_name
            stage_return , current_stage =  self.dict_game_env[room_name].stage()
            
            print(self.__current_state__(room_name=room_name))
            print(f"nextStage() passing value: room_name: {room_name}, stage_name: {stage_name}\n///")
            stage = list()
            
            for each_stage in stage_return:
                print(each_stage)
                if each_stage[1] == "end":
                    
                    self.dict_game_env.pop(room_name)
                stage.append(p_wkp.userStage(user=each_stage[0],operation=each_stage[1],target=each_stage[2],description=each_stage[3]))
            
            
            return p_wkp.stage(stage=stage,stage_name=current_stage)
        except:
            context.abort(grpc.StatusCode.NOT_FOUND, "Room Not found")

    def sendUserOperation(self,request,context):
        
        try:
            room_name = request.room.room_name
            stage_name = request.room.stage_name
            print(self.__current_state__(room_name=room_name))
            player_number = request.user
            operation = request.operation
            target = request.target
            description = request.chat
            print(f"sendUserOperation() passing value: player_number: {player_number}, operation: {operation}, target: {target}, description: {description}, stage_name: {stage_name}, room_name:{room_name}\n///")


            return p_wkp.result(result=self.dict_game_env[room_name].player_operation(
                    id=player_number,
                    operation=operation,
                    target_id=target,
                    description=description,
                    current_stage=stage_name))
        except:
            context.abort(grpc.StatusCode.NOT_FOUND, "Room Not found")
        


    def voteInfo(self,request,context):
        
        try:
            room_name = request.room_name
            stage_name = request.stage_name
            print(self.__current_state__(room_name=room_name))
            print(f"voteInfo() passing value: room_name: {room_name}, stage_name: {stage_name}\n///")
            list_player_voted = self.dict_game_env[room_name].check_player_voted_state()
            return p_wkp.playerState(state=list_player_voted)
        except:
            context.abort(grpc.StatusCode.NOT_FOUND, "Room Not found")



    def __current_state__(self,room_name):
        
        info = self.dict_game_env[room_name].get_game_env()

        return f"\nroom {room_name}{info}"

def parse_opt():

    parser =  argparse.ArgumentParser()
    parser.add_argument("--random",type=bool,default=False)

    return parser.parse_args()


def serve(opt):
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    p_wkpg.add_werewolf_killServicer_to_server(
        WerewolfKillService(opt), server
    )  
    
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig()
    opt = parse_opt()
    serve(opt)