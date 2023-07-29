from concurrent import futures
import logging

import grpc
import protobufs.werewolf_kill_pb2 as p_wkp
import protobufs.werewolf_kill_pb2_grpc as p_wkpg

from environment  import env


class WerewolfKillService(p_wkpg.werewolf_killServicer):

    def __init__(self):
        
        self.dict_game_env = dict()

    def checkRoleList(self,request,context):
        print("checkRoleList:\n",request)
        return p_wkp.result(result=env.check_role_list(role_list=request.role))


    def startGame(self,request,context):
        print("startGame:\n",request)
        room_name = request.room_name
        self.dict_game_env[room_name] = env(roles=request.role)

        role_list = self.dict_game_env[room_name].start_game()
        return p_wkp.roleList(role=role_list,room_name=room_name)

    def nextStage(self,request,context):
        print("nextStage:\n",request)
        room_name = request.room_name
        stage_name = request.stage_name
        stage_return , current_stage =  self.dict_game_env[room_name].stage()
        stage = list()
        for each_stage in stage_return:

            if each_stage[1] == "end":
                self.dict_game_env[room_name].pop(room_name)

            stage.append(p_wkp.userStage(user=each_stage[0],operation=each_stage[1],target=each_stage[2],description=each_stage[3]))
        
        
        return p_wkp.stage(stage=stage,stage_name=current_stage)

    def sendUserOperation(self,request,context):
        print("sendUserOperation:\n",request)
        room_name = request.room.room_name
        stage_name = request.room.stage_name
        player_number = request.user
        operation = request.operation
        target = request.target
        description = request.chat

        return p_wkp.result(result=self.dict_game_env[room_name].player_operation(
                player_number=player_number,
                operation=operation,
                target_player_number=target,
                description=description,
                current_stage=stage_name))
        


    def voteInfo(self,request,context):
        print("voteInfo:\n",request)
        room_name = request.room_name
        stage_name = request.stage_name
        list_player_voted = self.dict_game_env[room_name].check_player_voted_state()

        return p_wkp.playerState(state=list_player_voted)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    p_wkpg.add_werewolf_killServicer_to_server(
        WerewolfKillService(), server
    )  
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig()
    serve()